from django import forms
from django.core.validators import RegexValidator
from .models import Account, Group, ScrapingSession, MessageTemplate, ScrapedMember


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['phone', 'api_id', 'api_hash', 'name', 'is_active']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'api_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Telegram API ID'
            }),
            'api_hash': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Telegram API Hash'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display name for this account'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['account', 'name', 'identifier', 'is_active']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Display name for this group'
            }),
            'identifier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@groupname or https://t.me/joinchat/...'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(is_active=True)


class ScrapingSessionForm(forms.ModelForm):
    class Meta:
        model = ScrapingSession
        fields = ['account', 'group', 'use_message_scraping', 'message_limit']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'use_message_scraping': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'message_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 100,
                'max': 5000,
                'value': 500
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset = Account.objects.filter(is_active=True)
        self.fields['group'].queryset = Group.objects.filter(is_active=True)


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ['name', 'subject', 'content', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Template name'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional subject line'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Message content. Use {name} and {group_link} placeholders'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        }),
        help_text="Upload a CSV file with member data"
    )


class InviteSettingsForm(forms.Form):
    account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_group = forms.ModelChoiceField(
        queryset=Group.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    message_template = forms.ModelChoiceField(
        queryset=MessageTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    action = forms.ChoiceField(
        choices=[('invite', 'Invite to Group'), ('dm', 'Send Direct Message')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    interval = forms.IntegerField(
        initial=30,
        min_value=10,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seconds between actions'
        }),
        help_text="Delay between each invite/message (seconds)"
    )
    max_invites = forms.IntegerField(
        initial=50,
        min_value=1,
        max_value=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum invites'
        })
    )
    max_messages = forms.IntegerField(
        initial=100,
        min_value=1,
        max_value=1000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Maximum messages'
        })
    )


class MemberFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, first name, or last name...'
        })
    )
    show_bots = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    active_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )