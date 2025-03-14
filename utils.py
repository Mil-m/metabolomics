import pprint


def fetch_metadata_and_result_files(assays_content):
    
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
            'file name': assays_el['fileName']
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
        assays_el_data[number]['raw data file names'] = raw_data_lst
        
        assays_lst_data.append(assays_el_data)
        
    result_data['assays'] = assays_lst_data
    
    return result_data
