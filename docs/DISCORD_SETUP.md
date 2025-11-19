# Discord Collector Setup Guide

Complete guide to setting up automated Discord content collection from Options Insight server.

---

## Overview

The Discord collector runs **locally on your laptop** using your Discord login session (not a bot). It collects messages, images, PDFs, and video links from specified channels twice daily.

**Why local, not on Railway?**
- Uses your personal Discord account (no bot permissions needed)
- Discord's Terms of Service prohibit user-token bots on cloud servers
- Your laptop has Discord always running anyway

---

## Prerequisites

- Python 3.9+ installed
- Discord desktop app installed and logged in
- Member of "Options Insight Official" Discord server
- Access to the channels you want to monitor

---

## Setup Steps

### 1. Get Your Discord User Token

⚠️ **IMPORTANT**: Never share your user token with anyone!

**Method A: Browser Developer Tools**

1. Open Discord in your web browser (not desktop app)
2. Press `F12` to open Developer Tools
3. Go to the **Network** tab
4. Press `Ctrl+R` to reload the page
5. Type `api` in the filter box
6. Click on any request to `discord.com/api`
7. Under **Headers**, find **Authorization**
8. Copy the long string (that's your token)

**Method B: Console (Advanced)**

1. Open Discord in browser
2. Press `F12` → **Console** tab
3. Paste this code (carefully!):
   ```javascript
   (webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m).find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()
   ```
4. Copy the returned token

### 2. Add Token to Environment

Create/edit `.env` file in project root:

```bash
DISCORD_USER_TOKEN=your_token_here_no_quotes
```

### 3. Find Your Channel IDs

Run the helper script to list all channels you have access to:

```bash
python scripts/get_discord_channel_ids.py
```

This will show all servers and channels. Look for **"Options Insight Official"** and copy the channel IDs for:
- `stocks-chat`
- `crypto-weekly`
- `macro-daily`
- `spx-fixed-strike-vol`
- `vix-monitor`

### 4. Configure Channels

1. Copy the template:
   ```bash
   copy config\discord_channels.json.template config\discord_channels.json
   ```

2. Open `config/discord_channels.json` and fill in:
   - Server ID (from step 3)
   - Channel IDs for each channel

Example:
```json
{
  "server_name": "Options Insight Official",
  "server_id": "1234567890123456789",
  "channels_to_monitor": [
    {
      "name": "stocks-chat",
      "channel_id": "9876543210987654321",
      "priority": "high",
      ...
    }
  ]
}
```

### 5. Test Collection

Run a test collection to make sure everything works:

```bash
python scripts/discord_local.py --local-db
```

You should see:
- ✅ Login successful
- 📡 Collecting from each channel
- ✅ Messages saved to database

---

## Scheduling (Windows Task Scheduler)

### Create Scheduled Task

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Task** (not Basic Task)

### General Tab
- **Name**: Discord Collection - Morning
- **Description**: Collect Discord content from Options Insight
- **Security Options**: Run whether user is logged on or not
- ✅ Run with highest privileges

### Triggers Tab

Create two triggers:

**Trigger 1 - Morning**
- Begin the task: **On a schedule**
- Settings: **Daily**
- Start: **6:00 AM**
- ✅ Enabled

**Trigger 2 - Evening**
- Begin the task: **On a schedule**
- Settings: **Daily**
- Start: **6:00 PM**
- ✅ Enabled

### Actions Tab

- Action: **Start a program**
- Program/script: `C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe`
- Add arguments: `"C:\path\to\confluence\scripts\discord_local.py" --local-db`
- Start in: `C:\path\to\confluence`

### Conditions Tab

- ✅ Start only if the computer is on AC power
- ❌ Stop if the computer switches to battery power
- ✅ Wake the computer to run this task

### Settings Tab

- ✅ Allow task to be run on demand
- ✅ Run task as soon as possible after a scheduled start is missed
- ✅ If the task fails, restart every: **15 minutes** (3 attempts)
- Stop the task if it runs longer than: **30 minutes**

---

## Usage

### Manual Collection

```bash
# Collect and save to local database
python scripts/discord_local.py --local-db

# Collect and upload to Railway API
python scripts/discord_local.py --railway-api
```

### Check Logs

```bash
# View collection log
type logs\discord_collection.log

# Watch log in real-time (PowerShell)
Get-Content logs\discord_collection.log -Wait -Tail 50
```

### Verify Data

```python
# Check what was collected
from backend.models import SessionLocal, RawContent, Source

db = SessionLocal()
discord_source = db.query(Source).filter(Source.name == "discord").first()

# Count messages
count = db.query(RawContent).filter(RawContent.source_id == discord_source.id).count()
print(f"Total Discord messages: {count}")

# Show recent
recent = db.query(RawContent).filter(
    RawContent.source_id == discord_source.id
).order_by(RawContent.collected_at.desc()).limit(5).all()

for item in recent:
    print(f"{item.content_type}: {item.content_text[:50]}...")
```

---

## Troubleshooting

### "Login failed" Error

**Problem**: Invalid or expired user token

**Solution**:
1. Get a fresh token (see Step 1)
2. Update `.env` file
3. Make sure no extra spaces or quotes

### "Config file not found" Error

**Problem**: `config/discord_channels.json` doesn't exist

**Solution**:
```bash
copy config\discord_channels.json.template config\discord_channels.json
```
Then fill in your channel IDs.

### "Channel not found" Error

**Problem**: Channel ID is wrong or you don't have access

**Solution**:
1. Run `python scripts/get_discord_channel_ids.py` again
2. Verify you have access to the channel in Discord
3. Double-check the channel ID in your config

### No Messages Collected

**Possible reasons**:
1. **Lookback window**: Config defaults to 7 days. If channels are quiet, may be nothing new.
2. **Filters**: Check `min_message_length` and `ignore_patterns` in config
3. **Channel access**: Make sure you can see messages in Discord app

**Fix**: Temporarily set `lookback_days_first_run: 30` to collect more history.

### Task Scheduler Not Running

**Check**:
1. Task is **Enabled**
2. Python path is correct
3. Script path is correct
4. "Start in" directory is set
5. Computer was awake at scheduled time

**Test manually**:
```bash
# Right-click task → Run
# Check logs\discord_collection.log for errors
```

---

## What Gets Collected

### Text Messages
- All messages longer than configured minimum (default: 20 chars)
- Author name and ID
- Timestamp
- Channel name

### Images
- Downloaded to `downloads/discord/`
- Volatility charts, screenshots, etc.
- Filename format: `YYYYMMDD_HHMMSS_original_name.png`

### PDFs
- Downloaded to `downloads/discord/`
- Market reports, research documents
- Filename format: `YYYYMMDD_HHMMSS_original_name.pdf`

### Video Links
- Zoom/Webex meeting recordings (HIGH VALUE!)
- YouTube links
- Platform detected automatically
- URL stored for later transcription

### What's Filtered Out
- Bot messages
- Short messages (< 20 chars, unless they have attachments)
- Common greetings: "gm", "gn", "thanks"
- Commands starting with `!`

---

## Configuration Options

### collection_settings

```json
{
  "lookback_days_first_run": 7,        // How far back to collect on first run
  "collect_from_all_users": true,      // Collect from everyone, not just Imran
  "min_message_length": 20,            // Minimum message length
  "ignore_patterns": [...],            // Patterns to skip
  "max_messages_per_channel": 500      // Safety limit
}
```

### file_settings

```json
{
  "download_pdfs": true,               // Download PDF attachments
  "download_images": true,             // Download image attachments
  "extract_video_links": true,         // Extract video URLs
  "max_file_size_mb": 50               // Skip files larger than this
}
```

---

## Security & Privacy

### Token Security
- ✅ Token is stored locally in `.env` (gitignored)
- ✅ Never committed to GitHub
- ✅ Never shared with anyone
- ❌ Don't run this on a shared computer

### What Discord Sees
- Your account accessing Discord normally
- No difference from using Discord desktop app
- No API rate limits (uses the same as your normal usage)

### Data Storage
- All collected data saved locally OR sent to your Railway instance
- You control where data goes (`--local-db` vs `--railway-api`)
- No third parties involved

---

## Advanced Usage

### Custom Collection Schedule

Want to collect more frequently? Add more triggers in Task Scheduler:
- 6:00 AM
- 12:00 PM
- 6:00 PM
- 10:00 PM

### Selective Channel Collection

Edit `config/discord_channels.json` to only collect from certain channels:
```json
{
  "channels_to_monitor": [
    {
      "name": "stocks-chat",
      ...
    }
    // Comment out or remove other channels
  ]
}
```

### Test Without Saving

```bash
python scripts/discord_local.py --dry-run
```

---

## Next Steps

After Discord collection is working:
1. **Verify data**: Check that messages appear in database
2. **Run classifier**: `POST /analyze/classify-batch` to classify Discord content
3. **Check routing**: High-priority Imran videos should route to transcript harvester
4. **Monitor logs**: Watch for any errors over a few days

---

## Support

If you run into issues:
1. Check `logs/discord_collection.log`
2. Verify Discord token is fresh
3. Confirm channel IDs are correct
4. Make sure channels_to_monitor is valid JSON

---

**Last Updated**: 2025-11-18
