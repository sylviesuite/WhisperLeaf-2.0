"""
Time Capsule Backup System - Automated backup and versioning for Sovereign AI.

This module provides comprehensive backup, versioning, and point-in-time recovery
capabilities for the entire Sovereign AI system.
"""

import os
import json
import shutil
import sqlite3
import hashlib
import tarfile
import gzip
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import threading
import schedule
import time

@dataclass
class BackupMetadata:
    """Metadata for a backup snapshot."""
    backup_id: str
    timestamp: datetime
    backup_type: str  # full, incremental, differential
    description: str
    
    # Backup content
    files_included: List[str]
    total_size_bytes: int
    compressed_size_bytes: int
    
    # System state
    constitution_rules: int
    conversations: int
    documents: int
    
    # Backup integrity
    checksum: str
    verification_status: str  # verified, failed, pending
    
    # Metadata
    created_by: str = "system"
    tags: List[str] = None
    retention_days: int = 30
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class RestorePoint:
    """Represents a point-in-time restore point."""
    restore_id: str
    backup_id: str
    timestamp: datetime
    description: str
    
    # Restore scope
    restore_constitution: bool = True
    restore_conversations: bool = True
    restore_documents: bool = True
    restore_configuration: bool = True
    
    # Restore status
    status: str = "pending"  # pending, in_progress, completed, failed
    progress_percent: float = 0.0
    error_message: str = ""

