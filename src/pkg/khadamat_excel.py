import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
import os
import jdatetime
class data_store:
    def __init__(self):
        self.current_date = jdatetime.datetime.now().strftime('%Y/%m/%d')

    def _downloader(self):

        url = 'https://mdp.ihio.gov.ir/'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://mdp.ihio.gov.ir',
            'Connection': 'keep-alive',
            'Referer': 'https://mdp.ihio.gov.ir/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'iframe',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Priority': 'u=4',
        }


        session = requests.Session()
        session.headers.update(headers)

        response_get = session.get(url)
        soup = BeautifulSoup(response_get.text, 'html.parser')

        viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        if viewstate_generator:
            viewstate_generator_value = viewstate_generator['value']
        else:
            viewstate_generator_value = ''
        data = {
            'cmbServiceType': 'داروخانه',
            '_cmbServiceType_state': '[{"value":"842","text":"\\u062f\\u0627\\u0631\\u0648\\u062e\\u0627\\u0646\\u0647","index":0}]',
            'txtSrchSrvCode': '',
            'txtSrchSrvName': '',
            'txtSrchChgDate': '',
            'txtSrchChgDate2': '',
            'txtSerSize': '',
            'txtSrchFeranshiz': '',
            'cmbSrchSrvChgStatus': 'آخرين تغييرات',
            '_cmbSrchSrvChgStatus_state': '',
            'ComboBox1': '10',
            '_ComboBox1_state': '[{"value":"10","text":"10","index":0}]',
            '__VIEWSTATEGENERATOR': viewstate_generator_value,
            '__EVENTTARGET': 'ResourceManager1',
            '__EVENTARGUMENT': 'btnExcelExport|event|Click',
            '__ExtNetDirectEventMarker': 'delta=true',
        }

        values_dict = {
            "cmbServiceType": "842",
            "_cmbServiceType_state": "[{\"value\":\"842\",\"text\":\"\\u062f\\u0627\\u0631\\u0648\\u062e\\u0627\\u0646\\u0647\",\"index\":0}]",
            "txtSrchSrvCode": "",
            "txtSrchSrvName": "",
            "txtSrchChgDate": "",
            "txtSrchChgDate2": "",
            "txtSerSize": "",
            "txtSrchFeranshiz": "",
            "cmbSrchSrvChgStatus": "",
            "_cmbSrchSrvChgStatus_state": "",
            "cmbDeviceGroup": "",
            "_cmbDeviceGroup_state": "",
            "txtSerchUniversal": "",
            "cmbSrchFehrest": "",
            "_cmbSrchFehrest_state": "",
            "cmbSrchExpert": "",
            "_cmbSrchExpert_state": "",
            "cmbSrchRes": "",
            "_cmbSrchRes_state": "",
            "cmbSrchSpc": "",
            "_cmbSrchSpc_state": "",
            "cmbBimeProdType": "",
            "_cmbBimeProdType_state": "",
        }

        submit_direct_event_config = {
            "config": {
                "extraParams": {
                    "values": json.dumps(values_dict, ensure_ascii=False)
                }
            }
        }

        submit_direct_event_config_json = json.dumps(submit_direct_event_config, ensure_ascii=False)
        data['submitDirectEventConfig'] = submit_direct_event_config_json

        files = {
            'ucServiceDoc_fileDocument': ('', '', 'application/octet-stream'),
        }

        self.response = session.post(url, data=data, files=files)

    def _process(self):
        if self.response.status_code == 200:
            content_type = self.response.headers.get('Content-Type', '').lower()
            if 'application/vnd.ms-excel' in content_type.lower() or 'application/x-msexcel' in content_type.lower():
                self.df_current = pd.read_excel(BytesIO(self.response.content))
                self.record_file = 'data/Khadamat_excel.xlsx'
                if os.path.exists(self.record_file):
                    self.df_record = pd.read_excel(self.record_file)
                else:
                    self.df_record = pd.DataFrame()
                self.df_current['recorded_date'] = self.current_date
                df_combined = pd.concat([self.df_record, self.df_current], ignore_index=True)
                variable_column = ['رديف', 'recorded_date'] 
                cols_to_check = [col for col in df_combined.columns if col not in variable_column]
                df_deduplicated = df_combined.drop_duplicates(subset=cols_to_check, keep='first')
                df_deduplicated.to_excel(self.record_file, index=False)
                print('Khadamat excel file updated successfully.')
            else:
                print('Response is not an Excel file. Content-Type:', content_type)
        else:
            print(f'Failed to download file. Status code: {self.response.status_code}')
    def run(self):
        self._downloader()
        self._process()