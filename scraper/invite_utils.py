import asyncio
import csv
import io
import time
import random
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import PeerFloodError, UserPrivacyRestrictedError, FloodWaitError
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import SendMessageRequest
from django.conf import settings
from .models import Account, Group, ScrapedMember, InviteLog, DMLog, MessageTemplate


class TelegramInviter:
    """Utility class for Telegram invite and DM operations"""
    
    def __init__(self, account: Account):
        self.account = account
        self.client = None
    
    async def initialize_client(self):
        """Initialize Telegram client"""
        session_file = self.account.session_file_path
        self.client = TelegramClient(session_file, self.account.api_id, self.account.api_hash)
        await self.client.start(self.account.phone)
        return self.client
    
    def format_message(self, template: MessageTemplate, member: dict, group_link: str = ""):
        """Format message template with member data"""
        content = template.content
        
        # Get member name (prefer first name, fallback to username)
        name = member.get('first_name', '').strip()
        if not name:
            username = member.get('username', '').strip()
            name = username if username else f"User {member.get('id', '')}"
        
        # Replace placeholders
        replacements = {
            '{name}': name,
            '{first_name}': member.get('first_name', ''),
            '{last_name}': member.get('last_name', ''),
            '{username}': member.get('username', ''),
            '{group_link}': group_link,
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
        
        return content
    
    async def invite_user_to_group(self, user_id: int, target_group: Group, member_data: dict):
        """Invite a user to a group"""
        try:
            # Get the target group entity
            group_entity = await self.client.get_entity(target_group.identifier)
            
            # Get the user entity
            user_entity = await self.client.get_entity(user_id)
            
            # Invite user to channel/group
            await self.client(InviteToChannelRequest(
                channel=group_entity,
                users=[user_entity]
            ))
            
            return True, "Success"
            
        except PeerFloodError:
            return False, "Flood error - too many requests"
        except UserPrivacyRestrictedError:
            return False, "User privacy settings don't allow invites"
        except FloodWaitError as e:
            return False, f"Flood wait - wait {e.seconds} seconds"
        except Exception as e:
            return False, str(e)
    
    async def send_direct_message(self, user_id: int, message_content: str, member_data: dict):
        """Send a direct message to a user"""
        try:
            # Get the user entity
            user_entity = await self.client.get_entity(user_id)
            
            # Send message
            await self.client.send_message(user_entity, message_content)
            
            return True, "Success"
            
        except PeerFloodError:
            return False, "Flood error - too many requests"
        except UserPrivacyRestrictedError:
            return False, "User privacy settings don't allow messages"
        except FloodWaitError as e:
            return False, f"Flood wait - wait {e.seconds} seconds"
        except Exception as e:
            return False, str(e)
    
    async def run_invite_campaign(self, csv_data, target_group: Group, message_template: MessageTemplate, 
                                  settings_dict: dict):
        """Run invite campaign"""
        if not self.client:
            await self.initialize_client()
        
        # Parse settings
        interval = int(settings_dict.get('interval', 30))
        max_invites = int(settings_dict.get('max_invites', 50))
        
        # Track progress
        invited_count = 0
        failed_count = 0
        
        try:
            # Parse CSV data
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            members = list(csv_reader)
            
            # Get already invited users
            invited_user_ids = set(
                InviteLog.objects.filter(
                    account=self.account,
                    target_group=target_group,
                    status='success'
                ).values_list('member__telegram_id', flat=True)
            )
            
            for member in members:
                if invited_count >= max_invites:
                    break
                
                user_id = int(member.get('ID', 0))
                if not user_id or user_id in invited_user_ids:
                    continue
                
                # Try to get or create ScrapedMember for logging
                scraped_member = None
                try:
                    scraped_member = ScrapedMember.objects.filter(telegram_id=user_id).first()
                except:
                    pass
                
                # Attempt invite
                success, error_msg = await self.invite_user_to_group(user_id, target_group, member)
                
                # Log the attempt
                invite_log = InviteLog.objects.create(
                    account=self.account,
                    target_group=target_group,
                    member=scraped_member,
                    status='success' if success else 'failed',
                    error_message=error_msg if not success else ''
                )
                
                if success:
                    invited_count += 1
                    invited_user_ids.add(user_id)
                else:
                    failed_count += 1
                    
                    # Handle flood wait
                    if 'wait' in error_msg.lower():
                        try:
                            wait_time = int(''.join(filter(str.isdigit, error_msg)))
                            await asyncio.sleep(min(wait_time, 300))  # Max 5 minutes
                        except:
                            await asyncio.sleep(interval)
                
                # Wait between attempts
                if invited_count < max_invites:
                    await asyncio.sleep(interval + random.randint(1, 5))
            
            return True, f"Invited {invited_count} users, {failed_count} failed"
            
        except Exception as e:
            return False, str(e)
        finally:
            if self.client:
                await self.client.disconnect()
    
    async def run_dm_campaign(self, csv_data, message_template: MessageTemplate, settings_dict: dict):
        """Run DM campaign"""
        if not self.client:
            await self.initialize_client()
        
        # Parse settings
        interval = int(settings_dict.get('interval', 30))
        max_messages = int(settings_dict.get('max_messages', 100))
        group_link = settings_dict.get('group_link', '')
        
        # Track progress
        sent_count = 0
        failed_count = 0
        
        try:
            # Parse CSV data
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            members = list(csv_reader)
            
            # Get already messaged users
            messaged_user_ids = set(
                DMLog.objects.filter(
                    account=self.account,
                    message_template=message_template,
                    status='success'
                ).values_list('member__telegram_id', flat=True)
            )
            
            for member in members:
                if sent_count >= max_messages:
                    break
                
                user_id = int(member.get('ID', 0))
                if not user_id or user_id in messaged_user_ids:
                    continue
                
                # Format message
                message_content = self.format_message(message_template, member, group_link)
                
                # Try to get or create ScrapedMember for logging
                scraped_member = None
                try:
                    scraped_member = ScrapedMember.objects.filter(telegram_id=user_id).first()
                except:
                    pass
                
                # Attempt to send message
                success, error_msg = await self.send_direct_message(user_id, message_content, member)
                
                # Log the attempt
                dm_log = DMLog.objects.create(
                    account=self.account,
                    member=scraped_member,
                    message_template=message_template,
                    message_content=message_content,
                    status='success' if success else 'failed',
                    error_message=error_msg if not success else ''
                )
                
                if success:
                    sent_count += 1
                    messaged_user_ids.add(user_id)
                else:
                    failed_count += 1
                    
                    # Handle flood wait
                    if 'wait' in error_msg.lower():
                        try:
                            wait_time = int(''.join(filter(str.isdigit, error_msg)))
                            await asyncio.sleep(min(wait_time, 300))  # Max 5 minutes
                        except:
                            await asyncio.sleep(interval)
                
                # Wait between attempts
                if sent_count < max_messages:
                    await asyncio.sleep(interval + random.randint(1, 5))
            
            return True, f"Sent {sent_count} messages, {failed_count} failed"
            
        except Exception as e:
            return False, str(e)
        finally:
            if self.client:
                await self.client.disconnect()


def run_invite_campaign_async(account_id, csv_data, target_group_id, template_id, settings_dict):
    """Function to run invite campaign asynchronously"""
    async def _run():
        try:
            account = Account.objects.get(id=account_id)
            target_group = Group.objects.get(id=target_group_id)
            template = MessageTemplate.objects.get(id=template_id)
            
            inviter = TelegramInviter(account)
            success, result = await inviter.run_invite_campaign(
                csv_data, target_group, template, settings_dict
            )
            return success, result
        except Exception as e:
            return False, str(e)
    
    return asyncio.run(_run())


def run_dm_campaign_async(account_id, csv_data, template_id, settings_dict):
    """Function to run DM campaign asynchronously"""
    async def _run():
        try:
            account = Account.objects.get(id=account_id)
            template = MessageTemplate.objects.get(id=template_id)
            
            inviter = TelegramInviter(account)
            success, result = await inviter.run_dm_campaign(
                csv_data, template, settings_dict
            )
            return success, result
        except Exception as e:
            return False, str(e)
    
    return asyncio.run(_run())