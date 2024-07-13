import pandas as pd
import gspread
from gspread_formatting import *
import string
class DataManager:
    def __init__(self, website: str, insurance_df: pd.DataFrame, triple_price_df: pd.DataFrame):
        self.website = website
        self.insurance_df = insurance_df
        self.triple_price_df = triple_price_df

    def storage(self):
        """
        Storing the new data in the csv file for history call
        """
        data_dir = f"data/{self.website}Data.csv"
        # importing the historical data into a dataframe (if the data type is not determined, drop duplicate won't work)
        history_df = pd.read_csv(data_dir, dtype={
            'generic_code':'object','price':'float64',
            'coverage':'float64', 'subsidy':'float64'}
            )

        # converting generic_code into 5 digit number
        history_df['generic_code'] = history_df['generic_code'].str.pad(5, 'left', '0')

        # concatenating the new data with the history data and sort dataframe by date in ascending order
        # only keeping the data when the coverage or price is changed and removing duplicate data on the first date
        insurance_total_df = (
            pd.concat([history_df, self.insurance_df])
            .sort_values(by='date')
            .drop_duplicates(subset=['generic_code', 'price', 'coverage', 'subsidy'], keep='first')
            .reset_index(drop=True)
            )
        # writing the data to main csv file (still not overwritting)
        insurance_total_df.to_csv(data_dir, index=False, encoding='utf-8')
    def analysis(self):
        """
        Compares the scraped data with triple price to find generic codes that need to be updated in triple price
        
        Returns:
            insurance
        """
        if self.website == "Taamin":
            final_df = self.insurance_df.merge(self.triple_price_df[
                ['generic_code', 'نام کالا', 'درصد بیمه (تامین اجتماعی)', 'مبنای پرداختی بیمه (تامین اجتماعی)']],
                on='generic_code', how='left')
            # just keep the rows that their price or coverage is different and save them in a different dataframe
            c1 = final_df['price']==final_df['مبنای پرداختی بیمه (تامین اجتماعی)']
            c2 = final_df['coverage']==final_df['درصد بیمه (تامین اجتماعی)']
            self.insurance_update = final_df.drop(final_df[ c1 & c2 ].index)
            self.insurance_update.drop(columns=['درصد بیمه (تامین اجتماعی)', 'مبنای پرداختی بیمه (تامین اجتماعی)'], inplace=True)

        elif self.website == "Khadamat":
            final_df = self.insurance_df.merge(self.triple_price_df[
                ['generic_code', 'نام کالا', 'درصد بیمه (خدمات درمانی)', 'مبنای پرداختی بیمه (خدمات درمانی)']],
                on='generic_code', how='left')
            c1 = final_df['price']==final_df['مبنای پرداختی بیمه (خدمات درمانی)']
            c2 = final_df['coverage'] == final_df['درصد بیمه (خدمات درمانی)']
            self.insurance_update = final_df.drop(final_df[ c1 & c2 ].index)
            self.insurance_update.drop(columns=['درصد بیمه (خدمات درمانی)', 'مبنای پرداختی بیمه (خدمات درمانی)'], inplace=True)

        elif self.website == "Mosallah":
            final_df = self.insurance_df.merge(self.triple_price_df[
                ['generic_code', 'نام کالا', 'درصد بیمه (نیروهای مسلح)', 'مبنای پرداختی بیمه (نیروهای مسلح)']],
                on='generic_code', how='left')
            c1 = final_df['price']==final_df['مبنای پرداختی بیمه (نیروهای مسلح)']
            c2 = final_df['coverage']==final_df['درصد بیمه (نیروهای مسلح)']
            self.insurance_update = final_df.drop(final_df[ c1 & c2 ].index)
            self.insurance_update.drop(columns=['درصد بیمه (نیروهای مسلح)', 'مبنای پرداختی بیمه (نیروهای مسلح)'], inplace=True)
        return self.insurance_update
    def google_sheet_update(self):
        """
        Update a google sheet to inform supply chain planning team to imply the changes
        """

         # Authenticate with the JSON file
        client = gspread.service_account(filename="data/credentials.json")

        # Open the workbook and select the worksheet
        wb_1 = client.open("Insurance Update")
        worksheet = wb_1.worksheet(self.website)

        # Clear the existing data in the worksheet
        worksheet.clear()
        clear_format_request = {
            "requests": [
            {
            "deleteConditionalFormatRule": {
                "sheetId": worksheet.id,
                "index": 0
            }
            }
        ]
        }
        # Send the request to clear all formats
        wb_1.batch_update(clear_format_request)

        # define nedded column headers for supply chain
        columns = ['نام کالا', 'generic_code', 'price', 'coverage', 'date']

        # Handle non-JSON compliant float values in the DataFrame
        self.insurance_update = self.insurance_update[columns].replace([float('inf'), float('-inf'), float('nan')], '')

        # Calculate the range
        num_rows = self.insurance_update.shape[0]
        num_cols = self.insurance_update.shape[1]
        last_col_letter = string.ascii_uppercase[num_cols - 1]
        update_range = f'A1:{last_col_letter}{num_rows +1}'

        # Update the worksheet with the cleaned DataFrame's data
        worksheet.update(
            range_name=update_range,
            values=[self.insurance_update.columns.values.tolist()] + self.insurance_update.values.tolist(),
            value_input_option='USER_ENTERED'
            )
        # Apply formatting to the header row
        header_format = {
            "backgroundColor": {
                "red": 0.0,
                "green": 0.0,
                "blue": 0.5  # Dark blue color
            },
            "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}, "bold": True}
        }
        worksheet.format(f'A1:{last_col_letter}1', header_format)

        # Apply alternate color formatting for rows
        row_color_format = {
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": worksheet.id,
                        "startRowIndex": 1,  # Start after the header
                        "endRowIndex": num_rows + 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols,
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "CUSTOM_FORMULA",
                            "values": [{"userEnteredValue": "=ISEVEN(ROW())"}]
                        },
                        "format": {
                            "backgroundColor": {
                                "red": 0.85,
                                "green": 0.95,
                                "blue": 1.0  # Light blue color
                            }
                        }
                    }
                },
                "index": 0
         }
        }
        wb_1.batch_update({"requests": [row_color_format]})
        print(f"{self.website} google sheet is updated!")
