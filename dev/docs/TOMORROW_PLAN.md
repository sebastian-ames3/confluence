# Tomorrow's Work Plan - 2025-11-20

**Starting Point**: 3 collectors production-ready, 3 need completion

---

## Priority Order

### 1. Twitter Collector - Twitter API Implementation (HIGH)
**Status**: Framework complete, switching from ntscraper to official API
**Time Estimate**: 30-60 minutes
**Priority**: HIGH (daily actionable trade setups from @KTTECHPRIVATE)

**Steps**:
1. User signs up for Twitter API Free Tier:
   - Go to https://developer.twitter.com/en/portal/dashboard
   - Create app, get Bearer Token
   - Add to `.env`: `TWITTER_BEARER_TOKEN=xxx`
2. Update `collectors/twitter_scraper.py`:
   - Install tweepy: `pip install tweepy`
   - Replace ntscraper logic with Twitter API v3 calls
   - Use `client.get_users_tweets()` method
3. Test with both accounts (@KTTECHPRIVATE, @MelMattison1)
4. Verify data saves to database

**Expected Outcome**: Collect ~50-100 recent tweets from both accounts

---

### 2. 42 Macro Collector - Selenium Implementation (HIGH)
**Status**: Framework complete, needs Selenium for CloudFront bypass
**Time Estimate**: 1-2 hours
**Priority**: HIGH (daily Leadoff Morning Note, KISS Model)

**Steps**:
1. Install Selenium dependencies:
   ```bash
   pip install selenium webdriver-manager
   ```
2. Update `collectors/macro42.py`:
   - Add Selenium headless Chrome setup
   - Implement login automation (email, password, submit)
   - Navigate to /research page
   - Parse PDF links with BeautifulSoup
   - Download PDFs to downloads/42macro/
   - Extract video URLs
3. Add session persistence (save cookies between runs)
4. Test full collection cycle

**Expected Outcome**: Collect 3-5 recent PDFs and video URLs

---

### 3. KT Technical Website Collector - Build New Collector (HIGH)
**Status**: Not started, simple blog scraping
**Time Estimate**: 30-60 minutes
**Priority**: HIGH (weekly technical analysis, price charts)

**Steps**:
1. Create `collectors/kt_technical_website.py`:
   - BaseCollector pattern
   - Session-based login (email/password from .env)
   - Navigate to /blog-feed/
   - Parse weekly blog post
   - Extract price chart images
   - Extract synopsis text
2. Create test script: `scripts/test_kt_technical_collector.py`
3. Test authentication and collection

**Expected Outcome**: Collect latest weekly blog post with chart images

---

## After All Collectors Working

### 4. Database Initialization
**Steps**:
1. Run database migrations:
   ```bash
   python scripts/run_migrations.py
   ```
2. Test orchestration script with database saves:
   ```bash
   python scripts/run_collectors.py --sources youtube substack twitter
   ```
3. Verify data in database:
   ```python
   from backend.models import SessionLocal, RawContent
   db = SessionLocal()
   count = db.query(RawContent).count()
   print(f"Total content items: {count}")
   ```

---

### 5. Full Integration Test
**Steps**:
1. Run all collectors via orchestration:
   ```bash
   python scripts/run_collectors.py
   ```
2. Verify all sources collected
3. Check database has entries for each source
4. Confirm no errors in logs

---

### 6. Create Final PR
**Content**:
- All 6 collectors working
- Test results documented
- Database integration verified
- Ready for PRD-005 (Transcript Harvester)

---

## Environment Variables Needed

Ensure `.env` has:
```bash
# Already added:
DISCORD_USER_TOKEN=xxx
YOUTUBE_API_KEY=xxx
MACRO42_EMAIL=xxx
MACRO42_PASSWORD=xxx
KT_EMAIL=xxx
KT_PASSWORD=xxx
CLAUDE_API_KEY=xxx
WHISPER_API_KEY=xxx

# To add tomorrow:
TWITTER_BEARER_TOKEN=xxx  # From Twitter Developer Portal
```

---

## Current Status Summary

| Collector | Status | Next Action |
|-----------|--------|-------------|
| Discord | ✅ Working | None - production ready |
| YouTube | ✅ Working | None - production ready |
| Substack | ✅ Working | None - production ready |
| Twitter | 🔄 In Progress | Implement Twitter API |
| 42 Macro | 🔄 In Progress | Implement Selenium |
| KT Technical | ❌ Not Started | Build collector |

---

## Success Metrics for Tomorrow

- [ ] Twitter API collector working (50+ tweets collected)
- [ ] 42 Macro Selenium collector working (3+ PDFs collected)
- [ ] KT Technical website collector working (1 blog post collected)
- [ ] Database initialized and tested
- [ ] All 6 collectors integrated in orchestration script
- [ ] Full collection test successful (100+ items across all sources)
- [ ] PRD-004 marked as COMPLETE

---

## Then Move to PRD-005

Once all collectors working:
- **PRD-005: Transcript Harvester Agent**
- Extract alpha from video transcripts (Discord Imran videos, 42 Macro videos)
- Use Whisper API for transcription
- Claude analysis of transcripts
- This is where the real alpha extraction begins!

---

**End Goal**: Complete data collection infrastructure before focusing on AI analysis

**Last Updated**: 2025-11-19 23:30
