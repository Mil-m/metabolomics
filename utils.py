import pprint


def fetch_study_list(api_url: str, source: str, api_session):
    """

    :param api_url:
    :param source:
    :param api_session:
    :return:
    """
    response = api_session.get(api_url)
    if response.ok:
        json_data = response.json()
        if source == 'metabolights':
            study_lst = json_data.get('content', [])
        elif source == 'workbench':
            study_lst = [study['study_id'] for study in json_data.values() if 'study_id' in study]
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


def fetch_metadata_and_raw_files(assays_content):
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


def fetch_result_files(study_id: str, api_token: str, api_session):
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
