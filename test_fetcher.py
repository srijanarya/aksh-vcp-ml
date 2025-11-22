from src.data.corporate_announcement_fetcher import CorporateAnnouncementFetcher
import logging

logging.basicConfig(level=logging.INFO)

def main():
    fetcher = CorporateAnnouncementFetcher()
    print("Fetching latest announcements...")
    results = fetcher.fetch_latest_announcements()
    print(f"Fetched {len(results)} results")
    if results:
        print("Sample:", results[0])

if __name__ == "__main__":
    main()
