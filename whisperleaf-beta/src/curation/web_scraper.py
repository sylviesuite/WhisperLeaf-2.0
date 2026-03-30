"""
Web Scraping Framework for Content Extraction with Rate Limiting and Safety Checks.
"""

import requests
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple, Any, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from datetime import datetime, timezone, timedelta
import hashlib
import logging
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re
from collections import defaultdict
import json

@dataclass
class ScrapedContent:
    """Represents content scraped from a web page."""
    url: str
    title: str
    content: str
    description: str
    author: Optional[str]
    published_date: Optional[datetime]
    tags: List[str]
    links: List[str]
    images: List[str]
    content_type: str
    language: Optional[str]
    word_count: int
    scraped_at: datetime
    response_time: float
    status_code: int

@dataclass
class ScrapingRule:
    """Rules for scraping a specific domain or URL pattern."""
    domain: str
    delay_seconds: float = 1.0
    max_requests_per_minute: int = 30
    respect_robots_txt: bool = True
    allowed_content_types: Set[str] = None
    custom_headers: Dict[str, str] = None
    timeout: int = 30
    
    def __post_init__(self):
        if self.allowed_content_types is None:
            self.allowed_content_types = {'text/html', 'application/xhtml+xml'}
        if self.custom_headers is None:
            self.custom_headers = {}

class RateLimiter:
    """Rate limiter for web scraping requests."""
    
    def __init__(self):
        self.domain_requests: Dict[str, List[datetime]] = defaultdict(list)
        self.domain_last_request: Dict[str, datetime] = {}
    
    def can_make_request(self, domain: str, rule: ScrapingRule) -> Tuple[bool, float]:
        """
        Check if a request can be made to the domain.
        
        Returns:
            Tuple of (can_make_request, wait_time_seconds)
        """
        now = datetime.now()
        
        # Check delay between requests
        if domain in self.domain_last_request:
            time_since_last = (now - self.domain_last_request[domain]).total_seconds()
            if time_since_last < rule.delay_seconds:
                return False, rule.delay_seconds - time_since_last
        
        # Check requests per minute limit
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [req for req in self.domain_requests[domain] if req > minute_ago]
        
        if len(recent_requests) >= rule.max_requests_per_minute:
            oldest_request = min(recent_requests)
            wait_time = 60 - (now - oldest_request).total_seconds()
            return False, max(0, wait_time)
        
        return True, 0
    
    def record_request(self, domain: str):
        """Record that a request was made to the domain."""
        now = datetime.now()
        self.domain_last_request[domain] = now
        self.domain_requests[domain].append(now)
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        self.domain_requests[domain] = [req for req in self.domain_requests[domain] if req > minute_ago]

