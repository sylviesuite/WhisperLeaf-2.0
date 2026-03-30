"""
Integrated Curation API - Combines all curation components into a unified API.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
import sys
import os

# Add curation modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'curation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'api-server'))

from curation.source_manager import (
    SourceManager, CurationScheduler, SourceConfig, 
    SourceType, SourceStatus
)
from curation.content_filter import ContentFilter, FilterRule
from curation.rss_processor import RSSProcessor
from curation.web_scraper import WebScraper
from vault import VaultManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sovereign AI Curation Engine",
    description="Automated content curation system with RSS feeds, web scraping, and intelligent filtering",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
source_manager = SourceManager()
content_filter = ContentFilter()
scheduler = CurationScheduler(source_manager)
vault_manager = VaultManager()

# Pydantic models for API requests
class SourceCreateRequest(BaseModel):
    name: str
    source_type: str  # "rss_feed", "web_page"
    url: str
    scan_interval_minutes: int = 60
    max_items_per_scan: int = 50
    priority: int = 5
    tags: List[str] = []
    description: str = ""
    enable_filtering: bool = True

class SourceUpdateRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    scan_interval_minutes: Optional[int] = None
    max_items_per_scan: Optional[int] = None
    priority: Optional[int] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    enable_filtering: Optional[bool] = None

class FilterRuleRequest(BaseModel):
    name: str
    description: str
    enabled: bool = True
    weight: float = 1.0
    required_keywords: List[str] = []
    excluded_keywords: List[str] = []
    min_word_count: int = 50
    max_word_count: int = 50000
    min_quality_score: float = 0.3
    min_relevance_score: float = 0.4

class UserInterestsRequest(BaseModel):
    interests: List[str]

# Global variables for tracking processed content
processed_content_log = []
scheduler_callbacks_set = False

def setup_scheduler_callbacks():
    """Set up callbacks for the scheduler to track processed content."""
    global scheduler_callbacks_set
    
    if scheduler_callbacks_set:
        return
    
    def on_content_processed(source_id, content, filter_result):
        """Callback when content is processed."""
        try:
            # Store processed content in vault if accepted
            if filter_result.action.value == "accept":
                # Determine content type and extract metadata
                if hasattr(content, 'title'):  # RSS item
                    title = content.title
                    text_content = f"{content.title}\n\n{content.content}"
                    metadata = {
                        'source_id': source_id,
                        'source_type': 'rss_feed',
                        'author': content.author,
                        'published_date': content.published.isoformat() if content.published else None,
                        'tags': content.tags,
                        'link': content.link,
                        'quality_score': filter_result.score.quality_score,
                        'relevance_score': filter_result.score.relevance_score,
                        'overall_score': filter_result.score.overall_score
                    }
                else:  # Scraped content
                    title = content.title
                    text_content = content.content
                    metadata = {
                        'source_id': source_id,
                        'source_type': 'web_page',
                        'author': content.author,
                        'published_date': content.published_date.isoformat() if content.published_date else None,
                        'tags': content.tags,
                        'url': content.url,
                        'quality_score': filter_result.score.quality_score,
                        'relevance_score': filter_result.score.relevance_score,
                        'overall_score': filter_result.score.overall_score
                    }
                
                # Store in vault
                vault_manager.store_document(
                    title=title,
                    content=text_content,
                    content_type="text/plain",
                    metadata=metadata,
                    tags=metadata.get('tags', [])
                )
                
                logger.info(f"Stored content from {source_id} in vault: {title[:50]}...")
            
            # Log all processed content for statistics
            processed_content_log.append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source_id': source_id,
                'action': filter_result.action.value,
                'quality_score': filter_result.score.quality_score,
                'relevance_score': filter_result.score.relevance_score,
                'overall_score': filter_result.score.overall_score,
                'title': getattr(content, 'title', 'Unknown')[:100]
            })
            
        except Exception as e:
            logger.error(f"Error in content processed callback: {e}")
    
    def on_job_completed(job):
        """Callback when a curation job is completed."""
        logger.info(f"Curation job {job.id} completed: {job.status}")
    
    def on_error(source_id, error_message):
        """Callback when an error occurs during curation."""
        logger.error(f"Curation error in source {source_id}: {error_message}")
    
    # Set callbacks
    scheduler.on_content_processed = on_content_processed
    scheduler.on_job_completed = on_job_completed
    scheduler.on_error = on_error
    
    scheduler_callbacks_set = True

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Sovereign AI Curation Engine",
        "version": "1.0.0",
        "status": "running",
        "components": {
            "source_manager": "active",
            "content_filter": "active",
            "scheduler": "active" if scheduler.is_running else "stopped",
            "vault_manager": "active"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scheduler_running": scheduler.is_running,
        "total_sources": len(source_manager.sources),
        "active_sources": len(source_manager.list_sources(SourceStatus.ACTIVE))
    }

# Source Management Endpoints

@app.post("/api/sources")
async def create_source(source_request: SourceCreateRequest):
    """Create a new content source."""
    try:
        source_config = SourceConfig(
            id=f"{source_request.name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}",
            name=source_request.name,
            source_type=SourceType(source_request.source_type),
            url=source_request.url,
            scan_interval_minutes=source_request.scan_interval_minutes,
            max_items_per_scan=source_request.max_items_per_scan,
            priority=source_request.priority,
            tags=source_request.tags,
            description=source_request.description,
            enable_filtering=source_request.enable_filtering
        )
        
        success = source_manager.add_source(source_config)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create source")
        
        return {
            "message": "Source created successfully",
            "source_id": source_config.id,
            "source": {
                "id": source_config.id,
                "name": source_config.name,
                "source_type": source_config.source_type.value,
                "url": source_config.url,
                "status": source_config.status.value
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid source type: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

@app.get("/api/sources")
async def list_sources(status: Optional[str] = None):
    """List all content sources."""
    try:
        if status:
            sources = source_manager.list_sources(SourceStatus(status))
        else:
            sources = source_manager.list_sources()
        
        return {
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "source_type": source.source_type.value,
                    "url": source.url,
                    "status": source.status.value,
                    "priority": source.priority,
                    "scan_interval_minutes": source.scan_interval_minutes,
                    "tags": source.tags,
                    "description": source.description,
                    "last_scan": source.last_scan.isoformat() if source.last_scan else None,
                    "last_success": source.last_success.isoformat() if source.last_success else None,
                    "error_count": source.error_count,
                    "total_items_processed": source.total_items_processed,
                    "total_items_accepted": source.total_items_accepted,
                    "avg_quality_score": source.avg_quality_score,
                    "avg_relevance_score": source.avg_relevance_score,
                    "success_rate": source.success_rate
                }
                for source in sources
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {e}")

@app.get("/api/sources/{source_id}")
async def get_source(source_id: str):
    """Get a specific source."""
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return {
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type.value,
        "url": source.url,
        "status": source.status.value,
        "priority": source.priority,
        "scan_interval_minutes": source.scan_interval_minutes,
        "max_items_per_scan": source.max_items_per_scan,
        "tags": source.tags,
        "description": source.description,
        "enable_filtering": source.enable_filtering,
        "created_at": source.created_at.isoformat(),
        "last_scan": source.last_scan.isoformat() if source.last_scan else None,
        "last_success": source.last_success.isoformat() if source.last_success else None,
        "error_count": source.error_count,
        "total_items_processed": source.total_items_processed,
        "total_items_accepted": source.total_items_accepted,
        "avg_quality_score": source.avg_quality_score,
        "avg_relevance_score": source.avg_relevance_score,
        "success_rate": source.success_rate
    }

@app.put("/api/sources/{source_id}")
async def update_source(source_id: str, update_request: SourceUpdateRequest):
    """Update a source."""
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Prepare update data
    update_data = {}
    for field, value in update_request.dict(exclude_unset=True).items():
        update_data[field] = value
    
    success = source_manager.update_source(source_id, **update_data)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update source")
    
    return {"message": "Source updated successfully"}

@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: str):
    """Delete a source."""
    success = source_manager.remove_source(source_id)
    if not success:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return {"message": "Source deleted successfully"}

# Scheduler Endpoints

@app.post("/api/scheduler/start")
async def start_scheduler():
    """Start the automated scheduler."""
    setup_scheduler_callbacks()
    success = scheduler.start_scheduler()
    if not success:
        raise HTTPException(status_code=400, detail="Scheduler is already running")
    
    return {"message": "Scheduler started successfully"}

@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """Stop the automated scheduler."""
    success = scheduler.stop_scheduler()
    if not success:
        raise HTTPException(status_code=400, detail="Scheduler is not running")
    
    return {"message": "Scheduler stopped successfully"}

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and statistics."""
    stats = scheduler.get_scheduler_stats()
    return {
        "scheduler": stats,
        "recent_content": processed_content_log[-10:] if processed_content_log else []
    }

