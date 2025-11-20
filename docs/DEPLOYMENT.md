# Macro Confluence Hub - Deployment Guide

Complete guide for deploying the Macro Confluence Hub to Railway with automated scheduling.

---

## Overview

**Deployment Architecture:**
- **Railway**: Main backend + frontend (FastAPI + static files)
- **Railway Scheduler**: Automated collection at 6am & 6pm
- **Local (Laptop)**: Discord collector (runs via Windows Task Scheduler)
- **Database**: SQLite with persistent Railway volume

**Why This Setup?**
- Railway provides easy Python deployment with persistent storage
- Discord requires local execution (personal user token, no bot access)
- Scheduler ensures automated data collection twice daily
- All other collectors run server-side

---

## Prerequisites

- Railway account (Sebastian already has subscription)
- GitHub repository (code already pushed)
- All API keys and credentials ready
- Python 3.9+ on local laptop for Discord collection

---

## Part 1: Railway Deployment

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select `sebastian-ames3/confluence` repository
5. Railway will auto-detect Python and deploy

### Step 2: Configure Environment Variables

In Railway dashboard ’ Variables tab, add:

```bash
# AI APIs
CLAUDE_API_KEY=sk-ant-...
WHISPER_API_KEY=sk-...  # OpenAI key
YOUTUBE_API_KEY=AIza...

# Database
DATABASE_URL=sqlite:///data/confluence.db

# Security
SECRET_KEY=generate-random-32-char-string

# Source Credentials
MACRO42_EMAIL=your@email.com
MACRO42_PASSWORD=your_password
TWITTER_BEARER_TOKEN=Bearer_token_here
KT_EMAIL=your@email.com
KT_PASSWORD=your_password

# Environment
RAILWAY_ENV=production
```

**  Important:**
- Never commit these to git!
- Use Railway's environment variable encryption
- Rotate keys quarterly

### Step 3: Add Persistent Volume

1. Railway dashboard ’ Settings ’ Volumes
2. Click "Add Volume"
3. Mount path: `/data`
4. Size: 1GB (sufficient for SQLite database)

This ensures database persists across deployments.

### Step 4: Deploy

Railway auto-deploys on every push to `main` branch.

**Manual deploy:**
1. Railway dashboard ’ Deployments
2. Click "Deploy Now"
3. Wait for build (2-3 minutes)
4. Check logs for errors

**Health Check:**
```bash
curl https://your-app.up.railway.app/health
# Should return: {"status": "healthy", "database": "connected"}
```

### Step 5: Get Railway URL

1. Railway dashboard ’ Settings ’ Domains
2. Your app URL: `https://confluence-production.up.railway.app`
3. Copy this URL for Discord local script

---

## Part 2: Scheduler Setup

### Option A: Separate Railway Service (Recommended)

1. Railway dashboard ’ New Service ’ Empty Service
2. Name: "Confluence Scheduler"
3. Add same environment variables as main service
4. Deploy Command: `python backend/scheduler.py`
5. This runs the scheduler 24/7

### Option B: Railway Cron (Alternative)

1. Create `railway.json` in project root (already done)
2. Add cron configuration:
```json
{
  "cron": [
    {
      "name": "morning-collection",
      "schedule": "0 6 * * *",
      "command": "python backend/scheduler.py manual"
    },
    {
      "name": "evening-collection",
      "schedule": "0 18 * * *",
      "command": "python backend/scheduler.py manual"
    }
  ]
}
```

**Note:** Option A is more reliable as Railway cron is in beta.

### Scheduler Logs

View scheduler logs in Railway:
```
Railway dashboard ’ Service ’ Logs ’ Filter "scheduler"
```

Logs saved to `scheduler.log` in Railway volume.

---

## Part 3: Discord Local Setup (Sebastian's Laptop)

Discord collection runs locally because:
- Requires personal user session (no bot access)
- Discord.py-self needs logged-in account
- Sebastian's Discord always running on laptop

### Step 1: Install Dependencies

On your laptop:
```bash
pip install discord.py-self requests python-dotenv
```

### Step 2: Configure Environment

