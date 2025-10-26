# file: data_aggregator.py
"""
Data Aggregator Module
----------------------
Combines multiple CSV datasets (students, finance, akreditasi) into one unified DataFrame.
"""

import os
import pandas as pd
import requests
from pathlib import Path
from io import StringIO


class DataAggregator:
    """Aggregates multiple CSV files into one unified dataset."""

    def __init__(self, cache_dir: str = "data", verbose=True):
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.exists():
            print(f"⚠ Base directory not found. Creating: {self.cache_dir}")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"📂 DataAggregator initialized with base directory: {self.cache_dir}")

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
                if src.startswith("http://") or src.startswith("https://"):
                    print(f"🔗 Fetching from API: {src}")
                    resp = requests.get(src, timeout=15)
                    resp.raise_for_status()
                    df = pd.read_csv(StringIO(resp.text))
                    source_type = "api"
                else:
                    print(f"📁 Reading local CSV: {src}")
                    df = pd.read_csv(src)
                    source_type = "local"

                if df.empty:
                    print(f"⚠ Empty dataset skipped: {src}")
                    continue

                df["source_type"] = source_type
                df["source_file"] = Path(src).name
                frames.append(df)

                if cache:
                    cache_name = Path(src).name if source_type == "local" else src.split("/")[-1] + ".csv"
                    cache_path = self.cache_dir / cache_name
                    df.to_csv(cache_path, index=False, encoding="utf-8-sig")
                    print(f"💾 Cached: {cache_path}")

            except Exception as e:
                print(f"❌ Failed to ingest {src}: {e}")

        if not frames:
            raise ValueError("No valid data ingested from provided sources.")

        combined_df = pd.concat(frames, ignore_index=True, sort=False)
        print(f"\n✅ Ingested and combined {len(frames)} sources ({len(combined_df)} total rows).")
        return combined_df

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
    combined_df = aggregator.aggregate_all()
    if not combined_df.empty:
        print("\n--- SAMPLE OUTPUT ---")
        print(combined_df.head())
    else:
        print("No combined data available.")
