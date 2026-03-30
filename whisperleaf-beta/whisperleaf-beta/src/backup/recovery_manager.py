"""
Recovery Manager - Advanced point-in-time recovery for Sovereign AI.

This module provides sophisticated recovery capabilities including
selective restoration, rollback operations, and system state management.
"""

import os
import json
import shutil
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import threading
import time

from .backup_system import TimeCapsuleBackupSystem, BackupMetadata, RestorePoint

@dataclass
class SystemSnapshot:
    """Represents a complete system state snapshot."""
    snapshot_id: str
    timestamp: datetime
    description: str
    
    # System state
    constitution_snapshot: Dict[str, Any]
    conversation_count: int
    document_count: int
    configuration_snapshot: Dict[str, Any]
    
    # Performance metrics
    system_health: Dict[str, Any]
    resource_usage: Dict[str, Any]
    
    # Snapshot metadata
    created_by: str = "system"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class RecoveryPlan:
    """Represents a recovery plan with multiple steps."""
    plan_id: str
    description: str
    target_timestamp: datetime
    
    # Recovery steps
    steps: List[Dict[str, Any]]
    estimated_duration_minutes: int
    
    # Risk assessment
    risk_level: str  # low, medium, high
    affected_components: List[str]
    data_loss_risk: bool
    
    # Execution status
    status: str = "planned"  # planned, executing, completed, failed
    current_step: int = 0
    progress_percent: float = 0.0
    error_message: str = ""