Create `.env` file on laptop (or add to existing):
```bash
DISCORD_USER_TOKEN=your_discord_token_here
RAILWAY_API_URL=https://confluence-production.up.railway.app
```

**Get Discord Token:**
1. Open Discord in browser
2. Press F12 ’ Network tab
3. Reload page
4. Find any request to `discord.com/api`
5. Look for `Authorization` header
6. Copy the token value

### Step 3: Test Script

```bash
cd path/to/confluence
python scripts/discord_local.py --railway-api
```

Should see:
```
Discord Collection - 2025-11-19 18:00:00
=====================================
[OK] Collection complete: X items
[OK] Upload successful: 200
```

### Step 4: Windows Task Scheduler

1. Open Task Scheduler (search in Windows)
2. Create Task ’ General tab:
   - Name: "Confluence Discord 6AM"
   - Description: "Morning Discord collection"
   - Run whether user logged in or not: NO (Discord needs to be running)
   - Run with highest privileges: NO

3. Triggers tab ’ New:
   - Begin the task: On a schedule
   - Daily, recur every 1 days
   - Start: 6:00:00 AM
   - Advanced: Enable "Repeat task every" ’ unchecked
   - Enabled: YES

4. Actions tab ’ New:
   - Action: Start a program
   - Program/script: `C:\Path\To\Python\python.exe`
   - Add arguments: `C:\Path\To\confluence\scripts\discord_local.py --railway-api`
   - Start in: `C:\Path\To\confluence`

5. Conditions tab:
   - Start only if computer is on AC power: NO
   - Wake computer to run: NO
   - Start task only if computer is idle: NO

6. Settings tab:
   - Allow task to be run on demand: YES
   - If task fails, restart every: 15 minutes
   - Attempt to restart up to: 3 times
   - If running task does not end when requested: Do not start new instance

7. Repeat for 6PM:
   - Duplicate task, rename to "Confluence Discord 6PM"
   - Change trigger time to 6:00:00 PM

### Step 5: Test Scheduled Tasks

Right-click task ’ Run

Check logs:
```bash
cat C:\Path\To\confluence\scripts\discord_local.log
```

---

## Part 4: Verification

### Day 1: Initial Deployment

1. Check Railway deployment successful
2. Visit `https://your-app.up.railway.app`
3. Frontend should load (all 5 pages)
4. API docs: `https://your-app.up.railway.app/docs`

### Day 2-4: Monitor Collections

Check that collections run at 6am & 6pm:

**Railway Logs:**
```
6am: [OK] YouTube collection complete
6am: [OK] Substack collection complete
6am: [OK] Twitter collection complete
6am: [OK] 42 Macro collection complete
6am: [OK] KT Technical collection complete
```

**Discord Local Logs:**
```
6am: [OK] Discord collection complete: X items
6am: [OK] Upload successful: 200
```

### Database Check

```bash
# Connect to Railway database
railway run python
>>> from backend.models import *
>>> from sqlalchemy import create_engine
>>> engine = create_engine(DATABASE_URL)
>>> SessionLocal = sessionmaker(bind=engine)
>>> db = SessionLocal()
>>> db.query(RawContent).count()
# Should see growing number of content items
```

### Dashboard Check

Visit dashboard pages:
1. https://your-app.up.railway.app/index.html - Today's View
2. https://your-app.up.railway.app/themes.html - Themes
3. https://your-app.up.railway.app/sources.html - Sources
4. https://your-app.up.railway.app/matrix.html - Matrix
5. https://your-app.up.railway.app/historical.html - Historical

**Should See:**
- Sources populated with content
- Themes identified and scored
- Confluence matrix showing pillar scores
- Historical conviction trends

---

## Troubleshooting

### Railway Deployment Fails

**Check build logs:**
```
Railway ’ Deployments ’ Latest ’ Build Logs
```

**Common Issues:**
- Missing dependencies: Check `requirements.txt`
- Environment variables: Verify all keys set
- Database path: Ensure volume mounted at `/data`

**Fix:**
```bash
# Re-deploy
git push origin main
```

### Scheduler Not Running

**Check logs:**
```
Railway ’ Scheduler Service ’ Logs
```