class RobotsChecker:
    """Checks robots.txt compliance for web scraping."""
    
    def __init__(self, user_agent: str = "Sovereign AI Curation Bot"):
        self.user_agent = user_agent
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(hours=24)
    
    def can_fetch(self, url: str) -> bool:
        """Check if the URL can be fetched according to robots.txt."""
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Check cache
            if domain in self.robots_cache:
                if datetime.now() < self.cache_expiry[domain]:
                    rp = self.robots_cache[domain]
                    return rp.can_fetch(self.user_agent, url)
                else:
                    # Cache expired
                    del self.robots_cache[domain]
                    del self.cache_expiry[domain]
            
            # Fetch robots.txt
            robots_url = urljoin(domain, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            
            try:
                rp.read()
                self.robots_cache[domain] = rp
                self.cache_expiry[domain] = datetime.now() + self.cache_duration
                return rp.can_fetch(self.user_agent, url)
            except Exception:
                # If robots.txt can't be fetched, assume allowed
                return True
                
        except Exception:
            # If anything fails, assume allowed
            return True

class ContentExtractor:
    """Extracts structured content from HTML pages."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract structured content from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract basic metadata
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            author = self._extract_author(soup)
            published_date = self._extract_published_date(soup)
            language = self._extract_language(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract tags/keywords
            tags = self._extract_tags(soup)
            
            # Extract links and images
            links = self._extract_links(soup, url)
            images = self._extract_images(soup, url)
            
            # Calculate word count
            word_count = len(content.split()) if content else 0
            
            return {
                'title': title,
                'content': content,
                'description': description,
                'author': author,
                'published_date': published_date,
                'tags': tags,
                'links': links,
                'images': images,
                'language': language,
                'word_count': word_count
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting content from {url}: {e}")
            return {
                'title': '',
                'content': '',
                'description': '',
                'author': None,
                'published_date': None,
                'tags': [],
                'links': [],
                'images': [],
                'language': None,
                'word_count': 0
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try different title sources
        title_sources = [
            soup.find('meta', property='og:title'),
            soup.find('meta', attrs={'name': 'twitter:title'}),
            soup.find('title'),
            soup.find('h1')
        ]
        
        for source in title_sources:
            if source:
                if source.name == 'meta':
                    title = source.get('content', '').strip()
                else:
                    title = source.get_text().strip()
                
                if title:
                    return title
        
        return 'Untitled'
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        # Try different description sources
        desc_sources = [
            soup.find('meta', property='og:description'),
            soup.find('meta', attrs={'name': 'twitter:description'}),
            soup.find('meta', attrs={'name': 'description'}),
            soup.find('meta', attrs={'name': 'Description'})
        ]
        
        for source in desc_sources:
            if source:
                desc = source.get('content', '').strip()
                if desc:
                    return desc
        
        return ''
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author information."""
        # Try different author sources
        author_sources = [
            soup.find('meta', attrs={'name': 'author'}),
            soup.find('meta', property='article:author'),
            soup.find('meta', attrs={'name': 'twitter:creator'}),
            soup.find(class_=re.compile(r'author', re.I)),
            soup.find('span', class_=re.compile(r'byline', re.I))
        ]
        
        for source in author_sources:
            if source:
                if source.name == 'meta':
                    author = source.get('content', '').strip()
                else:
                    author = source.get_text().strip()
                
                if author:
                    return author
        
        return None
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract published date."""
        # Try different date sources
        date_sources = [
            soup.find('meta', property='article:published_time'),
            soup.find('meta', attrs={'name': 'pubdate'}),
            soup.find('time', datetime=True),
            soup.find(class_=re.compile(r'date', re.I))
        ]
        
        for source in date_sources:
            if source:
                if source.name == 'meta':
                    date_str = source.get('content', '')
                elif source.name == 'time':
                    date_str = source.get('datetime', '') or source.get_text()
                else:
                    date_str = source.get_text()
                
                if date_str:
                    try:
                        # Try to parse various date formats
                        from dateutil import parser
                        return parser.parse(date_str)
                    except:
                        continue
        
        return None
    
    def _extract_language(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page language."""
        # Try different language sources
        html_tag = soup.find('html')
        if html_tag:
            lang = html_tag.get('lang') or html_tag.get('xml:lang')
            if lang:
                return lang
        
        # Try meta tag
        lang_meta = soup.find('meta', attrs={'http-equiv': 'content-language'})
        if lang_meta:
            return lang_meta.get('content')
        
        return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page."""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try to find main content area
        content_selectors = [
            'article',
            '[role="main"]',
            'main',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '#content',
            '#main-content'
        ]
        
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                text = content_area.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Ensure we have substantial content
                    return self._clean_text(text)
        
        # Fallback: extract from body
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
            return self._clean_text(text)
        
        # Last resort: all text
        return self._clean_text(soup.get_text(separator=' ', strip=True))
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/keywords from the page."""
        tags = set()
        
        # Try meta keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            keywords = keywords_meta.get('content', '')
            tags.update(tag.strip() for tag in keywords.split(',') if tag.strip())
        
        # Try article tags
        article_tags = soup.find_all(class_=re.compile(r'tag', re.I))
        for tag_elem in article_tags:
            tag_text = tag_elem.get_text().strip()
            if tag_text:
                tags.add(tag_text)
        
        return list(tags)
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from the page."""
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Filter out non-HTTP links
            if absolute_url.startswith(('http://', 'https://')):
                links.add(absolute_url)
        
        return list(links)
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from the page."""
        images = set()
        
        for img in soup.find_all('img', src=True):
            src = img['src']
            absolute_url = urljoin(base_url, src)
            
            # Filter out non-HTTP images
            if absolute_url.startswith(('http://', 'https://')):
                images.add(absolute_url)
        
        return list(images)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()

class WebScraper:
    """Main web scraping class with rate limiting and content extraction."""
    
    def __init__(self, user_agent: str = "Sovereign AI Curation Bot 1.0"):
        self.user_agent = user_agent
        self.rate_limiter = RateLimiter()
        self.robots_checker = RobotsChecker(user_agent)
        self.content_extractor = ContentExtractor()
        self.scraping_rules: Dict[str, ScrapingRule] = {}
        
        # Default session configuration
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.logger = logging.getLogger(__name__)
    
    def add_scraping_rule(self, domain: str, rule: ScrapingRule):
        """Add a scraping rule for a specific domain."""
        self.scraping_rules[domain] = rule
        self.logger.info(f"Added scraping rule for domain: {domain}")
    
    def get_scraping_rule(self, url: str) -> ScrapingRule:
        """Get the scraping rule for a URL."""
        domain = urlparse(url).netloc
        
        # Check for exact domain match
        if domain in self.scraping_rules:
            return self.scraping_rules[domain]
        
        # Check for subdomain matches
        for rule_domain, rule in self.scraping_rules.items():
            if domain.endswith(rule_domain):
                return rule
        
        # Return default rule
        return ScrapingRule(domain=domain)
    
    def can_scrape_url(self, url: str) -> Tuple[bool, str]:
        """Check if a URL can be scraped."""
        try:
            parsed_url = urlparse(url)
            
            # Check URL scheme
            if parsed_url.scheme not in ['http', 'https']:
                return False, "Only HTTP and HTTPS URLs are supported"
            
            # Check robots.txt
            rule = self.get_scraping_rule(url)
            if rule.respect_robots_txt:
                if not self.robots_checker.can_fetch(url):
                    return False, "Blocked by robots.txt"
            
            # Check rate limiting
            domain = parsed_url.netloc
            can_request, wait_time = self.rate_limiter.can_make_request(domain, rule)
            if not can_request:
                return False, f"Rate limited, wait {wait_time:.1f} seconds"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def scrape_url(self, url: str, wait_if_rate_limited: bool = True) -> Optional[ScrapedContent]:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape
            wait_if_rate_limited: Whether to wait if rate limited
            
        Returns:
            ScrapedContent object or None if failed
        """
        start_time = time.time()
        
        try:
            # Check if we can scrape
            can_scrape, reason = self.can_scrape_url(url)
            if not can_scrape:
                if "Rate limited" in reason and wait_if_rate_limited:
                    wait_time = float(reason.split()[-2])
                    self.logger.info(f"Rate limited for {url}, waiting {wait_time:.1f} seconds")
                    time.sleep(wait_time)
                    # Try again after waiting
                    can_scrape, reason = self.can_scrape_url(url)
                
                if not can_scrape:
                    self.logger.warning(f"Cannot scrape {url}: {reason}")
                    return None
            
            # Get scraping rule
            rule = self.get_scraping_rule(url)
            domain = urlparse(url).netloc
            
            # Record the request
            self.rate_limiter.record_request(domain)
            
            # Make the request
            headers = self.session.headers.copy()
            headers.update(rule.custom_headers)
            
            response = self.session.get(
                url,
                headers=headers,
                timeout=rule.timeout,
                allow_redirects=True
            )
            
            response_time = time.time() - start_time
            
            # Check response
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').split(';')[0].strip()
            if content_type not in rule.allowed_content_types:
                self.logger.warning(f"Unsupported content type {content_type} for {url}")
                return None
            
            # Extract content
            extracted = self.content_extractor.extract_content(response.text, url)
            
            # Create ScrapedContent object
            scraped_content = ScrapedContent(
                url=url,
                title=extracted['title'],
                content=extracted['content'],
                description=extracted['description'],
                author=extracted['author'],
                published_date=extracted['published_date'],
                tags=extracted['tags'],
                links=extracted['links'],
                images=extracted['images'],
                content_type=content_type,
                language=extracted['language'],
                word_count=extracted['word_count'],
                scraped_at=datetime.now(timezone.utc),
                response_time=response_time,
                status_code=response.status_code
            )
            
            self.logger.info(f"Successfully scraped {url}: {scraped_content.word_count} words")
            return scraped_content
            
        except requests.RequestException as e:
            self.logger.error(f"Request error scraping {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url}: {e}")
            return None
    
    def scrape_urls(self, urls: List[str], max_concurrent: int = 5) -> List[ScrapedContent]:
        """
        Scrape multiple URLs with concurrency control.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of ScrapedContent objects
        """
        results = []
        
        # For now, implement sequential scraping
        # TODO: Implement async scraping for better performance
        for url in urls:
            scraped = self.scrape_url(url)
            if scraped:
                results.append(scraped)
        
        return results
    
    def get_scraping_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return {
            "domains_with_rules": len(self.scraping_rules),
            "robots_cache_size": len(self.robots_checker.robots_cache),
            "rate_limiter_domains": len(self.rate_limiter.domain_requests),
            "user_agent": self.user_agent
        }

