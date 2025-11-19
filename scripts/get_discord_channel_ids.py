"""
Discord Channel ID Discovery Script

One-time helper script to list all servers and channels accessible by your Discord account.
Use this to find the channel IDs needed for config/discord_channels.json

Usage:
    python scripts/get_discord_channel_ids.py

The script will prompt for your Discord user token, then list all servers and channels.
Copy the channel IDs you need into config/discord_channels.json
"""

import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def list_server_channels(user_token: str):
    """
    List all servers and channels accessible to the user.

    Args:
        user_token: Discord user token (not bot token)
    """
    client = discord.Client()

    @client.event
    async def on_ready():
        print(f"\n{'='*70}")
        print(f"Logged in as: {client.user.name} ({client.user.id})")
        print(f"{'='*70}\n")

        # List all servers
        print(f"Found {len(client.guilds)} server(s):\n")

        for guild in client.guilds:
            print(f"📍 Server: {guild.name}")
            print(f"   Server ID: {guild.id}")
            print(f"   Members: {guild.member_count}")
            print(f"   {'─'*66}")

            # Get text channels only
            text_channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]

            if not text_channels:
                print("   No text channels found")
                print()
                continue

            # Group by category
            categories = {}
            no_category = []

            for channel in text_channels:
                if channel.category:
                    cat_name = channel.category.name
                    if cat_name not in categories:
                        categories[cat_name] = []
                    categories[cat_name].append(channel)
                else:
                    no_category.append(channel)

            # Print channels by category
            for category_name in sorted(categories.keys()):
                print(f"\n   Category: {category_name}")
                for channel in sorted(categories[category_name], key=lambda c: c.position):
                    print(f"      📝 #{channel.name}")
                    print(f"         Channel ID: {channel.id}")

            # Print channels without category
            if no_category:
                print(f"\n   No Category:")
                for channel in sorted(no_category, key=lambda c: c.position):
                    print(f"      📝 #{channel.name}")
                    print(f"         Channel ID: {channel.id}")

            print(f"\n{'='*70}\n")

        print("\n✅ Channel listing complete!")
        print("\nNext steps:")
        print("1. Find the 'Options Insight Official' server above")
        print("2. Copy the channel IDs for:")
        print("   - stocks-chat")
        print("   - crypto-weekly")
        print("   - macro-daily")
        print("   - spx-fixed-strike-vol")
        print("   - vix-monitor")
        print("3. Update config/discord_channels.json with these IDs")
        print()

        await client.close()

    try:
        await client.start(user_token, bot=False)
    except discord.LoginFailure:
        print("\n❌ Login failed! Check your Discord user token.")
        print("\nHow to get your Discord user token:")
        print("1. Open Discord in your web browser")
        print("2. Press F12 to open Developer Tools")
        print("3. Go to the 'Network' tab")
        print("4. Press Ctrl+R to reload the page")
        print("5. Type 'api' in the filter box")
        print("6. Click on any request to 'discord.com/api'")
        print("7. Under 'Headers', find 'Authorization'")
        print("8. Copy the token value (long string)")
        print("\n⚠️  NEVER share your user token with anyone!")
        print()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("Discord Channel ID Discovery Tool")
    print("="*70 + "\n")

    # Try to get token from environment first
    user_token = os.getenv("DISCORD_USER_TOKEN")

    if not user_token:
        print("DISCORD_USER_TOKEN not found in environment.")
        print("\nPlease enter your Discord user token:")
        print("(or press Ctrl+C to cancel)\n")

        try:
            user_token = input("Discord Token: ").strip()
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return

        if not user_token:
            print("\n❌ No token provided. Exiting.")
            return

    print("\n🔐 Logging in to Discord...\n")

    await list_server_channels(user_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
