import asyncio
import csv
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError, UserPrivacyRestrictedError
from telethon.tl.types import Channel, Message, MessageActionChatAddUser, MessageService
from telethon.tl.functions.messages import GetHistoryRequest
from django.conf import settings
from .models import Account, Group, ScrapingSession, ScrapedMember


class TelegramScraper:
    """Utility class for Telegram scraping operations"""
    
    def __init__(self, account: Account):
        self.account = account
        self.client = None
    
    async def initialize_client(self):
        """Initialize Telegram client"""
        session_file = self.account.session_file_path
        self.client = TelegramClient(session_file, self.account.api_id, self.account.api_hash)
        await self.client.start(self.account.phone)
        return self.client
    
    async def get_group_info(self, entity):
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
                
        except Exception as e:
            print(f"Error getting group info: {e}")
        
        return info
    
    async def scrape_members_from_messages(self, entity, limit=1000):
        """Extract members from message history with detailed diagnostics"""
        participants = set()
        
        try:
            # Get message history
            offset_id = 0
            total_count_limit = limit
            
            history = await self.client(GetHistoryRequest(
                peer=entity,
                offset_id=offset_id,
                offset_date=None,
                add_offset=0,
                limit=min(100, total_count_limit),
                max_id=0,
                min_id=0,
                hash=0
            ))
            
            messages = history.messages
            
            for message in messages:
                if hasattr(message, 'from_id') and message.from_id:
                    participants.add(message.from_id.user_id)
                
                # Check for service messages (user joins)
                if isinstance(message, MessageService):
                    if isinstance(message.action, MessageActionChatAddUser):
                        for user_id in message.action.users:
                            participants.add(user_id)
            
            # Get full user objects
            full_participants = []
            for user_id in participants:
                try:
                    user = await self.client.get_entity(user_id)
                    full_participants.append(user)
                except Exception as e:
                    print(f"Error getting user {user_id}: {e}")
                    continue
            
            return full_participants
            
        except Exception as e:
            print(f"Error scraping from messages: {e}")
            return []
    
    async def scrape_group_members(self, group: Group, session: ScrapingSession):
        """Main scraping function"""
        if not self.client:
            await self.initialize_client()
        
        try:
            # Update session status
            session.status = 'running'
            session.save()
            
            # Get the entity (group/channel)
            entity = await self.client.get_entity(group.identifier)
            
            # Get detailed group information
            group_info = await self.get_group_info(entity)
            
            # Update group information
            group.name = group_info['title']
            group.group_type = group_info['type'].lower().replace(' ', '_')
            group.member_count = group_info['participants_count']
            group.save()
            
            all_participants = []
            
            if group_info['restricted']:
                print(f"Group {group.name} has restricted member visibility")
            
            # Try different scraping methods
            try:
                # Method 1: Try to get participants directly
                participants = await self.client.get_participants(entity, limit=None)
                all_participants.extend(participants)
            except Exception as e:
                print(f"Direct participants method failed: {e}")
                
                # Method 2: Scrape from message history
                if session.use_message_scraping:
                    print("Trying message history scraping...")
                    message_participants = await self.scrape_members_from_messages(
                        entity, session.message_limit
                    )
                    all_participants.extend(message_participants)
            
            # Remove duplicates based on user ID
            unique_participants = {}
            for user in all_participants:
                if hasattr(user, 'id'):
                    unique_participants[user.id] = user
            
            # Save scraped members to database
            members_created = 0
            for user in unique_participants.values():
                try:
                    member, created = ScrapedMember.objects.get_or_create(
                        session=session,
                        telegram_id=user.id,
                        defaults={
                            'username': getattr(user, 'username', '') or '',
                            'first_name': getattr(user, 'first_name', '') or '',
                            'last_name': getattr(user, 'last_name', '') or '',
                            'phone': getattr(user, 'phone', '') or '',
                            'access_hash': getattr(user, 'access_hash', None),
                            'is_bot': getattr(user, 'bot', False),
                            'is_verified': getattr(user, 'verified', False),
                            'is_premium': getattr(user, 'premium', False),
                        }
                    )
                    if created:
                        members_created += 1
                except Exception as e:
                    print(f"Error saving user {user.id}: {e}")
                    continue
            
            # Update session
            session.status = 'completed'
            session.total_members_found = members_created
            session.completed_at = datetime.now()
            
            # Generate CSV export
            csv_path = self.export_to_csv(session)
            session.csv_file_path = csv_path
            session.save()
            
            return True, members_created
            
        except Exception as e:
            # Update session with error
            session.status = 'failed'
            session.error_message = str(e)
            session.completed_at = datetime.now()
            session.save()
            return False, str(e)
        
        finally:
            if self.client:
                await self.client.disconnect()
    
    def export_to_csv(self, session: ScrapingSession):
        """Export scraped members to CSV"""
        # Ensure CSV exports directory exists
        csv_dir = getattr(settings, 'CSV_EXPORTS_DIR', 'csv_exports')
        os.makedirs(csv_dir, exist_ok=True)
        
        # Generate filename
        clean_group_name = session.group.name.replace(' ', '_').replace('/', '_')[:50]
        timestamp = session.started_at.strftime("%Y%m%d_%H%M%S")
        filename = f"members_{session.account.phone.replace('+', '')}_{clean_group_name}_{timestamp}.csv"
        csv_path = os.path.join(csv_dir, filename)
        
        # Write CSV
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Username', 'First Name', 'Last Name', 'Phone', 'Access Hash', 'Is Bot', 'Is Active'])
            
            for member in session.members.filter(is_active=True):
                writer.writerow([
                    member.telegram_id,
                    member.username or '',
                    member.first_name or '',
                    member.last_name or '',
                    member.phone or '',
                    member.access_hash or '',
                    member.is_bot,
                    member.is_active
                ])
        
        return csv_path


def run_scraping_session(session_id):
    """Function to run scraping session asynchronously"""
    async def _run():
        try:
            session = ScrapingSession.objects.get(id=session_id)
            scraper = TelegramScraper(session.account)
            success, result = await scraper.scrape_group_members(session.group, session)
            return success, result
        except Exception as e:
            return False, str(e)
    
    return asyncio.run(_run())