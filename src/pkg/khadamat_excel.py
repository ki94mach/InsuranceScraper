import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
import os

# Define the URL
url = 'https://mdp.ihio.gov.ir/'

# Define headers (excluding 'Content-Type' and 'Cookie')
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

# Create a session
session = requests.Session()
session.headers.update(headers)

# Initial GET request to get dynamic fields and establish a session
response_get = session.get(url)
soup = BeautifulSoup(response_get.text, 'html.parser')

# Extract dynamic fields
viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
if viewstate_generator:
    viewstate_generator_value = viewstate_generator['value']
else:
    viewstate_generator_value = ''

# Update data with dynamic fields
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

# Construct the values dictionary for 'submitDirectEventConfig'
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

# Construct 'submitDirectEventConfig'
submit_direct_event_config = {
    "config": {
        "extraParams": {
            "values": json.dumps(values_dict, ensure_ascii=False)
        }
    }
}

submit_direct_event_config_json = json.dumps(submit_direct_event_config, ensure_ascii=False)
data['submitDirectEventConfig'] = submit_direct_event_config_json

# Files (for empty file upload field)
files = {
    'ucServiceDoc_fileDocument': ('', '', 'application/octet-stream'),
}

# Send the POST request
response = session.post(url, data=data, files=files)

# Handle the response
if response.status_code == 200:
    content_type = response.headers.get('Content-Type', '').lower()
    if 'application/vnd.ms-excel' in content_type.lower() or 'application/x-msexcel' in content_type.lower():
        # Read the Excel file from response content into a DataFrame
        df_current = pd.read_excel(BytesIO(response.content))
        
        # Load the existing record DataFrame if it exists
        record_file = 'data/total_khadamat.xlsx'
        if os.path.exists(record_file):
            df_record = pd.read_excel(record_file)
        else:
            df_record = pd.DataFrame()
        
       # Append current data to the record data
        df_combined = pd.concat([df_record, df_current], ignore_index=True)
        
        # Define the column to exclude from duplication check
        variable_column = 'VariableColumn'  # Replace with your actual column name to exclude
        
        # Check if the variable_column exists
        if variable_column not in df_combined.columns:
            print(f"The column '{variable_column}' was not found in the data.")
        else:
            # Remove duplicates considering all columns except variable_column
            cols_to_check = [col for col in df_combined.columns if col != variable_column]
            df_deduplicated = df_combined.drop_duplicates(subset=cols_to_check, keep='last')
            
            # Save the deduplicated DataFrame to the record file
            df_deduplicated.to_excel(record_file, index=False)
            print('Record file updated successfully.')
            
            # Optionally, report the number of duplicates removed
            num_duplicates_removed = len(df_combined) - len(df_deduplicated)
            print(f"Duplicates removed: {num_duplicates_removed}")
    else:
        print('Response is not an Excel file. Content-Type:', content_type)
else:
    print(f'Failed to download file. Status code: {response.status_code}')