import pprint


def fetch_metadata_and_result_files(assays_content):
    """

    :param assays_content:
    :return:
    """
    
    result_data = {}
    
    # dataset’s title, description
    result_data['Dataset Title'] = assays_content['title']
    result_data['Dataset Description'] = assays_content['description']
    
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
            metabolite_assignment_file_name = assays_el['metaboliteAssignment']['metaboliteAssignmentFileName']
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
