import secrets
import logging
import requests
from flask import Flask, jsonify, render_template, url_for, redirect
from flask_bootstrap import Bootstrap

from forms import MetabolightsStudyInfo
from utils import fetch_metadata_and_result_files


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
Bootstrap(app)

app.logger.setLevel(logging.INFO)

session = requests.Session()


@app.route('/')
def index():
    return redirect(url_for('metabolomics'))


@app.route('/metabolights_login', methods=['POST'], strict_slashes=False)
def metabolights_login():
    """
    """
    login_url = "https://www.ebi.ac.uk/metabolights/ws/auth/login"

    login_data = {
        "email": "",
        "secret": ""
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = session.post(login_url, json=login_data, headers=headers)

    if response.ok:
        api_token = response.json()['content']['apiToken']

        jwt_token = response.headers['jwt']
        jwt_data = {
            "Jwt": jwt_token,
            "User": "mansurova@ebi.ac.uk"
        }
        response_jwt = session.post("https://www.ebi.ac.uk/metabolights/ws/auth/validate-token", json=jwt_data)

        if response_jwt.ok:
            return jsonify({
                "api_token": api_token,
                "jwt_token": jwt_token
            }), 200
        else:
            print(f"error in jwt validation; response code:{response_jwt.status_code}")
            return jsonify({
                "api_token": api_token,
                "jwt_token": ""
            }), 200
    else:
        return jsonify({
            "api_token": "",
            "jwt_token": ""
        }), response.status_code


@app.route('/metabolights_get_study_details/<study_id>', methods=['GET'], strict_slashes=False)
def metabolights_get_study_details(study_id: str):
    """
    """
    study_url = f"https://www.ebi.ac.uk/metabolights/ws/studies/public/study/{study_id}"
    response = session.get(study_url)

    if response.ok:
        return jsonify(response.json()['content']), 200
    else:
        return jsonify([]), response.status_code


@app.route('/metabolights_get_study_details_info/<study_id>', methods=['GET'], strict_slashes=False)
def metabolights_get_study_details_info(study_id: str):
    """
    """
    study_details, resp_code = metabolights_get_study_details(study_id=study_id)
    if resp_code == 200:
        study_info_data = fetch_metadata_and_result_files(assays_content=study_details.get_json())
        return render_template('study_info.html', data=study_info_data)
    else:
        return render_template('study_info.html', data={}), resp_code


@app.route('/metabolomics', methods=['GET', 'POST'])
def metabolomics():
    metabolights_form = MetabolightsStudyInfo()
    studies_response = session.get("https://www.ebi.ac.uk/metabolights/ws/studies")
    if studies_response.ok:
        studies_lst = studies_response.json()['content']
    else:
        studies_lst = []
    metabolights_form.study.choices = [(study, study) for study in studies_lst]

    if metabolights_form.validate_on_submit():
        selected_study = metabolights_form.study.data
        return redirect(url_for('metabolights_get_study_details_info', study_id=selected_study))

    return render_template('studies.html', form=metabolights_form)


@app.route('/metabolights_download_data', methods=['GET'], strict_slashes=False)
def metabolights_download_data(outp_dir: str):
    return


if __name__ == '__main__':
    app.run(debug=True)
