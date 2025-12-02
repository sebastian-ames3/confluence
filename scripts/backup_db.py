#!/usr/bin/env python3
"""
Database Backup Script

Creates timestamped backups of the SQLite database.
Keeps last N backups (configurable).

Usage:
    python scripts/backup_db.py           # Create backup
    python scripts/backup_db.py list      # List existing backups
    python scripts/backup_db.py restore <backup_name>  # Restore from backup

Can be scheduled via cron/Task Scheduler for regular backups.

PRD-017: Database backup strategy implementation.
"""

import shutil
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configuration
DB_PATH = Path(__file__).parent.parent / "database" / "confluence.db"
BACKUP_DIR = Path(__file__).parent.parent / "backups"
MAX_BACKUPS = 4  # Keep last 4 backups (1 month if weekly)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_database() -> bool:
    """
    Create timestamped backup of database.

    Returns:
        True if backup successful, False otherwise
    """
    if not DB_PATH.exists():
        logger.error(f"Database not found: {DB_PATH}")
        return False

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"confluence_{timestamp}.db"

    # Copy database
    try:
        shutil.copy2(DB_PATH, backup_path)
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        logger.info(f"Backup created: {backup_path} ({size_mb:.2f} MB)")
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False

    # Rotate old backups
    rotate_backups()

    return True


def rotate_backups():
    """Remove old backups, keeping only MAX_BACKUPS most recent."""
    backups = sorted(BACKUP_DIR.glob("confluence_*.db"))

    if len(backups) > MAX_BACKUPS:
        for old_backup in backups[:-MAX_BACKUPS]:
            logger.info(f"Removing old backup: {old_backup}")
            old_backup.unlink()


def list_backups():
    """List all existing backups."""
    if not BACKUP_DIR.exists():
        logger.info("No backups directory found")
        return

    backups = sorted(BACKUP_DIR.glob("confluence_*.db"))

    if not backups:
        logger.info("No backups found")
        return

    logger.info(f"Found {len(backups)} backup(s):")
    for backup in backups:
        size_mb = backup.stat().st_size / (1024 * 1024)
        # Parse timestamp from filename
        try:
            ts_str = backup.stem.replace("confluence_", "")
            ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            age = datetime.now() - ts
            age_str = f"{age.days}d ago" if age.days > 0 else f"{age.seconds // 3600}h ago"
        except ValueError:
            age_str = "unknown age"

        logger.info(f"  {backup.name} ({size_mb:.2f} MB) - {age_str}")


def restore_backup(backup_name: str) -> bool:
    """
    Restore database from backup.

    Args:
        backup_name: Name of backup file (e.g., 'confluence_20251201_120000.db')

    Returns:
        True if restore successful, False otherwise
    """
    backup_path = BACKUP_DIR / backup_name

    if not backup_path.exists():
        logger.error(f"Backup not found: {backup_path}")
        return False

    # Create backup of current DB before restore
    if DB_PATH.exists():
        pre_restore = DB_PATH.with_suffix(".db.pre_restore")
        shutil.copy2(DB_PATH, pre_restore)
        logger.info(f"Current DB backed up to: {pre_restore}")

    # Restore
    try:
        shutil.copy2(backup_path, DB_PATH)
        logger.info(f"Database restored from: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "list":
            list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            backup_name = sys.argv[2]
            success = restore_backup(backup_name)
            sys.exit(0 if success else 1)
        else:
            print("Usage:")
            print("  python scripts/backup_db.py           # Create backup")
            print("  python scripts/backup_db.py list      # List backups")
            print("  python scripts/backup_db.py restore <backup_name>  # Restore")
            sys.exit(1)
    else:
        success = backup_database()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
