"""Load/save generic codes that failed due to scrape timeouts (retry without harming good data)."""
import os
import re
from typing import List, Optional

import pandas as pd

TIMEOUT_LOG_PATTERN = re.compile(
    r"Timeout encountered on attempt 1 for code (\d+)",
    re.IGNORECASE,
)

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETRY_DIR = os.path.join(_SCRIPT_DIR, "data", "retry")


def _retry_path(website: str) -> str:
    return os.path.join(RETRY_DIR, f"{website.lower()}_failed_codes.csv")


def normalize_codes(codes) -> List[str]:
    return (
        pd.Series(codes, dtype="object")
        .dropna()
        .astype(str)
        .str.strip()
        .str.pad(5, "left", "0")
        .drop_duplicates()
        .tolist()
    )


def extract_timeout_codes_from_text(text: str) -> List[str]:
    """Unique generic codes that hit a page-input timeout (attempt 1 line in logs)."""
    raw = TIMEOUT_LOG_PATTERN.findall(text)
    return normalize_codes(raw)


def extract_timeout_codes_from_log(path: str) -> List[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return extract_timeout_codes_from_text(f.read())


def save_retry_codes(codes, website: str, source: str = "timeout") -> str:
    os.makedirs(RETRY_DIR, exist_ok=True)
    path = _retry_path(website)
    df = pd.DataFrame({
        "generic_code": normalize_codes(codes),
        "website": website,
        "reason": source,
    })
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def load_retry_codes(path: str = None, website: str = "Taamin") -> List[str]:
    path = path or _retry_path(website)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Retry codes file not found: {path}\n"
            f"Run a scrape first (timeouts are saved automatically) or place a CSV with generic_code."
        )
    df = pd.read_csv(path, dtype={"generic_code": str})
    if "generic_code" not in df.columns:
        raise ValueError(f"CSV must have a 'generic_code' column. Found: {list(df.columns)}")
    return normalize_codes(df["generic_code"])


def remove_failed_placeholders(
    history_df: pd.DataFrame,
    codes: List[str],
    date: str,
) -> pd.DataFrame:
    """Drop today's price=0 / coverage=0 rows for codes being retried (failed timeout placeholders)."""
    codes = normalize_codes(codes)
    mask = (
        history_df["generic_code"].isin(codes)
        & (history_df["price"] == 0)
        & (history_df["coverage"] == 0)
        & (history_df["date"].astype(str) == date)
    )
    return history_df.loc[~mask].reset_index(drop=True)
