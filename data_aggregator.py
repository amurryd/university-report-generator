"""
Data Aggregator Module
----------------------
Combines multiple CSV datasets (students, finance, akreditasi)
into one unified DataFrame — supporting local files or API sources.

Now supports auto-downloading multiple CSVs per dataset from a local FastAPI demo API.
"""

import os
import pandas as pd
import requests
from pathlib import Path
from io import StringIO
from bs4 import BeautifulSoup


class DataAggregator:
    """Aggregates multiple CSV files into one unified dataset."""

    def __init__(self, cache_dir: str = "data", verbose=True):
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.exists():
            print(f"⚠ Base directory not found. Creating: {self.cache_dir}")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"📂 DataAggregator initialized with base directory: {self.cache_dir}")

    # --------------------------------------------------------------
    # HELPER: Parse /data/{dataset} page to find all downloadable CSVs
    # --------------------------------------------------------------
    def _get_csv_links_from_api(self, api_url: str) -> list[str]:
        """Fetch list of downloadable CSV URLs from a /data/{dataset} API endpoint."""
        try:
            resp = requests.get(api_url, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            links = [
                f"http://127.0.0.1:8000{a['href']}"
                for a in soup.find_all("a", href=True)
                if a["href"].endswith(".csv")
            ]

            print(f"   ↳ Found {len(links)} CSV links under {api_url}")
            return links
        except Exception as e:
            print(f"   ❌ Failed to parse CSV links from {api_url}: {e}")
            return []

    # --------------------------------------------------------------
    # MAIN INGEST FUNCTION
    # --------------------------------------------------------------
    def ingest(self, sources: list[str], cache: bool = True) -> pd.DataFrame:
        """
        Ingest multiple CSV sources (either URLs or local file paths).
        Optionally caches them under cache_dir.
        Returns a single combined DataFrame.
        """
        print("\n🌐 Ingesting multiple CSV sources...")
        frames = []

        for src in sources:
            try:
                # ------------------------------
                # Handle API sources
                # ------------------------------
                if src.startswith("http://") or src.startswith("https://"):
                    print(f"🔗 Fetching from API: {src}")

                    # If /data/{dataset}, auto-fetch all downloadable CSVs
                    if "/data/" in src:
                        csv_links = self._get_csv_links_from_api(src)
                        if not csv_links:
                            print(f"⚠ No CSV links found for {src}")
                            continue

                        for link in csv_links:
                            try:
                                print(f"     ⬇ Downloading {link}")
                                r = requests.get(link, timeout=10)
                                r.raise_for_status()
                                df = pd.read_csv(StringIO(r.text))
                                if df.empty:
                                    print(f"     ⚠ Skipped empty CSV: {link}")
                                    continue

                                df["source_type"] = "api"
                                df["source_file"] = link.split("/")[-1]
                                frames.append(df)

                                if cache:
                                    cache_path = self.cache_dir / df["source_file"].iloc[0]
                                    df.to_csv(cache_path, index=False, encoding="utf-8-sig")
                                    print(f"     💾 Cached: {cache_path}")

                            except Exception as e:
                                print(f"     ❌ Failed to download {link}: {e}")

                        continue  # move to next dataset after fetching its CSVs

                    # Otherwise, just read a single remote CSV
                    resp = requests.get(src, timeout=15)
                    resp.raise_for_status()
                    df = pd.read_csv(StringIO(resp.text))
                    df["source_type"] = "api"
                    df["source_file"] = Path(src).name
                    frames.append(df)

                # ------------------------------
                # Handle local CSV files
                # ------------------------------
                else:
                    print(f"📁 Reading local CSV: {src}")
                    df = pd.read_csv(src)
                    if df.empty:
                        print(f"⚠ Empty dataset skipped: {src}")
                        continue
                    df["source_type"] = "local"
                    df["source_file"] = Path(src).name
                    frames.append(df)

                    if cache:
                        cache_name = Path(src).name
                        cache_path = self.cache_dir / cache_name
                        df.to_csv(cache_path, index=False, encoding="utf-8-sig")
                        print(f"💾 Cached: {cache_path}")

            except Exception as e:
                print(f"❌ Failed to ingest {src}: {e}")

        # ------------------------------
        # Combine all datasets
        # ------------------------------
        if not frames:
            raise ValueError("❌ No valid data ingested from provided sources.")

        combined_df = pd.concat(frames, ignore_index=True, sort=False)
        print(f"\n✅ Ingested and combined {len(frames)} sources ({len(combined_df)} total rows).")
        return combined_df

    # --------------------------------------------------------------
    # Read local folders (used in offline/local mode)
    # --------------------------------------------------------------
    def _read_csv_files_from_folder(self, folder_name: str) -> pd.DataFrame:
        folder_path = self.cache_dir / folder_name
        if not folder_path.exists():
            print(f"⚠ Folder not found: {folder_path}")
            return pd.DataFrame()

        csv_files = list(folder_path.glob("*.csv"))
        if not csv_files:
            print(f"⚠ No CSV files found in {folder_path}")
            return pd.DataFrame()

        frames = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                df["source_type"] = folder_name
                df["source_file"] = csv_file.name
                frames.append(df)
                print(f"  ✓ Loaded {csv_file.name} ({len(df)} rows)")
            except Exception as e:
                print(f"  ❌ Error reading {csv_file.name}: {e}")

        if frames:
            combined = pd.concat(frames, ignore_index=True)
            print(f"✅ Combined {len(frames)} CSVs from '{folder_name}' ({len(combined)} total rows)")
            return combined
        return pd.DataFrame()

    # --------------------------------------------------------------
    # Aggregate all or selected datasets
    # --------------------------------------------------------------
    def aggregate_all(self) -> pd.DataFrame:
        print("\n📊 Aggregating all datasets...")
        datasets = {}
        for folder in ["students", "finance", "akreditasi"]:
            df = self._read_csv_files_from_folder(folder)
            if not df.empty:
                datasets[folder] = df

        if not datasets:
            print("❌ No data found in any folder.")
            return pd.DataFrame()

        combined_df = pd.concat(datasets.values(), ignore_index=True, sort=False)
        print(f"\n✅ Aggregated dataset created with {len(combined_df)} total rows and {len(combined_df.columns)} columns.")
        print(f"   Source breakdown: {', '.join(datasets.keys())}")
        return combined_df

    def aggregate_selected(self, folders: list[str]) -> pd.DataFrame:
        print(f"\n📊 Aggregating selected datasets: {', '.join(folders)}")
        frames = []
        for folder in folders:
            df = self._read_csv_files_from_folder(folder)
            if not df.empty:
                frames.append(df)

        if frames:
            combined = pd.concat(frames, ignore_index=True, sort=False)
            print(f"✅ Aggregated {len(frames)} selected datasets ({len(combined)} total rows)")
            return combined
        print("⚠ No valid data found in selected folders.")
        return pd.DataFrame()


if __name__ == "__main__":
    aggregator = DataAggregator(cache_dir="data")
    # Example demo with fake API endpoints
    sources = [
        "http://127.0.0.1:8000/data/students",
        "http://127.0.0.1:8000/data/finance",
        "http://127.0.0.1:8000/data/akreditasi",
    ]
    combined_df = aggregator.ingest(sources)
    if not combined_df.empty:
        print("\n--- SAMPLE OUTPUT ---")
        print(combined_df.head())
    else:
        print("No combined data available.")
