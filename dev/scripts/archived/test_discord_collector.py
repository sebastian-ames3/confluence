"""
Test script for Discord collector with enhanced context tracking.

Tests the enhanced Discord collector features:
- Thread tracking (both Discord threads and reply chains)
- Reaction extraction
- Edit tracking
- Mention tracking (users, roles, channels)
- Message reference tracking
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.discord_self import DiscordSelfCollector
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_message_summary(message: dict):
    """Print a summary of a collected message."""
    metadata = message.get('metadata', {})

    print(f"\n{'='*80}")
    print(f"Message ID: {metadata.get('message_id')}")
    print(f"Author: {metadata.get('author')} (ID: {metadata.get('author_id')})")
    print(f"Channel: #{metadata.get('channel_name')}")
    print(f"Timestamp: {metadata.get('timestamp')}")

    # Edit info
    if metadata.get('is_edited'):
        print(f"[EDITED] at {metadata.get('edited_at')}")

    # Thread info
    thread_info = metadata.get('thread_info', {})
    if thread_info.get('is_in_thread'):
        print(f"[THREAD] In Thread: {thread_info.get('thread_name')} (ID: {thread_info.get('thread_id')})")
    if thread_info.get('is_reply'):
        print(f"[REPLY] Reply to: {thread_info.get('reply_to_message_id')}")
        if thread_info.get('reply_to_author_name'):
            print(f"        Author: {thread_info.get('reply_to_author_name')}")

    # Content
    content = message.get('content_text', '')
    if content:
        preview = content[:100] + "..." if len(content) > 100 else content
        print(f"Content: {preview}")

    # Mentions
    mentions = metadata.get('mentions', {})
    if mentions.get('users'):
        users = [f"@{u['username']}" for u in mentions['users']]
        print(f"[USER MENTIONS] {', '.join(users)}")
    if mentions.get('roles'):
        roles = [f"@{r['name']}" for r in mentions['roles']]
        print(f"[ROLE MENTIONS] {', '.join(roles)}")
    if mentions.get('everyone'):
        print(f"[MENTION] @everyone")

    # Reactions
    reactions = metadata.get('reactions', [])
    if reactions:
        # Convert emojis to safe ASCII representation for Windows console
        reaction_strs = []
        for r in reactions:
            emoji = r['emoji']
            # Try to encode emoji safely, fallback to [EMOJI] if it fails
            try:
                emoji.encode('cp1252')
                emoji_display = emoji
            except (UnicodeEncodeError, AttributeError):
                emoji_display = f"[EMOJI:{r.get('emoji_name', 'unknown')}]"
            reaction_strs.append(f"{emoji_display} ({r['count']})")
        print(f"[REACTIONS] {', '.join(reaction_strs)}")

    # Attachments
    attachments = metadata.get('attachments', [])
    if attachments:
        print(f"[ATTACHMENTS] {len(attachments)} files")
        for att in attachments:
            print(f"        {att['type']}: {att['filename']} ({att['size_mb']}MB)")

    # Video links
    video_links = metadata.get('video_links', [])
    if video_links:
        print(f"[VIDEO LINKS] {len(video_links)} links")
        for vid in video_links:
            print(f"        {vid['platform']}: {vid['url'][:50]}...")

    # Pinned
    if metadata.get('is_pinned'):
        print(f"[PINNED]")

    print(f"{'='*80}")


def analyze_conversation_structure(messages: list):
    """Analyze and display conversation structure."""
    print(f"\n{'='*80}")
    print("CONVERSATION STRUCTURE ANALYSIS")
    print(f"{'='*80}")

    # Count threads
    thread_messages = [m for m in messages if m.get('metadata', {}).get('thread_info', {}).get('is_in_thread')]
    reply_messages = [m for m in messages if m.get('metadata', {}).get('thread_info', {}).get('is_reply')]
    edited_messages = [m for m in messages if m.get('metadata', {}).get('is_edited')]

    print(f"\nTotal Messages: {len(messages)}")
    print(f"Thread Messages: {len(thread_messages)}")
    print(f"Reply Messages: {len(reply_messages)}")
    print(f"Edited Messages: {len(edited_messages)}")

    # Reaction analysis
    all_reactions = []
    for msg in messages:
        reactions = msg.get('metadata', {}).get('reactions', [])
        all_reactions.extend(reactions)

    if all_reactions:
        print(f"\nTotal Reactions: {len(all_reactions)}")
        reaction_counts = {}
        for r in all_reactions:
            emoji = r['emoji']
            reaction_counts[emoji] = reaction_counts.get(emoji, 0) + r['count']

        print("Top Reactions:")
        for emoji, count in sorted(reaction_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            # Try to print emoji safely
            try:
                emoji.encode('cp1252')
                emoji_display = emoji
            except (UnicodeEncodeError, AttributeError):
                emoji_display = "[EMOJI]"
            print(f"  {emoji_display}: {count}")

    # Mention analysis
    mentioned_users = set()
    mentioned_roles = set()
    for msg in messages:
        mentions = msg.get('metadata', {}).get('mentions', {})
        for user in mentions.get('users', []):
            mentioned_users.add(user['username'])
        for role in mentions.get('roles', []):
            mentioned_roles.add(role['name'])

    if mentioned_users:
        print(f"\nUnique Users Mentioned: {len(mentioned_users)}")
        print(f"  {', '.join(list(mentioned_users)[:10])}")

    if mentioned_roles:
        print(f"\nRoles Mentioned: {len(mentioned_roles)}")
        print(f"  {', '.join(mentioned_roles)}")

    # Reply chain analysis
    if reply_messages:
        print(f"\n[REPLY CHAINS]")
        reply_map = {}
        for msg in reply_messages:
            thread_info = msg.get('metadata', {}).get('thread_info', {})
            parent_id = thread_info.get('reply_to_message_id')
            msg_id = msg.get('metadata', {}).get('message_id')
            if parent_id:
                if parent_id not in reply_map:
                    reply_map[parent_id] = []
                reply_map[parent_id].append(msg_id)

        print(f"  {len(reply_map)} messages have replies")
        max_replies = max((len(v) for v in reply_map.values()), default=0)
        print(f"  Longest chain: {max_replies} replies")


async def test_discord_collector():
    """Test the Discord collector."""
    load_dotenv()

    # Get Discord token from environment
    discord_token = os.getenv('DISCORD_USER_TOKEN')

    if not discord_token:
        logger.error("DISCORD_USER_TOKEN not found in environment variables")
        logger.info("Please add DISCORD_USER_TOKEN to your .env file")
        return

    # Initialize collector
    logger.info("Initializing Discord collector...")
    try:
        collector = DiscordSelfCollector(
            user_token=discord_token,
            config_path="config/discord_channels.json",
            use_local_db=False  # Don't save to DB for testing
        )
    except FileNotFoundError:
        logger.error("Discord channels config not found")
        logger.info("Please create config/discord_channels.json from the template")
        return

    # Run collection
    logger.info("Starting Discord collection test...")
    try:
        messages = await collector.collect()

        if not messages:
            logger.warning("No messages collected")
            return

        logger.info(f"\n[SUCCESS] Collected {len(messages)} messages")

        # Show detailed view of first few messages
        logger.info("\n" + "="*80)
        logger.info("DETAILED MESSAGE SAMPLES (first 5)")
        logger.info("="*80)
        for msg in messages[:5]:
            print_message_summary(msg)

        # Analyze conversation structure
        analyze_conversation_structure(messages)

        # Save sample output to file
        output_file = Path("test_output") / f"discord_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(messages[:10], f, indent=2, ensure_ascii=False)

        logger.info(f"\n[SAVED] Sample output saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error during collection: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_discord_collector())