class RecoveryManager:
    """Advanced recovery management for Sovereign AI."""
    
    def __init__(self, backup_system: TimeCapsuleBackupSystem):
        self.backup_system = backup_system
        self.base_path = backup_system.base_path / "recovery"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Recovery database
        self.db_path = self.base_path / "recovery.db"
        self.init_database()
        
        # System state tracking
        self.snapshots_path = self.base_path / "snapshots"
        self.snapshots_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Initialize the recovery database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    constitution_snapshot TEXT,
                    conversation_count INTEGER,
                    document_count INTEGER,
                    configuration_snapshot TEXT,
                    system_health TEXT,
                    resource_usage TEXT,
                    created_by TEXT,
                    tags TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recovery_plans (
                    plan_id TEXT PRIMARY KEY,
                    description TEXT,
                    target_timestamp TEXT,
                    steps TEXT,
                    estimated_duration_minutes INTEGER,
                    risk_level TEXT,
                    affected_components TEXT,
                    data_loss_risk BOOLEAN,
                    status TEXT,
                    current_step INTEGER,
                    progress_percent REAL,
                    error_message TEXT
                )
            """)
            
            conn.commit()
    
    def create_system_snapshot(self, description: str = "") -> str:
        """Create a comprehensive system state snapshot."""
        snapshot_id = f"snapshot_{int(datetime.now().timestamp())}"
        timestamp = datetime.now(timezone.utc)
        
        self.logger.info(f"Creating system snapshot: {snapshot_id}")
        
        try:
            # Capture constitution state
            constitution_snapshot = self._capture_constitution_state()
            
            # Capture system statistics
            conversation_count = self._count_conversations()
            document_count = self._count_documents()
            
            # Capture configuration state
            configuration_snapshot = self._capture_configuration_state()
            
            # Capture system health metrics
            system_health = self._capture_system_health()
            
            # Capture resource usage
            resource_usage = self._capture_resource_usage()
            
            # Create snapshot object
            snapshot = SystemSnapshot(
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                description=description or f"System snapshot at {timestamp.isoformat()}",
                constitution_snapshot=constitution_snapshot,
                conversation_count=conversation_count,
                document_count=document_count,
                configuration_snapshot=configuration_snapshot,
                system_health=system_health,
                resource_usage=resource_usage
            )
            
            # Save snapshot to database
            self._save_system_snapshot(snapshot)
            
            # Save detailed snapshot data to file
            snapshot_file = self.snapshots_path / f"{snapshot_id}.json"
            with open(snapshot_file, 'w') as f:
                json.dump(asdict(snapshot), f, indent=2, default=str)
            
            self.logger.info(f"System snapshot {snapshot_id} created successfully")
            return snapshot_id
            
        except Exception as e:
            self.logger.error(f"Error creating system snapshot: {e}")
            raise
    
    def create_recovery_plan(self, target_timestamp: datetime, 
                           components: List[str] = None) -> str:
        """Create a recovery plan to restore system to a specific point in time."""
        plan_id = f"recovery_plan_{int(datetime.now().timestamp())}"
        
        self.logger.info(f"Creating recovery plan {plan_id} for {target_timestamp}")
        
        try:
            # Find the best backup for the target timestamp
            best_backup = self._find_best_backup_for_timestamp(target_timestamp)
            if not best_backup:
                raise ValueError(f"No suitable backup found for timestamp {target_timestamp}")
            
            # Determine affected components
            if components is None:
                components = ["constitution", "conversations", "documents", "configuration"]
            
            # Assess risk level
            risk_level = self._assess_recovery_risk(target_timestamp, components)
            
            # Create recovery steps
            steps = self._create_recovery_steps(best_backup, components)
            
            # Estimate duration
            estimated_duration = self._estimate_recovery_duration(steps)
            
            # Check for data loss risk
            data_loss_risk = self._assess_data_loss_risk(target_timestamp)
            
            # Create recovery plan
            plan = RecoveryPlan(
                plan_id=plan_id,
                description=f"Recovery to {target_timestamp.isoformat()}",
                target_timestamp=target_timestamp,
                steps=steps,
                estimated_duration_minutes=estimated_duration,
                risk_level=risk_level,
                affected_components=components,
                data_loss_risk=data_loss_risk
            )
            
            # Save recovery plan
            self._save_recovery_plan(plan)
            
            self.logger.info(f"Recovery plan {plan_id} created")
            self.logger.info(f"  Target: {target_timestamp}")
            self.logger.info(f"  Risk level: {risk_level}")
            self.logger.info(f"  Estimated duration: {estimated_duration} minutes")
            self.logger.info(f"  Data loss risk: {data_loss_risk}")
            
            return plan_id
            
        except Exception as e:
            self.logger.error(f"Error creating recovery plan: {e}")
            raise
    
    def execute_recovery_plan(self, plan_id: str) -> bool:
        """Execute a recovery plan."""
        self.logger.info(f"Executing recovery plan {plan_id}")
        
        try:
            # Load recovery plan
            plan = self._load_recovery_plan(plan_id)
            if not plan:
                raise ValueError(f"Recovery plan {plan_id} not found")
            
            # Update plan status
            plan.status = "executing"
            plan.current_step = 0
            plan.progress_percent = 0.0
            self._update_recovery_plan(plan)
            
            # Create pre-recovery snapshot
            pre_recovery_snapshot = self.create_system_snapshot(
                f"Pre-recovery snapshot for plan {plan_id}"
            )
            
            # Execute each step
            total_steps = len(plan.steps)
            for i, step in enumerate(plan.steps):
                self.logger.info(f"Executing step {i+1}/{total_steps}: {step['description']}")
                
                plan.current_step = i + 1
                plan.progress_percent = ((i + 1) / total_steps) * 100
                self._update_recovery_plan(plan)
                
                # Execute the step
                success = self._execute_recovery_step(step)
                if not success:
                    raise Exception(f"Recovery step failed: {step['description']}")
            
            # Mark plan as completed
            plan.status = "completed"
            plan.progress_percent = 100.0
            self._update_recovery_plan(plan)
            
            # Create post-recovery snapshot
            post_recovery_snapshot = self.create_system_snapshot(
                f"Post-recovery snapshot for plan {plan_id}"
            )
            
            self.logger.info(f"Recovery plan {plan_id} executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing recovery plan {plan_id}: {e}")
            
            # Mark plan as failed
            if 'plan' in locals():
                plan.status = "failed"
                plan.error_message = str(e)
                self._update_recovery_plan(plan)
            
            return False
    
    def rollback_to_snapshot(self, snapshot_id: str) -> bool:
        """Rollback system to a specific snapshot."""
        self.logger.info(f"Rolling back to snapshot {snapshot_id}")
        
        try:
            # Load snapshot
            snapshot = self._load_system_snapshot(snapshot_id)
            if not snapshot:
                raise ValueError(f"Snapshot {snapshot_id} not found")
            
            # Create current snapshot before rollback
            current_snapshot = self.create_system_snapshot(
                f"Pre-rollback snapshot before {snapshot_id}"
            )
            
            # Restore constitution state
            self._restore_constitution_state(snapshot.constitution_snapshot)
            
            # Restore configuration state
            self._restore_configuration_state(snapshot.configuration_snapshot)
            
            self.logger.info(f"Rollback to snapshot {snapshot_id} completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rolling back to snapshot {snapshot_id}: {e}")
            return False
    
    def list_system_snapshots(self, limit: int = 50) -> List[SystemSnapshot]:
        """List available system snapshots."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM system_snapshots 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            snapshots = []
            
            for row in rows:
                snapshot = SystemSnapshot(
                    snapshot_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    description=row[2],
                    constitution_snapshot=json.loads(row[3]) if row[3] else {},
                    conversation_count=row[4],
                    document_count=row[5],
                    configuration_snapshot=json.loads(row[6]) if row[6] else {},
                    system_health=json.loads(row[7]) if row[7] else {},
                    resource_usage=json.loads(row[8]) if row[8] else {},
                    created_by=row[9],
                    tags=json.loads(row[10]) if row[10] else []
                )
                snapshots.append(snapshot)
            
            return snapshots
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status."""
        snapshots = self.list_system_snapshots(10)
        
        # Get recent recovery plans
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT plan_id, status, progress_percent, error_message 
                FROM recovery_plans 
                ORDER BY plan_id DESC 
                LIMIT 10
            """)
            recent_plans = cursor.fetchall()
        
        return {
            "snapshots": {
                "total_snapshots": len(snapshots),
                "latest_snapshot": snapshots[0].timestamp.isoformat() if snapshots else None,
                "oldest_snapshot": snapshots[-1].timestamp.isoformat() if snapshots else None
            },
            "recovery_plans": {
                "total_plans": len(recent_plans),
                "active_plans": len([p for p in recent_plans if p[1] == "executing"]),
                "completed_plans": len([p for p in recent_plans if p[1] == "completed"]),
                "failed_plans": len([p for p in recent_plans if p[1] == "failed"])
            },
            "system_health": self._capture_system_health()
        }
    
    def _find_best_backup_for_timestamp(self, target_timestamp: datetime) -> Optional[BackupMetadata]:
        """Find the best backup for a target timestamp."""
        backups = self.backup_system.list_backups()
        
        # Find backups before the target timestamp
        suitable_backups = [
            b for b in backups 
            if b.timestamp <= target_timestamp and b.verification_status == "verified"
        ]
        
        if not suitable_backups:
            return None
        
        # Return the most recent backup before the target
        return max(suitable_backups, key=lambda b: b.timestamp)
    
    def _assess_recovery_risk(self, target_timestamp: datetime, components: List[str]) -> str:
        """Assess the risk level of a recovery operation."""
        now = datetime.now(timezone.utc)
        time_diff = now - target_timestamp
        
        # Risk factors
        risk_score = 0
        
        # Time-based risk
        if time_diff.days > 30:
            risk_score += 2
        elif time_diff.days > 7:
            risk_score += 1
        
        # Component-based risk
        if "constitution" in components:
            risk_score += 2  # High risk for constitution changes
        if "configuration" in components:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 4:
            return "high"
        elif risk_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _create_recovery_steps(self, backup: BackupMetadata, components: List[str]) -> List[Dict[str, Any]]:
        """Create detailed recovery steps."""
        steps = []
        
        # Step 1: Create pre-recovery backup
        steps.append({
            "type": "backup",
            "description": "Create pre-recovery backup",
            "action": "create_backup",
            "parameters": {"backup_type": "full", "description": "Pre-recovery backup"}
        })
        
        # Step 2: Stop services
        steps.append({
            "type": "service",
            "description": "Stop AI services",
            "action": "stop_services",
            "parameters": {}
        })
        
        # Step 3: Restore from backup
        restore_scope = {comp: True for comp in components}
        steps.append({
            "type": "restore",
            "description": f"Restore from backup {backup.backup_id}",
            "action": "restore_backup",
            "parameters": {
                "backup_id": backup.backup_id,
                "restore_scope": restore_scope
            }
        })
        
        # Step 4: Verify restoration
        steps.append({
            "type": "verification",
            "description": "Verify system integrity",
            "action": "verify_system",
            "parameters": {"components": components}
        })
        
        # Step 5: Restart services
        steps.append({
            "type": "service",
            "description": "Restart AI services",
            "action": "start_services",
            "parameters": {}
        })
        
        return steps
    
    def _estimate_recovery_duration(self, steps: List[Dict[str, Any]]) -> int:
        """Estimate recovery duration in minutes."""
        duration_map = {
            "backup": 10,
            "service": 2,
            "restore": 15,
            "verification": 5
        }
        
        total_duration = 0
        for step in steps:
            step_type = step.get("type", "unknown")
            total_duration += duration_map.get(step_type, 5)
        
        return total_duration
    
    def _assess_data_loss_risk(self, target_timestamp: datetime) -> bool:
        """Assess if there's a risk of data loss."""
        now = datetime.now(timezone.utc)
        time_diff = now - target_timestamp
        
        # If rolling back more than 1 day, there's potential data loss
        return time_diff.days > 1
    
    def _execute_recovery_step(self, step: Dict[str, Any]) -> bool:
        """Execute a single recovery step."""
        try:
            action = step.get("action")
            parameters = step.get("parameters", {})
            
            if action == "create_backup":
                self.backup_system.create_backup(
                    backup_type=parameters.get("backup_type", "full"),
                    description=parameters.get("description", "Recovery backup")
                )
            
            elif action == "restore_backup":
                self.backup_system.restore_from_backup(
                    backup_id=parameters["backup_id"],
                    restore_scope=parameters.get("restore_scope", {})
                )
            
            elif action == "stop_services":
                # In a real implementation, this would stop AI services
                self.logger.info("Services stopped (simulated)")
            
            elif action == "start_services":
                # In a real implementation, this would start AI services
                self.logger.info("Services started (simulated)")
            
            elif action == "verify_system":
                # In a real implementation, this would verify system integrity
                self.logger.info("System verification completed (simulated)")
            
            else:
                self.logger.warning(f"Unknown recovery action: {action}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing recovery step: {e}")
            return False
    
    def _capture_constitution_state(self) -> Dict[str, Any]:
        """Capture current constitution state."""
        try:
            constitution_path = Path("./data/constitution.json")
            if constitution_path.exists():
                with open(constitution_path) as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Error capturing constitution state: {e}")
        
        return {}
    
    def _capture_configuration_state(self) -> Dict[str, Any]:
        """Capture current configuration state."""
        config_state = {}
        
        try:
            # Capture various configuration files
            config_files = [
                "./config/config.yaml",
                "./.env",
                "./time_capsule/backup_config.json"
            ]
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file) as f:
                        if config_file.endswith('.json'):
                            config_state[config_file] = json.load(f)
                        else:
                            config_state[config_file] = f.read()
                            
        except Exception as e:
            self.logger.warning(f"Error capturing configuration state: {e}")
        
        return config_state
    
    def _capture_system_health(self) -> Dict[str, Any]:
        """Capture current system health metrics."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "backup_system_status": "active",
            "constitutional_engine_status": "active",
            "chat_api_status": "active"
        }
    
    def _capture_resource_usage(self) -> Dict[str, Any]:
        """Capture current resource usage."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "disk_usage_mb": 0,  # Would be calculated in real implementation
            "memory_usage_mb": 0,  # Would be calculated in real implementation
            "cpu_usage_percent": 0  # Would be calculated in real implementation
        }
    
    def _count_conversations(self) -> int:
        """Count current conversations."""
        try:
            conversations_path = Path("./conversations")
            if conversations_path.exists():
                return len(list(conversations_path.glob("*.json")))
        except Exception:
            pass
        return 0
    
    def _count_documents(self) -> int:
        """Count current documents."""
        try:
            documents_path = Path("./vault")
            if documents_path.exists():
                return len(list(documents_path.glob("**/*")))
        except Exception:
            pass
        return 0
    
    def _restore_constitution_state(self, constitution_state: Dict[str, Any]):
        """Restore constitution state."""
        try:
            constitution_path = Path("./data/constitution.json")
            constitution_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(constitution_path, 'w') as f:
                json.dump(constitution_state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error restoring constitution state: {e}")
            raise
    
    def _restore_configuration_state(self, configuration_state: Dict[str, Any]):
        """Restore configuration state."""
        try:
            for config_file, content in configuration_state.items():
                config_path = Path(config_file)
                config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(config_path, 'w') as f:
                    if isinstance(content, dict):
                        json.dump(content, f, indent=2)
                    else:
                        f.write(content)
                        
        except Exception as e:
            self.logger.error(f"Error restoring configuration state: {e}")
            raise
    
    def _save_system_snapshot(self, snapshot: SystemSnapshot):
        """Save system snapshot to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO system_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.timestamp.isoformat(),
                snapshot.description,
                json.dumps(snapshot.constitution_snapshot),
                snapshot.conversation_count,
                snapshot.document_count,
                json.dumps(snapshot.configuration_snapshot),
                json.dumps(snapshot.system_health),
                json.dumps(snapshot.resource_usage),
                snapshot.created_by,
                json.dumps(snapshot.tags)
            ))
            conn.commit()
    
    def _load_system_snapshot(self, snapshot_id: str) -> Optional[SystemSnapshot]:
        """Load system snapshot from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM system_snapshots WHERE snapshot_id = ?",
                (snapshot_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return SystemSnapshot(
                    snapshot_id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    description=row[2],
                    constitution_snapshot=json.loads(row[3]) if row[3] else {},
                    conversation_count=row[4],
                    document_count=row[5],
                    configuration_snapshot=json.loads(row[6]) if row[6] else {},
                    system_health=json.loads(row[7]) if row[7] else {},
                    resource_usage=json.loads(row[8]) if row[8] else {},
                    created_by=row[9],
                    tags=json.loads(row[10]) if row[10] else []
                )
        
        return None
    
    def _save_recovery_plan(self, plan: RecoveryPlan):
        """Save recovery plan to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO recovery_plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.plan_id,
                plan.description,
                plan.target_timestamp.isoformat(),
                json.dumps(plan.steps),
                plan.estimated_duration_minutes,
                plan.risk_level,
                json.dumps(plan.affected_components),
                plan.data_loss_risk,
                plan.status,
                plan.current_step,
                plan.progress_percent,
                plan.error_message
            ))
            conn.commit()
    
    def _load_recovery_plan(self, plan_id: str) -> Optional[RecoveryPlan]:
        """Load recovery plan from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM recovery_plans WHERE plan_id = ?",
                (plan_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return RecoveryPlan(
                    plan_id=row[0],
                    description=row[1],
                    target_timestamp=datetime.fromisoformat(row[2]),
                    steps=json.loads(row[3]) if row[3] else [],
                    estimated_duration_minutes=row[4],
                    risk_level=row[5],
                    affected_components=json.loads(row[6]) if row[6] else [],
                    data_loss_risk=row[7],
                    status=row[8],
                    current_step=row[9],
                    progress_percent=row[10],
                    error_message=row[11]
                )
        
        return None
    
    def _update_recovery_plan(self, plan: RecoveryPlan):
        """Update recovery plan in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE recovery_plans SET 
                    status = ?, current_step = ?, progress_percent = ?, error_message = ?
                WHERE plan_id = ?
            """, (
                plan.status,
                plan.current_step,
                plan.progress_percent,
                plan.error_message,
                plan.plan_id
            ))
            conn.commit()

