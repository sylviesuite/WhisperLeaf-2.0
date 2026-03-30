"""
Automated Scheduling and Source Management System for Content Curation.
"""

import json
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from pathlib import Path
import schedule
import time

from .rss_processor import RSSProcessor, FeedInfo, FeedItem
from .web_scraper import WebScraper, ScrapedContent
from .content_filter import ContentFilter, FilterResult, FilterAction

class SourceType(Enum):
    """Types of content sources."""
    RSS_FEED = "rss_feed"
    WEB_PAGE = "web_page"
    WEB_SEARCH = "web_search"
    MANUAL = "manual"

class SourceStatus(Enum):
    """Status of a content source."""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class SourceConfig:
    """Configuration for a content source."""
    id: str
    name: str
    source_type: SourceType
    url: str
    status: SourceStatus = SourceStatus.ACTIVE
    
    # Scheduling configuration
    scan_interval_minutes: int = 60
    max_items_per_scan: int = 50
    priority: int = 1  # 1-10, higher is more important
    
    # Processing configuration
    enable_filtering: bool = True
    custom_filter_rules: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata and tracking
    tags: List[str] = field(default_factory=list)
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_scan: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error_count: int = 0
    total_items_processed: int = 0
    total_items_accepted: int = 0
    
    # Statistics
    avg_quality_score: float = 0.0
    avg_relevance_score: float = 0.0
    success_rate: float = 1.0

@dataclass
class CurationJob:
    """Represents a scheduled curation job."""
    id: str
    source_id: str
    scheduled_time: datetime
    priority: int
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    items_processed: int = 0
    items_accepted: int = 0

