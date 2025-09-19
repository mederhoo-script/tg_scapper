from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator
import os


class Account(models.Model):
    """Telegram account credentials"""
    phone = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')]
    )
    api_id = models.CharField(max_length=50)
    api_hash = models.CharField(max_length=100)
    name = models.CharField(max_length=100, blank=True, help_text="Display name for this account")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name or self.phone}"
    
    @property
    def session_file_path(self):
        """Path to Telegram session file"""
        from django.conf import settings
        sessions_dir = getattr(settings, 'TELEGRAM_SESSIONS_DIR', 'telegram_sessions')
        os.makedirs(sessions_dir, exist_ok=True)
        return os.path.join(sessions_dir, f"session_{self.phone.replace('+', '')}")


class Group(models.Model):
    """Telegram groups attached to accounts"""
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=200, help_text="Display name for this group")
    identifier = models.CharField(max_length=200, help_text="Username or invite link")
    group_type = models.CharField(
        max_length=20,
        choices=[
            ('channel', 'Channel'),
            ('group', 'Group'),
            ('supergroup', 'Supergroup'),
            ('broadcast', 'Broadcast Channel'),
        ],
        blank=True
    )
    member_count = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['account', 'identifier']
    
    def __str__(self):
        return f"{self.name} ({self.account.phone})"


class ScrapingSession(models.Model):
    """Record of scraping sessions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='scraping_sessions')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='scraping_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_members_found = models.IntegerField(default=0)
    use_message_scraping = models.BooleanField(default=True)
    message_limit = models.IntegerField(default=500)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    csv_file_path = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Scraping {self.group.name} - {self.status}"
    
    @property
    def duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        return None


class ScrapedMember(models.Model):
    """Individual scraped member data"""
    session = models.ForeignKey(ScrapingSession, on_delete=models.CASCADE, related_name='members')
    telegram_id = models.BigIntegerField()
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    access_hash = models.BigIntegerField(null=True, blank=True)
    is_bot = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Set to False to exclude from exports/invites")
    scraped_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['username', 'first_name']
        unique_together = ['session', 'telegram_id']
    
    def __str__(self):
        name_parts = [self.first_name, self.last_name]
        name = ' '.join(filter(None, name_parts))
        if self.username:
            return f"@{self.username}" + (f" ({name})" if name else "")
        return name or f"User {self.telegram_id}"


class MessageTemplate(models.Model):
    """Message templates for invites and DMs"""
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField(help_text="Use {name} and {group_link} placeholders")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class InviteLog(models.Model):
    """Log of invite attempts"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('already_member', 'Already Member'),
        ('privacy_restricted', 'Privacy Restricted'),
        ('flood_wait', 'Flood Wait'),
        ('user_not_found', 'User Not Found'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='invite_logs')
    target_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invite_logs')
    member = models.ForeignKey(ScrapedMember, on_delete=models.CASCADE, related_name='invite_logs')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"Invite {self.member} to {self.target_group.name} - {self.status}"


class DMLog(models.Model):
    """Log of DM attempts"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('privacy_restricted', 'Privacy Restricted'),
        ('flood_wait', 'Flood Wait'),
        ('user_not_found', 'User Not Found'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='dm_logs')
    member = models.ForeignKey(ScrapedMember, on_delete=models.CASCADE, related_name='dm_logs')
    message_template = models.ForeignKey(MessageTemplate, on_delete=models.CASCADE, related_name='dm_logs')
    message_content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"DM to {self.member} - {self.status}"


class Settings(models.Model):
    """Application settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Settings"
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    @classmethod
    def get_setting(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, key, value, description=""):
        obj, created = cls.objects.get_or_create(key=key, defaults={'description': description})
        obj.value = str(value)
        obj.save()
        return obj
