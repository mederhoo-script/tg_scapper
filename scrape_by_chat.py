import json
import os
import csv
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError, UserPrivacyRestrictedError
from telethon.tl.types import Channel, Message, MessageActionChatAddUser, MessageService
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta
import time

CONFIG_FILE = "config.json"

def banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                   Telegram Member Scraper                   ║
║                  Enhanced Diagnostics Version               ║
╚══════════════════════════════════════════════════════════════╝
""")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        config = {"accounts": []}
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return config
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def add_account(config):
    print("\n" + "="*50)
    print("ADD NEW ACCOUNT")
    print("="*50)
    
    api_id = input("Enter API ID: ").strip()
    api_hash = input("Enter API Hash: ").strip()
    phone = input("Enter phone number (with country code): ").strip()
    
    config["accounts"].append({
        "api_id": api_id,
        "api_hash": api_hash,
        "phone": phone,
        "groups": []
    })
    save_config(config)
    print("✅ Account added successfully!")

def add_group(config):
    if not config["accounts"]:
        print("⚠️ No accounts found. Please add an account first.")
        return
    
    print("\n" + "="*50)
    print("ADD GROUP TO ACCOUNT")
    print("="*50)
    
    for i, acc in enumerate(config["accounts"], 1):
        print(f"{i}. {acc['phone']}")
    
    try:
        choice = int(input("\nSelect account to add group to: ")) - 1
        if choice < 0 or choice >= len(config["accounts"]):
            print("❌ Invalid selection!")
            return
    except ValueError:
        print("❌ Please enter a valid number!")
        return
    
    group = input("Enter group username or invite link: ").strip()
    if not group:
        print("❌ Group name/link cannot be empty!")
        return
    
    config["accounts"][choice]["groups"].append(group)
    save_config(config)
    print("✅ Group added successfully!")

def delete_account(config):
    if not config["accounts"]:
        print("⚠️ No accounts to delete.")
        return
    
    print("\n" + "="*50)
    print("DELETE ACCOUNT")
    print("="*50)
    
    for i, acc in enumerate(config["accounts"], 1):
        print(f"{i}. {acc['phone']}")
    
    try:
        choice = int(input("\nSelect account to delete: ")) - 1
        if choice < 0 or choice >= len(config["accounts"]):
            print("❌ Invalid selection!")
            return
    except ValueError:
        print("❌ Please enter a valid number!")
        return
    
    removed = config["accounts"].pop(choice)
    save_config(config)
    print(f"🗑️ Deleted account {removed['phone']}")

async def scrape_members_from_messages(client, entity, limit=1000):
    """Extract members from message history with detailed diagnostics"""
    print("📨 Scanning message history for members...")
    
    members_from_messages = set()
    all_messages = []
    offset_id = 0
    message_count = 0
    user_messages_found = 0
    service_messages_found = 0
    
    try:
        # Try different time periods to find messages
        time_periods = [
            datetime.now() - timedelta(days=7),    # 1 week ago
            datetime.now() - timedelta(days=30),   # 1 month ago
            datetime.now() - timedelta(days=90),   # 3 months ago
            datetime.now() - timedelta(days=180),  # 6 months ago
            None  # No date limit
        ]
        
        for time_period in time_periods:
            print(f"🔍 Searching messages from {time_period if time_period else 'all time'}...")
            
            # Fetch messages in batches
            for i in range(0, limit, 100):
                batch_size = min(100, limit - i)
                if batch_size <= 0:
                    break
                    
                print(f"📖 Fetching messages {i+1} to {i+batch_size}...")
                
                try:
                    history = await client(GetHistoryRequest(
                        peer=entity,
                        limit=batch_size,
                        offset_date=time_period,
                        offset_id=offset_id,
                        min_id=0,
                        max_id=0,
                        add_offset=0,
                        hash=0
                    ))
                    
                    if not history or not hasattr(history, 'messages') or not history.messages:
                        print("ℹ️ No more messages found in this time period.")
                        break
                        
                    messages = history.messages
                    all_messages.extend(messages)
                    message_count += len(messages)
                    
                    # Update offset for next batch
                    offset_id = messages[-1].id
                    
                    # Process each message to extract user information
                    for message in messages:
                        # Check if it's a service message (user joined, etc.)
                        if isinstance(message, MessageService):
                            service_messages_found += 1
                            if (hasattr(message, 'action') and 
                                isinstance(message.action, MessageActionChatAddUser)):
                                for user_id in message.action.users:
                                    members_from_messages.add(user_id)
                                    user_messages_found += 1
                        
                        # Check if it's a regular message with a user
                        elif hasattr(message, 'from_id') and message.from_id:
                            if hasattr(message.from_id, 'user_id'):
                                user_id = message.from_id.user_id
                                if user_id:
                                    members_from_messages.add(user_id)
                                    user_messages_found += 1
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"⚠️ Error fetching message batch: {e}")
                    break
            
            # If we found some messages, we can stop trying different time periods
            if message_count > 0:
                break
        
        print(f"ℹ️ Total messages scanned: {message_count}")
        print(f"ℹ️ Service messages found: {service_messages_found}")
        print(f"ℹ️ User messages found: {user_messages_found}")
        print(f"✅ Found {len(members_from_messages)} unique users in message history")
        
        # Now get full user objects for each unique ID
        users = []
        for user_id in list(members_from_messages):
            try:
                user = await client.get_entity(user_id)
                users.append(user)
            except Exception as e:
                print(f"⚠️ Could not fetch user {user_id}: {e}")
        
        return users
        
    except Exception as e:
        print(f"❌ Error scanning messages: {e}")
        return []

async def get_group_info(client, entity):
    """Get detailed information about the group/channel"""
    info = {
        "type": "Unknown",
        "participants_count": 0,
        "is_channel": False,
        "is_group": False,
        "is_supergroup": False,
        "is_broadcast": False,
        "restricted": False,
        "title": "Unknown"
    }
    
    try:
        if hasattr(entity, 'title'):
            info['title'] = entity.title
        
        if hasattr(entity, 'participants_count'):
            info['participants_count'] = entity.participants_count or 0
        
        if hasattr(entity, 'broadcast'):
            info['is_broadcast'] = entity.broadcast
            info['type'] = "Broadcast Channel" if entity.broadcast else "Group"
        
        if hasattr(entity, 'megagroup'):
            info['is_supergroup'] = entity.megagroup
            info['type'] = "Supergroup" if entity.megagroup else "Group"
        
        if hasattr(entity, 'restricted'):
            info['restricted'] = entity.restricted
            
        # Try to get more info by checking the entity type
        if isinstance(entity, Channel):
            info['is_channel'] = True
            if not info['type'] == "Unknown":
                info['type'] = "Channel"
        
    except Exception as e:
        print(f"⚠️ Could not get detailed group info: {e}")
    
    return info

async def scrape_members_async(acc, group_identifier, use_message_scraping=True, message_limit=500):
    client = TelegramClient(f"session_{acc['phone']}", acc["api_id"], acc["api_hash"])
    await client.start(acc['phone'])
    
    print(f"🔍 Scraping members from {group_identifier}...")
    print("This may take several minutes...")
    
    all_participants = []
    total_count = 0
    group_info = {}
    
    try:
        # Try to get the entity (group/channel)
        entity = await client.get_entity(group_identifier)
        
        # Get detailed group information
        group_info = await get_group_info(client, entity)
        print(f"Group/Channel: {group_info['title']}")
        print(f"Type: {group_info['type']}")
        
        if group_info['participants_count'] > 0:
            total_count = group_info['participants_count']
            print(f"Total members according to Telegram: {total_count}")
        else:
            print("Total members: Unknown or not available")
            
        if group_info['restricted']:
            print("⚠️ This group has restrictions that may limit access")
        
        # First, try to get regular participants (only works for groups, not broadcast channels)
        if not group_info['is_broadcast']:
            try:
                participants = await client.get_participants(entity)
                all_participants.extend(participants)
                print(f"📊 Found {len(participants)} participants through regular method")
            except Exception as e:
                print(f"⚠️ Could not get participants directly: {e}")
                if "CHAT_ADMIN_REQUIRED" in str(e):
                    print("❌ You need to be an admin to access the member list")
        else:
            print("ℹ️ This is a broadcast channel - member list not accessible")
        
        # Then, use message-based scraping if requested
        if use_message_scraping:
            message_members = await scrape_members_from_messages(client, entity, message_limit)
            
            # Add message-based members that aren't already in our list
            existing_ids = {user.id for user in all_participants}
            for user in message_members:
                if user.id not in existing_ids:
                    all_participants.append(user)
                    existing_ids.add(user.id)
            
            print(f"📊 Total unique members found: {len(all_participants)}")
    
    except FloodWaitError as e:
        print(f"⏳ Flood wait error: Need to wait {e.seconds} seconds")
        print("Waiting and then continuing...")
        await asyncio.sleep(e.seconds)
        # Try again after waiting
        return await scrape_members_async(acc, group_identifier, use_message_scraping, message_limit)
    except ChannelPrivateError:
        print("❌ The channel/group is private and you need to be a member to access it.")
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    finally:
        await client.disconnect()
    
    return all_participants, total_count, group_info

def continue_with_accounts(config):
    if not config["accounts"]:
        print("⚠️ No accounts found.")
        return
    
    print("\n" + "="*50)
    print("SELECT ACCOUNT TO SCRAPE")
    print("="*50)
    
    for i, acc in enumerate(config["accounts"], 1):
        print(f"{i}. {acc['phone']}")
    
    try:
        acc_choice = int(input("\nSelect account to use: ")) - 1
        if acc_choice < 0 or acc_choice >= len(config["accounts"]):
            print("❌ Invalid selection!")
            return
    except ValueError:
        print("❌ Please enter a valid number!")
        return
    
    acc = config["accounts"][acc_choice]

    if not acc["groups"]:
        print("⚠️ No groups saved for this account.")
        return
    
    print("\nSelect a group to scrape:")
    for i, grp in enumerate(acc["groups"], 1):
        print(f"{i}. {grp}")
    
    try:
        grp_choice = int(input("\nSelect group to scrape: ")) - 1
        if grp_choice < 0 or grp_choice >= len(acc["groups"]):
            print("❌ Invalid selection!")
            return
    except ValueError:
        print("❌ Please enter a valid number!")
        return
    
    group = acc["groups"][grp_choice]
    
    # Ask about message scraping parameters
    print("\n" + "="*50)
    print("MESSAGE-BASED SCRAPING OPTIONS")
    print("="*50)
    use_message_scraping = input("Use message-based scraping? (y/n): ").strip().lower() == 'y'
    
    message_limit = 500
    if use_message_scraping:
        try:
            message_limit = int(input("How many messages to scan? (default 500): ") or "500")
        except ValueError:
            print("Using default value of 500 messages")
            message_limit = 500
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    participants, total_count, group_info = loop.run_until_complete(
        scrape_members_async(acc, group, use_message_scraping, message_limit)
    )
    
    if participants:
        # Clean group name for filename
        clean_group_name = group_info['title'].replace(' ', '_').replace('/', '_').replace('\\', '_')[:50]
        if not clean_group_name or clean_group_name == "Unknown":
            clean_group_name = group.replace('https://t.me/', '').replace('@', '').replace('/', '_')[:50]
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"members_{acc['phone'].replace('+', '')}_{clean_group_name}_{timestamp}.csv"
        
        with open(filename, "w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Username", "First Name", "Last Name", "Phone", "Access Hash"])
            
            for user in participants:
                writer.writerow([
                    user.id,
                    user.username if user.username else "",
                    user.first_name if user.first_name else "",
                    user.last_name if user.last_name else "",
                    user.phone if user.phone else "",
                    user.access_hash if hasattr(user, 'access_hash') else ""
                ])
        
        print(f"\n{'='*60}")
        print("SCRAPING RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Group: {group_info['title']}")
        print(f"Type: {group_info['type']}")
        if total_count > 0:
            print(f"Telegram reports total members: {total_count}")
        print(f"Successfully scraped members: {len(participants)}")
        print(f"Data saved to: {filename}")
        
        # Provide explanations based on the results
        if len(participants) == 0:
            print("\n❌ No members found. Possible reasons:")
            print("   - The group might be very inactive")
            print("   - Privacy settings prevent accessing members")
            print("   - You might not have sufficient permissions")
            print("   - It might be a broadcast channel with no visible members")
        elif total_count > 0 and len(participants) < total_count:
            print("\n⚠️  NOTE: Limited members found. Possible reasons:")
            print("   - Telegram limits member visibility for regular users")
            print("   - The group might have privacy restrictions")
            print("   - You might not be an administrator")
            if group_info['is_broadcast']:
                print("   - This is a broadcast channel - members are not visible")
        
    else:
        print("❌ No members were scraped.")

def display_stats(config):
    total_accounts = len(config["accounts"])
    total_groups = sum(len(acc["groups"]) for acc in config["accounts"])
    
    print("\n" + "="*50)
    print("CURRENT STATISTICS")
    print("="*50)
    print(f"Total accounts: {total_accounts}")
    print(f"Total groups: {total_groups}")
    
    if total_accounts > 0:
        print("\nAccount details:")
        for i, acc in enumerate(config["accounts"], 1):
            print(f"{i}. {acc['phone']} - {len(acc['groups'])} groups")

def main():
    config = load_config()
    
    while True:
        banner()
        display_stats(config)
        
        print("\n" + "="*50)
        print("MAIN MENU")
        print("="*50)
        print("1. Add new account")
        print("2. Add group to existing account")
        print("3. Delete account")
        print("4. Scrape members from a group")
        print("5. View limitations info")
        print("6. Exit")
        print("="*50)
        
        choice = input("\nChoose an option (1-6): ").strip()
        
        if choice == "1":
            add_account(config)
        elif choice == "2":
            add_group(config)
        elif choice == "3":
            delete_account(config)
        elif choice == "4":
            continue_with_accounts(config)
        elif choice == "5":
            print("\n" + "="*60)
            print("SCRAPING LIMITATIONS INFORMATION")
            print("="*60)
            print("1. Telegram restricts member visibility in large groups")
            print("2. Regular users can typically only see:")
            print("   - Group administrators")
            print("   - Recently active members")
            print("   - Members they've interacted with")
            print("3. Broadcast channels don't have visible member lists")
            print("4. To access full member lists, you need:")
            print("   - Administrator privileges in the group")
            print("   - Or use Telegram's built-in export feature (admins only)")
            print("5. Message-based scraping works best in active groups")
        elif choice == "6":
            print("\n👋 Exiting. Thank you for using Telegram Scraper Tool!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()