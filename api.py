import io
import logging
import secrets
import zipfile
import requests
from flask import Flask, jsonify, render_template, url_for, redirect, request, flash, session, send_file
from flask_bootstrap import Bootstrap

from forms import MetabolightsForm, MetabolightsLoginForm, MetabolomicsWorkbenchForm, MetabobankForm
from utils import (metabolights_fetch_metadata_and_raw_files, metabolights_fetch_result_files, fetch_study_list,
                   metabolights_get_study_details, metabolomics_workbench_get_study_details,
                   metabobank_get_study_details)
from logging_config import logger

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
Bootstrap(app)

app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)

api_session = requests.Session()


@app.route('/')
def index():
    """
    Redirects the root URL to the metabolomics page.
    :return: a redirect response to the '/metabolomics' endpoint
    """
    return redirect(url_for('metabolomics'))


@app.route('/metabolights_login', methods=['POST'], strict_slashes=False)
def metabolights_login(email: str, secret: str):
    """
    MetaboLights login function used in the 'metabolights-login' form
    :param email: user email
    :param secret: user password
    :return: a JSON response with the 'api_token' and 'jwt_token' and HTTP status code
    """
    login_url = "https://www.ebi.ac.uk/metabolights/ws/auth/login"

    login_data = {
        "email": email,
        "secret": secret
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = api_session.post(login_url, json=login_data, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred: {e}")
        return {}, 500

    if response.ok:
        api_token = response.json()['content']['apiToken']

        jwt_token = response.headers['jwt']
        jwt_data = {
            "Jwt": jwt_token,
            "User": "mansurova@ebi.ac.uk"
        }
        response_jwt = api_session.post("https://www.ebi.ac.uk/metabolights/ws/auth/validate-token", json=jwt_data)

        if response_jwt.ok:
            return jsonify({
                "api_token": api_token,
                "jwt_token": jwt_token
            }), 200
        else:
            logger.error(f"error in jwt validation; response code:{response_jwt.status_code}")
            flash(f"error in jwt validation; response code:{response_jwt.status_code}", 'success')
            return jsonify({
                "api_token": api_token,
                "jwt_token": ""
            }), 200
    else:
        return jsonify({
            "api_token": "",
            "jwt_token": ""
        }), response.status_code


@app.route('/metabolights_get_study_details_info/<study_id>', methods=['GET'], strict_slashes=False)
def metabolights_get_study_details_info(study_id: str):
    """
    Retrieves study details from MetaboLights and renders the study information page.
    :param study_id: current study id
    :return: an HTML page rendered with study metadata and raw files;
             if available, includes result file names when the API token is present in the session
             with an option of download them
    """
    study_details, resp_code = metabolights_get_study_details(study_id=study_id, api_session=api_session)
    if resp_code == 200:
        study_info_data = metabolights_fetch_metadata_and_raw_files(assays_content=study_details)
        if 'api_token' in session:
            study_result_files, _ = metabolights_fetch_result_files(
                study_id=study_id,
                api_token=session['api_token'],
                api_session=api_session
            )
            study_info_data['result_file_names'] = study_result_files
        return render_template('metabolights_study_info.html', data=study_info_data, study_id=study_id)
    else:
        return render_template('metabolights_study_info.html', data={}, study_id=study_id), resp_code


@app.route('/metabolights_download_file/<study_id>/<filename>', methods=['GET'], strict_slashes=False)
def metabolights_download_file(study_id: str, filename: str):
    """
    Downloads a specified file for a given MetaboLights study.
    :param study_id: current study id
    :param filename: filename of the current file
    :return: a file response; if the filename is 'metadata', the file is wrapped into a ZIP archive before sending;
             otherwise, the file content is sent directly; in case of an error, returns the HTTP status code
    """
    url = f"https://www.ebi.ac.uk/metabolights/ws/studies/{study_id}/download"

    request_data = {
        'study_id': study_id,
        'file': filename
    }

    try:
        response = api_session.get(url, params=request_data, stream=True)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred: {e}")
        return {}, 500

    if response.ok:
        if filename == 'metadata':
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr('metadata.zip', response.content)

            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                as_attachment=True,
                attachment_filename='metadata.zip',
                mimetype='application/zip'
            )
        else:
            file_data = response.content
            return send_file(
                io.BytesIO(file_data),
                as_attachment=True,
                attachment_filename=filename
            )
    else:
        return response.status_code


@app.route('/metabolomics_workbench_get_study_details_info/<study_id>', methods=['GET'], strict_slashes=False)
def metabolomics_workbench_get_study_details_info(study_id: str):
    """
    Retrieves study details from the Metabolomics Workbench and renders the corresponding study information page.
    :param study_id: current study id
    :return: an HTML page rendered with the study information if retrieval is successful; otherwise,
             an HTML page with empty data and the relevant HTTP status code.
    """
    study_info_data, resp_code = metabolomics_workbench_get_study_details(study_id=study_id, api_session=api_session)
    if resp_code == 200:
        return render_template('metabolomics_workbench_study_info.html', data=study_info_data, study_id=study_id)
    else:
        return render_template('metabolomics_workbench_study_info.html', data={}, study_id=study_id), resp_code

@app.route('/metabobank_get_study_details_info/<study_id>', methods=['GET'], strict_slashes=False)
def metabobank_get_study_details_info(study_id: str):
    """
    Retrieves study details from the Metabobank and renders the corresponding study information page.
    :param study_id: current study id
    :return: an HTML page rendered with the study information if retrieval is successful; otherwise,
             an HTML page with empty data and the relevant HTTP status code.
    """
    study_info_data, resp_code = metabobank_get_study_details(study_id=study_id, api_session=api_session)
    if resp_code == 200:
        return render_template('metabobank_study_info.html', data=study_info_data, study_id=study_id)
    else:
        return render_template('metabobank_study_info.html', data={}, study_id=study_id), resp_code


@app.route('/metabobank_download_file/<path:file_url>', methods=['GET'], strict_slashes=False)
def metabobank_download_file(file_url: str):
    """
    Downloads a specified file for a given Metabobank study.
    :param file_url: url of the current file
    :return: the file content is sent directly; in case of an error, returns the HTTP status code
    """
    try:
        response = api_session.get(url=file_url, stream=True)
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error occurred: {e}")
        return {}, 500

    if response.ok:
        file_name = file_url.split('/')[-1]
        return send_file(
            io.BytesIO(response.content),
            as_attachment=True,
            attachment_filename=file_name
        )
    else:
        logger.error(f"Error downloading file: {file_url}")
        flash(f"Error downloading file: {file_url}", "error")
        return response.status_code


def fetch_metabolights_studies():
    api_url = "https://www.ebi.ac.uk/metabolights/ws/studies"
    return fetch_study_list(api_url=api_url, source='metabolights', api_session=api_session)


def fetch_workbench_studies():
    api_url = "https://www.metabolomicsworkbench.org/rest/study/study_id/ST/summary"
    return fetch_study_list(api_url=api_url, source='workbench', api_session=api_session)


def fetch_metabobank_studies():
    api_url = "https://ddbj.nig.ac.jp/public/metabobank/study/"
    return fetch_study_list(api_url=api_url, source='metabobank', api_session=api_session)


@app.route('/fetch_metabolights_studies')
def fetch_metabolights_studies_json():
    return jsonify(fetch_metabolights_studies())


@app.route('/fetch_workbench_studies')
def fetch_workbench_studies_json():
    return jsonify(fetch_workbench_studies())


@app.route('/fetch_metabobank_studies')
def fetch_metabobank_studies_json():
    return jsonify(fetch_metabobank_studies())


@app.route('/metabolomics', methods=['GET', 'POST'])
def metabolomics():
    """
    Displays the main page containing forms for selecting studies and logging in.
    :return: an HTML page rendered with the study selection and login forms or
             a redirect response based on the form submission
    """
    metabolights_login_form = MetabolightsLoginForm()
    metabolights_form = MetabolightsForm()
    metabolomicsworkbench_form = MetabolomicsWorkbenchForm()
    metabobank_form = MetabobankForm()

    if request.method == 'POST':
        form_type = request.form.get('form-name')

        if form_type == 'metabolights-selection':
            metabolights_form.study.choices = fetch_metabolights_studies()
        elif form_type == 'metabolomicsworkbench-selection':
            metabolomicsworkbench_form.study.choices = fetch_workbench_studies()
        elif form_type == 'metabobank-selection':
            metabobank_form.study.choices = fetch_metabobank_studies()

        if form_type == 'metabolights-login':
            email = request.form.get('email')
            password = request.form.get('password')
            response_data, resp_code = metabolights_login(email=email, secret=password)
            response_json_data = response_data.get_json()
            if resp_code == 200:
                session['api_token'] = response_json_data['api_token']
                session['jwt_token'] = response_json_data['jwt_token']
                flash('You logged in MetaboLights successfully!', 'success')
                return redirect(url_for('metabolomics'))
            else:
                flash('Wrong email or password for MetaboLights, try again.', 'error')
                return redirect(url_for('metabolomics'))
        elif form_type == 'metabolights-selection' and metabolights_form.validate_on_submit():
            selected_study = metabolights_form.study.data
            return redirect(url_for('metabolights_get_study_details_info', study_id=selected_study))
        elif form_type == 'metabolomicsworkbench-selection' and metabolomicsworkbench_form.validate_on_submit():
            selected_study = metabolomicsworkbench_form.study.data
            return redirect(url_for('metabolomics_workbench_get_study_details_info', study_id=selected_study))
        elif form_type == 'metabobank-selection' and metabobank_form.validate_on_submit():
            selected_study = metabobank_form.study.data
            return redirect(url_for('metabobank_get_study_details_info', study_id=selected_study))

    return render_template(
        'studies.html',
        metabolights_form=metabolights_form,
        metabolights_login_form=metabolights_login_form,
        metabolomicsworkbench_form=metabolomicsworkbench_form,
        metabobank_form=metabobank_form
    )


if __name__ == '__main__':
    app.run()
