import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='openpyxl')
from pkg.manager import  DataManager
from pkg.tripleprice import TriplePrice 
from pkg.scraper import WebScraper
from pkg.processing import DataProcessing
from pkg.khadamat import KhadamatData
from pkg.mosallah import MosallahData

def main():
    khadamat = KhadamatData()
    khadamat.run()

    mosallah = MosallahData()
    mosallah.run()

    tp_object = TriplePrice()
    triple_price_df = tp_object.download_file()
    generic_codes = triple_price_df['generic_code']
    website = 'Taamin'
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
