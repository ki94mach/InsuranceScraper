from bs4 import BeautifulSoup
import pandas as pd
import jdatetime
import os
import csv
class DataProcessing:
    def __init__(self , website: str,generic_codes: list, all_html: list, found_codes: list, not_found_codes: list):
        self.generic_codes = generic_codes
        self.website = website
        self.all_html = all_html
        self.found_codes = found_codes
        self.not_found_codes = not_found_codes
        self.current_date = jdatetime.datetime.now().strftime('%Y/%m/%d')
    
    def parser(self):
        """
        Parses html list to dataframe based on website

        """
        if self.website == 'Khadamat':
            column_header = [
            'a', 'index','change_date','generic_code','brand_code',
            'fda_code','erx_code','api','dosage_form','str','indication',
            'condition','price','coverage_per','coverage_amount','subsidy',
            'price_w/o_subsidy','insurance_coverage','date','description',
            ]
            self.insurance_df = pd.DataFrame(columns=column_header)
            for html_row in self.all_html:
                # if html_row is None or not isinstance(html_row, str) or len(html_row) == 0:
                #     continue
                soup = BeautifulSoup(html_row, 'html.parser')
                for tr in soup.find_all('tr'):
                    data = {}  # Initialize an empty dictionary to store the data
                    for i, td in enumerate(tr.find_all('td')):
                        column_name = column_header[i]
                        if td.find('br'):  # Check if the 'br' tag is present
                            # Split the text on line breaks
                            values = td.get_text(separator='\n').split('\n')
                            # Store the first value in the original column
                            data[column_name] = values[0]
                            # Store the remaining values in additional columns
                            for j, value in enumerate(values[1:], 2):  # Start enumeration from 2
                                data[f'{column_name}_{j}'] = value
                        else:
                            # If no 'br' tag is present, just store the text as is
                            data[column_name] = td.text.strip()
                    
                    # Create a new DataFrame row from the data dictionary
                    row = pd.DataFrame([data])
                    self.insurance_df = pd.concat([self.insurance_df, row], ignore_index=True)

        elif self.website == "Taamin":
            column_header = [
                'generic_code','generic_name','insurance','hospital',
                'document_office','medical_record','maximum_prescribed',
                'web','uid_register','eprescription','price_w/o_subsidy',
                'coverage_w/o_subsidy','subsidy','price','A','B','C',
                ]
            self.insurance_df = pd.DataFrame(columns=column_header)
            # Find rows in the HTML and concat them in the final_df
            for html_row in self.all_html:
                # if html_row is None or not isinstance(html_row, str) or len(html_row) == 0:
                #     continue
                soup = BeautifulSoup(html_row,'html.parser')
                data = [td.text.strip() for td in soup.find_all('td')]
                row = pd.DataFrame([data], columns=column_header)
                self.insurance_df = pd.concat([self.insurance_df, row], ignore_index=True)

        elif self.website == "Mosallah":
            # column_header = [
            #     'generic_code', 'generic_name', 'brand_name', 'dosage_form', 'price',
            #     'date','insurance','midwife_prescription','gp_prescription','hospital',
            #     'specialist','approval','reciever','maximum_prescribed','uid_register',
            #     'pharmacy_is_authorize_to_approve','patient_per','special_patient_per',
            #     'veteran_per',
            #     ]
            # self.insurance_df = pd.DataFrame(columns=column_header)
            # # Find rows in the HTML and concatinate them in the final_df
            # for html_row in self.all_html:
            #     soup = BeautifulSoup(html_row,'html.parser')
            #     data = [td.text.strip() for td in soup.find_all('td')][:19]
            #     row = pd.DataFrame([data], columns=column_header)
            #     self.insurance_df = pd.concat([self.insurance_df, row], ignore_index=True)
            # # some generic_codes have "null" in petient_per so they don't have insurance coverage, 
            # # they should be removed from found_codes and added to notfound_codes and then removed from the dataframe
            # for index, row in self.insurance_df.iterrows():
            #     if row['patient_per'] == 'null':
            #         self.not_found_codes.append(row['generic_code'])
            #         self.found_codes.remove(row['generic_code'])
            # self.insurance_df = self.insurance_df[self.insurance_df['patient_per'] != 'null']
            mosallah_path = "data/Mosallah_file.csv"
            df_record = pd.read_csv(mosallah_path)
            
    def save_raw(self):
        """
        Saves raw data for history call checks
        """
        raw_path = f"data/{self.website}_raw.csv"
        if not os.path.exists(raw_path):
            with open(raw_path, "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.insurance_df.columns)
        raw_df = pd.read_csv(raw_path, header=0, dtype='str')
        self.insurance_df.fillna('', inplace=True)
        raw_df.fillna('', inplace=True)
        total_raw = (
            pd.concat([raw_df, self.insurance_df])  
            .reset_index(drop=True)
            .drop_duplicates(keep="first")
            )
        total_raw.to_csv(raw_path, index=False, encoding='utf-8-sig')
    def clean_data(self) -> pd.DataFrame:
        if self.website == 'Khadamat':
            # This part is for dealing with generic codes with multiple rows
            # first remove the rows with same generic codes, price and coverage percentage
            # stored the brand codes that we want in KhadamatGenericBrand.csv
            #remove the generic codes with different brand code from the main dataframe
            # save these generic codes and brand codes in a csv file
            # khadamat_generic_brand='KhadamatGenericBrand.csv'
            # khadamat_df1.to_csv(khadamat_generic_brand,columns=['generic_code','brand_code'])
            khadamat_generic_brand = pd.read_csv('data/KhadamatGenericBrand.csv', dtype={'generic_code':'object', 'brand_code':'object'})
            # converting generic_code and brand_code into 5 digit number
            khadamat_generic_brand['generic_code'] = khadamat_generic_brand['generic_code'].str.pad(5, 'left', '0')
            khadamat_generic_brand['brand_code'] = khadamat_generic_brand['brand_code'].str.pad(5, 'left','0')
            # lets bring brand_codes that we want to the khadamat_df and remove those that does not match our brand_codes
            self.insurance_df = self.insurance_df.merge(khadamat_generic_brand[['generic_code','brand_code']], on='generic_code',how='left')
            c1 = self.insurance_df['brand_code_x']!=self.insurance_df['brand_code_y']
            c2 = self.insurance_df['brand_code_y'].notna()
            self.insurance_df = self.insurance_df.drop(self.insurance_df[c1 & c2].index )
            
            # Generate a generic_name colum from aoi, dosage_form and str collumn
            self.insurance_df['generic_name'] = self.insurance_df['api'] + " " + self.insurance_df['dosage_form'] + " " + self.insurance_df['str']
            self.insurance_df['change_date_2'] = self.insurance_df['change_date_2'].fillna(self.insurance_df['date'])
            # remove unwanted columns
            self.insurance_df = self.insurance_df[[
                'generic_code','generic_name','change_date_2','price',
                'coverage_per','coverage_per_2','coverage_per_3', 'subsidy'
                ]]
            
            # Remove commas from each column individually
            self.insurance_df['price'] = self.insurance_df['price'].str.replace(',', '')
            self.insurance_df['subsidy'] = self.insurance_df['subsidy'].str.replace(',', '')

            # Replace empty strings with 0 in each column individually
            for col in ['price', 'coverage_per', 'coverage_per_2', 'coverage_per_3', 'subsidy']:
                self.insurance_df[col] = self.insurance_df[col].replace('', 0)

            # Change the data type of these columns to float (this step may not be necessary as pd.to_numeric should already have converted them to float)
            self.insurance_df = self.insurance_df.astype({'price': 'float64', 'subsidy': 'float64', 'coverage_per': 'float64',
                                'coverage_per_2': 'float64', 'coverage_per_3': 'float64'})

            # lets rename the column headers
            self.insurance_df.rename(columns={'change_date_2':'date',
                                        'coverage_per':'coverage_per_1'}, inplace=True)

            per_columns = ['coverage_per_1', 'coverage_per_2', 'coverage_per_3']
            # Round coverage to two digits
            self.insurance_df[per_columns] = self.insurance_df[per_columns].round(2)
            # keeping the maximum percentage
            self.insurance_df['coverage'] = self.insurance_df[per_columns].max(axis=1)
            # lets remove duplicated values that doesn't affect our purpose
            self.insurance_df.drop_duplicates(subset=['generic_code','price','coverage'], ignore_index=True, inplace=True)
            self.insurance_df.drop(columns=per_columns, inplace=True)
            # checking if there are multipe rows for each generic code
            
        elif self.website == "Taamin":
            # removing '%' from coverage_w/o_subsidy and change the type to float
            self.insurance_df['coverage_w/o_subsidy'] = self.insurance_df['coverage_w/o_subsidy'].str.replace('%', '', regex=True).astype('float64')

            # astype function didn't change the type and reason is unknown, checked for any non-numeric value in these columns but nothing was found 
            # even trimmed but still didn't work
            self.insurance_df['price'] = self.insurance_df['price'].str.replace(',', '')
            self.insurance_df['subsidy'] = self.insurance_df['subsidy'].str.replace(',', '')
            columns_to_convert = ['price_w/o_subsidy', 'subsidy', 'price']
            self.insurance_df[columns_to_convert] = self.insurance_df[columns_to_convert].apply(pd.to_numeric, errors='coerce')

            # calculating real coverage and then remove 'columns_to_convert
            self.insurance_df['coverage'] = ((
                self.insurance_df['price_w/o_subsidy'] * self.insurance_df['coverage_w/o_subsidy']/100) + self.insurance_df['subsidy']) / self.insurance_df['price'] * 100
            self.insurance_df['coverage'] = self.insurance_df['coverage'].round(2)

            # removing unused columns
            columns_to_drop = ['insurance','hospital','document_office','medical_record','maximum_prescribed',
                            'web','uid_register','eprescription','A','B','C',
                            'price_w/o_subsidy', 'coverage_w/o_subsidy']
            self.insurance_df.drop(columns=columns_to_drop, inplace=True)

            #inserting todays date in jalali format
            self.insurance_df['date'] = self.current_date

            # converting generic_code into 5 digit number
            self.insurance_df['generic_code'] = self.insurance_df['generic_code'].str.pad(5,'left','0')

        elif self.website == "Mosallah":
            columns_to_drop = [
                'brand_name', 'dosage_form', 'insurance', 'midwife_prescription',
                'gp_prescription', 'hospital', 'specialist', 'approval', 'reciever',
                'maximum_prescribed', 'uid_register', 'pharmacy_is_authorize_to_approve',
                'special_patient_per', 'veteran_per'
                ]
            self.insurance_df.drop(columns=columns_to_drop, inplace=True)

            # change the data type of price and patient_per to float
            self.insurance_df = self.insurance_df.astype({'price':'float64', 'patient_per':'float64'})
            # calculating insurance coverage
            self.insurance_df['coverage'] = (100 - self.insurance_df['patient_per']).round(2)
            # round coverage in two digits
            #mosallah_df['coverage'] = mosallah_df['coverage'].round(2)
            # remove patient_per column
            self.insurance_df.drop(columns=['patient_per'], inplace=True)

        # Create a DataFrame from not_found_codes with price and coverage set to zero
        not_found_df = pd.DataFrame({
            'generic_code': self.not_found_codes,
            'price': [0] * len(self.not_found_codes),
            'coverage': [0] * len(self.not_found_codes),
            'date': [self.current_date] * len(self.not_found_codes)
        })
        # Concatenate the new DataFrame with the existing one
        self.insurance_df = pd.concat([self.insurance_df, not_found_df], ignore_index=True).reset_index(drop=True)

        if self.insurance_df.duplicated(subset=["generic_code"]).any():
            duplicates = self.insurance_df[self.insurance_df.duplicated(subset=['generic_code'])]
            print(duplicates)
            print(f"Duplicate generic code values found in {self.website} DataFrame.")
        
        return self.insurance_df
    def code_count(self):
        print(
            f'Total number of generic codes for "{self.website.title()}": {len(self.generic_codes)}',
            f'\nAvailable generic codes in "{self.website.title()}": {len(self.found_codes)}',
            f'\nUnavailable generic codes in "{self.website.title()}": {len(self.not_found_codes)}',
            )
