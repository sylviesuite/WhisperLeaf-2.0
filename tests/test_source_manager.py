"""
Test script for source management and automated scheduling.
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'curation'))

from curation.source_manager import (
    SourceManager, CurationScheduler, SourceConfig, 
    SourceType, SourceStatus, CurationJob
)
from curation.content_filter import FilterAction
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_source_manager():
    """Test the source manager functionality."""
    print("Testing Source Manager...")
    print("=" * 60)
    
    # Create source manager
    manager = SourceManager(config_file="./data/test_sources_config.json")
    
    # Create test sources
    test_sources = [
        SourceConfig(
            id="bbc_news",
            name="BBC News RSS",
            source_type=SourceType.RSS_FEED,
            url="https://feeds.bbci.co.uk/news/rss.xml",
            scan_interval_minutes=30,
            max_items_per_scan=10,
            priority=8,
            tags=["news", "international"],
            description="BBC international news feed"
        ),
        SourceConfig(
            id="slashdot_tech",
            name="Slashdot Technology",
            source_type=SourceType.RSS_FEED,
            url="https://rss.slashdot.org/Slashdot/slashdotMain",
            scan_interval_minutes=60,
            max_items_per_scan=15,
            priority=6,
            tags=["technology", "programming"],
            description="Technology news and discussions"
        ),
        SourceConfig(
            id="example_page",
            name="Example Web Page",
            source_type=SourceType.WEB_PAGE,
            url="https://example.com",
            scan_interval_minutes=120,
            max_items_per_scan=1,
            priority=3,
            tags=["example", "test"],
            description="Test web page for scraping"
        )
    ]
    
    # Add sources
    print("Adding test sources...")
    for source in test_sources:
        success = manager.add_source(source)
        print(f"  Added {source.name}: {'✓' if success else '✗'}")
    
    # List sources
    print(f"\nListing all sources:")
    all_sources = manager.list_sources()
    for source in all_sources:
        print(f"  - {source.name} ({source.id}): {source.status.value}, Priority: {source.priority}")
    
    # Test source filtering
    print(f"\nRSS Feed sources:")
    rss_sources = manager.get_sources_by_type(SourceType.RSS_FEED)
    for source in rss_sources:
        print(f"  - {source.name}: {source.url}")
    
    # Test source updates
    print(f"\nUpdating source status...")
    success = manager.update_source("example_page", status="paused", priority=1)
    print(f"Updated example_page: {'✓' if success else '✗'}")
    
    # Test source statistics update
    print(f"\nUpdating source statistics...")
    manager.update_source_stats("bbc_news", quality_score=0.8, relevance_score=0.7, success=True)
    manager.update_source_stats("bbc_news", quality_score=0.6, relevance_score=0.9, success=True)
    
    updated_source = manager.get_source("bbc_news")
    if updated_source:
        print(f"BBC News stats:")
        print(f"  Avg Quality: {updated_source.avg_quality_score:.3f}")
        print(f"  Avg Relevance: {updated_source.avg_relevance_score:.3f}")
        print(f"  Success Rate: {updated_source.success_rate:.3f}")
        print(f"  Total Processed: {updated_source.total_items_processed}")
    
    return manager

def test_curation_scheduler(source_manager):
    """Test the curation scheduler."""
    print("\n\nTesting Curation Scheduler...")
    print("=" * 60)
    
    # Create scheduler
    scheduler = CurationScheduler(source_manager)
    
    # Set up callbacks to track processed content
    processed_content = []
    completed_jobs = []
    
    def on_content_processed(source_id, content, filter_result):
        processed_content.append({
            'source_id': source_id,
            'content_type': type(content).__name__,
            'action': filter_result.action.value,
            'quality_score': filter_result.score.quality_score,
            'relevance_score': filter_result.score.relevance_score
        })
        print(f"  Content processed from {source_id}: {filter_result.action.value}")
    
    def on_job_completed(job):
        completed_jobs.append(job)
        print(f"  Job {job.id} completed: {job.status}")
    
    def on_error(source_id, error_message):
        print(f"  Error in {source_id}: {error_message}")
    
    # Set callbacks
    scheduler.on_content_processed = on_content_processed
    scheduler.on_job_completed = on_job_completed
    scheduler.on_error = on_error
    
    # Configure content filter with user interests
    scheduler.content_filter.set_user_interests(['technology', 'news', 'artificial intelligence'])
    
    # Test manual job scheduling
    print("Scheduling manual jobs...")
    
    # Schedule jobs for active sources
    active_sources = source_manager.list_sources(SourceStatus.ACTIVE)
    job_ids = []
    
    for source in active_sources:
        job_id = scheduler.schedule_source_scan(source.id)
        if job_id:
            job_ids.append(job_id)
            print(f"  Scheduled job {job_id} for {source.name}")
    
    # Execute jobs manually
    print(f"\nExecuting {len(job_ids)} scheduled jobs...")
    for job_id in job_ids:
        print(f"\nExecuting job {job_id}...")
        success = scheduler.execute_job(job_id)
        print(f"Job {job_id} result: {'✓' if success else '✗'}")
        
        # Show job status
        job_status = scheduler.get_job_status(job_id)
        if job_status:
            print(f"  Status: {job_status['status']}")
            print(f"  Items processed: {job_status['items_processed']}")
            print(f"  Items accepted: {job_status['items_accepted']}")
            if job_status['error_message']:
                print(f"  Error: {job_status['error_message']}")
    
    # Show processed content summary
    print(f"\nContent Processing Summary:")
    print(f"  Total items processed: {len(processed_content)}")
    
    if processed_content:
        actions = {}
        avg_quality = 0
        avg_relevance = 0
        
        for item in processed_content:
            action = item['action']
            actions[action] = actions.get(action, 0) + 1
            avg_quality += item['quality_score']
            avg_relevance += item['relevance_score']
        
        avg_quality /= len(processed_content)
        avg_relevance /= len(processed_content)
        
        print(f"  Actions taken:")
        for action, count in actions.items():
            print(f"    {action}: {count}")
        print(f"  Average quality score: {avg_quality:.3f}")
        print(f"  Average relevance score: {avg_relevance:.3f}")
    
    # Show scheduler statistics
    stats = scheduler.get_scheduler_stats()
    print(f"\nScheduler Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    
    return scheduler

def test_automated_scheduling(scheduler):
    """Test automated scheduling (brief test)."""
    print("\n\nTesting Automated Scheduling...")
    print("=" * 60)
    
    print("Starting automated scheduler for 10 seconds...")
    
    # Start the scheduler
    scheduler.start_scheduler()
    
    # Let it run for a short time
    time.sleep(10)
    
    # Stop the scheduler
    scheduler.stop_scheduler()
    
    print("Automated scheduler test completed")
    
    # Show final stats
    stats = scheduler.get_scheduler_stats()
    print(f"Final scheduler stats:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

def test_source_performance_tracking():
    """Test source performance tracking over time."""
    print("\n\nTesting Source Performance Tracking...")
    print("=" * 60)
    
    manager = SourceManager(config_file="./data/performance_test_config.json")
    
    # Create a test source
    test_source = SourceConfig(
        id="performance_test",
        name="Performance Test Source",
        source_type=SourceType.RSS_FEED,
        url="https://feeds.bbci.co.uk/news/rss.xml",
        scan_interval_minutes=60
    )
    
    manager.add_source(test_source)
    
    # Simulate processing multiple items with varying quality
    test_data = [
        (0.9, 0.8, True),   # High quality, high relevance, accepted
        (0.7, 0.6, True),   # Good quality, good relevance, accepted
        (0.3, 0.2, False),  # Low quality, low relevance, rejected
        (0.8, 0.9, True),   # High quality, high relevance, accepted
        (0.4, 0.3, False),  # Low quality, low relevance, rejected
        (0.6, 0.7, True),   # Medium quality, good relevance, accepted
    ]
    
    print("Simulating content processing...")
    for i, (quality, relevance, success) in enumerate(test_data, 1):
        manager.update_source_stats("performance_test", quality, relevance, success)
        
        source = manager.get_source("performance_test")
        print(f"  Item {i}: Q={quality:.1f}, R={relevance:.1f}, Success={success}")
        print(f"    Running avg quality: {source.avg_quality_score:.3f}")
        print(f"    Running avg relevance: {source.avg_relevance_score:.3f}")
        print(f"    Success rate: {source.success_rate:.3f}")
    
    # Show final source performance
    final_source = manager.get_source("performance_test")
    print(f"\nFinal Performance Metrics:")
    print(f"  Total items processed: {final_source.total_items_processed}")
    print(f"  Total items accepted: {final_source.total_items_accepted}")
    print(f"  Average quality score: {final_source.avg_quality_score:.3f}")
    print(f"  Average relevance score: {final_source.avg_relevance_score:.3f}")
    print(f"  Overall success rate: {final_source.success_rate:.3f}")

if __name__ == "__main__":
    # Run all tests
    source_manager = test_source_manager()
    scheduler = test_curation_scheduler(source_manager)
    test_automated_scheduling(scheduler)
    test_source_performance_tracking()
    
    print("\n✓ Source management and scheduling tests completed!")