class TimeCapsuleBackupSystem:
    """Comprehensive backup and recovery system for Sovereign AI."""
    
    def __init__(self, base_path: str = "./time_capsule"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Backup storage paths
        self.backups_path = self.base_path / "backups"
        self.metadata_path = self.base_path / "metadata"
        self.temp_path = self.base_path / "temp"
        
        for path in [self.backups_path, self.metadata_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Database for backup metadata
        self.db_path = self.metadata_path / "backup_metadata.db"
        self.init_database()
        
        # System paths to backup
        self.system_paths = {
            "constitution": "./data",
            "conversations": "./conversations",
            "documents": "./vault",
            "configuration": "./config",
            "curation": "./curation_data",
            "logs": "./logs"
        }
        
        # Backup scheduler
        self.scheduler_thread = None
        self.scheduler_running = False
        
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self.load_backup_config()
    
    def init_database(self):
        """Initialize the backup metadata database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    description TEXT,
                    files_included TEXT,
                    total_size_bytes INTEGER,
                    compressed_size_bytes INTEGER,
                    constitution_rules INTEGER,
                    conversations INTEGER,
                    documents INTEGER,
                    checksum TEXT,
                    verification_status TEXT,
                    created_by TEXT,
                    tags TEXT,
                    retention_days INTEGER
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS restore_points (
                    restore_id TEXT PRIMARY KEY,
                    backup_id TEXT,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    restore_constitution BOOLEAN,
                    restore_conversations BOOLEAN,
                    restore_documents BOOLEAN,
                    restore_configuration BOOLEAN,
                    status TEXT,
                    progress_percent REAL,
                    error_message TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
                )
            """)
            
            conn.commit()
    
    def create_backup(self, backup_type: str = "full", description: str = "", 
                     tags: List[str] = None) -> str:
        """Create a new backup snapshot."""
        # Use microseconds for better uniqueness
        timestamp_micro = int(datetime.now().timestamp() * 1000000)
        backup_id = f"backup_{timestamp_micro}_{backup_type}"
        timestamp = datetime.now(timezone.utc)
        
        self.logger.info(f"Creating {backup_type} backup: {backup_id}")
        
        try:
            # Create temporary directory for this backup
            temp_backup_path = self.temp_path / backup_id
            temp_backup_path.mkdir(parents=True, exist_ok=True)
            
            # Collect files to backup
            files_to_backup = self._collect_backup_files(backup_type)
            
            # Copy files to temporary location
            total_size = 0
            for source_path, relative_path in files_to_backup:
                if os.path.exists(source_path):
                    dest_path = temp_backup_path / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if os.path.isfile(source_path):
                        shutil.copy2(source_path, dest_path)
                        total_size += os.path.getsize(source_path)
                    elif os.path.isdir(source_path):
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                        total_size += self._get_directory_size(source_path)
            
            # Create backup archive
            archive_path = self.backups_path / f"{backup_id}.tar.gz"
            compressed_size = self._create_compressed_archive(temp_backup_path, archive_path)
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(archive_path)
            
            # Collect system statistics
            stats = self._collect_system_stats()
            
            # Create backup metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp,
                backup_type=backup_type,
                description=description or f"Automated {backup_type} backup",
                files_included=[rel_path for _, rel_path in files_to_backup],
                total_size_bytes=total_size,
                compressed_size_bytes=compressed_size,
                constitution_rules=stats.get("constitution_rules", 0),
                conversations=stats.get("conversations", 0),
                documents=stats.get("documents", 0),
                checksum=checksum,
                verification_status="verified",
                tags=tags or []
            )
            
            # Save metadata to database
            self._save_backup_metadata(metadata)
            
            # Clean up temporary files
            shutil.rmtree(temp_backup_path)
            
            self.logger.info(f"Backup {backup_id} created successfully")
            self.logger.info(f"  Size: {total_size:,} bytes -> {compressed_size:,} bytes")
            self.logger.info(f"  Compression ratio: {compressed_size/total_size:.2%}")
            
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Error creating backup {backup_id}: {e}")
            # Clean up on error
            if temp_backup_path.exists():
                shutil.rmtree(temp_backup_path)
            raise
    
    def restore_from_backup(self, backup_id: str, restore_scope: Dict[str, bool] = None) -> str:
        """Restore system from a backup."""
        restore_id = f"restore_{int(datetime.now().timestamp())}"
        timestamp = datetime.now(timezone.utc)
        
        # Default restore scope
        if restore_scope is None:
            restore_scope = {
                "constitution": True,
                "conversations": True,
                "documents": True,
                "configuration": True
            }
        
        self.logger.info(f"Starting restore {restore_id} from backup {backup_id}")
        
        try:
            # Verify backup exists
            backup_metadata = self.get_backup_metadata(backup_id)
            if not backup_metadata:
                raise ValueError(f"Backup {backup_id} not found")
            
            # Create restore point record
            restore_point = RestorePoint(
                restore_id=restore_id,
                backup_id=backup_id,
                timestamp=timestamp,
                description=f"Restore from {backup_id}",
                restore_constitution=restore_scope.get("constitution", True),
                restore_conversations=restore_scope.get("conversations", True),
                restore_documents=restore_scope.get("documents", True),
                restore_configuration=restore_scope.get("configuration", True),
                status="in_progress"
            )
            
            self._save_restore_point(restore_point)
            
            # Extract backup archive
            archive_path = self.backups_path / f"{backup_id}.tar.gz"
            temp_restore_path = self.temp_path / restore_id
            
            self._extract_compressed_archive(archive_path, temp_restore_path)
            
            # Restore files based on scope
            restored_files = 0
            total_files = len(backup_metadata.files_included)
            
            for file_path in backup_metadata.files_included:
                source_path = temp_restore_path / file_path
                
                # Determine if this file should be restored
                should_restore = False
                if "constitution" in file_path and restore_scope.get("constitution", True):
                    should_restore = True
                elif "conversation" in file_path and restore_scope.get("conversations", True):
                    should_restore = True
                elif "document" in file_path and restore_scope.get("documents", True):
                    should_restore = True
                elif "config" in file_path and restore_scope.get("configuration", True):
                    should_restore = True
                
                if should_restore and source_path.exists():
                    dest_path = Path(file_path)
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if source_path.is_file():
                        shutil.copy2(source_path, dest_path)
                    elif source_path.is_dir():
                        if dest_path.exists():
                            shutil.rmtree(dest_path)
                        shutil.copytree(source_path, dest_path)
                
                restored_files += 1
                progress = (restored_files / total_files) * 100
                
                # Update progress
                restore_point.progress_percent = progress
                self._update_restore_point(restore_point)
            
            # Mark restore as completed
            restore_point.status = "completed"
            restore_point.progress_percent = 100.0
            self._update_restore_point(restore_point)
            
            # Clean up temporary files
            shutil.rmtree(temp_restore_path)
            
            self.logger.info(f"Restore {restore_id} completed successfully")
            return restore_id
            
        except Exception as e:
            self.logger.error(f"Error during restore {restore_id}: {e}")
            
            # Mark restore as failed
            restore_point.status = "failed"
            restore_point.error_message = str(e)
            self._update_restore_point(restore_point)
            
            raise
    
    def list_backups(self, backup_type: str = None, limit: int = 50) -> List[BackupMetadata]:
        """List available backups."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM backups"
            params = []
            
            if backup_type:
                query += " WHERE backup_type = ?"
                params.append(backup_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            backups = []
            for row in rows:
                backup = BackupMetadata(
                    backup_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    backup_type=row[2],
                    description=row[3],
                    files_included=json.loads(row[4]) if row[4] else [],
                    total_size_bytes=row[5],
                    compressed_size_bytes=row[6],
                    constitution_rules=row[7],
                    conversations=row[8],
                    documents=row[9],
                    checksum=row[10],
                    verification_status=row[11],
                    created_by=row[12],
                    tags=json.loads(row[13]) if row[13] else [],
                    retention_days=row[14]
                )
                backups.append(backup)
            
            return backups
    
    def get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get metadata for a specific backup."""
        backups = self.list_backups()
        for backup in backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup and its metadata."""
        try:
            # Remove backup file
            archive_path = self.backups_path / f"{backup_id}.tar.gz"
            if archive_path.exists():
                archive_path.unlink()
            
            # Remove metadata
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM backups WHERE backup_id = ?", (backup_id,))
                conn.execute("DELETE FROM restore_points WHERE backup_id = ?", (backup_id,))
                conn.commit()
            
            self.logger.info(f"Deleted backup {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting backup {backup_id}: {e}")
            return False
    
    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity."""
        try:
            backup_metadata = self.get_backup_metadata(backup_id)
            if not backup_metadata:
                return False
            
            archive_path = self.backups_path / f"{backup_id}.tar.gz"
            if not archive_path.exists():
                return False
            
            # Verify checksum
            current_checksum = self._calculate_file_checksum(archive_path)
            if current_checksum != backup_metadata.checksum:
                self.logger.error(f"Checksum mismatch for backup {backup_id}")
                return False
            
            # Try to extract (test extraction)
            temp_verify_path = self.temp_path / f"verify_{backup_id}"
            try:
                self._extract_compressed_archive(archive_path, temp_verify_path)
                shutil.rmtree(temp_verify_path)
                return True
            except Exception as e:
                self.logger.error(f"Archive extraction test failed for {backup_id}: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verifying backup {backup_id}: {e}")
            return False
    
    def start_automated_backups(self):
        """Start the automated backup scheduler."""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        
        # Schedule different types of backups
        schedule.every().day.at("02:00").do(self._scheduled_full_backup)
        schedule.every(6).hours.do(self._scheduled_incremental_backup)
        schedule.every().sunday.at("01:00").do(self._cleanup_old_backups)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Automated backup scheduler started")
    
    def stop_automated_backups(self):
        """Stop the automated backup scheduler."""
        self.scheduler_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Automated backup scheduler stopped")
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get comprehensive backup system statistics."""
        backups = self.list_backups()
        
        if not backups:
            return {
                "total_backups": 0,
                "total_size_bytes": 0,
                "total_compressed_bytes": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "backup_types": {},
                "average_compression_ratio": 0.0
            }
        
        total_size = sum(b.total_size_bytes for b in backups)
        total_compressed = sum(b.compressed_size_bytes for b in backups)
        
        backup_types = {}
        for backup in backups:
            backup_types[backup.backup_type] = backup_types.get(backup.backup_type, 0) + 1
        
        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_compressed_bytes": total_compressed,
            "oldest_backup": min(backups, key=lambda b: b.timestamp).timestamp.isoformat(),
            "newest_backup": max(backups, key=lambda b: b.timestamp).timestamp.isoformat(),
            "backup_types": backup_types,
            "average_compression_ratio": total_compressed / total_size if total_size > 0 else 0.0,
            "scheduler_running": self.scheduler_running
        }
    
    def _collect_backup_files(self, backup_type: str) -> List[Tuple[str, str]]:
        """Collect files to include in backup."""
        files_to_backup = []
        
        for category, path in self.system_paths.items():
            if os.path.exists(path):
                if os.path.isfile(path):
                    files_to_backup.append((path, f"{category}/{os.path.basename(path)}"))
                elif os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            source_path = os.path.join(root, file)
                            relative_path = os.path.relpath(source_path, ".")
                            files_to_backup.append((source_path, relative_path))
        
        return files_to_backup
    
    def _collect_system_stats(self) -> Dict[str, int]:
        """Collect current system statistics."""
        stats = {
            "constitution_rules": 0,
            "conversations": 0,
            "documents": 0
        }
        
        try:
            # Count constitution rules
            constitution_path = Path("./data/constitution.json")
            if constitution_path.exists():
                with open(constitution_path) as f:
                    data = json.load(f)
                    stats["constitution_rules"] = len(data.get("rules", {}))
            
            # Count conversations
            conversations_path = Path("./conversations")
            if conversations_path.exists():
                stats["conversations"] = len(list(conversations_path.glob("*.json")))
            
            # Count documents
            documents_path = Path("./vault")
            if documents_path.exists():
                stats["documents"] = len(list(documents_path.glob("**/*")))
                
        except Exception as e:
            self.logger.warning(f"Error collecting system stats: {e}")
        
        return stats
    
    def _create_compressed_archive(self, source_path: Path, archive_path: Path) -> int:
        """Create a compressed tar.gz archive."""
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_path, arcname=".")
        
        return os.path.getsize(archive_path)
    
    def _extract_compressed_archive(self, archive_path: Path, dest_path: Path):
        """Extract a compressed tar.gz archive."""
        dest_path.mkdir(parents=True, exist_ok=True)
        
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(dest_path)
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_directory_size(self, path: str) -> int:
        """Get total size of a directory."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
    
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO backups VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.backup_id,
                metadata.timestamp.isoformat(),
                metadata.backup_type,
                metadata.description,
                json.dumps(metadata.files_included),
                metadata.total_size_bytes,
                metadata.compressed_size_bytes,
                metadata.constitution_rules,
                metadata.conversations,
                metadata.documents,
                metadata.checksum,
                metadata.verification_status,
                metadata.created_by,
                json.dumps(metadata.tags),
                metadata.retention_days
            ))
            conn.commit()
    
    def _save_restore_point(self, restore_point: RestorePoint):
        """Save restore point to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO restore_points VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                restore_point.restore_id,
                restore_point.backup_id,
                restore_point.timestamp.isoformat(),
                restore_point.description,
                restore_point.restore_constitution,
                restore_point.restore_conversations,
                restore_point.restore_documents,
                restore_point.restore_configuration,
                restore_point.status,
                restore_point.progress_percent,
                restore_point.error_message
            ))
            conn.commit()
    
    def _update_restore_point(self, restore_point: RestorePoint):
        """Update restore point in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE restore_points SET 
                    status = ?, progress_percent = ?, error_message = ?
                WHERE restore_id = ?
            """, (
                restore_point.status,
                restore_point.progress_percent,
                restore_point.error_message,
                restore_point.restore_id
            ))
            conn.commit()
    
    def _scheduled_full_backup(self):
        """Scheduled full backup."""
        try:
            self.create_backup("full", "Scheduled daily full backup", ["automated", "daily"])
        except Exception as e:
            self.logger.error(f"Scheduled full backup failed: {e}")
    
    def _scheduled_incremental_backup(self):
        """Scheduled incremental backup."""
        try:
            self.create_backup("incremental", "Scheduled incremental backup", ["automated", "incremental"])
        except Exception as e:
            self.logger.error(f"Scheduled incremental backup failed: {e}")
    
    def _cleanup_old_backups(self):
        """Clean up old backups based on retention policy."""
        try:
            backups = self.list_backups()
            now = datetime.now(timezone.utc)
            
            for backup in backups:
                age_days = (now - backup.timestamp).days
                if age_days > backup.retention_days:
                    self.delete_backup(backup.backup_id)
                    self.logger.info(f"Deleted expired backup {backup.backup_id} (age: {age_days} days)")
                    
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
    
    def _run_scheduler(self):
        """Run the backup scheduler."""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def load_backup_config(self) -> Dict[str, Any]:
        """Load backup configuration."""
        config_path = self.base_path / "backup_config.json"
        
        default_config = {
            "retention_days": 30,
            "max_backups": 100,
            "compression_level": 6,
            "verify_after_backup": True,
            "automated_backups": True
        }
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except Exception as e:
                self.logger.warning(f"Error loading backup config: {e}")
        
        # Save default config
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config

