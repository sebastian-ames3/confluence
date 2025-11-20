"""
Cleanup Manager

Manages automated cleanup of temp files and database records to prevent storage bloat.

Features:
- Temp file cleanup (extracted images, transcripts)
- Database record archiving and deletion
- Storage statistics tracking
- Configurable retention policies
- Dry-run mode for testing
"""

import os
import logging
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sqlite3

logger = logging.getLogger(__name__)

# Default retention policies (in seconds)
DEFAULT_RETENTION = {
    "extracted_images": 24 * 3600,      # 24 hours
    "transcripts": 48 * 3600,            # 48 hours
    "other_temp": 24 * 3600,             # 24 hours
    "raw_content_db": 180 * 86400,       # 6 months
    "analyzed_content_db": 180 * 86400,  # 6 months
    "extracted_images_db": 7 * 86400,    # 7 days
}


class CleanupManager:
    """
    Manages automated cleanup of temp files and database records.

    Prevents storage bloat by:
    - Deleting old temp files (images, transcripts)
    - Archiving and deleting old database records
    - Tracking storage usage statistics
    """

    def __init__(
        self,
        db_path: str = "database/confluence.db",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Cleanup Manager.

        Args:
            db_path: Path to SQLite database
            config: Optional configuration overrides
        """
        self.db_path = db_path
        self.config = config or {}
        self.retention_policy = self.config.get("retention", DEFAULT_RETENTION)

        logger.info("Initialized CleanupManager")

    def cleanup_temp_files(
        self,
        temp_dir: str = "temp",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Delete temp files older than retention policy.

        Args:
            temp_dir: Root temp directory
            dry_run: If True, only report what would be deleted (don't actually delete)

        Returns:
            Cleanup statistics
        """
        try:
            logger.info(f"Starting temp file cleanup (dry_run={dry_run})")

            if not os.path.exists(temp_dir):
                logger.warning(f"Temp directory does not exist: {temp_dir}")
                return {
                    "status": "skipped",
                    "reason": "Temp directory does not exist",
                    "files_deleted": 0,
                    "space_freed_mb": 0
                }

            files_to_delete = []
            total_size = 0
            now = datetime.now()

            # Walk through temp directory
            for root, dirs, files in os.walk(temp_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)

                    # Get file age
                    try:
                        file_stat = os.stat(file_path)
                        file_age_seconds = (now - datetime.fromtimestamp(file_stat.st_mtime)).total_seconds()
                        file_size = file_stat.st_size

                        # Determine retention policy based on subdirectory
                        retention_seconds = self._get_retention_for_file(root)

                        # Check if file should be deleted
                        if file_age_seconds > retention_seconds:
                            # Safety check: Never delete files < 1 hour old
                            if file_age_seconds < 3600:
                                logger.warning(
                                    f"Skipping recent file (< 1 hour old): {file_path}"
                                )
                                continue

                            files_to_delete.append({
                                "path": file_path,
                                "size": file_size,
                                "age_hours": file_age_seconds / 3600
                            })
                            total_size += file_size

                    except Exception as e:
                        logger.error(f"Error checking file {file_path}: {e}")

            # Delete files (if not dry run)
            deleted_count = 0
            if not dry_run:
                for file_info in files_to_delete:
                    try:
                        os.remove(file_info["path"])
                        deleted_count += 1
                        logger.debug(
                            f"Deleted: {file_info['path']} "
                            f"(age: {file_info['age_hours']:.1f}h, size: {file_info['size']/1024/1024:.2f} MB)"
                        )
                    except Exception as e:
                        logger.error(f"Failed to delete {file_info['path']}: {e}")

            space_freed_mb = total_size / 1024 / 1024

            logger.info(
                f"Temp file cleanup complete: "
                f"{deleted_count if not dry_run else len(files_to_delete)} files "
                f"({'would be ' if dry_run else ''}deleted), "
                f"{space_freed_mb:.2f} MB {'would be ' if dry_run else ''}freed"
            )

            return {
                "status": "success",
                "dry_run": dry_run,
                "files_deleted": deleted_count if not dry_run else 0,
                "files_identified": len(files_to_delete),
                "space_freed_mb": space_freed_mb if not dry_run else 0,
                "space_identified_mb": space_freed_mb,
                "files": files_to_delete[:10]  # Return first 10 for inspection
            }

        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "files_deleted": 0,
                "space_freed_mb": 0
            }

    def cleanup_database(
        self,
        archive_path: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Archive and delete old database records.

        Args:
            archive_path: Directory to save archived records (optional)
            dry_run: If True, only report what would be deleted

        Returns:
            Cleanup statistics
        """
        try:
            logger.info(f"Starting database cleanup (dry_run={dry_run})")

            if not os.path.exists(self.db_path):
                logger.warning(f"Database does not exist: {self.db_path}")
                return {
                    "status": "skipped",
                    "reason": "Database does not exist"
                }

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            results = {
                "status": "success",
                "dry_run": dry_run,
                "tables_cleaned": {}
            }

            # 1. Clean raw_content (processed records older than 6 months)
            raw_cutoff = datetime.now() - timedelta(seconds=self.retention_policy["raw_content_db"])
            raw_cutoff_str = raw_cutoff.isoformat()

            # Count records to delete
            cursor.execute(
                "SELECT COUNT(*) FROM raw_content WHERE processed = 1 AND collected_at < ?",
                (raw_cutoff_str,)
            )
            raw_count = cursor.fetchone()[0]

            if raw_count > 0 and not dry_run:
                # Archive if path provided
                if archive_path:
                    self._archive_records(
                        cursor,
                        "raw_content",
                        f"processed = 1 AND collected_at < '{raw_cutoff_str}'",
                        archive_path
                    )

                # Delete
                cursor.execute(
                    "DELETE FROM raw_content WHERE processed = 1 AND collected_at < ?",
                    (raw_cutoff_str,)
                )
                logger.info(f"Deleted {cursor.rowcount} old raw_content records")

            results["tables_cleaned"]["raw_content"] = {
                "records_identified": raw_count,
                "records_deleted": cursor.rowcount if not dry_run else 0
            }

            # 2. Clean analyzed_content (older than 6 months)
            analyzed_cutoff = datetime.now() - timedelta(seconds=self.retention_policy["analyzed_content_db"])
            analyzed_cutoff_str = analyzed_cutoff.isoformat()

            cursor.execute(
                "SELECT COUNT(*) FROM analyzed_content WHERE analyzed_at < ?",
                (analyzed_cutoff_str,)
            )
            analyzed_count = cursor.fetchone()[0]

            if analyzed_count > 0 and not dry_run:
                if archive_path:
                    self._archive_records(
                        cursor,
                        "analyzed_content",
                        f"analyzed_at < '{analyzed_cutoff_str}'",
                        archive_path
                    )

                cursor.execute(
                    "DELETE FROM analyzed_content WHERE analyzed_at < ?",
                    (analyzed_cutoff_str,)
                )
                logger.info(f"Deleted {cursor.rowcount} old analyzed_content records")

            results["tables_cleaned"]["analyzed_content"] = {
                "records_identified": analyzed_count,
                "records_deleted": cursor.rowcount if not dry_run else 0
            }

            # 3. Clean extracted_images (older than 7 days) - if table exists
            try:
                images_cutoff = datetime.now() - timedelta(seconds=self.retention_policy["extracted_images_db"])
                images_cutoff_str = images_cutoff.isoformat()

                cursor.execute(
                    "SELECT COUNT(*) FROM extracted_images WHERE created_at < ?",
                    (images_cutoff_str,)
                )
                images_count = cursor.fetchone()[0]

                if images_count > 0 and not dry_run:
                    cursor.execute(
                        "DELETE FROM extracted_images WHERE created_at < ?",
                        (images_cutoff_str,)
                    )
                    logger.info(f"Deleted {cursor.rowcount} old extracted_images records")

                results["tables_cleaned"]["extracted_images"] = {
                    "records_identified": images_count,
                    "records_deleted": cursor.rowcount if not dry_run else 0
                }
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    logger.debug("extracted_images table does not exist yet - skipping")
                    results["tables_cleaned"]["extracted_images"] = {
                        "records_identified": 0,
                        "records_deleted": 0,
                        "note": "Table does not exist"
                    }
                else:
                    raise

            # Commit changes
            if not dry_run:
                conn.commit()

            conn.close()

            total_identified = sum(t["records_identified"] for t in results["tables_cleaned"].values())
            total_deleted = sum(t["records_deleted"] for t in results["tables_cleaned"].values())

            logger.info(
                f"Database cleanup complete: "
                f"{total_deleted if not dry_run else total_identified} records "
                f"{'would be ' if dry_run else ''}deleted"
            )

            results["total_records_identified"] = total_identified
            results["total_records_deleted"] = total_deleted

            return results

        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get current storage usage statistics.

        Returns:
            Storage statistics
        """
        try:
            logger.info("Gathering storage statistics")

            stats = {
                "temp_files": {},
                "database": {},
                "total_disk_usage_mb": 0
            }

            # Get temp directory stats
            temp_dir = "temp"
            if os.path.exists(temp_dir):
                temp_size = 0
                temp_count = 0

                for root, dirs, files in os.walk(temp_dir):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        try:
                            temp_size += os.path.getsize(file_path)
                            temp_count += 1
                        except:
                            pass

                stats["temp_files"] = {
                    "size_mb": temp_size / 1024 / 1024,
                    "file_count": temp_count
                }
                stats["total_disk_usage_mb"] += temp_size / 1024 / 1024

            # Get database stats
            if os.path.exists(self.db_path):
                db_size = os.path.getsize(self.db_path)
                stats["database"] = {
                    "size_mb": db_size / 1024 / 1024,
                    "path": self.db_path
                }
                stats["total_disk_usage_mb"] += db_size / 1024 / 1024

                # Get record counts
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    try:
                        cursor.execute("SELECT COUNT(*) FROM raw_content")
                        stats["database"]["raw_content_count"] = cursor.fetchone()[0]
                    except:
                        stats["database"]["raw_content_count"] = 0

                    try:
                        cursor.execute("SELECT COUNT(*) FROM analyzed_content")
                        stats["database"]["analyzed_content_count"] = cursor.fetchone()[0]
                    except:
                        stats["database"]["analyzed_content_count"] = 0

                    try:
                        cursor.execute("SELECT COUNT(*) FROM extracted_images")
                        stats["database"]["extracted_images_count"] = cursor.fetchone()[0]
                    except:
                        stats["database"]["extracted_images_count"] = 0

                    conn.close()
                except Exception as e:
                    logger.warning(f"Could not connect to database: {e}")

            logger.info(f"Total disk usage: {stats['total_disk_usage_mb']:.2f} MB")

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "error": str(e)
            }

    def _get_retention_for_file(self, file_path: str) -> int:
        """
        Get retention policy for a file based on its path.

        Args:
            file_path: File path

        Returns:
            Retention period in seconds
        """
        if "extracted_images" in file_path:
            return self.retention_policy["extracted_images"]
        elif "transcripts" in file_path:
            return self.retention_policy["transcripts"]
        else:
            return self.retention_policy["other_temp"]

    def _archive_records(
        self,
        cursor: sqlite3.Cursor,
        table_name: str,
        where_clause: str,
        archive_path: str
    ):
        """
        Archive database records to JSON before deletion.

        Args:
            cursor: Database cursor
            table_name: Table to archive from
            where_clause: WHERE clause for selecting records
            archive_path: Directory to save archives
        """
        try:
            # Create archive directory
            os.makedirs(archive_path, exist_ok=True)

            # Get records
            cursor.execute(f"SELECT * FROM {table_name} WHERE {where_clause}")
            records = cursor.fetchall()

            if not records:
                return

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            # Convert to list of dicts
            records_dict = [dict(zip(columns, record)) for record in records]

            # Save to JSON
            archive_filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            archive_filepath = os.path.join(archive_path, archive_filename)

            with open(archive_filepath, 'w') as f:
                json.dump(records_dict, f, indent=2)

            logger.info(
                f"Archived {len(records)} {table_name} records to {archive_filepath}"
            )

        except Exception as e:
            logger.error(f"Failed to archive {table_name} records: {e}")
