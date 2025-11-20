# PRD: Automated Database & File Cleanup

**Status:** Planning
**Priority:** Medium (Maintenance)
**Owner:** Sebastian Ames
**Created:** 2025-11-20
**Target:** Post-MVP Enhancement

---

## Executive Summary

Implement automated cleanup of temporary files and database records to prevent storage bloat and maintain system performance.

**Problem:** Extracted PDF images accumulate in temp directories (~150MB/day), database grows with unprocessed content, no cleanup strategy.

**Solution:** Automated cleanup jobs that remove old temp files, archive processed content, and maintain database health.

**Impact:**
- Prevent storage bloat (keep under 1GB total)
- Maintain database performance
- Automatic, hands-off maintenance

---

## Background

### Current State
- PDF images extracted to `temp/extracted_images/` (~5-10MB per PDF)
- Images persist indefinitely (no cleanup)
- Daily collection: 4-6 PDFs × 10MB = 40-60MB/day
- Monthly accumulation: ~1.5GB
- Database grows with all historical content

### The Problem
1. **Storage Bloat:** Temp images never deleted, accumulate indefinitely
2. **Database Growth:** Old processed content remains forever
3. **Performance:** Large temp directories slow file operations
4. **Cost:** Storage costs on deployment (Railway: $0.25/GB/month)

### Why This Matters
- Prevents system degradation over time
- Keeps deployment costs predictable
- Professional system maintenance

---

## User Stories

**As Sebastian**, I want temp files automatically cleaned up after analysis, so I don't have to manually manage storage.

**As the system**, I want to delete processed temp files after 24 hours and archive old database content after 6 months to maintain performance.

**As an operator**, I want configurable retention policies so I can adjust based on needs.

---

## Technical Design

### Cleanup Strategies

#### 1. Temp File Cleanup

**What to Clean:**
- `temp/extracted_images/**/*.png` - Extracted PDF images
- `temp/extracted_images/**/*.jpeg` - Extracted PDF images
- `temp/transcripts/**/*` - Downloaded video files
- `temp/**/*` - Any other temp files

**When to Clean:**
- **Immediate:** After successful analysis (cleanup in finally block)
- **Scheduled:** Daily job deletes files older than 24 hours
- **On-demand:** Manual cleanup script

**Retention Policy:**
```python
DEFAULT_RETENTION = {
    "extracted_images": 24 * 3600,  # 24 hours
    "transcripts": 48 * 3600,        # 48 hours
    "other": 24 * 3600               # 24 hours
}
```

#### 2. Database Cleanup

**What to Clean:**
- `raw_content` where `processed=1` and `collected_at < 6 months ago`
- `analyzed_content` where `analyzed_at < 6 months ago`
- `extracted_images` where `created_at < 7 days ago`

**Retention Policy:**
```python
RETENTION_POLICY = {
    "raw_content": 180 * 86400,      # 6 months
    "analyzed_content": 180 * 86400,  # 6 months
    "extracted_images": 7 * 86400,    # 7 days
    "confluence_scores": None,        # Keep forever
    "themes": None                    # Keep forever
}
```

**Archive Before Delete:**
- Export to JSON before deleting (optional)
- Store in `archives/YYYY-MM/` directory

### Implementation Components

#### CleanupManager

```python
class CleanupManager:
    """Manages automated cleanup of temp files and database records."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.retention_policy = config.get("retention", DEFAULT_RETENTION)

    def cleanup_temp_files(self, age_seconds: int = 86400):
        """Delete temp files older than age_seconds."""
        pass

    def cleanup_database(self, dry_run: bool = False):
        """Archive and delete old database records."""
        pass

    def get_storage_stats(self) -> Dict[str, Any]:
        """Return current storage usage statistics."""
        pass
```

### Scheduled Jobs

**Daily Cleanup (2am):**
```python
schedule.every().day.at("02:00").do(cleanup_temp_files)
schedule.every().day.at("02:30").do(cleanup_database)
```

**Weekly Stats (Sunday 3am):**
```python
schedule.every().sunday.at("03:00").do(generate_cleanup_report)
```

### Safety Mechanisms

1. **Dry Run Mode:** Test cleanup without deleting
2. **Backup Before Delete:** Optional archiving to JSON
3. **Minimum Age Check:** Never delete files < 1 hour old
4. **Disk Space Check:** Only cleanup if disk usage > 80%
5. **Foreign Key Cascade:** Database deletes respect FK constraints

---

## Implementation Plan

### Phase 1: Immediate Cleanup (Day 1)
- Add `finally` blocks to PDF Analyzer to cleanup temp images
- Add `finally` blocks to Transcript Harvester to cleanup videos
- Test with real analysis runs

### Phase 2: Scheduled Cleanup (Day 1-2)
- Create `CleanupManager` class
- Implement `cleanup_temp_files()` method
- Add scheduled job to run daily at 2am
- Test scheduled execution

### Phase 3: Database Cleanup (Day 2)
- Implement `cleanup_database()` method
- Add archive-before-delete logic
- Create retention policy configuration
- Test with dry-run mode

### Phase 4: Monitoring (Day 2-3)
- Add storage statistics tracking
- Create cleanup report generation
- Add logging for all cleanup operations
- Test monitoring and reporting

