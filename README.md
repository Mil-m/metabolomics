# metabolomics

This repository, in collaboration with **mtbls-service**, provides functionalities to interact with MetaboLights, Metabolomics Workbench and Metabobank study data.

- MetaboLights service: Provides user login functionality, detailed study and assays information retrieval, and downloading study-related result files via its API.
- Metabolomics Workbench service: Allows viewing of study details and its assays retrieved via its API.
- Metabobank service: Integrates with its API for retrieving and downloading study-related files.

---
# MetaboLights Service

## General Features

- **Retrieval of Study Metadata:**  
  Retrieve metadata for studies, including the study title and description.

- **Assay Data Extraction:**  
  Access detailed assay information, including:
  - **Assay Number**
  - **Measurement**
  - **Technology**
  - **Platform**
  - **File Name**
  - **Reported Metabolite Names**
  - A list of **Raw Data File Names** used in the assay

- **Result Files Access (Authenticated):**  
  Upon successful authentication via the login form, you gain access to additional study result files (displayed in the *Result Files* section) that can be downloaded through provided links.

## Endpoints

- **Main Page:**  
  `/metabolomics`  
  The main page where you can access the study selection and authentication form.

- **MetaboLights Study Details:**  
  `/metabolights_get_study_details_info/<study_id>`  
  A page that displays detailed study data for a given MetaboLights study, including metadata, assay data, and (if authenticated) result files.

---

# Metabolomics Workbench Service

## General Features

- **Study Metadata Retrieval:**  
  Retrieve key metadata for studies, including:
  - **Study Title**
  - **Species**
  - **Institute**
  - **Analysis Type**
  - **Number of Samples**

- **Assay Data Extraction:**  
  Access detailed assay information for each study, including:
  - **Assay Number**
  - **Analysis Id**
  - **Analysis Summary**
  - **Reported Metabolite Name**
  - **Refmet Name**

## Endpoints

- **Metabolomics Workbench Study Details:**  
  `/metabolomics_workbench_get_study_details_info/<study_id>`  
  A page that displays detailed study data for a given Metabolomics Workbench study, including study metadata and assay data.

---

# Metabobank Service

## General Features

- **File Listings:**  
  Access detailed study file information, including:
  - **Results Files:** A list of result files, which can be downloaded via provided links.
  - **Raw Files:** A list of raw data files used in the study.

## Endpoints

- **Metabobank Study Details:**  
  `/metabobank_get_study_details_info/<study_id>`  
  A page that displays detailed study data for a given Metabobank study, including the lists of results files and raw files.

---

# Running the Project

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Using the Flask CLI:**
- **Standard Run:**
 ```bash
export FLASK_APP=api.py && flask run
 ```
 This starts the application without explicitly enabling development features.

- **Development Mode:**
 ```bash
 export FLASK_APP=api.py && export FLASK_ENV=development && flask run
 ```
 By setting `FLASK_ENV=development`, Flask:
   - Enables debug mode (auto-reloading on code changes)
   - Provides detailed error messages
   - Automatically re-imports modules when changes are detected

The service will be available at:
http://127.0.0.1:5000/metabolomics

**Running in Docker:**
```bash
docker build -t metabolomics-app .
docker run -p 5000:5000 metabolomics-app
```

---

**Unit Tests (made by ChatGPT o3-mini)**

```bash
cd ./tests && python3 -m unittest test_app.py
```
