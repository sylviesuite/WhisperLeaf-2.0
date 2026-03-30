"""
Feed Monitoring and Scheduling System for RSS feeds.
"""

import schedule
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timezone, timedelta
import logging
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from .rss_processor import RSSProcessor, FeedInfo, FeedItem

class FeedStatus(Enum):
    """Status of a monitored feed."""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class MonitoredFeed:
    """Configuration for a monitored RSS feed."""
    url: str
    name: str
    scan_interval_minutes: int = 60
    max_items_per_scan: int = 50
    status: FeedStatus = FeedStatus.ACTIVE
    last_scan: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error_count: int = 0
    total_items_processed: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "name": self.name,
            "scan_interval_minutes": self.scan_interval_minutes,
            "max_items_per_scan": self.max_items_per_scan,
            "status": self.status.value,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "error_count": self.error_count,
            "total_items_processed": self.total_items_processed,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitoredFeed':
        """Create from dictionary."""
        feed = cls(
            url=data["url"],
            name=data["name"],
            scan_interval_minutes=data.get("scan_interval_minutes", 60),
            max_items_per_scan=data.get("max_items_per_scan", 50),
            status=FeedStatus(data.get("status", "active")),
            error_count=data.get("error_count", 0),
            total_items_processed=data.get("total_items_processed", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
        
        # Parse datetime fields
        if data.get("last_scan"):
            feed.last_scan = datetime.fromisoformat(data["last_scan"])
        if data.get("last_success"):
            feed.last_success = datetime.fromisoformat(data["last_success"])
        
        return feed

class FeedMonitor:
    """Monitors RSS feeds and schedules automatic scanning."""
    
    def __init__(self, config_file: str = "./data/feed_monitor_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.rss_processor = RSSProcessor()
        self.monitored_feeds: Dict[str, MonitoredFeed] = {}
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Callbacks for feed events
        self.on_feed_processed: Optional[Callable[[str, FeedInfo, List[FeedItem]], None]] = None
        self.on_feed_error: Optional[Callable[[str, str], None]] = None
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Load existing configuration
        self.load_config()
    
    def add_feed(self, url: str, name: str, scan_interval_minutes: int = 60, 
                 max_items_per_scan: int = 50, tags: Optional[List[str]] = None) -> bool:
        """
        Add a new feed to monitor.
        
        Args:
            url: RSS feed URL
            name: Human-readable name for the feed
            scan_interval_minutes: How often to scan the feed
            max_items_per_scan: Maximum items to process per scan
            tags: Optional tags for categorization
            
        Returns:
            True if feed was added successfully
        """
        try:
            # Validate the feed first
            is_valid, message = self.rss_processor.validate_feed_url(url)
            if not is_valid:
                self.logger.error(f"Cannot add invalid feed {url}: {message}")
                return False
            
            # Create monitored feed
            feed = MonitoredFeed(
                url=url,
                name=name,
                scan_interval_minutes=scan_interval_minutes,
                max_items_per_scan=max_items_per_scan,
                tags=tags or []
            )
            
            self.monitored_feeds[url] = feed
            self.save_config()
            
            self.logger.info(f"Added feed: {name} ({url})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding feed {url}: {e}")
            return False
    
    def remove_feed(self, url: str) -> bool:
        """Remove a feed from monitoring."""
        if url in self.monitored_feeds:
            feed_name = self.monitored_feeds[url].name
            del self.monitored_feeds[url]
            self.save_config()
            self.logger.info(f"Removed feed: {feed_name} ({url})")
            return True
        return False
    
    def update_feed(self, url: str, **kwargs) -> bool:
        """Update feed configuration."""
        if url not in self.monitored_feeds:
            return False
        
        feed = self.monitored_feeds[url]
        
        # Update allowed fields
        for key, value in kwargs.items():
            if hasattr(feed, key):
                if key == "status" and isinstance(value, str):
                    feed.status = FeedStatus(value)
                else:
                    setattr(feed, key, value)
        
        self.save_config()
        self.logger.info(f"Updated feed: {feed.name} ({url})")
        return True
    
    def get_feed_status(self, url: str) -> Optional[Dict[str, Any]]:
        """Get status information for a specific feed."""
        if url not in self.monitored_feeds:
            return None
        
        feed = self.monitored_feeds[url]
        return {
            "url": feed.url,
            "name": feed.name,
            "status": feed.status.value,
            "last_scan": feed.last_scan.isoformat() if feed.last_scan else None,
            "last_success": feed.last_success.isoformat() if feed.last_success else None,
            "error_count": feed.error_count,
            "total_items_processed": feed.total_items_processed,
            "scan_interval_minutes": feed.scan_interval_minutes,
            "next_scan": self._calculate_next_scan(feed).isoformat() if feed.last_scan else "pending"
        }
    
    def list_feeds(self) -> List[Dict[str, Any]]:
        """List all monitored feeds with their status."""
        return [self.get_feed_status(url) for url in self.monitored_feeds.keys()]
    
    def scan_feed(self, url: str) -> bool:
        """Manually scan a specific feed."""
        if url not in self.monitored_feeds:
            self.logger.error(f"Feed not found: {url}")
            return False
        
        feed = self.monitored_feeds[url]
        
        if feed.status != FeedStatus.ACTIVE:
            self.logger.warning(f"Skipping inactive feed: {feed.name}")
            return False
        
        try:
            self.logger.info(f"Scanning feed: {feed.name} ({url})")
            
            # Update scan time
            feed.last_scan = datetime.now(timezone.utc)
            
            # Process the feed
            feed_info, feed_items = self.rss_processor.process_feed(
                url, max_items=feed.max_items_per_scan
            )
            
            if feed_info is None:
                raise Exception("Failed to fetch feed")
            
            # Update success metrics
            feed.last_success = datetime.now(timezone.utc)
            feed.error_count = 0
            feed.total_items_processed += len(feed_items)
            
            # Call callback if set
            if self.on_feed_processed:
                self.on_feed_processed(url, feed_info, feed_items)
            
            self.save_config()
            self.logger.info(f"Successfully scanned {feed.name}: {len(feed_items)} items")
            return True
            
        except Exception as e:
            # Update error metrics
            feed.error_count += 1
            error_msg = str(e)
            
            # Disable feed if too many errors
            if feed.error_count >= 5:
                feed.status = FeedStatus.ERROR
                self.logger.error(f"Disabling feed {feed.name} due to repeated errors")
            
            # Call error callback if set
            if self.on_feed_error:
                self.on_feed_error(url, error_msg)
            
            self.save_config()
            self.logger.error(f"Error scanning feed {feed.name}: {error_msg}")
            return False
    
    def scan_all_feeds(self) -> Dict[str, bool]:
        """Scan all active feeds."""
        results = {}
        
        for url, feed in self.monitored_feeds.items():
            if feed.status == FeedStatus.ACTIVE:
                results[url] = self.scan_feed(url)
            else:
                results[url] = False
        
        return results
    
    def start_monitoring(self) -> bool:
        """Start the automatic feed monitoring."""
        if self.is_running:
            self.logger.warning("Feed monitoring is already running")
            return False
        
        self.is_running = True
        
        # Schedule feeds based on their intervals
        self._schedule_feeds()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Started feed monitoring")
        return True
    
    def stop_monitoring(self) -> bool:
        """Stop the automatic feed monitoring."""
        if not self.is_running:
            return False
        
        self.is_running = False
        
        # Clear scheduled jobs
        schedule.clear()
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Stopped feed monitoring")
        return True
    
    def _schedule_feeds(self):
        """Schedule all active feeds for monitoring."""
        schedule.clear()
        
        for url, feed in self.monitored_feeds.items():
            if feed.status == FeedStatus.ACTIVE:
                # Schedule based on interval
                schedule.every(feed.scan_interval_minutes).minutes.do(
                    self.scan_feed, url
                )
                
                self.logger.debug(f"Scheduled {feed.name} every {feed.scan_interval_minutes} minutes")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def _calculate_next_scan(self, feed: MonitoredFeed) -> datetime:
        """Calculate when the next scan should occur."""
        if not feed.last_scan:
            return datetime.now(timezone.utc)
        
        return feed.last_scan + timedelta(minutes=feed.scan_interval_minutes)
    
    def save_config(self):
        """Save feed configuration to file."""
        try:
            config_data = {
                "feeds": {url: feed.to_dict() for url, feed in self.monitored_feeds.items()},
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def load_config(self):
        """Load feed configuration from file."""
        try:
            if not self.config_file.exists():
                return
            
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Load feeds
            feeds_data = config_data.get("feeds", {})
            for url, feed_data in feeds_data.items():
                self.monitored_feeds[url] = MonitoredFeed.from_dict(feed_data)
            
            self.logger.info(f"Loaded {len(self.monitored_feeds)} feeds from config")
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get overall monitoring statistics."""
        total_feeds = len(self.monitored_feeds)
        active_feeds = sum(1 for f in self.monitored_feeds.values() if f.status == FeedStatus.ACTIVE)
        error_feeds = sum(1 for f in self.monitored_feeds.values() if f.status == FeedStatus.ERROR)
        total_items = sum(f.total_items_processed for f in self.monitored_feeds.values())
        
        return {
            "total_feeds": total_feeds,
            "active_feeds": active_feeds,
            "error_feeds": error_feeds,
            "paused_feeds": total_feeds - active_feeds - error_feeds,
            "total_items_processed": total_items,
            "is_monitoring": self.is_running,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

