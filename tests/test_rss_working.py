"""
Test script for RSS processing with working feeds.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'curation'))

from curation.rss_processor import RSSProcessor
from curation.feed_monitor import FeedMonitor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_working_feeds():
    """Test with feeds that should work."""
    processor = RSSProcessor()
    
    # Test with working feeds
    test_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",  # BBC News
        "https://rss.slashdot.org/Slashdot/slashdotMain",  # Slashdot
        "https://feeds.reuters.com/reuters/topNews",  # Reuters
    ]
    
    print("Testing RSS Processor with working feeds...")
    print("=" * 60)
    
    working_feeds = []
    
    for feed_url in test_feeds:
        print(f"\nTesting feed: {feed_url}")
        
        # Test validation
        is_valid, message = processor.validate_feed_url(feed_url)
        print(f"Validation: {'✓' if is_valid else '✗'} - {message}")
        
        if is_valid:
            working_feeds.append(feed_url)
            
            # Test processing
            feed_info, feed_items = processor.process_feed(feed_url, max_items=2)
            
            if feed_info:
                print(f"Feed Title: {feed_info.title}")
                print(f"Total Items: {feed_info.total_items}")
                print(f"Language: {feed_info.language}")
                
                print(f"\nFirst {len(feed_items)} items:")
                for i, item in enumerate(feed_items, 1):
                    print(f"  {i}. {item.title[:80]}...")
                    print(f"     Published: {item.published}")
                    print(f"     Content: {item.content[:100]}...")
            else:
                print("Failed to process feed")
        
        print("-" * 40)
    
    # Test feed monitor with working feeds
    if working_feeds:
        print(f"\nTesting Feed Monitor with {len(working_feeds)} working feeds...")
        print("=" * 60)
        
        monitor = FeedMonitor(config_file="./data/working_feed_config.json")
        
        # Add working feeds
        for i, url in enumerate(working_feeds):
            name = f"Test Feed {i+1}"
            success = monitor.add_feed(url, name, scan_interval_minutes=60)
            print(f"Added feed '{name}': {'✓' if success else '✗'}")
        
        # List feeds
        print("\nMonitored feeds:")
        feeds = monitor.list_feeds()
        for feed in feeds:
            print(f"  - {feed['name']}: {feed['status']}")
        
        # Test manual scan of first working feed
        if working_feeds:
            print(f"\nTesting manual scan of first feed...")
            success = monitor.scan_feed(working_feeds[0])
            print(f"Manual scan: {'✓' if success else '✗'}")
        
        # Show updated stats
        stats = monitor.get_monitoring_stats()
        print(f"\nFinal monitoring stats:")
        print(f"  Total feeds: {stats['total_feeds']}")
        print(f"  Active feeds: {stats['active_feeds']}")
        print(f"  Total items processed: {stats['total_items_processed']}")

if __name__ == "__main__":
    test_working_feeds()
    print("\n✓ RSS processing tests with working feeds completed!")

