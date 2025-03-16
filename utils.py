from bs4 import BeautifulSoup


def fetch_study_list(api_url: str, source: str, api_session):
    """

    :param api_url:
    :param source:
    :param api_session:
    :return:
    """
    response = api_session.get(api_url)
    study_lst = []
    if response.ok:
        if source == 'metabolights':
            json_data = response.json()
            study_lst = json_data.get('content', [])
        elif source == 'workbench':
            json_data = response.json()
            study_lst = [study['study_id'] for study in json_data.values() if 'study_id' in study]
        elif source == 'metabobank':
            soup = BeautifulSoup(response.text, "lxml")
            for link in soup.find_all("a"):
                href = link.get("href")
                if href and href.endswith("/"):
                    if href.startswith('MTBK'):
                        study_lst.append(href.strip("/"))
        return [(study, study) for study in study_lst]
    return []


def metabolights_get_study_details(study_id: str, api_session):
    """

    :param study_id:
    :param api_session:
    :return:
    """

    study_url = f"https://www.ebi.ac.uk/metabolights/ws/studies/public/study/{study_id}"
    response = api_session.get(study_url)

    if response.ok:
        return response.json()['content'], 200
    else:
        return {}, response.status_code


def metabolights_fetch_metadata_and_raw_files(assays_content):
    """

    :param assays_content:
    :return:
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


def metabolights_fetch_result_files(study_id: str, api_token: str, api_session):
    """

    :param study_id:
    :param api_token:
    :param api_session:
    :return:
    """

    url = f"https://www.ebi.ac.uk/metabolights/ws/studies/{study_id}/files?include_raw_data=false"

    request_data = {
        'study_id': study_id,
        'user_token': api_token
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = api_session.get(url, json=request_data, headers=headers)

    if response.ok:
        response_data = response.json()
        response_files = [el['file'] for el in response_data['study']]
        return response_files, 200
    else:
        return [], response.status_code


def metabolomics_workbench_get_study_details(study_id: str, api_session):
    """

    :param study_id:
    :param api_session:
    :return:
    """

    study_url = f"https://www.metabolomicsworkbench.org/rest/study/study_id/{study_id}/summary"
    response = api_session.get(study_url)
    if response.ok:
        study_info_data = response.json()

        metabolites_url = f"https://www.metabolomicsworkbench.org/rest/study/study_id/{study_id}/metabolites"
        metabolites_response = api_session.get(metabolites_url)
        if metabolites_response.ok:
            metabolites_data = metabolites_response.json()
            if metabolites_data:
                assays_lst_data = []
                for number, assays_el in metabolites_data.items():
                    assays_el_data = {}
                    assays_el_data[number] = {}

                    assays_el_data[number]['metadata'] = {
                        'analysis_id': assays_el['analysis_id'],
                        'analysis_summary': assays_el['analysis_summary'],
                        'reported_metabolite_name': assays_el['metabolite_name'],
                        'refmet_name': assays_el['refmet_name']
                    }

                    assays_lst_data.append(assays_el_data)

                study_info_data['assays'] = assays_lst_data

            return study_info_data, 200
        else:
            return {}, metabolites_response.status_code
    else:
        return {}, response.status_code


def metabobank_fetch_result_and_raw_files(study_id: str, api_session):
    """

    :param study_id:
    :param api_session:
    :return:
    """

    def get_directories(url: str):
        """

        :param url:
        :return:
        """
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
        results_files = [el for el in results_files if el.endswith('txt')]
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
            results_files = [el for el in directories if el.endswith('txt')]
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


def metabobank_get_study_details(study_id: str, api_session):
    """

    :param study_id:
    :param api_session:
    :return:
    """

    study_info_data = {}

    files, resp_code = metabobank_fetch_result_and_raw_files(study_id=study_id, api_session=api_session)

    study_info_data['results_files'] = files[0]
    study_info_data['raw_files'] = files[1]

    return study_info_data, resp_code
