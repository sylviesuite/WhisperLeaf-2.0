"""
Test script for content filtering and quality assessment.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'curation'))

from curation.content_filter import (
    ContentFilter, FilterRule, ContentQualityAnalyzer, 
    RelevanceAnalyzer, DuplicateDetector, FilterAction
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_quality_analyzer():
    """Test the content quality analyzer."""
    print("Testing Content Quality Analyzer...")
    print("=" * 60)
    
    analyzer = ContentQualityAnalyzer()
    
    # Test different types of content
    test_contents = [
        {
            'name': 'High Quality Article',
            'content': """
            Artificial Intelligence Research: A Comprehensive Analysis
            
            This research paper presents a comprehensive analysis of recent developments 
            in artificial intelligence. The study examines various methodologies and 
            their applications in real-world scenarios.
            
            Introduction
            
            The field of artificial intelligence has experienced unprecedented growth 
            in recent years. This paper aims to provide evidence-based insights into 
            the current state of AI research and its future implications.
            
            Methodology
            
            Our research methodology involved analyzing peer-reviewed publications 
            from leading academic journals. We examined data from over 500 studies 
            published between 2020 and 2024.
            
            Findings
            
            The analysis reveals several key trends in AI development:
            - Increased focus on ethical AI frameworks
            - Growing adoption of transformer architectures
            - Enhanced performance in natural language processing tasks
            
            Conclusion
            
            The evidence suggests that AI research continues to advance rapidly, 
            with significant implications for various industries and society as a whole.
            """,
            'metadata': {
                'title': 'Artificial Intelligence Research: A Comprehensive Analysis',
                'author': 'Dr. Jane Smith',
                'tags': ['AI', 'research', 'analysis', 'technology']
            }
        },
        {
            'name': 'Low Quality Content',
            'content': "OMG!!! You won't BELIEVE this SHOCKING secret!!! Click here NOW!!!",
            'metadata': {
                'title': 'SHOCKING SECRET REVEALED!!!',
                'tags': ['clickbait', 'shocking']
            }
        },
        {
            'name': 'Medium Quality Blog Post',
            'content': """
            Getting Started with Python Programming
            
            Python is a popular programming language that's great for beginners. 
            In this post, I'll share some tips for learning Python effectively.
            
            First, start with the basics like variables and data types. Then move 
            on to control structures like loops and conditionals. Practice is key!
            
            Here are some good resources:
            - Python.org official tutorial
            - Codecademy Python course
            - Practice problems on HackerRank
            
            Remember, learning programming takes time and patience. Don't get 
            discouraged if you don't understand everything immediately.
            """,
            'metadata': {
                'title': 'Getting Started with Python Programming',
                'author': 'John Doe',
                'tags': ['python', 'programming', 'tutorial']
            }
        },
        {
            'name': 'Very Short Content',
            'content': "AI is cool.",
            'metadata': {'title': 'AI'}
        }
    ]
    
    for test_case in test_contents:
        print(f"\nAnalyzing: {test_case['name']}")
        print("-" * 40)
        
        score = analyzer.analyze_quality(test_case['content'], test_case['metadata'])
        
        print(f"Quality Score: {score.quality_score:.3f}")
        print(f"Overall Score: {score.overall_score:.3f}")
        print(f"Confidence: {score.confidence:.3f}")
        print(f"Reasons: {', '.join(score.reasons)}")
        print(f"Word Count: {score.metadata.get('word_count', 'N/A')}")

def test_relevance_analyzer():
    """Test the relevance analyzer."""
    print("\n\nTesting Relevance Analyzer...")
    print("=" * 60)
    
    # Set up analyzer with user interests
    user_interests = ['artificial intelligence', 'machine learning', 'programming', 'technology']
    analyzer = RelevanceAnalyzer(user_interests)
    
    test_contents = [
        {
            'name': 'Highly Relevant AI Content',
            'content': """
            Machine learning algorithms have revolutionized artificial intelligence 
            applications. Deep learning neural networks are particularly effective 
            for natural language processing and computer vision tasks.
            """,
            'metadata': {
                'title': 'Advances in Machine Learning and AI',
                'tags': ['AI', 'machine learning', 'deep learning']
            }
        },
        {
            'name': 'Somewhat Relevant Tech Content',
            'content': """
            The latest smartphone features include improved cameras and faster processors. 
            Technology companies are competing to create the most innovative devices 
            for consumers worldwide.
            """,
            'metadata': {
                'title': 'Latest Smartphone Technology Trends',
                'tags': ['technology', 'smartphones', 'innovation']
            }
        },
        {
            'name': 'Irrelevant Content',
            'content': """
            The weather today is sunny with a chance of rain in the afternoon. 
            Don't forget to bring an umbrella if you're going out. The temperature 
            will reach a high of 75 degrees Fahrenheit.
            """,
            'metadata': {
                'title': 'Today\'s Weather Forecast',
                'tags': ['weather', 'forecast', 'rain']
            }
        }
    ]
    
    for test_case in test_contents:
        print(f"\nAnalyzing: {test_case['name']}")
        print("-" * 40)
        
        relevance_score = analyzer.analyze_relevance(test_case['content'], test_case['metadata'])
        
        print(f"Relevance Score: {relevance_score:.3f}")
        print(f"User Interests: {user_interests}")

def test_duplicate_detector():
    """Test the duplicate detector."""
    print("\n\nTesting Duplicate Detector...")
    print("=" * 60)
    
    detector = DuplicateDetector()
    
    # Test content
    original_content = """
    Artificial intelligence is transforming the way we work and live. 
    Machine learning algorithms are becoming more sophisticated every day.
    """
    
    duplicate_content = """
    Artificial intelligence is transforming the way we work and live. 
    Machine learning algorithms are becoming more sophisticated every day.
    """
    
    similar_content = """
    AI is changing how we work and live. Machine learning algorithms 
    are getting more advanced each day.
    """
    
    different_content = """
    The weather is nice today. I think I'll go for a walk in the park.
    """
    
    test_cases = [
        ('Original Content', original_content),
        ('Exact Duplicate', duplicate_content),
        ('Similar Content', similar_content),
        ('Different Content', different_content),
        ('Original Again', original_content)  # Test exact duplicate detection
    ]
    
    for name, content in test_cases:
        print(f"\nTesting: {name}")
        print("-" * 30)
        
        is_duplicate, similarity, original_hash = detector.is_duplicate(content)
        
        print(f"Is Duplicate: {is_duplicate}")
        print(f"Similarity Score: {similarity:.3f}")
        print(f"Original Hash: {original_hash[:8] if original_hash else 'None'}...")
    
    # Show detector stats
    stats = detector.get_duplicate_stats()
    print(f"\nDuplicate Detector Stats:")
    print(f"Total Content Hashes: {stats['total_content_hashes']}")
    print(f"Similarity Threshold: {stats['similarity_threshold']}")

def test_content_filter():
    """Test the complete content filtering system."""
    print("\n\nTesting Complete Content Filter...")
    print("=" * 60)
    
    # Create filter with custom rules
    custom_rule = FilterRule(
        name="AI Content Filter",
        description="Filter for AI-related content",
        required_keywords=['artificial intelligence', 'machine learning', 'AI', 'ML', 'technology'],
        excluded_keywords=['clickbait', 'shocking', 'secret'],
        min_word_count=30,
        min_quality_score=0.4,
        min_relevance_score=0.3
    )
    
    content_filter = ContentFilter([custom_rule])
    
    # Set user interests
    content_filter.set_user_interests(['artificial intelligence', 'machine learning', 'programming'])
    
    # Test different content
    test_contents = [
        {
            'name': 'High Quality AI Article',
            'content': """
            Recent advances in artificial intelligence have led to breakthrough 
            applications in healthcare, finance, and transportation. Machine learning 
            algorithms are now capable of processing vast amounts of data to identify 
            patterns and make predictions with unprecedented accuracy.
            
            Deep learning neural networks have shown particular promise in image 
            recognition and natural language processing tasks. These technologies 
            are transforming industries and creating new opportunities for innovation.
            """,
            'metadata': {
                'title': 'AI Breakthroughs in Various Industries',
                'tags': ['AI', 'machine learning', 'technology', 'innovation']
            },
            'source_url': 'https://example.com/ai-article'
        },
        {
            'name': 'Low Quality Clickbait',
            'content': "You won't believe this shocking AI secret that tech companies don't want you to know!",
            'metadata': {
                'title': 'SHOCKING AI SECRET REVEALED',
                'tags': ['AI', 'shocking', 'secret']
            },
            'source_url': 'https://clickbait.com/shocking-secret'
        },
        {
            'name': 'Irrelevant Content',
            'content': """
            The best pizza recipes include fresh ingredients and proper cooking techniques. 
            Start with high-quality flour for the dough and use San Marzano tomatoes 
            for the sauce. Don't forget to preheat your oven to the highest temperature.
            """,
            'metadata': {
                'title': 'Best Pizza Recipes',
                'tags': ['cooking', 'pizza', 'recipes']
            },
            'source_url': 'https://cooking.com/pizza-recipes'
        },
        {
            'name': 'Short AI Content',
            'content': "AI is the future of technology.",
            'metadata': {
                'title': 'AI Future',
                'tags': ['AI', 'technology']
            },
            'source_url': 'https://tech.com/ai-future'
        }
    ]
    
    for test_case in test_contents:
        print(f"\nFiltering: {test_case['name']}")
        print("-" * 40)
        
        result = content_filter.filter_content(
            test_case['content'], 
            test_case['metadata'], 
            test_case['source_url']
        )
        
        print(f"Action: {result.action.value.upper()}")
        print(f"Quality Score: {result.score.quality_score:.3f}")
        print(f"Relevance Score: {result.score.relevance_score:.3f}")
        print(f"Overall Score: {result.score.overall_score:.3f}")
        print(f"Confidence: {result.score.confidence:.3f}")
        print(f"Reasons: {', '.join(result.score.reasons)}")
    
    # Show filter statistics
    print(f"\nFilter Statistics:")
    stats = content_filter.get_filter_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    test_quality_analyzer()
    test_relevance_analyzer()
    test_duplicate_detector()
    test_content_filter()
    print("\n✓ Content filtering tests completed!")

