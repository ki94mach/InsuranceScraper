import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
class WebScraper:
    def __init__(self, website: str, generic_codes: list):
        
        self.website = website
        self.driver = webdriver.Firefox()
        self.generic_codes = generic_codes
        self.wait = WebDriverWait(self.driver, 20)
        self.max_attempts = 3
        self.all_tables_html, self.found_codes, self.notfound_codes = ([] for i in range(3))


    def run_crawler(self) -> list:
        """
        Calls the right function for scraping based on self.website
        and retrieves dataframe for other data processing functions

        Returns: 
            all table html: list
            found codes: int
            not found code: int
        """
        if self.website == "Khadamat":
            #navigating to the website
            url = 'https://mdp.ihio.gov.ir/'
            self.driver.get(url)

            #if timeoutexception, the website will be refreshed for up to three times 
            # when the url is loaded there two clicks before beginning the search
            self.wait.until(EC.element_to_be_clickable((By.ID, 'button-1181'))).click()
            self.wait.until(EC.element_to_be_clickable((By.ID, 'cmbSrchSrvChgStatus-trigger-_trigger1'))).click()
            # iterate through the generic codes
            for code in self.generic_codes:
                for attempt in range(self.max_attempts):
                    try:
                        table_html = self._khadamat_crawler(self.driver, code)
                        if table_html is None :
                            self.notfound_codes.append(code)
                        else:
                            self.found_codes.append(code)
                            self.all_tables_html.append(table_html)
                        break
                    except TimeoutException:
                        print(f"Timeout encountered on attempt {attempt + 1} for code {code}. Refreshing and retrying...")
                        self.driver.refresh()  # Refresh the page before the next attempt.
                        # when the url is loaded there two clicks before beginning the search
                        self.wait.until(EC.element_to_be_clickable((By.ID, 'button-1181'))).click()
                        self.wait.until(EC.element_to_be_clickable((By.ID, 'cmbSrchSrvChgStatus-trigger-_trigger1'))).click()
            self.driver.quit()
            return self.all_tables_html, self.found_codes, self.notfound_codes
        else:
            
            url_mosallah = '''
            https://esata.ir/web/sakhad/drug?p_p_id=sakhadDrug_WAR_sakhadDrug&p_p_lifecycle=0&p_p_state=normal&p_
            p_mode=view&p_p_col_id=column-1&p_p_col_pos=1&p_p_col_count=3&_sakhadDrug_WAR_sakhadDrug_render=search
            '''
            url_taamin = 'https://darman.tamin.ir/Forms/Public/Druglist.aspx?pagename=hdpDrugList'
            self.driver.get(url_mosallah if self.website =="Mosallah" else url_taamin )
            
            for code in self.generic_codes:
                table_html = (self._mosallah_crawler(self.driver, code) if self.website =="Mosallah" else self._taamin_crawler(self.driver, code))
                if table_html is None or not isinstance(table_html, str) or len(table_html) == 0:
                    self.notfound_codes.append(code) 
                else:
                    self.found_codes.append(code)
                    self.all_tables_html.append(table_html)
            self.driver.quit()
            return self.all_tables_html, self.found_codes, self.notfound_codes


    def _mosallah_crawler(self, driver: webdriver.Firefox, code: int) -> str :
        """
        Crawls the mosallah website for every genric code

        Input:
            driver: a webdriver instance
            code: an integer code from generic_codes
        
        Returns:
            An html string for later parsing
        """
        #if timeoutexception, the website will be refreshed for up to three times 
        for attempt in range(self.max_attempts):
            try:    
                # because the mosallah site renders after every search I had to make sure that every elemnt is presented
                self.wait.until(EC.presence_of_all_elements_located((By.ID, '_sakhadDrug_WAR_sakhadDrug_drugId')))
                # Locate the input field by its HTML attributes (you need to inspect the page source to find these attributes)
                code_input = driver.find_element(By.ID, '_sakhadDrug_WAR_sakhadDrug_drugId')
                # Input generic_code code
                code_input.clear()  # Clear any existing text in the input field
                code_input.send_keys(code)

                #wait for the search bar to disappear
                self.wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "lfr-spa-loading-bar")))
                # because the mosallah site renders after every search I had to make sure that every element is presented in html
                # Locate and click the search button
                search_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn.btn-info.btn-sm')))
                search_button.click()
                self.wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "lfr-spa-loading-bar")))
                self.wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "lfr-spa-loading-bar")))
                # Wait for the table to load
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'table-data')))
                # checking if the row is not empty
                rows = driver.find_elements(By.CSS_SELECTOR, 'tbody.table-data > tr')
                if not rows:  # If list of rows is empty, there are no results
                    # print(f"No results found for code: {code}")
                    return None
                else:  # If rows are found, we proceed with extracting the data
                    table = driver.find_element(By.CLASS_NAME, 'table-data')
                    table_html = table.get_attribute('outerHTML')
                    return table_html
            except TimeoutException:
                print(f"Timeout encountered on attempt {attempt + 1} for code {code}. Refreshing and retrying...")
                driver.refresh()  # Refresh the page before the next attempt.
                time.sleep(3)  # A short pause before the next attempt may help.
        print(f"Failed to retrieve data for code {code} after {self.max_attempts} attempts.")
        return None
    
    def _taamin_crawler(self, driver: webdriver.Firefox, code: int) -> str:
        """
        Crawls the taamin website for every genric code

        Input:
            driver: a webdriver instance
            code: an integer code from generic_codes
        
        Returns:
            An html string for later parsing
        """
        self.wait.until(EC.presence_of_all_elements_located((By.ID, "ctl00_ContentPlaceHolder1_txtDrugCode")))
        # Locate the input field by its HTML attributes (you need to inspect the page source to find these attributes)
        code_input = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtDrugCode')

        # Input generic_code code
        code_input.clear()  # Clear any existing text in the input field
        code_input.send_keys(code)

        # Locate and click the search button
        search_button = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_btnSearch')
        search_button.click()

        # Wait for the table to load
        try:
            table = self.wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_Grd_Dr_DXDataRow0")))
            table_html = table.get_attribute('outerHTML')
            return table_html
        except TimeoutException:
            #print(code,'WAS NOT FOUND')
            return None
    def _khadamat_crawler(self, driver: webdriver.Firefox, code: int) -> str:
        """
        Crawls the taamin website for every genric code

        Input:
            driver: a webdriver instance
            code: an integer code from generic_codes
        
        Returns:
            An html string for later parsing
        """
        # because the site renders after every search I had to make sure that every elemnt is presented
        self.wait.until(EC.presence_of_all_elements_located((By.ID, 'txtSrchSrvCode-inputEl')))
        # Locate the input field by its HTML attributes (you need to inspect the page source to find these attributes)
        code_input = driver.find_element(By.ID, 'txtSrchSrvCode-inputEl')
        # Input generic_code code
        code_input.clear()  # Clear any existing text in the input field
        code_input.send_keys(code)
        # because the mosallah site renders after every search I had to make sure that every element is presented in html
        # Locate and click the search button
        search_button = self.wait.until(EC.element_to_be_clickable((By.ID, 'BtnSrchService')))
        search_button.click()
        #wait for the search bar to appear and then disappear
        self.wait.until(EC.visibility_of_element_located(((By.CSS_SELECTOR, ".x-mask-msg.x-mask-loading"))))
        self.wait.until(EC.invisibility_of_element_located(((By.CSS_SELECTOR, ".x-mask-msg.x-mask-loading"))))
        # Wait for the table to load
        time.sleep(2)
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'x-grid-item-container')))
        # checking if the row is not empty
        rows = driver.find_elements(By.CLASS_NAME, 'x-grid-row')
        if not rows:  # If list of rows is empty, there are no results
            #print(f"No results found for code: {code}")
            return None
        else:  # If rows are found, we proceed with extracting the data
            table = driver.find_element(By.CLASS_NAME, 'x-grid-item-container')
            table_html = table.get_attribute('outerHTML')
            return table_html
        