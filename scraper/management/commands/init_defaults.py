from django.core.management.base import BaseCommand
from scraper.models import Settings, MessageTemplate


class Command(BaseCommand):
    help = 'Initialize default settings and templates'

    def handle(self, *args, **options):
        # Create default settings
        default_settings = [
            ('default_interval', '30', 'Default interval between actions (seconds)'),
            ('max_invites', '50', 'Maximum invites per campaign'),
            ('max_messages', '100', 'Maximum DMs per campaign'),
            ('message_scraping_limit', '500', 'Default message scraping limit'),
            ('log_retention_days', '30', 'Days to retain logs'),
        ]
        
        for key, value, description in default_settings:
            obj, created = Settings.objects.get_or_create(
                key=key,
                defaults={'value': value, 'description': description}
            )
            if created:
                self.stdout.write(f'Created setting: {key}')
        
        # Create default message template
        default_template = """Hi {name},

We've created a new Telegram group where we continue discussions:
👉 {group_link}

You're welcome to join us!"""
        
        template, created = MessageTemplate.objects.get_or_create(
            name='Default Invite Template',
            defaults={
                'content': default_template,
                'subject': 'Join our discussion group',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write('Created default message template')
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized defaults'))