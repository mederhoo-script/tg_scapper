import json
import csv
import random
import time
import os
from telethon.sync import TelegramClient
from telethon.errors import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest

CONFIG_FILE = "config_adder.json"
INVITE_MESSAGE = """Hi {name},

We’ve created a new Telegram group where we continue discussions:
👉 {group_link}

You’re welcome to join us!
"""
INVITES_LOG_FILE = "invites_log.csv"
DM_LOG_FILE = "dm_log.csv"

# ---------------------- Config functions ----------------------
def load_or_create_config():
    if not os.path.exists(CONFIG_FILE):
        config = {
            "accounts": [],
            "target_groups": [],
            "messages": [INVITE_MESSAGE],
            "settings": {
                "default_interval": 30,
                "max_invites": 50,
                "max_messages": 100
            }
        }
        save_config(config)
        print(f"✅ Created new config file: {CONFIG_FILE}")
        return config
    else:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# ---------------------- Banner and menu ----------------------
def banner():
    print("\n" + "="*50)
    print("   🚀 Telegram Adder by Mederhoo 🚀   ")
    print("="*50 + "\n")

def main_menu():
    banner()
    print("1. ➕ Send invites/DM using CSV")
    print("2. ⚙️ Manage Config (Accounts, Groups, Messages)")
    print("3. 🚪 Exit")
    return input("\n👉 Choose an option: ")

# ---------------------- Config management ----------------------
def manage_config():
    global config
    while True:
        print("\n--- Config Management ---")
        print("1. Add Account")
        print("2. Add Target Group")
        print("3. Add Message")
        print("4. Back to Main Menu")
        choice = input("Choose an option: ")

        if choice == "1":
            phone = input("Enter phone number: ")
            api_id = int(input("Enter api_id: "))
            api_hash = input("Enter api_hash: ")
            config["accounts"].append({"phone": phone, "api_id": api_id, "api_hash": api_hash})
            save_config(config)
            print("✅ Account added!")

        elif choice == "2":
            name = input("Enter group name: ")
            link = input("Enter group link (username or invite link): ")
            config["target_groups"].append({"name": name, "link": link})
            save_config(config)
            print("✅ Target group added!")

        elif choice == "3":
            msg = input("Enter message (use {name} and {group_link} placeholders):\n")
            config["messages"].append(msg)
            save_config(config)
            print("✅ Message added!")

        elif choice == "4":
            break
        else:
            print("⚠️ Invalid choice, try again.")

# ---------------------- Helper functions ----------------------
def choose_account(accounts):
    print("\nAvailable Accounts:")
    for i, acc in enumerate(accounts, 1):
        print(f"{i}. {acc['phone']}")
    idx = int(input("Choose account number: ")) - 1
    return accounts[idx]

def choose_group(groups):
    print("\nAvailable Target Groups:")
    for i, grp in enumerate(groups, 1):
        print(f"{i}. {grp['name']} ({grp['link']})")
    idx = int(input("Choose group number: ")) - 1
    return groups[idx]

def choose_message(messages, group_link):
    print("\nAvailable Messages:")
    for i, msg in enumerate(messages, 1):
        preview = msg.replace("\n", " ")[:50]
        print(f"{i}. {preview}...")
    print(f"{len(messages)+1}. Add new message")
    idx = int(input("Choose message number: ")) - 1
    if idx == len(messages):
        new_msg = input("Enter new message (use {name} and {group_link} placeholders):\n")
        messages.append(new_msg)
        save_config(config)
        return new_msg.replace("{group_link}", group_link)
    return messages[idx].replace("{group_link}", group_link)

def choose_csv():
    files = [f for f in os.listdir(".") if f.endswith(".csv")]
    if not files:
        print("⚠️ No CSV files found in this folder.")
        exit()
    print("\nAvailable CSV files:")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    idx = int(input("Choose CSV file number: ")) - 1
    return files[idx]

def invite_or_message():
    print("\n1. Invite to Group")
    print("2. Send Direct Message")
    choice = input("Choose action: ")
    return "invite" if choice == "1" else "dm"

def ask_interval(default_interval):
    try:
        custom = input(f"\nSet interval in seconds (press Enter for default {default_interval}): ")
        return int(custom) if custom.strip() else default_interval
    except ValueError:
        return default_interval

def ask_max_count(default_max, action_name):
    try:
        custom = input(f"Set maximum {action_name} (press Enter for default {default_max}): ")
        return int(custom) if custom.strip() else default_max
    except ValueError:
        return default_max

def load_log(file):
    if not os.path.exists(file):
        with open(file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["username"])
        return set()
    with open(file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return set(row["username"] for row in reader)

def append_log(file, username):
    with open(file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([username])

# ---------------------- Main adder function ----------------------
def run_adder():
    global config
    account = choose_account(config["accounts"])
    target_group = choose_group(config["target_groups"])
    message = choose_message(config["messages"], target_group["link"])
    action = invite_or_message()
    interval = ask_interval(config["settings"].get("default_interval", 30))
    max_invites = ask_max_count(config["settings"].get("max_invites", 50), "invites")
    max_messages = ask_max_count(config["settings"].get("max_messages", 100), "DMs")
    csv_file = choose_csv()

    client = TelegramClient(account["phone"], account["api_id"], account["api_hash"])
    client.start()

    # Load scraped users
    users = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        users = list(reader)

    invited_users = load_log(INVITES_LOG_FILE)
    messaged_users = load_log(DM_LOG_FILE)

    count_invites = 0
    count_messages = 0

    for user in users:
        username = user.get("Username") or user.get("username")
        if not username:
            continue
        if username in invited_users or username in messaged_users:
            continue  # skip already processed users

        try:
            if action == "invite":
                try:
                    client(InviteToChannelRequest(target_group["link"], [username]))
                    print(f"✅ Invited {username} to {target_group['name']}")
                    invited_users.add(username)
                    append_log(INVITES_LOG_FILE, username)
                    count_invites += 1
                    if count_invites >= max_invites:
                        break
                except Exception as e:
                    print(f"⚠️ Invite failed for {username}: {e}")
                    if username not in messaged_users:
                        client.send_message(username, message.format(name=username))
                        print(f"📩 Sent fallback DM to {username}")
                        messaged_users.add(username)
                        append_log(DM_LOG_FILE, username)
                        count_messages += 1
                        if count_messages >= max_messages:
                            break
            else:  # DM only
                client.send_message(username, message.format(name=username))
                print(f"📩 Messaged {username}")
                messaged_users.add(username)
                append_log(DM_LOG_FILE, username)
                count_messages += 1
                if count_messages >= max_messages:
                    break

            time.sleep(random.randint(interval, interval + 10))

        except PeerFloodError:
            print("❌ Too many requests, Telegram blocked this action temporarily.")
            break
        except UserPrivacyRestrictedError:
            print(f"⚠️ {username} does not accept messages or invites.")
            continue
        except Exception as e:
            print(f"⚠️ Error with {username}: {e}")
            continue

    client.disconnect()
    print(f"🎉 Task completed. Invites: {count_invites}, DMs: {count_messages}\n")

# ---------------------- Entry point ----------------------
if __name__ == "__main__":
    config = load_or_create_config()  # Load once globally
    while True:
        choice = main_menu()
        if choice == "1":
            run_adder()
        elif choice == "2":
            manage_config()
        elif choice == "3":
            print("👋 Goodbye from Mederhoo’s Adder!\n")
            break
        else:
            print("⚠️ Invalid choice, try again.\n")