**Common Issues:**
- Wrong timezone (Railway uses UTC)
- Service not started
- Environment variables missing

**Fix:**
```bash
# Manual trigger to test
python backend/scheduler.py manual
```

### Discord Collection Fails

**Check local logs:**
```bash
cat scripts/discord_local.log
```

**Common Issues:**
- Discord token expired (re-extract from browser)
- Discord not running on laptop
- Network connectivity to Railway

**Fix:**
```bash
# Test manually
python scripts/discord_local.py --railway-api
```

### Database Issues

**Check Railway volume:**
```
Railway ’ Service ’ Data ’ Volumes
```

**Common Issues:**
- Volume not mounted
- Path mismatch
- Permissions

**Fix:**
```bash
# SSH into Railway
railway run bash
ls -la /data/
```

---

## Monitoring

### Metrics to Track

1. **Collection Success Rate**
   - Target: >95% success
   - Check: Railway logs for errors

2. **API Costs**
   - Claude API: ~$40/month
   - OpenAI Whisper: ~$20/month
   - Target: <$75/month total

3. **Database Size**
   - Target: <1GB (90 days retention)
   - Check: Railway volume usage

4. **Uptime**
   - Target: >99% uptime
   - Check: Railway status page

### Alerts (Future)

Set up Railway notifications for:
- Deployment failures
- Service crashes
- High API costs
- Database >900MB

---

## Backup Strategy

### Database Backups

**Automated (Weekly):**
```bash
# Add to Railway scheduler
0 0 * * 0  # Sunday midnight
python scripts/backup_database.py
```

**Manual:**
```bash
railway run cat /data/confluence.db > confluence_backup_$(date +%Y%m%d).db
```

**Restore:**
```bash
railway run "cat > /data/confluence.db" < confluence_backup_20251119.db
```

### Code Backups

- GitHub repository (already backed up)
- Local clones on Sebastian's machines
- Railway auto-backups deployments

---

## Rollback Plan

If deployment breaks:

1. **Revert Code:**
```bash
git revert HEAD
git push origin main
# Railway auto-deploys previous version
```

2. **Restore Database:**
```bash
railway run "cat > /data/confluence.db" < latest_backup.db
```

3. **Check Services:**
- Main API: https://your-app.up.railway.app/health
- Scheduler: Check logs for "Scheduler Started"
- Discord: Run local script manually

---

## Cost Monitoring

### Railway Costs
- Subscription: $X/month (Sebastian already pays)
- Stays within plan limits

### API Costs
- Track in Railway ’ Billing
- Set budget alerts at $100/month
- Review monthly usage

**Estimated Monthly Costs:**
- Claude API: $40
- Whisper API: $20
- Railway: Included in subscription
- **Total: ~$60/month**

---

## Security Checklist

- [ ] All API keys in Railway environment variables
- [ ] No credentials committed to git
- [ ] Railway volumes encrypted
- [ ] Discord token rotated quarterly
- [ ] Database backups encrypted
- [ ] HTTPS enabled (Railway default)
- [ ] CORS configured for production domain only

---

## Post-Deployment

### Week 1

- Monitor collection success rate daily
- Check database growing correctly
- Verify all sources collecting
- Test Discord local script both runs (6am, 6pm)

### Month 1

- Review API costs
- Database size check
- Collection reliability stats
- User feedback (Sebastian's usage)

### Quarterly

- Rotate API keys
- Update dependencies
- Database backup verification
- Cost optimization review

---

## Success Criteria

 Railway deployment successful
 6am collection runs automatically (3 consecutive days)
 6pm collection runs automatically (3 consecutive days)
 Discord script runs on laptop (both times)
 All 5 sources collecting data
 Dashboard shows real data
 No errors in logs for 72 hours

**When all checked:** **<‰ Production Ready!**

---

## Support

**Issues:** https://github.com/sebastian-ames3/confluence/issues
**Railway Docs:** https://docs.railway.app
**Discord.py-self:** https://github.com/dolfies/discord.py-self

---

**Last Updated:** 2025-11-19
**Version:** 1.0 (PRD-011 Complete)
