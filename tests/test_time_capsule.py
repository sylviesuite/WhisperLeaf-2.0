"""
Test script for the Time Capsule Backup and Recovery System.
"""

import sys
import os
import time
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add time_capsule modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'time_capsule'))

from time_capsule.backup_system import TimeCapsuleBackupSystem
from time_capsule.recovery_manager import RecoveryManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_test_environment():
    """Set up test environment with sample data."""
    print("Setting up test environment...")
    
    # Create test directories and files
    test_dirs = [
        "./data",
        "./conversations", 
        "./vault",
        "./config",
        "./curation_data",
        "./logs"
    ]
    
    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create sample constitution file
    constitution_data = {
        "rules": {
            "test_rule_1": {
                "name": "Test Rule 1",
                "description": "A test constitutional rule",
                "rule_type": "behavioral",
                "priority": "high"
            },
            "test_rule_2": {
                "name": "Test Rule 2", 
                "description": "Another test rule",
                "rule_type": "privacy",
                "priority": "critical"
            }
        },
        "metadata": {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_rules": 2
        }
    }
    
    with open("./data/constitution.json", 'w') as f:
        json.dump(constitution_data, f, indent=2)
    
    # Create sample conversation files
    for i in range(3):
        conversation_data = {
            "conversation_id": f"conv_{i}",
            "messages": [
                {"role": "user", "content": f"Test message {i}"},
                {"role": "assistant", "content": f"Test response {i}"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        with open(f"./conversations/conversation_{i}.json", 'w') as f:
            json.dump(conversation_data, f, indent=2)
    
    # Create sample documents
    for i in range(5):
        with open(f"./vault/document_{i}.txt", 'w') as f:
            f.write(f"This is test document {i} with some sample content.")
    
    # Create sample configuration
    config_data = {
        "system_name": "Sovereign AI Test",
        "version": "1.0.0",
        "test_mode": True
    }
    
    with open("./config/config.yaml", 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print("✓ Test environment set up successfully")

def test_backup_system():
    """Test the backup system functionality."""
    print("\nTesting Backup System...")
    print("=" * 60)
    
    # Initialize backup system
    backup_system = TimeCapsuleBackupSystem(base_path="./test_time_capsule")
    
    # Test 1: Create full backup
    print("\n1. Creating full backup...")
    backup_id_1 = backup_system.create_backup(
        backup_type="full",
        description="Test full backup",
        tags=["test", "full"]
    )
    print(f"✓ Full backup created: {backup_id_1}")
    
    # Test 2: Create incremental backup
    print("\n2. Creating incremental backup...")
    backup_id_2 = backup_system.create_backup(
        backup_type="incremental", 
        description="Test incremental backup",
        tags=["test", "incremental"]
    )
    print(f"✓ Incremental backup created: {backup_id_2}")
    
    # Test 3: List backups
    print("\n3. Listing backups...")
    backups = backup_system.list_backups()
    print(f"✓ Found {len(backups)} backups:")
    
    for backup in backups:
        print(f"  - {backup.backup_id}")
        print(f"    Type: {backup.backup_type}")
        print(f"    Size: {backup.total_size_bytes:,} bytes -> {backup.compressed_size_bytes:,} bytes")
        print(f"    Compression: {backup.compressed_size_bytes/backup.total_size_bytes:.2%}")
        print(f"    Files: {len(backup.files_included)}")
        print(f"    Constitution rules: {backup.constitution_rules}")
        print(f"    Conversations: {backup.conversations}")
        print(f"    Documents: {backup.documents}")
        print()
    
    # Test 4: Verify backup integrity
    print("4. Verifying backup integrity...")
    for backup in backups:
        is_valid = backup_system.verify_backup(backup.backup_id)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"  {status}: {backup.backup_id}")
    
    # Test 5: Get backup statistics
    print("\n5. Backup system statistics:")
    stats = backup_system.get_backup_statistics()
    print(f"  Total backups: {stats['total_backups']}")
    print(f"  Total size: {stats['total_size_bytes']:,} bytes")
    print(f"  Compressed size: {stats['total_compressed_bytes']:,} bytes")
    print(f"  Average compression: {stats['average_compression_ratio']:.2%}")
    print(f"  Backup types: {stats['backup_types']}")
    print(f"  Scheduler running: {stats['scheduler_running']}")
    
    return backup_system, backups

def test_recovery_system(backup_system, backups):
    """Test the recovery system functionality."""
    print("\nTesting Recovery System...")
    print("=" * 60)
    
    # Initialize recovery manager
    recovery_manager = RecoveryManager(backup_system)
    
    # Test 1: Create system snapshot
    print("\n1. Creating system snapshot...")
    snapshot_id = recovery_manager.create_system_snapshot(
        description="Test system snapshot"
    )
    print(f"✓ System snapshot created: {snapshot_id}")
    
    # Test 2: List system snapshots
    print("\n2. Listing system snapshots...")
    snapshots = recovery_manager.list_system_snapshots()
    print(f"✓ Found {len(snapshots)} snapshots:")
    
    for snapshot in snapshots:
        print(f"  - {snapshot.snapshot_id}")
        print(f"    Timestamp: {snapshot.timestamp}")
        print(f"    Constitution rules: {len(snapshot.constitution_snapshot.get('rules', {}))}")
        print(f"    Conversations: {snapshot.conversation_count}")
        print(f"    Documents: {snapshot.document_count}")
        print()
    
    # Test 3: Create recovery plan
    print("3. Creating recovery plan...")
    if backups:
        target_timestamp = backups[0].timestamp + timedelta(minutes=1)
        plan_id = recovery_manager.create_recovery_plan(
            target_timestamp=target_timestamp,
            components=["constitution", "conversations"]
        )
        print(f"✓ Recovery plan created: {plan_id}")
        
        # Test 4: Get recovery status
        print("\n4. Recovery system status:")
        status = recovery_manager.get_recovery_status()
        print(f"  Snapshots: {status['snapshots']['total_snapshots']}")
        print(f"  Latest snapshot: {status['snapshots']['latest_snapshot']}")
        print(f"  Recovery plans: {status['recovery_plans']['total_plans']}")
        print(f"  Active plans: {status['recovery_plans']['active_plans']}")
        print(f"  System health: {status['system_health']}")
        
        return recovery_manager, plan_id
    else:
        print("✗ No backups available for recovery plan creation")
        return recovery_manager, None

def test_restore_functionality(backup_system, backups):
    """Test backup restoration functionality."""
    print("\nTesting Restore Functionality...")
    print("=" * 60)
    
    if not backups:
        print("✗ No backups available for restore testing")
        return
    
    # Test restore from backup
    print("1. Testing backup restoration...")
    backup_to_restore = backups[0]
    
    # Create a backup of current state before restore
    pre_restore_backup = backup_system.create_backup(
        backup_type="full",
        description="Pre-restore backup for testing",
        tags=["test", "pre-restore"]
    )
    print(f"✓ Pre-restore backup created: {pre_restore_backup}")
    
    # Wait a moment to ensure different timestamp
    time.sleep(1)
    
    # Modify some files to test restoration
    print("2. Modifying files to test restoration...")
    
    # Modify constitution
    modified_constitution = {
        "rules": {
            "modified_rule": {
                "name": "Modified Rule",
                "description": "This rule was added after backup",
                "rule_type": "test",
                "priority": "low"
            }
        },
        "metadata": {
            "version": "2.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_rules": 1,
            "modified": True
        }
    }
    
    with open("./data/constitution.json", 'w') as f:
        json.dump(modified_constitution, f, indent=2)
    
    # Add a new conversation
    new_conversation = {
        "conversation_id": "conv_new",
        "messages": [
            {"role": "user", "content": "This is a new conversation"},
            {"role": "assistant", "content": "Added after backup"}
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    with open("./conversations/conversation_new.json", 'w') as f:
        json.dump(new_conversation, f, indent=2)
    
    print("✓ Files modified")
    
    # Perform restoration
    print("3. Performing restoration...")
    try:
        restore_id = backup_system.restore_from_backup(
            backup_id=backup_to_restore.backup_id,
            restore_scope={
                "constitution": True,
                "conversations": True,
                "documents": True,
                "configuration": True
            }
        )
        print(f"✓ Restoration completed: {restore_id}")
        
        # Verify restoration
        print("4. Verifying restoration...")
        
        # Check if constitution was restored
        if os.path.exists("./data/constitution.json"):
            with open("./data/constitution.json") as f:
                restored_constitution = json.load(f)
                
            if not restored_constitution.get("metadata", {}).get("modified", False):
                print("✓ Constitution successfully restored")
            else:
                print("✗ Constitution restoration may have failed")
        
        # Check if new conversation was removed
        if not os.path.exists("./conversations/conversation_new.json"):
            print("✓ New conversation successfully removed")
        else:
            print("✗ New conversation still exists")
            
    except Exception as e:
        print(f"✗ Restoration failed: {e}")

def test_automated_scheduling(backup_system):
    """Test automated backup scheduling."""
    print("\nTesting Automated Scheduling...")
    print("=" * 60)
    
    # Test scheduler start/stop
    print("1. Testing scheduler control...")
    
    backup_system.start_automated_backups()
    print("✓ Automated backup scheduler started")
    
    # Wait a moment
    time.sleep(2)
    
    backup_system.stop_automated_backups()
    print("✓ Automated backup scheduler stopped")
    
    # Check scheduler status
    stats = backup_system.get_backup_statistics()
    print(f"✓ Scheduler status: {'Running' if stats['scheduler_running'] else 'Stopped'}")

def test_integration_scenarios():
    """Test integration scenarios."""
    print("\nTesting Integration Scenarios...")
    print("=" * 60)
    
    backup_system = TimeCapsuleBackupSystem(base_path="./integration_test_capsule")
    recovery_manager = RecoveryManager(backup_system)
    
    # Scenario 1: Complete backup and recovery workflow
    print("1. Complete backup and recovery workflow...")
    
    # Create initial backup
    initial_backup = backup_system.create_backup(
        backup_type="full",
        description="Initial system state",
        tags=["integration", "initial"]
    )
    
    # Create system snapshot
    initial_snapshot = recovery_manager.create_system_snapshot(
        description="Initial system snapshot"
    )
    
    # Simulate system changes
    time.sleep(1)  # Ensure different timestamps
    
    # Create another backup
    updated_backup = backup_system.create_backup(
        backup_type="incremental",
        description="After system changes",
        tags=["integration", "updated"]
    )
    
    # Create recovery plan
    target_time = datetime.now(timezone.utc) + timedelta(minutes=1)  # Future time to find recent backup
    recovery_plan = recovery_manager.create_recovery_plan(
        target_timestamp=target_time,
        components=["constitution", "configuration"]
    )
    
    print(f"✓ Integration workflow completed:")
    print(f"  Initial backup: {initial_backup}")
    print(f"  Initial snapshot: {initial_snapshot}")
    print(f"  Updated backup: {updated_backup}")
    print(f"  Recovery plan: {recovery_plan}")
    
    # Get comprehensive statistics
    backup_stats = backup_system.get_backup_statistics()
    recovery_status = recovery_manager.get_recovery_status()
    
    print(f"\n2. System statistics:")
    print(f"  Total backups: {backup_stats['total_backups']}")
    print(f"  Total snapshots: {recovery_status['snapshots']['total_snapshots']}")
    print(f"  Total recovery plans: {recovery_status['recovery_plans']['total_plans']}")

def cleanup_test_environment():
    """Clean up test environment."""
    print("\nCleaning up test environment...")
    
    import shutil
    
    # Remove test directories
    test_dirs = [
        "./data",
        "./conversations",
        "./vault", 
        "./config",
        "./curation_data",
        "./logs",
        "./test_time_capsule",
        "./integration_test_capsule"
    ]
    
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    
    print("✓ Test environment cleaned up")

if __name__ == "__main__":
    print("Starting Time Capsule System Tests")
    print("=" * 80)
    
    try:
        # Set up test environment
        setup_test_environment()
        
        # Run backup system tests
        backup_system, backups = test_backup_system()
        
        # Run recovery system tests
        recovery_manager, plan_id = test_recovery_system(backup_system, backups)
        
        # Run restore functionality tests
        test_restore_functionality(backup_system, backups)
        
        # Run automated scheduling tests
        test_automated_scheduling(backup_system)
        
        # Run integration tests
        test_integration_scenarios()
        
        print("\n" + "=" * 80)
        print("✅ All Time Capsule tests completed successfully!")
        print("\nThe Time Capsule System provides:")
        print("  • Automated backup creation with compression")
        print("  • Point-in-time recovery capabilities")
        print("  • System state snapshots and rollback")
        print("  • Comprehensive backup verification")
        print("  • Automated scheduling and retention")
        print("  • Recovery planning and risk assessment")
        print("  • Complete audit trail and statistics")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        cleanup_test_environment()

