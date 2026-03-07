"""
Test script for RSS processing functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'curation'))

from curation.rss_processor import RSSProcessor
from curation.feed_monitor import FeedMonitor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_rss_processor():
    """Test the RSS processor with some real feeds."""
    processor = RSSProcessor()
    
    # Test feeds
    test_feeds = [
        "https://feeds.feedburner.com/oreilly/radar",  # O'Reilly Radar
        "https://rss.cnn.com/rss/edition.rss",  # CNN
        "https://feeds.bbci.co.uk/news/rss.xml",  # BBC News
    ]
    
    print("Testing RSS Processor...")
    print("=" * 50)
    
    for feed_url in test_feeds:
        print(f"\nTesting feed: {feed_url}")
        
        # Test validation
        is_valid, message = processor.validate_feed_url(feed_url)
        print(f"Validation: {'✓' if is_valid else '✗'} - {message}")
        
        if is_valid:
            # Test processing
            feed_info, feed_items = processor.process_feed(feed_url, max_items=3)
            
            if feed_info:
                print(f"Feed Title: {feed_info.title}")
                print(f"Total Items: {feed_info.total_items}")
                print(f"Language: {feed_info.language}")
                print(f"Last Updated: {feed_info.last_updated}")
                
                print(f"\nFirst {len(feed_items)} items:")
                for i, item in enumerate(feed_items, 1):
                    print(f"  {i}. {item.title}")
                    print(f"     Published: {item.published}")
                    print(f"     Tags: {item.tags}")
                    print(f"     Content length: {len(item.content)} chars")
            else:
                print("Failed to process feed")
        
        print("-" * 30)

def test_feed_monitor():
    """Test the feed monitoring system."""
    print("\nTesting Feed Monitor...")
    print("=" * 50)
    
    monitor = FeedMonitor(config_file="./data/test_feed_config.json")
    
    # Add some test feeds
    test_feeds = [
        ("https://feeds.feedburner.com/oreilly/radar", "O'Reilly Radar", 120),
        ("https://rss.cnn.com/rss/edition.rss", "CNN News", 60),
    ]
    
    for url, name, interval in test_feeds:
        success = monitor.add_feed(url, name, scan_interval_minutes=interval)
        print(f"Added feed '{name}': {'✓' if success else '✗'}")
    
    # List feeds
    print("\nMonitored feeds:")
    feeds = monitor.list_feeds()
    for feed in feeds:
        print(f"  - {feed['name']}: {feed['status']}")
    
    # Test manual scan
    print("\nTesting manual scan...")
    for url, name, _ in test_feeds:
        success = monitor.scan_feed(url)
        print(f"Scanned '{name}': {'✓' if success else '✗'}")
    
    # Show stats
    stats = monitor.get_monitoring_stats()
    print(f"\nMonitoring stats:")
    print(f"  Total feeds: {stats['total_feeds']}")
    print(f"  Active feeds: {stats['active_feeds']}")
    print(f"  Total items processed: {stats['total_items_processed']}")

if __name__ == "__main__":
    test_rss_processor()
    test_feed_monitor()
    print("\n✓ RSS processing tests completed!")