@app.post("/api/scheduler/scan/{source_id}")
async def manual_scan(source_id: str, background_tasks: BackgroundTasks):
    """Manually trigger a scan for a specific source."""
    source = source_manager.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    setup_scheduler_callbacks()
    
    # Schedule the job
    job_id = scheduler.schedule_source_scan(source_id)
    if not job_id:
        raise HTTPException(status_code=400, detail="Failed to schedule scan")
    
    # Execute in background
    background_tasks.add_task(scheduler.execute_job, job_id)
    
    return {
        "message": "Manual scan initiated",
        "job_id": job_id,
        "source_name": source.name
    }

# Content Filter Endpoints

@app.post("/api/filter/interests")
async def set_user_interests(interests_request: UserInterestsRequest):
    """Set user interests for content relevance filtering."""
    content_filter.set_user_interests(interests_request.interests)
    return {
        "message": "User interests updated successfully",
        "interests": interests_request.interests
    }

@app.get("/api/filter/stats")
async def get_filter_stats():
    """Get content filtering statistics."""
    return content_filter.get_filter_stats()

# Vault Integration Endpoints

@app.get("/api/vault/documents")
async def get_curated_documents(limit: int = 50, offset: int = 0):
    """Get curated documents from the vault."""
    documents = vault_manager.list_documents(limit=limit, offset=offset)
    return {
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "created_at": doc.created_at.isoformat(),
                "tags": doc.tags,
                "metadata": doc.metadata_json
            }
            for doc in documents
        ]
    }

