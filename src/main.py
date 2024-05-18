from pkg.manager import  DataManager
from pkg.tripleprice import TriplePrice 
from pkg.scraper import WebScraper
from pkg.processing import DataProcessing
def main():
    # Create an object from TriplePrice
    tp_object = TriplePrice()

    # Download triple price and save it in a DataFrame
    triple_price_df = tp_object.download_file()

    # generic codes as a list
    generic_codes = triple_price_df['generic_code']

    # Insurance websites
    websites = ['Mosallah', 'Khadamat', 'Taamin']
    for website in websites:
        scraper = WebScraper(website, generic_codes)
        all_html, found_codes, not_found_codes = scraper.run_crawler()
        processor = DataProcessing(website, generic_codes, all_html, found_codes, not_found_codes)
        processor.parser()
        insurance_df = processor.clean_data()
        processor.code_count()
        manager = DataManager(website, insurance_df, triple_price_df)
        manager.storage()
        manager.analysis()
        manager.google_sheet_update()
if __name__ == "__main__":
    main()
