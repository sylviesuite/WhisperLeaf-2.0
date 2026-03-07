"""
Simple test to debug content extraction issues.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'curation'))

from curation.web_scraper import ContentExtractor
import requests
from bs4 import BeautifulSoup

def test_content_extraction():
    """Test content extraction with simple HTML."""
    
    # Test with simple HTML
    simple_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Page</title>
        <meta name="description" content="This is a test page">
        <meta name="author" content="Test Author">
        <meta name="keywords" content="test, html, content">
    </head>
    <body>
        <h1>Main Title</h1>
        <article>
            <p>This is the main content of the page. It contains several sentences.</p>
            <p>This is another paragraph with more content.</p>
        </article>
        <a href="https://example.com">Example Link</a>
        <img src="https://example.com/image.jpg" alt="Test Image">
    </body>
    </html>
    """
    
    print("Testing Content Extraction with Simple HTML...")
    print("=" * 60)
    
    extractor = ContentExtractor()
    
    try:
        result = extractor.extract_content(simple_html, "https://test.com")
        
        print("Extraction Results:")
        print(f"  Title: {result['title']}")
        print(f"  Description: {result['description']}")
        print(f"  Author: {result['author']}")
        print(f"  Content: {result['content'][:100]}...")
        print(f"  Word count: {result['word_count']}")
        print(f"  Tags: {result['tags']}")
        print(f"  Links: {result['links']}")
        print(f"  Images: {result['images']}")
        print(f"  Language: {result['language']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_real_page():
    """Test with a real simple page."""
    print("\nTesting with real page...")
    print("=" * 60)
    
    try:
        response = requests.get("https://example.com", timeout=10)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Content type: {response.headers.get('content-type')}")
        print(f"Content length: {len(response.text)} chars")
        
        # Show first 500 chars of HTML
        print(f"HTML preview: {response.text[:500]}...")
        
        # Test extraction
        extractor = ContentExtractor()
        result = extractor.extract_content(response.text, "https://example.com")
        
        print("\nExtraction Results:")
        print(f"  Title: {result['title']}")
        print(f"  Description: {result['description']}")
        print(f"  Content: {result['content'][:200]}...")
        print(f"  Word count: {result['word_count']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_beautifulsoup_directly():
    """Test BeautifulSoup directly to isolate the issue."""
    print("\nTesting BeautifulSoup directly...")
    print("=" * 60)
    
    html = """
    <html>
    <head>
        <title>Test</title>
        <meta name="description" content="Test description">
    </head>
    <body>
        <h1>Hello World</h1>
        <p>This is test content.</p>
    </body>
    </html>
    """
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test different find methods
        print("Testing find methods:")
        
        title = soup.find('title')
        print(f"  Title tag: {title}")
        print(f"  Title text: {title.get_text() if title else 'None'}")
        
        # Test meta tag finding
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        print(f"  Meta description: {meta_desc}")
        print(f"  Meta content: {meta_desc.get('content') if meta_desc else 'None'}")
        
        # Test content extraction
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
            print(f"  Body text: {text}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_beautifulsoup_directly()
    test_content_extraction()
    test_real_page()

