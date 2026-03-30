"""
RSS Feed Processing System for Automated Content Curation.
"""

import feedparser
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import time
from urllib.parse import urljoin, urlparse
import logging
from dataclasses import dataclass
import re

@dataclass
class FeedItem:
    """Represents a single item from an RSS feed."""
    title: str
    link: str
    description: str
    published: Optional[datetime]
    author: Optional[str]
    content: str
    tags: List[str]
    guid: str
    source_feed: str

@dataclass
class FeedInfo:
    """Represents metadata about an RSS feed."""
    title: str
    link: str
    description: str
    language: Optional[str]
    last_updated: Optional[datetime]
    total_items: int
    feed_url: str

class RSSProcessor:
    """Processes RSS feeds and extracts content for curation."""
    
    def __init__(self, user_agent: str = "Sovereign AI Curation Engine 1.0"):
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Feed parsing configuration
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 2
    
    def validate_feed_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate if a URL is a valid RSS/Atom feed.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic URL validation
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL format"
            
            if parsed.scheme not in ['http', 'https']:
                return False, "Only HTTP and HTTPS URLs are supported"
            
            # Try to fetch and parse the feed
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse the feed
            feed = feedparser.parse(response.content)
            
            # Check if it's a valid feed
            if feed.bozo and feed.bozo_exception:
                return False, f"Feed parsing error: {feed.bozo_exception}"
            
            if not hasattr(feed, 'feed') or not feed.entries:
                return False, "No valid feed content found"
            
            return True, "Valid RSS/Atom feed"
            
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def fetch_feed(self, url: str) -> Optional[feedparser.FeedParserDict]:
        """
        Fetch and parse an RSS feed with retry logic.
        
        Args:
            url: RSS feed URL
            
        Returns:
            Parsed feed data or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Fetching feed: {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Parse the feed
                feed = feedparser.parse(response.content)
                
                # Check for parsing errors
                if feed.bozo and feed.bozo_exception:
                    self.logger.warning(f"Feed parsing warning for {url}: {feed.bozo_exception}")
                
                return feed
                
            except requests.RequestException as e:
                self.logger.warning(f"Network error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    
            except Exception as e:
                self.logger.error(f"Unexpected error fetching {url}: {e}")
                break
        
        return None
    
    def extract_feed_info(self, feed: feedparser.FeedParserDict, feed_url: str) -> FeedInfo:
        """Extract metadata information from a parsed feed."""
        feed_data = feed.feed
        
        # Extract basic info
        title = getattr(feed_data, 'title', 'Unknown Feed')
        link = getattr(feed_data, 'link', feed_url)
        description = getattr(feed_data, 'description', '')
        language = getattr(feed_data, 'language', None)
        
        # Extract last updated time
        last_updated = None
        if hasattr(feed_data, 'updated_parsed') and feed_data.updated_parsed:
            last_updated = datetime(*feed_data.updated_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(feed_data, 'published_parsed') and feed_data.published_parsed:
            last_updated = datetime(*feed_data.published_parsed[:6], tzinfo=timezone.utc)
        
        return FeedInfo(
            title=title,
            link=link,
            description=description,
            language=language,
            last_updated=last_updated,
            total_items=len(feed.entries),
            feed_url=feed_url
        )
    
    def extract_feed_items(self, feed: feedparser.FeedParserDict, feed_url: str, 
                          max_items: Optional[int] = None) -> List[FeedItem]:
        """
        Extract individual items from a parsed feed.
        
        Args:
            feed: Parsed feed data
            feed_url: Original feed URL
            max_items: Maximum number of items to extract
            
        Returns:
            List of FeedItem objects
        """
        items = []
        entries = feed.entries[:max_items] if max_items else feed.entries
        
        for entry in entries:
            try:
                # Extract basic fields
                title = getattr(entry, 'title', 'Untitled')
                link = getattr(entry, 'link', '')
                description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
                author = getattr(entry, 'author', None)
                
                # Extract published date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                # Extract content
                content = self._extract_content(entry)
                
                # Extract tags
                tags = self._extract_tags(entry)
                
                # Generate GUID
                guid = getattr(entry, 'id', '') or getattr(entry, 'guid', '') or link
                if not guid:
                    # Generate hash-based GUID
                    guid = hashlib.md5(f"{title}{link}{published}".encode()).hexdigest()
                
                item = FeedItem(
                    title=title,
                    link=link,
                    description=description,
                    published=published,
                    author=author,
                    content=content,
                    tags=tags,
                    guid=guid,
                    source_feed=feed_url
                )
                
                items.append(item)
                
            except Exception as e:
                self.logger.warning(f"Error processing feed item: {e}")
                continue
        
        return items
    
    def _extract_content(self, entry: feedparser.FeedParserDict) -> str:
        """Extract the main content from a feed entry."""
        content = ""
        
        # Try different content fields in order of preference
        if hasattr(entry, 'content') and entry.content:
            # RSS 2.0 content
            for content_item in entry.content:
                if content_item.get('type') == 'text/html':
                    content = content_item.get('value', '')
                    break
                elif content_item.get('type') == 'text/plain':
                    content = content_item.get('value', '')
        
        # Fallback to summary/description
        if not content:
            content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        
        # Clean HTML tags if present
        if content:
            content = self._clean_html(content)
        
        return content
    
    def _extract_tags(self, entry: feedparser.FeedParserDict) -> List[str]:
        """Extract tags/categories from a feed entry."""
        tags = []
        
        # Extract from tags field
        if hasattr(entry, 'tags'):
            for tag in entry.tags:
                if isinstance(tag, dict):
                    term = tag.get('term', '').strip()
                    if term:
                        tags.append(term)
                else:
                    tags.append(str(tag).strip())
        
        # Extract from category field
        if hasattr(entry, 'category'):
            category = entry.category.strip()
            if category:
                tags.append(category)
        
        # Remove duplicates and empty tags
        tags = list(set(tag for tag in tags if tag))
        
        return tags
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content and extract plain text."""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except ImportError:
            # Fallback: simple regex-based HTML removal
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            # If all else fails, return original content
            return html_content
    
    def process_feed(self, feed_url: str, max_items: Optional[int] = None) -> Tuple[Optional[FeedInfo], List[FeedItem]]:
        """
        Process a complete RSS feed and extract all information.
        
        Args:
            feed_url: RSS feed URL
            max_items: Maximum number of items to process
            
        Returns:
            Tuple of (feed_info, feed_items)
        """
        # Fetch the feed
        feed = self.fetch_feed(feed_url)
        if not feed:
            return None, []
        
        # Extract feed information
        feed_info = self.extract_feed_info(feed, feed_url)
        
        # Extract feed items
        feed_items = self.extract_feed_items(feed, feed_url, max_items)
        
        self.logger.info(f"Processed feed '{feed_info.title}': {len(feed_items)} items")
        
        return feed_info, feed_items
    
    def get_feed_health(self, feed_url: str) -> Dict[str, Any]:
        """
        Check the health and status of an RSS feed.
        
        Returns:
            Dictionary with health information
        """
        start_time = time.time()
        
        try:
            # Validate feed
            is_valid, message = self.validate_feed_url(feed_url)
            
            if not is_valid:
                return {
                    "status": "invalid",
                    "message": message,
                    "response_time": time.time() - start_time,
                    "last_checked": datetime.now(timezone.utc).isoformat()
                }
            
            # Fetch feed for detailed health check
            feed = self.fetch_feed(feed_url)
            
            if not feed:
                return {
                    "status": "unreachable",
                    "message": "Could not fetch feed",
                    "response_time": time.time() - start_time,
                    "last_checked": datetime.now(timezone.utc).isoformat()
                }
            
            # Analyze feed health
            feed_info = self.extract_feed_info(feed, feed_url)
            
            return {
                "status": "healthy",
                "message": "Feed is accessible and valid",
                "response_time": time.time() - start_time,
                "last_checked": datetime.now(timezone.utc).isoformat(),
                "feed_title": feed_info.title,
                "total_items": feed_info.total_items,
                "last_updated": feed_info.last_updated.isoformat() if feed_info.last_updated else None,
                "language": feed_info.language
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "response_time": time.time() - start_time,
                "last_checked": datetime.now(timezone.utc).isoformat()
            }