---

## Configuration

### cleanup_config.json

```json
{
  "temp_files": {
    "enabled": true,
    "retention_hours": 24,
    "paths": [
      "temp/extracted_images",
      "temp/transcripts"
    ],
    "schedule": "02:00"
  },
  "database": {
    "enabled": true,
    "archive_before_delete": true,
    "archive_path": "archives",
    "retention_days": {
      "raw_content": 180,
      "analyzed_content": 180,
      "extracted_images": 7
    },
    "schedule": "02:30"
  },
  "safety": {
    "dry_run": false,
    "min_age_hours": 1,
    "backup_before_delete": true,
    "require_disk_usage_threshold": 0.8
  }
}
```

### Environment Variables

```bash
CLEANUP_ENABLED=true
CLEANUP_RETENTION_HOURS=24
CLEANUP_ARCHIVE_ENABLED=true
CLEANUP_SCHEDULE="02:00"
```

---

## Testing Strategy

### Unit Tests
- Test age calculation logic
- Test file deletion with mock filesystem
- Test database query generation
- Test dry-run mode

### Integration Tests
- Create temp files, verify cleanup
- Insert old database records, verify deletion
- Test foreign key cascade behavior
- Test archive creation

### Production Testing
- Run in dry-run mode for 1 week
- Monitor logs for errors
- Verify expected files are marked for deletion
- Enable deletion after validation

---

## Monitoring & Alerts

### Metrics to Track

```python
{
  "storage": {
    "temp_files_size_mb": 150,
    "temp_files_count": 1420,
    "database_size_mb": 45,
    "total_disk_usage_pct": 65
  },
  "cleanup": {
    "last_run": "2025-11-20T02:00:00Z",
    "files_deleted": 847,
    "space_freed_mb": 120,
    "database_records_deleted": 340,
    "errors": 0
  }
}
```

### Alerts

- **Storage > 900MB:** Warning (approaching 1GB limit)
- **Cleanup failed:** Error alert
- **Cleanup hasn't run in 48h:** Warning
- **Disk usage > 95%:** Critical

---

## Risks & Mitigation

### Risk 1: Accidental Deletion
**Problem:** Delete files/data still in use
**Mitigation:**
- Dry-run mode for testing
- Minimum age threshold (1 hour)
- Backup before delete
- Comprehensive logging

### Risk 2: FK Constraint Violations
**Problem:** Delete parent records with children
**Mitigation:**
- Use CASCADE deletes in schema
- Test FK behavior before production
- Archive entire record graph

### Risk 3: Cleanup During Analysis
**Problem:** Delete temp files while analysis running
**Mitigation:**
- File locking (if possible)
- Run cleanup at 2am (off-peak)
- Check file age (> 1 hour)

### Risk 4: Over-Aggressive Cleanup
**Problem:** Delete data user wants to keep
**Mitigation:**
- Configurable retention periods
- Archive before delete (optional)
- Never delete confluence_scores or themes

---

## Cost Analysis

### Storage Costs (Railway)

**Without Cleanup:**
- Temp files: ~1.5GB/month
- Database: ~50MB/month
- Total: ~1.55GB
- Cost: 1.55 × $0.25 = **$0.39/month**

**With Cleanup:**
- Temp files: ~100MB (rolling 24h)
- Database: ~30MB (archived)
- Total: ~130MB
- Cost: 0.13 × $0.25 = **$0.03/month**

**Savings: $0.36/month** (minimal but prevents unbounded growth)

### Development Cost
- **Implementation:** 2-3 days
- **ROI:** Prevents future storage issues (priceless)

---

## Success Metrics

**Must Have:**
- Temp files never exceed 200MB
- Database size stays under 100MB
- Cleanup runs successfully daily
- Zero accidental deletions

**Nice to Have:**
- Temp files < 100MB
- Cleanup completes in < 5 minutes
- Automated alerts on failures
- Storage reports generated weekly

**Track:**
- Storage usage over time
- Cleanup success rate
- Files/records deleted per run
- Errors encountered

---

## Future Enhancements

### Phase 2 (Optional)
- **Intelligent archiving:** Compress old content to S3
- **Selective retention:** Keep high-confluence content longer
- **Auto-scaling:** Adjust retention based on disk usage
- **Cleanup API:** Manual trigger via dashboard

### Phase 3 (Optional)
- **Cloud storage:** Move archives to S3/GCS
- **Backup/restore:** Full backup before major cleanup
- **Analytics:** Track what content gets deleted vs. kept
- **User control:** Let Sebastian configure retention per source

---

## Dependencies

- ✅ Database schema (exists)
- ✅ File system structure (exists)
- New: CleanupManager module
- New: Cleanup configuration file

---

## Timeline

**Day 1:** Immediate cleanup (finally blocks)
**Day 2:** Scheduled cleanup (temp files + database)
**Day 3:** Testing, monitoring, production rollout
**Total:** 2-3 days

---

## Approval Checklist

Before implementing:
- [ ] PRD reviewed and approved
- [ ] Retention policies agreed upon
- [ ] Safety mechanisms documented
- [ ] Testing plan validated
- [ ] Monitoring strategy defined

---

**Version:** 1.0
**Last Updated:** 2025-11-20
