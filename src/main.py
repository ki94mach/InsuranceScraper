import os
import jdatetime
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='openpyxl')
from pkg.manager import DataManager
from pkg.tripleprice import TriplePrice
from pkg.scraper import WebScraper
from pkg.processing import DataProcessing
from pkg.khadamat import KhadamatData
# from pkg.mosallah import MosallahData

# Data directory is under src (same folder as main.py)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR, "data")
BATCH_DIR = os.path.join(_DATA_DIR, "batch")
BATCH_GENERIC_CODES_PATH = os.path.join(BATCH_DIR, "generic_codes.csv")


def load_generic_codes_from_csv(path: str = None) -> list:
    """
    Load generic codes from a CSV file (e.g. data/batch/generic_codes.csv).
    CSV must have a column named 'generic_code'. Codes are normalized to 5-digit strings.
    """
    path = path or BATCH_GENERIC_CODES_PATH
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Batch generic codes file not found: {path}\n"
            f"Create a CSV with a 'generic_code' column and place it at {path}"
        )
    import pandas as pd
    df = pd.read_csv(path, dtype={"generic_code": str})
    if "generic_code" not in df.columns:
        raise ValueError(f"CSV must have a 'generic_code' column. Found: {list(df.columns)}")
    codes = (
        df["generic_code"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.pad(5, "left", "0")
        .drop_duplicates()
        .tolist()
    )
    if not codes:
        raise ValueError(f"No generic codes found in {path}")
    return codes


def main():
    websites = ['Khadamat', 'Taamin']
    khadamat = KhadamatData()
    # mosallah = MosallahData()
    while True:
        choice = input('''
            Please Select an Option:\n
            1. All\n
            2. Mossallah\n
            3. Khadamat\n
            4. Taamin\n\n
            5. Khadamat File\n
            6. Mosallah File\n
            7. Batch (generic codes from CSV – save to data/batch)\n
            Enter your choice (1/2/3/4/5/6/7):\n
            To exit enter Q\n
            ''')
        selected_websites = []
        batch_mode = False
        if choice == "Q":
            break
        elif choice == '7':
            batch_mode = True
            try:
                generic_codes = load_generic_codes_from_csv()
            except (FileNotFoundError, ValueError) as e:
                print(e)
                continue
            print(f"Loaded {len(generic_codes)} generic codes from {BATCH_GENERIC_CODES_PATH}")
            selected_websites = websites
            triple_price_df = None
        elif choice == '1':
            khadamat.run()
            selected_websites = websites
            tp_object = TriplePrice()
            triple_price_df = tp_object.download_file()
            generic_codes = triple_price_df['generic_code']
        # elif choice == '2':
        #     mosallah.run()
        #     selected_websites.append('Mosallah')
        elif choice == '3':
            khadamat.run()
            selected_websites.append('Khadamat')
            tp_object = TriplePrice()
            triple_price_df = tp_object.download_file()
            generic_codes = triple_price_df['generic_code']
        elif choice == '4':
            selected_websites.append('Taamin')
            tp_object = TriplePrice()
            triple_price_df = tp_object.download_file()
            generic_codes = triple_price_df['generic_code']
        elif choice == '5':
            khadamat.run()
            continue
        # elif choice == '6':
        #     mosallah.run()
        #     continue
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, or 7.")
            continue

        # Batch: output under data/batch/<jalali_today>/; filenames use Jalali date only (no time)
        if batch_mode:
            jalali_today = jdatetime.datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join(BATCH_DIR, jalali_today)
            batch_timestamp = jalali_today  # Jalali date only in filename, e.g. batch_KhadamatData_1403-11-19.csv
        else:
            output_dir = None
            batch_timestamp = None
        for website in selected_websites:
            print(f"Running operations for {website}...")
            scraper = WebScraper(website, generic_codes)
            all_html, found_codes, not_found_codes = scraper.run_crawler()
            processor = DataProcessing(
                website, generic_codes, all_html, found_codes, not_found_codes,
                output_dir=output_dir,
            )
            processor.parser()
            if not batch_mode:
                processor.save_raw()
            insurance_df = processor.clean_data()
            # Dummy triple_price_df for batch (only storage is used; no triple-price columns needed)
            manager_tp = triple_price_df if triple_price_df is not None else insurance_df[["generic_code"]].drop_duplicates()
            manager = DataManager(website, insurance_df, manager_tp, output_dir=output_dir, batch_mode=batch_mode, batch_timestamp=batch_timestamp)
            manager.storage()
            if not batch_mode:
                insurance_update = manager.analysis()
                manager.google_sheet_update()
            else:
                print(f"Batch results for {website} saved to {os.path.join(output_dir, f'batch_{website}Data_{batch_timestamp}.csv')}")
if __name__ == "__main__":
    main()