@app.get("/api/vault/search")
async def search_curated_content(query: str, limit: int = 20):
    """Search curated content in the vault."""
    results = vault_manager.search_documents(query, limit=limit)
    return {
        "query": query,
        "results": [
            {
                "id": doc.id,
                "title": doc.title,
                "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "relevance_score": score,
                "tags": doc.tags,
                "metadata": doc.metadata_json
            }
            for doc, score in results
        ]
    }

# Statistics and Monitoring Endpoints

@app.get("/api/stats/overview")
async def get_system_overview():
    """Get overall system statistics."""
    source_stats = {
        "total_sources": len(source_manager.sources),
        "active_sources": len(source_manager.list_sources(SourceStatus.ACTIVE)),
        "paused_sources": len(source_manager.list_sources(SourceStatus.PAUSED)),
        "error_sources": len(source_manager.list_sources(SourceStatus.ERROR))
    }
    
    scheduler_stats = scheduler.get_scheduler_stats()
    filter_stats = content_filter.get_filter_stats()
    
    # Vault statistics
    try:
        vault_stats = {
            "total_documents": len(vault_manager.list_documents(limit=1000)),
            "status": "active"
        }
    except Exception as e:
        vault_stats = {"total_documents": 0, "status": "error", "error": str(e)}
    
    return {
        "system": {
            "status": "running",
            "uptime": "N/A",  # Could be implemented with start time tracking
            "scheduler_running": scheduler.is_running
        },
        "sources": source_stats,
        "scheduler": scheduler_stats,
        "filter": filter_stats,
        "vault": vault_stats,
        "recent_activity": {
            "processed_content_count": len(processed_content_log),
            "recent_items": processed_content_log[-5:] if processed_content_log else []
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

