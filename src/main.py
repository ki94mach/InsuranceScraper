import os
import jdatetime
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='openpyxl')
from pkg.manager import DataManager
from pkg.tripleprice import TriplePrice
from pkg.scraper import WebScraper
from pkg.processing import DataProcessing
from pkg.khadamat import KhadamatData

# Data directory is under src (same folder as main.py)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_SCRIPT_DIR, "data")
BATCH_DIR = os.path.join(_DATA_DIR, "batch")
BATCH_GENERIC_CODES_PATH = os.path.join(BATCH_DIR, "generic_codes.csv")

WEBSITES = ["Khadamat", "Taamin"]


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


def print_menu():
    print("\n" + "=" * 50)
    print("  Insurance Scraper")
    print("=" * 50)
    print("\nRoutine (Dropbox + history + Google Sheet):")
    print("  1. All (Khadamat + Taamin)")
    print("  2. Khadamat only")
    print("  3. Taamin only")
    print("\nUtility:")
    print("  4. Khadamat File only")
    print("\nBatch (CSV codes → data/batch/<jalali_date>/):")
    print("  5. Batch scrape (choose Khadamat / Taamin / Both)")
    print("\n  Q. Quit")
    print("-" * 50)


def batch_choose_websites() -> list:
    """Let user choose which websites to run for batch scraping."""
    while True:
        print("\nBatch: which sources to scrape?")
        print("  1. Khadamat only")
        print("  2. Taamin only")
        print("  3. Both (Khadamat + Taamin)")
        sub = input("Choice [1/2/3]: ").strip()
        if sub == "1":
            return ["Khadamat"]
        if sub == "2":
            return ["Taamin"]
        if sub == "3":
            return WEBSITES.copy()
        print("Invalid. Enter 1, 2, or 3.")


def run_scraping(website: str, generic_codes, output_dir, batch_mode: bool, batch_timestamp: str, triple_price_df):
    """Run scraper + processing + storage for one website."""
    print(f"Running {website}...")
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
    manager_tp = (
        triple_price_df
        if triple_price_df is not None
        else insurance_df[["generic_code"]].drop_duplicates()
    )
    manager = DataManager(
        website, insurance_df, manager_tp,
        output_dir=output_dir,
        batch_mode=batch_mode,
        batch_timestamp=batch_timestamp,
    )
    manager.storage()
    if not batch_mode:
        manager.analysis()
        manager.google_sheet_update()
    elif output_dir and batch_timestamp:
        print(f"  → {os.path.join(output_dir, f'batch_{website}Data_{batch_timestamp}.csv')}")


def main():
    khadamat = KhadamatData()
    while True:
        print_menu()
        choice = input("Choice: ").strip().upper()
        if choice == "Q":
            break

        selected_websites = []
        batch_mode = False
        triple_price_df = None
        generic_codes = None

        if choice == "1":
            # Routine: All
            khadamat.run()
            selected_websites = WEBSITES.copy()
            tp_object = TriplePrice()
            triple_price_df = tp_object.download_file()
            generic_codes = triple_price_df["generic_code"]

        elif choice == "2":
            # Routine: Khadamat only
            khadamat.run()
            selected_websites = ["Khadamat"]
            tp_object = TriplePrice()
            triple_price_df = tp_object.download_file()
            generic_codes = triple_price_df["generic_code"]

        elif choice == "3":
            # Routine: Taamin only
            selected_websites = ["Taamin"]
            tp_object = TriplePrice()
            triple_price_df = tp_object.download_file()
            generic_codes = triple_price_df["generic_code"]

        elif choice == "4":
            # Utility: Khadamat File only
            khadamat.run()
            continue

        elif choice == "5":
            # Batch: load codes from CSV, then choose Khadamat / Taamin / Both
            try:
                generic_codes = load_generic_codes_from_csv()
            except (FileNotFoundError, ValueError) as e:
                print(e)
                continue
            print(f"Loaded {len(generic_codes)} generic codes from {BATCH_GENERIC_CODES_PATH}")
            selected_websites = batch_choose_websites()
            batch_mode = True

        else:
            print("Invalid choice. Enter 1–5 or Q.")
            continue

        # Set output dir and batch timestamp for batch mode
        if batch_mode:
            jalali_today = jdatetime.datetime.now().strftime("%Y-%m-%d")
            output_dir = os.path.join(BATCH_DIR, jalali_today)
            batch_timestamp = jalali_today
        else:
            output_dir = None
            batch_timestamp = None

        for website in selected_websites:
            run_scraping(
                website, generic_codes, output_dir,
                batch_mode, batch_timestamp, triple_price_df,
            )


if __name__ == "__main__":
    main()
