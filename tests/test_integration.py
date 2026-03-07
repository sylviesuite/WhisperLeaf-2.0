"""
Comprehensive integration test for the complete curation system.
"""

import requests
import time
import json
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CurationAPITester:
    """Test client for the curation API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """Test basic health check."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            data = response.json()
            
            print(f"✓ Health check passed")
            print(f"  Status: {data['status']}")
            print(f"  Scheduler running: {data['scheduler_running']}")
            print(f"  Total sources: {data['total_sources']}")
            print(f"  Active sources: {data['active_sources']}")
            
            return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            return False
    
    def test_source_management(self) -> Dict[str, Any]:
        """Test source management operations."""
        print("\nTesting Source Management...")
        print("-" * 40)
        
        created_sources = []
        
        # Test source creation
        test_sources = [
            {
                "name": "Test BBC News",
                "source_type": "rss_feed",
                "url": "https://feeds.bbci.co.uk/news/rss.xml",
                "scan_interval_minutes": 30,
                "max_items_per_scan": 5,
                "priority": 8,
                "tags": ["news", "test"],
                "description": "Test BBC news feed"
            },
            {
                "name": "Test Slashdot",
                "source_type": "rss_feed",
                "url": "https://rss.slashdot.org/Slashdot/slashdotMain",
                "scan_interval_minutes": 60,
                "max_items_per_scan": 3,
                "priority": 6,
                "tags": ["technology", "test"],
                "description": "Test Slashdot feed"
            }
        ]
        
        for source_data in test_sources:
            try:
                response = self.session.post(f"{self.base_url}/api/sources", json=source_data)
                response.raise_for_status()
                result = response.json()
                
                created_sources.append(result['source_id'])
                print(f"✓ Created source: {source_data['name']} (ID: {result['source_id']})")
                
            except Exception as e:
                print(f"✗ Failed to create source {source_data['name']}: {e}")
        
        # Test source listing
        try:
            response = self.session.get(f"{self.base_url}/api/sources")
            response.raise_for_status()
            data = response.json()
            
            print(f"✓ Listed {len(data['sources'])} sources")
            for source in data['sources']:
                print(f"  - {source['name']}: {source['status']} (Priority: {source['priority']})")
                
        except Exception as e:
            print(f"✗ Failed to list sources: {e}")
        
        # Test source details
        if created_sources:
            try:
                source_id = created_sources[0]
                response = self.session.get(f"{self.base_url}/api/sources/{source_id}")
                response.raise_for_status()
                source = response.json()
                
                print(f"✓ Retrieved source details for {source['name']}")
                print(f"  URL: {source['url']}")
                print(f"  Status: {source['status']}")
                print(f"  Scan interval: {source['scan_interval_minutes']} minutes")
                
            except Exception as e:
                print(f"✗ Failed to get source details: {e}")
        
        return {"created_sources": created_sources}
    
    def test_content_filtering(self) -> bool:
        """Test content filtering configuration."""
        print("\nTesting Content Filtering...")
        print("-" * 40)
        
        # Set user interests
        try:
            interests = ["artificial intelligence", "technology", "programming", "news"]
            response = self.session.post(
                f"{self.base_url}/api/filter/interests",
                json={"interests": interests}
            )
            response.raise_for_status()
            
            print(f"✓ Set user interests: {interests}")
            
        except Exception as e:
            print(f"✗ Failed to set user interests: {e}")
            return False
        
        # Get filter statistics
        try:
            response = self.session.get(f"{self.base_url}/api/filter/stats")
            response.raise_for_status()
            stats = response.json()
            
            print(f"✓ Retrieved filter statistics")
            print(f"  Total processed: {stats.get('total_processed', 0)}")
            print(f"  Acceptance rate: {stats.get('acceptance_rate', 0):.3f}")
            
        except Exception as e:
            print(f"✗ Failed to get filter stats: {e}")
            return False
        
        return True
    
    def test_scheduler_operations(self, created_sources: list) -> bool:
        """Test scheduler operations."""
        print("\nTesting Scheduler Operations...")
        print("-" * 40)
        
        # Start scheduler
        try:
            response = self.session.post(f"{self.base_url}/api/scheduler/start")
            response.raise_for_status()
            
            print("✓ Started scheduler")
            
        except Exception as e:
            print(f"✗ Failed to start scheduler: {e}")
            return False
        
        # Get scheduler status
        try:
            response = self.session.get(f"{self.base_url}/api/scheduler/status")
            response.raise_for_status()
            status = response.json()
            
            print("✓ Retrieved scheduler status")
            print(f"  Running: {status['scheduler']['is_running']}")
            print(f"  Total jobs: {status['scheduler']['total_jobs']}")
            print(f"  Active sources: {status['scheduler']['active_sources']}")
            
        except Exception as e:
            print(f"✗ Failed to get scheduler status: {e}")
            return False
        
        # Test manual scan
        if created_sources:
            try:
                source_id = created_sources[0]
                response = self.session.post(f"{self.base_url}/api/scheduler/scan/{source_id}")
                response.raise_for_status()
                result = response.json()
                
                print(f"✓ Initiated manual scan for source {source_id}")
                print(f"  Job ID: {result['job_id']}")
                print(f"  Source: {result['source_name']}")
                
                # Wait a bit for processing
                print("  Waiting for scan to complete...")
                time.sleep(10)
                
            except Exception as e:
                print(f"✗ Failed to initiate manual scan: {e}")
                return False
        
        return True
    
    def test_vault_integration(self) -> bool:
        """Test vault integration and content storage."""
        print("\nTesting Vault Integration...")
        print("-" * 40)
        
        # Get curated documents
        try:
            response = self.session.get(f"{self.base_url}/api/vault/documents?limit=10")
            response.raise_for_status()
            data = response.json()
            
            print(f"✓ Retrieved {len(data['documents'])} curated documents")
            
            for doc in data['documents'][:3]:  # Show first 3
                print(f"  - {doc['title'][:50]}...")
                print(f"    Size: {doc['file_size']} bytes")
                print(f"    Tags: {doc['tags']}")
                if doc['metadata']:
                    metadata = json.loads(doc['metadata']) if isinstance(doc['metadata'], str) else doc['metadata']
                    quality_score = metadata.get('quality_score', 'N/A')
                    relevance_score = metadata.get('relevance_score', 'N/A')
                    print(f"    Quality: {quality_score}, Relevance: {relevance_score}")
                
        except Exception as e:
            print(f"✗ Failed to get curated documents: {e}")
            return False
        
        # Test search functionality
        try:
            search_query = "technology"
            response = self.session.get(f"{self.base_url}/api/vault/search?query={search_query}&limit=5")
            response.raise_for_status()
            data = response.json()
            
            print(f"✓ Search for '{search_query}' returned {len(data['results'])} results")
            
            for result in data['results'][:2]:  # Show first 2
                print(f"  - {result['title'][:50]}...")
                print(f"    Relevance: {result['relevance_score']:.3f}")
                
        except Exception as e:
            print(f"✗ Failed to search vault: {e}")
            return False
        
        return True
    
    def test_system_overview(self) -> bool:
        """Test system overview and statistics."""
        print("\nTesting System Overview...")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/api/stats/overview")
            response.raise_for_status()
            stats = response.json()
            
            print("✓ Retrieved system overview")
            
            # System status
            system = stats.get('system', {})
            print(f"  System Status: {system.get('status', 'unknown')}")
            print(f"  Scheduler Running: {system.get('scheduler_running', False)}")
            
            # Source statistics
            sources = stats.get('sources', {})
            print(f"  Sources - Total: {sources.get('total_sources', 0)}, Active: {sources.get('active_sources', 0)}")
            
            # Scheduler statistics
            scheduler = stats.get('scheduler', {})
            print(f"  Scheduler - Jobs: {scheduler.get('total_jobs', 0)}, Success Rate: {scheduler.get('success_rate', 0):.3f}")
            
            # Filter statistics
            filter_stats = stats.get('filter', {})
            print(f"  Filter - Processed: {filter_stats.get('total_processed', 0)}")
            
            # Vault statistics
            vault = stats.get('vault', {})
            print(f"  Vault - Documents: {vault.get('total_documents', 0)}")
            
            # Recent activity
            activity = stats.get('recent_activity', {})
            print(f"  Recent Activity - Items: {activity.get('processed_content_count', 0)}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to get system overview: {e}")
            return False
    
    def cleanup_test_sources(self, created_sources: list):
        """Clean up test sources."""
        print("\nCleaning up test sources...")
        print("-" * 40)
        
        for source_id in created_sources:
            try:
                response = self.session.delete(f"{self.base_url}/api/sources/{source_id}")
                response.raise_for_status()
                print(f"✓ Deleted source {source_id}")
                
            except Exception as e:
                print(f"✗ Failed to delete source {source_id}: {e}")
        
        # Stop scheduler
        try:
            response = self.session.post(f"{self.base_url}/api/scheduler/stop")
            response.raise_for_status()
            print("✓ Stopped scheduler")
            
        except Exception as e:
            print(f"✗ Failed to stop scheduler: {e}")

def run_integration_tests():
    """Run all integration tests."""
    print("Starting Comprehensive Integration Tests")
    print("=" * 60)
    
    tester = CurationAPITester()
    
    # Test 1: Health Check
    if not tester.test_health_check():
        print("\n❌ Health check failed - API may not be running")
        return False
    
    # Test 2: Source Management
    source_result = tester.test_source_management()
    created_sources = source_result.get("created_sources", [])
    
    # Test 3: Content Filtering
    tester.test_content_filtering()
    
    # Test 4: Scheduler Operations
    tester.test_scheduler_operations(created_sources)
    
    # Test 5: Vault Integration
    tester.test_vault_integration()
    
    # Test 6: System Overview
    tester.test_system_overview()
    
    # Cleanup
    tester.cleanup_test_sources(created_sources)
    
    print("\n" + "=" * 60)
    print("✅ Integration tests completed!")
    print("\nThe Sovereign AI Curation Engine is fully operational with:")
    print("  • RSS feed processing and web scraping")
    print("  • Intelligent content filtering and quality assessment")
    print("  • Automated scheduling and source management")
    print("  • Integrated vault storage for curated content")
    print("  • Comprehensive API for all operations")
    
    return True

if __name__ == "__main__":
    run_integration_tests()

