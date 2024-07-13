# Suppress the specific warning from openpyxl
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='openpyxl')

from pkg.manager import  DataManager
from pkg.tripleprice import TriplePrice 
from pkg.scraper import WebScraper
from pkg.processing import DataProcessing
def main():
    tp_object = TriplePrice()
    # Download triple price and save it in a DataFrame
    triple_price_df = tp_object.download_file()

    # generic codes as a list
    generic_codes = triple_price_df['generic_code']

    # Insurance websites
    websites = ['Mosallah', 'Khadamat', 'Taamin']
    choice = input('''
          Please Select an Option:\n
          1. All\n
          2. Mossallah\n
          3. Khadamat\n
          4. Taamin\n
          Enter your choice (1/2/3/4): 
          ''')
    selected_websites = []
    if choice == '1':
        selected_websites = websites
    elif choice == '2':
        selected_websites.append('Mosallah')
    elif choice == '3':
        selected_websites.append('Khadamat')
    elif choice == '4':
        selected_websites.append('Taamin')
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")
        return
    for website in selected_websites:
        print(f"Running operations for {website}...")
        scraper = WebScraper(website, generic_codes)
        all_html, found_codes, not_found_codes = scraper.run_crawler()
        processor = DataProcessing(website, generic_codes, all_html, found_codes, not_found_codes)
        processor.parser()
        processor.save_raw()
        insurance_df = processor.clean_data()
        # processor.code_count()
        manager = DataManager(website, insurance_df, triple_price_df)
        manager.storage()
        insurance_update = manager.analysis()
        manager.google_sheet_update()
if __name__ == "__main__":
    main()
