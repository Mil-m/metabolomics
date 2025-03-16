import os
import sys
import unittest
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import app, api_session


class DummyResponse:
    def __init__(self, ok=True, status_code=200, content=b"", json_data=None):
        self.ok = ok
        self.status_code = status_code
        self.content = content
        self._json_data = json_data

    def json(self):
        return self._json_data if self._json_data is not None else {}

    @property
    def text(self):
        return json.dumps(self._json_data) if self._json_data is not None else ""


def dummy_get(url, **kwargs):
    if "metabolights/ws/studies/public/study/MTBLS105" in url:
        fake_study = {
            "title": "MetaboLights Study",
            "description": "Study description",
            "assays": [
                {
                    "assayNumber": "1",
                    "measurement": "Measurement Test",
                    "technology": "Tech Test",
                    "platform": "Platform Test",
                    "fileName": "result.txt",
                    "assayTable": {"data": [["FILES/rawfile.cdf"]]}
                }
            ]
        }
        return DummyResponse(ok=True, status_code=200, json_data={'content': fake_study})
    elif "metabolights/ws/studies" in url:
        fake_list = {"content": ["MTBLS105", "MTBLS106"]}
        return DummyResponse(ok=True, status_code=200, json_data=fake_list)
    elif "metabolomicsworkbench.org/rest/study/study_id/ST/summary" in url:
        fake_data = {"study_id": "ST_TEST", "title": "Workbench Study", "assays": []}
        return DummyResponse(ok=True, status_code=200, json_data=fake_data)
    elif "ddbj.nig.ac.jp/public/metabobank/study/MTBKS6" in url and "OtherData" not in url:
        fake_study_info = {
            "results_files": ["https://ddbj.nig.ac.jp/public/metabobank/study/MTBKS6/OtherData/file1.txt"],
            "raw_files": ["raw1.cdf"]
        }
        return DummyResponse(ok=True, status_code=200, json_data=fake_study_info)
    elif "ddbj.nig.ac.jp/public/metabobank/study/MTBKS6/OtherData" in url:
        if "060510root_noise3NIST_TEST.txt" in url:
            return DummyResponse(ok=False, status_code=404, content=b"")
        else:
            return DummyResponse(ok=True, status_code=200, content=b"Fake file content")
    return DummyResponse(ok=True, status_code=200, json_data={})


class FlaskEndpointsTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        api_session.get = dummy_get

    def test_index_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_metabolights_get_study_details_info(self):
        response = self.client.get('/metabolights_get_study_details_info/MTBLS105')
        self.assertEqual(response.status_code, 200)

    def test_metabolights_download_file(self):
        response = self.client.get('/metabolights_download_file/MTBLS105/somefile.txt')
        self.assertEqual(response.status_code, 200)

    def test_metabolomics_workbench_get_study_details_info(self):
        response = self.client.get('/metabolomics_workbench_get_study_details_info/ST_TEST')
        self.assertEqual(response.status_code, 200)

    def test_metabobank_get_study_details_info(self):
        response = self.client.get('/metabobank_get_study_details_info/MTBKS6')
        self.assertEqual(response.status_code, 200)

    def test_metabobank_download_file_success(self):
        file_url = "https://ddbj.nig.ac.jp/public/metabobank/study/MTBKS6/OtherData/file1.txt"
        response = self.client.get(f'/metabobank_download_file/{file_url}')
        self.assertEqual(response.status_code, 200)

    def test_metabobank_download_file_fail(self):
        file_url = "https://ddbj.nig.ac.jp/public/metabobank/study/MTBKS6/OtherData/060510root_noise3NIST_TEST.txt"
        with self.assertRaises(TypeError):
            self.client.get(f'/metabobank_download_file/{file_url}')

    def test_metabolomics_page(self):
        response = self.client.get('/metabolomics')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
