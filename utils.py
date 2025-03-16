import functools
import time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import requests

from logging_config import logger

_cache = {}
CACHE_EXPIRY = 3600


def cached(expiry=CACHE_EXPIRY):
    """
    Decorator to cache function results with a specified expiry time.
    :param expiry: the lifetime of the cache in seconds
    :return: a decorator that caches the function's result
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            if key in _cache:
                result, timestamp = _cache[key]
                if time.time() - timestamp < expiry:
                    return result

            result = func(*args, **kwargs)
            _cache[key] = (result, time.time())
            return result

        return wrapper

    return decorator


@cached()
def fetch_study_list(api_url: str, source: str, api_session: requests.Session):
    """
    Fetches a list of studies from the given API URL and returns a list of tuples.
    :param api_url: current url
    :param source: current data source; acceptable values: 'metabolights', 'workbench', 'metabobank'
    :param api_session: current session
    :return: a list of tuples (value, label) to be used for the selection in the user form
    """

    logger.info(f"Fetching study list from {source} (URL: {api_url})")

    # process the response based on the source
    def process_response(content, is_ok, source):
        study_lst = []
        if not is_ok or not content:
            return []

        try:
            if source == 'metabolights':
                import json
                json_data = json.loads(content)
                study_lst = json_data.get('content', [])
            elif source == 'workbench':
                import json
                json_data = json.loads(content)
                study_lst = [study['study_id'] for study in json_data.values() if 'study_id' in study]
            elif source == 'metabobank':
                soup = BeautifulSoup(content, "html.parser")
                for link in soup.find_all("a"):
                    href = link.get("href")
                    if href and href.endswith("/"):
                        if href.startswith('MTBK'):
                            study_lst.append(href.strip("/"))
            return [(study, study) for study in study_lst]
        except Exception as e:
            logger.error(f"Error processing response from {source}: {e}")
            return []

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: api_session.get(api_url))
        try:
            response = future.result(timeout=30)
            if response.ok:
                return process_response(response.text, True, source)
        except Exception as e:
            logger.info(f"Async fetch failed: {e}")

    try:
        response = api_session.get(api_url)
        if response.ok:
            return process_response(response.text, True, source)
    except Exception as e:
        logger.info(f"Sync fetch failed: {e}")

    return []


def metabolights_get_study_details(study_id: str, api_session: requests.Session):
    """
    Fetches study details from MetaboLights for the given study.
    :param study_id: current study id
    :param api_session: current session
    :return: a dictionary of the study data and the HTTP status code
    """

    study_url = f"https://www.ebi.ac.uk/metabolights/ws/studies/public/study/{study_id}"

    try:
        response = api_session.get(study_url)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred: {e}")
        return {}, 500

    if response.ok:
        return response.json()['content'], 200
    else:
        return {}, response.status_code


def metabolights_fetch_metadata_and_raw_files(assays_content: dict):
    """
    Extracts metadata and raw file names from the study content returned by MetaboLights.
    :param assays_content: a dictionary containing study data from MetaboLights
    :return: a dictionary with the study title, description, and a list of assays with their metadata and raw file names
    """

    result_data = {}
    
    # dataset’s title, description
    result_data['title'] = assays_content['title']
    result_data['description'] = assays_content['description']
    
    assays_lst_data = []
    
    assays_data=assays_content['assays']
    for assays_el in assays_data:
        assays_el_data = {}
        
        # a. metadata and result file names for each dataset
        number = assays_el['assayNumber']
        assays_el_data[number] = {}
        assays_el_data[number]['metadata'] = {
            'measurement': assays_el['measurement'],
            'technology': assays_el['technology'],
            'platform': assays_el['platform'],
            'assay_number': assays_el['assayNumber'],
            'file_name': assays_el['fileName']
        }
        
        # d. reported metabolite names
        if 'metaboliteAssignment' in assays_el:
            reported_metabolite_names = assays_el['metaboliteAssignment']['metaboliteAssignmentLines']
            assays_el_data[number]['reported_metabolite_names'] = reported_metabolite_names
        
        # c. raw data file names
        assays_data = assays_el['assayTable']['data']
        raw_data_lst = []
        for assays_info in assays_data:
            raw_data_lst.append([el[len('FILES/'):] for el in assays_info if el.startswith('FILES/')])
        assays_el_data[number]['raw_data_file_names'] = raw_data_lst
        
        assays_lst_data.append(assays_el_data)
        
    result_data['assays'] = assays_lst_data
    
    return result_data


def metabolights_fetch_result_files(study_id: str, api_token: str, api_session: requests.Session):
    """
    Fetches the list of result files for a given MetaboLights study.
    Will be executed only if the client logged-in into the MetaboLights.
    :param study_id: current study id
    :param api_token: current api token
    :param api_session: current session
    :return: list of the result files (or an empty list) and the HTTP status code
    """

    url = f"https://www.ebi.ac.uk/metabolights/ws/studies/{study_id}/files?include_raw_data=false"

    request_data = {
        'study_id': study_id,
        'user_token': api_token
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = api_session.get(url, json=request_data, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred: {e}")
        return [], 500

    if response.ok:
        response_data = response.json()
        response_files = [el['file'] for el in response_data['study']]
        return response_files, 200
    else:
        return [], response.status_code


def metabolomics_workbench_get_study_details(study_id: str, api_session: requests.Session):
    """
    Fetches study details from Metabolomics Workbench for a given study, including assays data.
    :param study_id: current study id
    :param api_session: current session
    :return: dictionary with study details and the HTTP status code
    """

    study_url = f"https://www.metabolomicsworkbench.org/rest/study/study_id/{study_id}/summary"

    try:
        response = api_session.get(study_url)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred: {e}")
        return {}, 500

    if response.ok:
        study_info_data = response.json()

        metabolites_url = f"https://www.metabolomicsworkbench.org/rest/study/study_id/{study_id}/metabolites"
        try:
            metabolites_response = api_session.get(metabolites_url)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error occurred: {e}")
            return {}, 500

        if metabolites_response.ok:
            metabolites_data = metabolites_response.json()
            if metabolites_data:
                assays_lst_data = []
                if all(key.isdigit() for key in metabolites_data.keys()):
                    for key, record in metabolites_data.items():
                        assays_el_data = {}
                        assays_el_data[key] = {
                            'metadata': {
                                'analysis_id': record.get('analysis_id'),
                                'analysis_summary': record.get('analysis_summary'),
                                'reported_metabolite_name': record.get('metabolite_name'),
                                'refmet_name': record.get('refmet_name')
                            }
                        }
                        assays_lst_data.append(assays_el_data)
                else:
                    assays_el_data = {}
                    assays_el_data[1] = {
                        'metadata': {
                            'analysis_id': metabolites_data.get('analysis_id'),
                            'analysis_summary': metabolites_data.get('analysis_summary'),
                            'reported_metabolite_name': metabolites_data.get('metabolite_name'),
                            'refmet_name': metabolites_data.get('refmet_name')
                        }
                    }
                    assays_lst_data.append(assays_el_data)

                study_info_data['assays'] = assays_lst_data

            return study_info_data, 200
        else:
            return {}, metabolites_response.status_code
    else:
        return {}, response.status_code


def metabobank_fetch_result_and_raw_files(study_id: str, api_session: requests.Session):
    """
    Fetches lists of result files and raw data files for a given Metabobank study.
    :param study_id: current study id
    :param api_session: current session
    :return: A tuple containing a pair of lists
             ([list of result files], [list of raw files]) and the HTTP status code
    """

    def get_directories(url: str):
        directories = []

        response = api_session.get(url)
        if response.status_code != 200:
            return [], response.status_code

        soup = BeautifulSoup(response.text, "lxml")
        for link in soup.find_all("a"):
            href = link.get("href")
            if href:
                directories.append(href.strip("/"))

        return directories, 200

    def get_result_files(url: str):
        results_files, _ = get_directories(url=f"{url}OtherData/")
        results_files = [f"{url}OtherData/{el}" for el in results_files if el.endswith('txt')]
        return results_files

    def get_raw_files(url: str):
        raw_files, _ = get_directories(url=f"{url}Rawdata/")
        if len(raw_files) == 0:
            raw_files, _ = get_directories(url=f"{url}rawdata/")
        raw_files_lst = [el for el in raw_files if el.endswith('cdf') or el.endswith('zip')]
        if len(raw_files_lst) == 0:
            for dir in raw_files:
                batch, _ = get_directories(url=f"{base_url}Rawdata/{dir}/")
                raw_files_lst += [el for el in batch if el.endswith('cdf') or el.endswith('zip')]
        return raw_files_lst

    def get_raw_result_files(url: str):
        directories, resp_code = get_directories(url=url)
        results_files = []
        raw_files = []

        if 'OtherData' in directories:
            results_files = get_result_files(url=url)
        if 'Rawdata' in directories:
            raw_files = get_raw_files(url=url)
        else:
            results_files = [f"{url}{el}" for el in directories if el.endswith('txt')]
            if 'raw' in directories:
                raw_files = get_raw_files(url=f"{url}raw/")

        return directories, results_files, raw_files, resp_code

    base_url = f"https://ddbj.nig.ac.jp/public/metabobank/study/{study_id}/"

    directories, results_files, raw_files, resp_code = get_raw_result_files(url=base_url)

    e_directories = [el for el in directories if el.startswith('E')]
    for e_dir in e_directories:
        url = f"{base_url}{e_dir}/"
        _, e_results_files, e_raw_files, e_resp_code = get_raw_result_files(url=url)
        results_files += e_results_files
        raw_files += e_raw_files

    return (results_files, raw_files), resp_code


def metabobank_get_study_details(study_id: str, api_session: requests.Session):
    """
    Fetches study details from Metabobank, including lists of result files and raw data files.
    :param study_id: current study id
    :param api_session: current session
    :return: dictionary with study details and the HTTP status code
    """

    study_info_data = {}

    files, resp_code = metabobank_fetch_result_and_raw_files(study_id=study_id, api_session=api_session)

    study_info_data['results_files'] = files[0]
    study_info_data['raw_files'] = files[1]

    return study_info_data, resp_code
