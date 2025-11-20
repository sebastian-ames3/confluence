"""
Test Cleanup Manager

Tests the automated cleanup system for temp files and database records.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.cleanup_manager import CleanupManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_storage_stats():
    """Test storage statistics gathering."""
    logger.info("=" * 80)
    logger.info("TEST: Storage Statistics")
    logger.info("=" * 80)

    cleanup_mgr = CleanupManager()
    stats = cleanup_mgr.get_storage_stats()

    logger.info("\nStorage Statistics:")
    logger.info(f"  Temp Files: {stats.get('temp_files', {}).get('size_mb', 0):.2f} MB")
    logger.info(f"  Temp File Count: {stats.get('temp_files', {}).get('file_count', 0)}")
    logger.info(f"  Database: {stats.get('database', {}).get('size_mb', 0):.2f} MB")
    logger.info(f"  Total Disk Usage: {stats.get('total_disk_usage_mb', 0):.2f} MB")

    if 'database' in stats:
        logger.info(f"\nDatabase Records:")
        logger.info(f"  raw_content: {stats['database'].get('raw_content_count', 0)}")
        logger.info(f"  analyzed_content: {stats['database'].get('analyzed_content_count', 0)}")
        logger.info(f"  extracted_images: {stats['database'].get('extracted_images_count', 0)}")

    return stats


def test_temp_file_cleanup_dry_run():
    """Test temp file cleanup in dry-run mode."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Temp File Cleanup (Dry Run)")
    logger.info("=" * 80)

    cleanup_mgr = CleanupManager()
    result = cleanup_mgr.cleanup_temp_files(dry_run=True)

    logger.info(f"\nDry Run Results:")
    logger.info(f"  Status: {result.get('status')}")
    logger.info(f"  Files Identified: {result.get('files_identified', 0)}")
    logger.info(f"  Space Would Be Freed: {result.get('space_identified_mb', 0):.2f} MB")

    if result.get('files_identified', 0) > 0:
        logger.info(f"\nSample Files (first 5):")
        for file_info in result.get('files', [])[:5]:
            logger.info(
                f"    - {file_info['path']} "
                f"(age: {file_info['age_hours']:.1f}h, size: {file_info['size']/1024:.2f} KB)"
            )

    return result


def test_database_cleanup_dry_run():
    """Test database cleanup in dry-run mode."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Database Cleanup (Dry Run)")
    logger.info("=" * 80)

    cleanup_mgr = CleanupManager()
    result = cleanup_mgr.cleanup_database(dry_run=True)

    logger.info(f"\nDry Run Results:")
    logger.info(f"  Status: {result.get('status')}")
    logger.info(f"  Total Records Identified: {result.get('total_records_identified', 0)}")

    if 'tables_cleaned' in result:
        logger.info(f"\nTables:")
        for table, info in result['tables_cleaned'].items():
            logger.info(
                f"    - {table}: {info['records_identified']} records "
                f"would be deleted"
            )

    return result


def test_full_cleanup_dry_run():
    """Run full cleanup test (dry run)."""
    logger.info("\n" + "=" * 80)
    logger.info("FULL CLEANUP TEST (DRY RUN)")
    logger.info("=" * 80)

    # Get initial stats
    logger.info("\n1. Initial Storage Statistics:")
    initial_stats = test_storage_stats()

    # Test temp file cleanup
    logger.info("\n2. Temp File Cleanup (Dry Run):")
    temp_result = test_temp_file_cleanup_dry_run()

    # Test database cleanup
    logger.info("\n3. Database Cleanup (Dry Run):")
    db_result = test_database_cleanup_dry_run()

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    total_space_to_free = temp_result.get('space_identified_mb', 0)
    total_files_to_delete = temp_result.get('files_identified', 0)
    total_records_to_delete = db_result.get('total_records_identified', 0)

    logger.info(f"\nCurrent Usage:")
    logger.info(f"  Total Disk: {initial_stats.get('total_disk_usage_mb', 0):.2f} MB")
    logger.info(f"\nCleanup Would Free:")
    logger.info(f"  Temp Files: {total_files_to_delete} files, {total_space_to_free:.2f} MB")
    logger.info(f"  Database Records: {total_records_to_delete} records")

    if total_space_to_free > 0 or total_records_to_delete > 0:
        logger.info(f"\n✅ Cleanup system operational - ready to free space")
    else:
        logger.info(f"\n✅ No cleanup needed - system is clean")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            test_storage_stats()
        elif sys.argv[1] == "temp":
            test_temp_file_cleanup_dry_run()
        elif sys.argv[1] == "db":
            test_database_cleanup_dry_run()
        else:
            logger.error(f"Unknown test: {sys.argv[1]}")
            logger.info("Usage: python test_cleanup.py [stats|temp|db]")
    else:
        # Run full test
        test_full_cleanup_dry_run()
