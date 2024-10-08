import requests
from bs4 import BeautifulSoup
import re
import os
from io import BytesIO
from datetime import datetime
from urllib.parse import unquote
import pandas as pd
import jdatetime

class MosallahData:
    def __init__(self):       
        self.webpage_url = 'https://esata.ir/%D8%AA%D8%B9%D8%B1%D9%81%D9%87-%D8%AF%D8%A7%D8%B1%D9%88%DB%8C%DB%8C'
        self.session = requests.Session()

    def _file_finder(self):
        response = self.session.get(self.webpage_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            links = soup.find_all('a', href=True)
            latest_file_url = None
            latest_date = None
            pattern = re.compile(r'.*list daro.*\.csv$', re.IGNORECASE)
            for link in links:
                href = link['href']
                href_decoded = unquote(href)
                if pattern.match(href_decoded):
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', href_decoded)
                    if date_match:
                        file_date_str = date_match.group(1)
                        file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                        if latest_date is None or file_date > latest_date:
                            return href
        else:
            print(f'Failed to connect to Estada.ir . Status code: {response.status_code}')
                    
    def _downloader(self):
        latest_file_url = self._file_finder()
        if latest_file_url:
            if latest_file_url.startswith('http'):
                full_url = latest_file_url
            else:
                full_url = 'https://esata.ir' + latest_file_url

            response = self.session.get(full_url)
            if response.status_code == 200:
                self.df_current = pd.read_csv(BytesIO(response.content), encoding='utf-8')
            else:
                print(f'Failed to download file. Status code: {response.status_code}')
        else:
            print('No matching CSV file URL found on the page.')

    def _processor(self):
            current_date = jdatetime.datetime.now().strftime('%Y/%m/%d')
            self.df_current['recorded_date'] = current_date
            filename = 'data/Mosallah_file.csv'
            if os.path.exists(filename):
                self.df_record = pd.read_csv(filename, encoding='utf-8')
            else:
                self.df_record = pd.DataFrame()
            if not self.df_record.empty:
                df_existing_columns = set(self.df_record.columns)
                df_new_columns = set(self.df_current.columns)
                if df_existing_columns != df_new_columns:
                    print('Warning: Column mismatch between existing and new data.')
                df_combined = pd.concat([self.df_record, self.df_current], ignore_index=True)
                variable_column = ['سريال تعرفه', 'recorded_date'] 
                cols_to_check = [col for col in df_combined.columns if col not in variable_column]
                df_deduplicated = df_combined.drop_duplicates(subset=cols_to_check, keep='first')
                df_deduplicated.to_csv(filename, index=False, encoding='utf-8-sig')
                print('Mosallah file updated successfully.')
            else:
                self.df_current.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f'New data saved as {filename}.')

    def run(self):
        self._downloader()
        self._processor()
