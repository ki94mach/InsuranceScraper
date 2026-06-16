import pandas as pd
import requests
import os
from getpass import getpass
from io import BytesIO

class TriplePrice():

    def download_file(self):
        
        """
        Downloads the triple price and call the process data function at the end
        
        """
        url = "https://dms.orchidpharmed.com/OneDrive/Supply%20Chain/Supply%20Chain%20Team_DMS/47.%20Triple%20Price/new/%D9%81%D8%B1%D9%85%20%D9%82%DB%8C%D9%85%D8%AA%20%D8%B3%D9%87%20%DA%AF%D8%A7%D9%86%D9%87sc-fr-008.xlsx"
        response = self._download_with_optional_auth(url)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" in content_type:
                raise Exception(
                    "Triple price URL returned HTML instead of Excel. "
                    "Authentication may still be required or the URL points to a web page."
                )
            return self._process_data(response.content)
        else:
            raise Exception(
                "Failed to download triple price file. "
                f"HTTP status: {response.status_code}, final URL: {response.url}"
            )

    def _download_with_optional_auth(self, url: str) -> requests.Response:
        """
        Download file and retry once with credentials on auth failure.
        """
        response = requests.get(url, timeout=60)
        if response.status_code in (401, 403):
            username = os.getenv("TRIPLEPRICE_USERNAME")
            password = os.getenv("TRIPLEPRICE_PASSWORD")

            if not username:
                username = input("TriplePrice username (DOMAIN\\username or username): ").strip()
            if not password:
                password = getpass("TriplePrice password: ")

            try:
                from requests_ntlm import HttpNtlmAuth
                response = requests.get(
                    url,
                    auth=HttpNtlmAuth(username, password),
                    timeout=60,
                )
            except ImportError:
                # Fallback to basic auth if NTLM package is unavailable.
                response = requests.get(url, auth=(username, password), timeout=60)
        return response
    def _process_data(self, content) -> pd.DataFrame:
        """
        process the triple price excel file

        Inputs:
            content: response.content from download file

        Returns:
            Triple price DataFrame
        """
        # Define constants for ease of modification and readability
        columns = "B,I,S,T,,U,W,X,Z,AA"
        types = {
            'S': 'str', 'T': 'float64', 'U': 'int64',
            'W': 'float64', 'X': 'int64', 'Z': 'float64',
            'AA': 'str'
            }
        excel_data = BytesIO(content)
        # Processing the data
        triple_price = pd.read_excel(
            excel_data, sheet_name=1, dtype=types, header=None,
            nrows=None, usecols=columns, skiprows=3
            )
        triple_price = (triple_price.rename(columns=triple_price.iloc[0])
                        .iloc[1:]
                        .reset_index(drop=True)
                        .rename(columns=lambda x: x.strip())
                        .dropna(subset=['کد ژنریک'])
                        .query("`کد ژنریک` != 'ندارد'")
                        .assign(**{'کد ژنریک': lambda df: df['کد ژنریک']
                                .astype(str).str.pad(5, 'left', '0')})
                        .drop_duplicates(subset=['کد ژنریک'])
                        .rename(columns={'کد ژنریک': 'generic_code'})
                        .reset_index(drop=True))
        
        return triple_price
