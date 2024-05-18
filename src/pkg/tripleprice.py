import pandas as pd
import requests
class TriplePrice():

    def download_file(self):
        
        """
        Downloads the triple price and call the process data function at the end
        
        """
        url = 'https://www.dropbox.com/scl/fi/s0hhfi55a0e3v8qqgnncf/sc-fr-008.xlsx?rlkey=8e71apbya25f3wuqanmmgu25h&dl=1'
        response = requests.get(url)
        if response.status_code == 200:
            return self._process_data(response.content)
        else:
            raise Exception("Failed to download the file.")
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

        # Processing the data
        triple_price = pd.read_excel(
            content, sheet_name=0, dtype=types, header=None,
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