class SourceManager:
    """Manages content sources and their configurations."""
    
    def __init__(self, config_file: str = "./data/sources_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.sources: Dict[str, SourceConfig] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load existing configuration
        self.load_config()
    
    def add_source(self, source_config: SourceConfig) -> bool:
        """Add a new content source."""
        try:
            self.sources[source_config.id] = source_config
            self.save_config()
            self.logger.info(f"Added source: {source_config.name} ({source_config.id})")
            return True
        except Exception as e:
            self.logger.error(f"Error adding source {source_config.id}: {e}")
            return False
    
    def remove_source(self, source_id: str) -> bool:
        """Remove a content source."""
        if source_id in self.sources:
            source_name = self.sources[source_id].name
            del self.sources[source_id]
            self.save_config()
            self.logger.info(f"Removed source: {source_name} ({source_id})")
            return True
        return False
    
    def update_source(self, source_id: str, **kwargs) -> bool:
        """Update source configuration."""
        if source_id not in self.sources:
            return False
        
        source = self.sources[source_id]
        
        # Update allowed fields
        for key, value in kwargs.items():
            if hasattr(source, key):
                if key == 'status' and isinstance(value, str):
                    source.status = SourceStatus(value)
                elif key == 'source_type' and isinstance(value, str):
                    source.source_type = SourceType(value)
                else:
                    setattr(source, key, value)
        
        self.save_config()
        self.logger.info(f"Updated source: {source.name} ({source_id})")
        return True
    
    def get_source(self, source_id: str) -> Optional[SourceConfig]:
        """Get a specific source configuration."""
        return self.sources.get(source_id)
    
    def list_sources(self, status: Optional[SourceStatus] = None) -> List[SourceConfig]:
        """List all sources, optionally filtered by status."""
        sources = list(self.sources.values())
        if status:
            sources = [s for s in sources if s.status == status]
        return sorted(sources, key=lambda x: x.priority, reverse=True)
    
    def get_sources_by_type(self, source_type: SourceType) -> List[SourceConfig]:
        """Get sources by type."""
        return [s for s in self.sources.values() if s.source_type == source_type]
    
    def update_source_stats(self, source_id: str, quality_score: float, 
                          relevance_score: float, success: bool):
        """Update source statistics."""
        if source_id not in self.sources:
            return
        
        source = self.sources[source_id]
        
        # Update running averages
        total_processed = source.total_items_processed
        if total_processed > 0:
            source.avg_quality_score = (
                (source.avg_quality_score * total_processed + quality_score) / 
                (total_processed + 1)
            )
            source.avg_relevance_score = (
                (source.avg_relevance_score * total_processed + relevance_score) / 
                (total_processed + 1)
            )
        else:
            source.avg_quality_score = quality_score
            source.avg_relevance_score = relevance_score
        
        source.total_items_processed += 1
        if success:
            source.total_items_accepted += 1
        
        # Update success rate
        source.success_rate = source.total_items_accepted / source.total_items_processed
        
        self.save_config()
    
    def save_config(self):
        """Save source configuration to file."""
        try:
            config_data = {
                'sources': {
                    source_id: {
                        **asdict(source),
                        'source_type': source.source_type.value,
                        'status': source.status.value,
                        'created_at': source.created_at.isoformat(),
                        'last_scan': source.last_scan.isoformat() if source.last_scan else None,
                        'last_success': source.last_success.isoformat() if source.last_success else None
                    }
                    for source_id, source in self.sources.items()
                },
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def load_config(self):
        """Load source configuration from file."""
        try:
            if not self.config_file.exists():
                return
            
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load sources
            sources_data = config_data.get('sources', {})
            for source_id, source_data in sources_data.items():
                # Parse datetime fields
                source_data['created_at'] = datetime.fromisoformat(source_data['created_at'])
                if source_data.get('last_scan'):
                    source_data['last_scan'] = datetime.fromisoformat(source_data['last_scan'])
                if source_data.get('last_success'):
                    source_data['last_success'] = datetime.fromisoformat(source_data['last_success'])
                
                # Parse enums
                source_data['source_type'] = SourceType(source_data['source_type'])
                source_data['status'] = SourceStatus(source_data['status'])
                
                self.sources[source_id] = SourceConfig(**source_data)
            
            self.logger.info(f"Loaded {len(self.sources)} sources from config")
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")

class CurationScheduler:
    """Schedules and manages automated content curation jobs."""
    
    def __init__(self, source_manager: SourceManager):
        self.source_manager = source_manager
        self.rss_processor = RSSProcessor()
        self.web_scraper = WebScraper()
        self.content_filter = ContentFilter()
        
        self.jobs: Dict[str, CurationJob] = {}
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        # Callbacks for events
        self.on_content_processed: Optional[Callable[[str, Any, FilterResult], None]] = None
        self.on_job_completed: Optional[Callable[[CurationJob], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None
        
        self.logger = logging.getLogger(__name__)
    
    def start_scheduler(self) -> bool:
        """Start the automated scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return False
        
        self.is_running = True
        
        # Schedule sources based on their intervals
        self._schedule_sources()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Started curation scheduler")
        return True
    
    def stop_scheduler(self) -> bool:
        """Stop the automated scheduler."""
        if not self.is_running:
            return False
        
        self.is_running = False
        
        # Clear scheduled jobs
        schedule.clear()
        
        # Wait for thread to finish
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Stopped curation scheduler")
        return True
    
    def schedule_source_scan(self, source_id: str, delay_minutes: int = 0) -> Optional[str]:
        """Schedule a scan for a specific source."""
        source = self.source_manager.get_source(source_id)
        if not source or source.status != SourceStatus.ACTIVE:
            return None
        
        job_id = f"{source_id}_{int(time.time())}"
        scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
        
        job = CurationJob(
            id=job_id,
            source_id=source_id,
            scheduled_time=scheduled_time,
            priority=source.priority
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Scheduled job {job_id} for source {source.name}")
        return job_id
    
    def execute_job(self, job_id: str) -> bool:
        """Execute a specific curation job."""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        source = self.source_manager.get_source(job.source_id)
        
        if not source:
            job.status = "failed"
            job.error_message = "Source not found"
            return False
        
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Executing job {job_id} for source {source.name}")
            
            # Process based on source type
            if source.source_type == SourceType.RSS_FEED:
                success = self._process_rss_source(source, job)
            elif source.source_type == SourceType.WEB_PAGE:
                success = self._process_web_source(source, job)
            else:
                job.error_message = f"Unsupported source type: {source.source_type}"
                success = False
            
            # Update job status
            job.status = "completed" if success else "failed"
            job.completed_at = datetime.now(timezone.utc)
            
            # Update source timestamps
            source.last_scan = datetime.now(timezone.utc)
            if success:
                source.last_success = source.last_scan
                source.error_count = 0
            else:
                source.error_count += 1
            
            self.source_manager.save_config()
            
            # Call completion callback
            if self.on_job_completed:
                self.on_job_completed(job)
            
            return success
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            
            source.error_count += 1
            self.source_manager.save_config()
            
            if self.on_error:
                self.on_error(job.source_id, str(e))
            
            self.logger.error(f"Job {job_id} failed: {e}")
            return False
    
    def _process_rss_source(self, source: SourceConfig, job: CurationJob) -> bool:
        """Process an RSS feed source."""
        try:
            feed_info, feed_items = self.rss_processor.process_feed(
                source.url, max_items=source.max_items_per_scan
            )
            
            if not feed_info:
                job.error_message = "Failed to fetch RSS feed"
                return False
            
            processed_count = 0
            accepted_count = 0
            
            for item in feed_items:
                # Convert RSS item to content for filtering
                content = f"{item.title}\n\n{item.content}"
                metadata = {
                    'title': item.title,
                    'author': item.author,
                    'published_date': item.published,
                    'tags': item.tags,
                    'source_url': item.link
                }
                
                # Apply content filtering if enabled
                if source.enable_filtering:
                    filter_result = self.content_filter.filter_content(
                        content, metadata, item.link
                    )
                    
                    # Update source statistics
                    self.source_manager.update_source_stats(
                        source.id,
                        filter_result.score.quality_score,
                        filter_result.score.relevance_score,
                        filter_result.action == FilterAction.ACCEPT
                    )
                    
                    if filter_result.action == FilterAction.ACCEPT:
                        accepted_count += 1
                    
                    # Call content processed callback
                    if self.on_content_processed:
                        self.on_content_processed(source.id, item, filter_result)
                else:
                    accepted_count += 1
                    if self.on_content_processed:
                        # Create a dummy filter result for unfiltered content
                        from .content_filter import ContentScore
                        dummy_result = FilterResult(
                            action=FilterAction.ACCEPT,
                            score=ContentScore(0.5, 0.5, 0.5, 0.5),
                            content_hash="",
                            filtered_at=datetime.now(timezone.utc)
                        )
                        self.on_content_processed(source.id, item, dummy_result)
                
                processed_count += 1
            
            job.items_processed = processed_count
            job.items_accepted = accepted_count
            
            self.logger.info(f"Processed {processed_count} items from {source.name}, accepted {accepted_count}")
            return True
            
        except Exception as e:
            job.error_message = str(e)
            return False
    
    def _process_web_source(self, source: SourceConfig, job: CurationJob) -> bool:
        """Process a web page source."""
        try:
            scraped_content = self.web_scraper.scrape_url(source.url)
            
            if not scraped_content:
                job.error_message = "Failed to scrape web page"
                return False
            
            # Apply content filtering if enabled
            if source.enable_filtering:
                metadata = {
                    'title': scraped_content.title,
                    'author': scraped_content.author,
                    'published_date': scraped_content.published_date,
                    'tags': scraped_content.tags,
                    'source_url': scraped_content.url
                }
                
                filter_result = self.content_filter.filter_content(
                    scraped_content.content, metadata, scraped_content.url
                )
                
                # Update source statistics
                self.source_manager.update_source_stats(
                    source.id,
                    filter_result.score.quality_score,
                    filter_result.score.relevance_score,
                    filter_result.action == FilterAction.ACCEPT
                )
                
                accepted = 1 if filter_result.action == FilterAction.ACCEPT else 0
                
                # Call content processed callback
                if self.on_content_processed:
                    self.on_content_processed(source.id, scraped_content, filter_result)
            else:
                accepted = 1
                if self.on_content_processed:
                    # Create a dummy filter result for unfiltered content
                    from .content_filter import ContentScore
                    dummy_result = FilterResult(
                        action=FilterAction.ACCEPT,
                        score=ContentScore(0.5, 0.5, 0.5, 0.5),
                        content_hash="",
                        filtered_at=datetime.now(timezone.utc)
                    )
                    self.on_content_processed(source.id, scraped_content, dummy_result)
            
            job.items_processed = 1
            job.items_accepted = accepted
            
            self.logger.info(f"Processed web page from {source.name}, accepted: {accepted}")
            return True
            
        except Exception as e:
            job.error_message = str(e)
            return False
    
    def _schedule_sources(self):
        """Schedule all active sources for monitoring."""
        schedule.clear()
        
        active_sources = self.source_manager.list_sources(SourceStatus.ACTIVE)
        
        for source in active_sources:
            # Schedule based on interval
            schedule.every(source.scan_interval_minutes).minutes.do(
                self._create_scheduled_job, source.id
            )
            
            self.logger.debug(f"Scheduled {source.name} every {source.scan_interval_minutes} minutes")
    
    def _create_scheduled_job(self, source_id: str):
        """Create a scheduled job for a source."""
        job_id = self.schedule_source_scan(source_id)
        if job_id:
            # Execute immediately in a separate thread to avoid blocking scheduler
            threading.Thread(target=self.execute_job, args=(job_id,), daemon=True).start()
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job."""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        return {
            'id': job.id,
            'source_id': job.source_id,
            'status': job.status,
            'scheduled_time': job.scheduled_time.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'items_processed': job.items_processed,
            'items_accepted': job.items_accepted,
            'error_message': job.error_message
        }
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total_jobs = len(self.jobs)
        completed_jobs = sum(1 for job in self.jobs.values() if job.status == "completed")
        failed_jobs = sum(1 for job in self.jobs.values() if job.status == "failed")
        running_jobs = sum(1 for job in self.jobs.values() if job.status == "running")
        
        return {
            'is_running': self.is_running,
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'success_rate': completed_jobs / total_jobs if total_jobs > 0 else 0,
            'active_sources': len(self.source_manager.list_sources(SourceStatus.ACTIVE))
        }

