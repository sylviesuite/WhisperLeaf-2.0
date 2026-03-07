"""
Test script for web scraping functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'curation'))

from curation.web_scraper import WebScraper, ScrapingRule
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_web_scraper():
    """Test the web scraper with various websites."""
    scraper = WebScraper()
    
    # Test URLs
    test_urls = [
        "https://example.com",  # Simple test page
        "https://httpbin.org/html",  # Test HTML page
        "https://www.bbc.com/news",  # News site
        "https://en.wikipedia.org/wiki/Artificial_intelligence",  # Wikipedia
    ]
    
    print("Testing Web Scraper...")
    print("=" * 60)
    
    # Add custom scraping rules
    scraper.add_scraping_rule("example.com", ScrapingRule(
        domain="example.com",
        delay_seconds=0.5,
        max_requests_per_minute=60
    ))
    
    scraper.add_scraping_rule("httpbin.org", ScrapingRule(
        domain="httpbin.org",
        delay_seconds=0.5,
        max_requests_per_minute=60
    ))
    
    scraper.add_scraping_rule("bbc.com", ScrapingRule(
        domain="bbc.com",
        delay_seconds=2.0,
        max_requests_per_minute=20,
        respect_robots_txt=True
    ))
    
    scraper.add_scraping_rule("wikipedia.org", ScrapingRule(
        domain="wikipedia.org",
        delay_seconds=1.0,
        max_requests_per_minute=30,
        respect_robots_txt=True
    ))
    
    successful_scrapes = []
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        
        # Check if we can scrape
        can_scrape, reason = scraper.can_scrape_url(url)
        print(f"Can scrape: {'✓' if can_scrape else '✗'} - {reason}")
        
        if can_scrape:
            # Attempt to scrape
            scraped_content = scraper.scrape_url(url)
            
            if scraped_content:
                successful_scrapes.append(scraped_content)
                print(f"✓ Successfully scraped!")
                print(f"  Title: {scraped_content.title[:80]}...")
                print(f"  Content length: {len(scraped_content.content)} chars")
                print(f"  Word count: {scraped_content.word_count}")
                print(f"  Author: {scraped_content.author}")
                print(f"  Language: {scraped_content.language}")
                print(f"  Tags: {scraped_content.tags[:5]}")  # First 5 tags
                print(f"  Links found: {len(scraped_content.links)}")
                print(f"  Images found: {len(scraped_content.images)}")
                print(f"  Response time: {scraped_content.response_time:.2f}s")
                print(f"  Status code: {scraped_content.status_code}")
                
                # Show content preview
                if scraped_content.content:
                    preview = scraped_content.content[:200].replace('\n', ' ')
                    print(f"  Content preview: {preview}...")
            else:
                print("✗ Failed to scrape content")
        
        print("-" * 40)
    
    # Show scraping statistics
    stats = scraper.get_scraping_stats()
    print(f"\nScraping Statistics:")
    print(f"  Domains with rules: {stats['domains_with_rules']}")
    print(f"  Robots cache size: {stats['robots_cache_size']}")
    print(f"  Rate limiter domains: {stats['rate_limiter_domains']}")
    print(f"  User agent: {stats['user_agent']}")
    
    print(f"\nSuccessfully scraped {len(successful_scrapes)} out of {len(test_urls)} URLs")
    
    return successful_scrapes

def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\nTesting Rate Limiting...")
    print("=" * 60)
    
    scraper = WebScraper()
    
    # Add a strict rate limiting rule
    scraper.add_scraping_rule("httpbin.org", ScrapingRule(
        domain="httpbin.org",
        delay_seconds=2.0,
        max_requests_per_minute=3
    ))
    
    test_url = "https://httpbin.org/html"
    
    print(f"Testing rate limiting with {test_url}")
    print("Making 5 rapid requests...")
    
    for i in range(5):
        print(f"\nRequest {i+1}:")
        can_scrape, reason = scraper.can_scrape_url(test_url)
        print(f"  Can scrape: {'✓' if can_scrape else '✗'} - {reason}")
        
        if can_scrape:
            scraped = scraper.scrape_url(test_url, wait_if_rate_limited=False)
            print(f"  Scrape result: {'✓' if scraped else '✗'}")
        else:
            print(f"  Blocked by rate limiter")

def test_robots_txt():
    """Test robots.txt compliance."""
    print("\nTesting Robots.txt Compliance...")
    print("=" * 60)
    
    scraper = WebScraper()
    
    # Test URLs with different robots.txt policies
    test_urls = [
        "https://www.google.com/search?q=test",  # Should be blocked
        "https://httpbin.org/robots.txt",  # Check robots.txt itself
        "https://example.com/",  # Usually allows all
    ]
    
    for url in test_urls:
        print(f"\nTesting robots.txt for: {url}")
        can_fetch = scraper.robots_checker.can_fetch(url)
        print(f"  Robots.txt allows: {'✓' if can_fetch else '✗'}")

if __name__ == "__main__":
    successful_scrapes = test_web_scraper()
    test_rate_limiting()
    test_robots_txt()
    print("\n✓ Web scraping tests completed!")

