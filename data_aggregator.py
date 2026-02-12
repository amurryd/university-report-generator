"""
Data Aggregator Module
----------------------
Combines multiple datasets into one unified DataFrame.

Supports:
- Local CSV ingestion
- CSV-based APIs (demo/fake API)
- JSON-based APIs (UGM Datamart)
- OAuth 2.0 protected APIs
- Caching
"""

import pandas as pd
import requests
from pathlib import Path
from io import StringIO
from bs4 import BeautifulSoup
import hashlib


class DataAggregator:
    def __init__(self, cache_dir="data", oauth_client=None):
        self.cache_dir = Path(cache_dir)
        self.oauth_client = oauth_client
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        print(f"📂 DataAggregator initialized with cache directory: {self.cache_dir}")

    # --------------------------------------------------------------
    # MAIN INGEST FUNCTION
    # --------------------------------------------------------------
    def ingest(self, sources: list[str], cache: bool = True) -> pd.DataFrame:
        print("\n🌐 Ingesting data sources...")
        frames = []

        headers = {}
        if self.oauth_client:
            headers.update(self.oauth_client.auth_headers())

        for src in sources:
            try:
                # ------------------------------
                # API SOURCE
                # ------------------------------
                if src.startswith("http"):
                    print(f"🔗 Fetching API: {src}")
                    resp = requests.get(src, headers=headers, timeout=20)
                    resp.raise_for_status()

                    content_type = resp.headers.get("Content-Type", "")

                    # ---- JSON API (UGM Datamart) ----
                    if "application/json" in content_type:
                        df = self._handle_json_api(src, resp.json(), cache)
                        if df is not None:
                            frames.append(df)

                    # ---- CSV or HTML CSV index ----
                    else:
                        csv_links = self._get_csv_links_from_api(src)
                        for link in csv_links:
                            df = self._download_csv(link, headers, cache)
                            if df is not None:
                                frames.append(df)

                # ------------------------------
                # LOCAL CSV
                # ------------------------------
                else:
                    print(f"📁 Reading local CSV: {src}")
                    df = pd.read_csv(src, encoding="utf-8-sig")
                    df["source_type"] = "local"
                    df["source_file"] = Path(src).name
                    frames.append(df)

            except Exception as e:
                print(f"❌ Failed to ingest {src}: {e}")

        if not frames:
            raise ValueError("❌ No valid data ingested from provided sources.")

        combined_df = pd.concat(frames, ignore_index=True, sort=False)
        print(f"\n✅ Combined {len(frames)} sources ({len(combined_df)} total rows)")
        return combined_df

    # --------------------------------------------------------------
    # JSON API HANDLER (UGM)
    # --------------------------------------------------------------
    def _handle_json_api(self, url, payload, cache):
        # Handle case where payload is directly a list
        if isinstance(payload, list):
            records = payload
        # Handle case where payload is a dict with nested data
        elif isinstance(payload, dict):
            records = payload.get("data") or payload.get("items") or payload.get("results")
        else:
            print(f"⚠ Unexpected JSON structure from API: {url}")
            return None

        if not records or not isinstance(records, list):
            print(f"⚠ No usable records from JSON API: {url}")
            return None

        df = pd.DataFrame(records)
        df["source_type"] = "api-json"
        df["source_endpoint"] = url

        if cache:
            cache_path = self._cache_path(url)
            df.to_csv(cache_path, index=False, encoding="utf-8-sig")
            print(f"💾 Cached JSON API → CSV: {cache_path}")

        print(f"✓ Loaded {len(df)} rows from JSON API")
        return df

    # --------------------------------------------------------------
    # CSV AUTO-DISCOVERY (DEMO API)
    # --------------------------------------------------------------
    def _get_csv_links_from_api(self, api_url):
        try:
            resp = requests.get(api_url, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            links = [
                a["href"] if a["href"].startswith("http")
                else f"{api_url.rstrip('/')}/{a['href'].lstrip('/')}"
                for a in soup.find_all("a", href=True)
                if a["href"].endswith(".csv")
            ]

            print(f"   ↳ Found {len(links)} CSV links")
            return links

        except Exception as e:
            print(f"⚠ CSV discovery failed: {e}")
            return []

    # --------------------------------------------------------------
    # DOWNLOAD CSV
    # --------------------------------------------------------------
    def _download_csv(self, url, headers, cache):
        cache_path = self._cache_path(url)

        if cache and cache_path.exists():
            print(f"💾 Loaded from cache: {url}")
            return pd.read_csv(cache_path)

        print(f"⬇ Downloading CSV: {url}")
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()

        df = pd.read_csv(StringIO(r.text))
        if df.empty:
            print(f"⚠ Empty CSV skipped: {url}")
            return None

        df["source_type"] = "api-csv"
        df["source_file"] = url.split("/")[-1]

        if cache:
            df.to_csv(cache_path, index=False, encoding="utf-8-sig")

        return df

    # --------------------------------------------------------------
    # CACHE HELPER
    # --------------------------------------------------------------
    def _cache_path(self, key):
        return self.cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.csv"