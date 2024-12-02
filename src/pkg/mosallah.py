import requests
from bs4 import BeautifulSoup
import re
import os
from io import BytesIO
from datetime import datetime
from urllib.parse import unquote
import pandas as pd
import jdatetime
import csv

class MosallahData:
    def __init__(self):       
        self.webpage_url = 'https://esata.ir/node/47514'
        self.session = requests.Session()

    def _file_finder(self):
        response = self.session.get(self.webpage_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            links = soup.find_all('a', href=True)
            latest_file_url = None
            latest_date = None
            # Adjusted regex pattern to match filenames ending with a date in DD-MM-YYYY.csv format
            pattern = re.compile(r'.*(\d{2}-\d{2}-\d{4})*\.csv$', re.IGNORECASE)
            for link in links:
                href = link['href']
                href_decoded = unquote(href)
                match = pattern.match(href_decoded)
                if match:
                    # Extract the date from the filename
                    file_date_str = match.group(1)  # e.g., '01-08-1403'
                    # Split the date into day, month, and year
                    date_parts = file_date_str.split('-')
                    if len(date_parts) == 3:
                        day, month, year = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                        # Create a jdatetime.date object (Solar Hijri date)
                        try:
                            file_date_shamsi = jdatetime.date(year, month, day)
                            # Convert to Gregorian date for comparison
                            gregorian_date = file_date_shamsi.togregorian()
                            # Update the latest file URL if this file is newer
                            if latest_date is None or gregorian_date > latest_date:
                                latest_date = gregorian_date
                                latest_file_url = href
                        except ValueError as e:
                            print(f"Invalid date in filename: {file_date_str}")
                            continue
        else:
            print(f'Failed to connect to esata.ir. Status code: {response.status_code}')
            return None  # Return None if connection failed
        return latest_file_url
                    
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
                df_deduplicated.to_csv(filename, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
                print('Mosallah file updated successfully.')
            else:
                self.df_current.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f'New data saved as {filename}.')

    def run(self):
        self._downloader()
        self._processor()
