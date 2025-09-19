from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
import csv
import os
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import FloodWaitError, ChannelPrivateError, UserPrivacyRestrictedError
from telethon.tl.types import Channel, Message, MessageActionChatAddUser, MessageService
from telethon.tl.functions.messages import GetHistoryRequest

from .models import (
    Account, Group, ScrapingSession, ScrapedMember, 
    MessageTemplate, InviteLog, DMLog, Settings
)
from .forms import (
    AccountForm, GroupForm, MessageTemplateForm, 
    ScrapingSessionForm, CSVUploadForm, InviteSettingsForm
)


def dashboard(request):
    """Main dashboard view"""
    context = {
        'accounts_count': Account.objects.filter(is_active=True).count(),
        'groups_count': Group.objects.filter(is_active=True).count(),
        'sessions_count': ScrapingSession.objects.count(),
        'members_count': ScrapedMember.objects.filter(is_active=True).count(),
        'recent_sessions': ScrapingSession.objects.select_related('account', 'group')[:5],
        'recent_invites': InviteLog.objects.select_related('account', 'member')[:10],
        'recent_dms': DMLog.objects.select_related('account', 'member')[:10],
    }
    return render(request, 'scraper/dashboard.html', context)


# Account Management Views
def account_list(request):
    """List all accounts"""
    accounts = Account.objects.annotate(groups_count=Count('groups')).order_by('-created_at')
    return render(request, 'scraper/accounts/list.html', {'accounts': accounts})


def account_create(request):
    """Create new account"""
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save()
            messages.success(request, f'Account {account.phone} created successfully!')
            return redirect('account_list')
    else:
        form = AccountForm()
    return render(request, 'scraper/accounts/form.html', {'form': form, 'title': 'Add Account'})


def account_edit(request, pk):
    """Edit account"""
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f'Account {account.phone} updated successfully!')
            return redirect('account_list')
    else:
        form = AccountForm(instance=account)
    return render(request, 'scraper/accounts/form.html', {
        'form': form, 
        'account': account, 
        'title': 'Edit Account'
    })


def account_delete(request, pk):
    """Delete account"""
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        phone = account.phone
        account.delete()
        messages.success(request, f'Account {phone} deleted successfully!')
        return redirect('account_list')
    return render(request, 'scraper/accounts/delete.html', {'account': account})


# Group Management Views
def group_list(request):
    """List all groups"""
    groups = Group.objects.select_related('account').order_by('-created_at')
    accounts = Account.objects.filter(is_active=True)
    
    # Filter by account if provided
    account_id = request.GET.get('account')
    if account_id:
        groups = groups.filter(account_id=account_id)
    
    return render(request, 'scraper/groups/list.html', {
        'groups': groups,
        'accounts': accounts,
        'selected_account': account_id
    })


def group_create(request):
    """Create new group"""
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f'Group {group.name} added successfully!')
            return redirect('group_list')
    else:
        form = GroupForm()
    return render(request, 'scraper/groups/form.html', {'form': form, 'title': 'Add Group'})


def group_edit(request, pk):
    """Edit group"""
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f'Group {group.name} updated successfully!')
            return redirect('group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'scraper/groups/form.html', {
        'form': form, 
        'group': group, 
        'title': 'Edit Group'
    })


def group_delete(request, pk):
    """Delete group"""
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, f'Group {name} deleted successfully!')
        return redirect('group_list')
    return render(request, 'scraper/groups/delete.html', {'group': group})


# Scraping Views
def scraping_sessions(request):
    """List scraping sessions"""
    sessions = ScrapingSession.objects.select_related('account', 'group').order_by('-started_at')
    return render(request, 'scraper/scraping/sessions.html', {'sessions': sessions})


def start_scraping(request):
    """Start new scraping session"""
    if request.method == 'POST':
        form = ScrapingSessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            # Start scraping in background (simplified for now)
            messages.success(request, f'Scraping session started for {session.group.name}!')
            return redirect('scraping_sessions')
    else:
        form = ScrapingSessionForm()
    return render(request, 'scraper/scraping/start.html', {'form': form})


def scraped_members(request, session_id):
    """View and manage scraped members"""
    session = get_object_or_404(ScrapingSession, pk=session_id)
    members = session.members.all()
    
    # Apply filters
    search = request.GET.get('search')
    if search:
        members = members.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    show_bots = request.GET.get('show_bots')
    if show_bots != 'on':
        members = members.filter(is_bot=False)
    
    active_only = request.GET.get('active_only', 'on')
    if active_only == 'on':
        members = members.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(members, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'scraper/scraping/members.html', {
        'session': session,
        'page_obj': page_obj,
        'search': search,
        'show_bots': show_bots,
        'active_only': active_only
    })


@require_http_methods(["POST"])
def toggle_member_active(request, member_id):
    """Toggle member active status"""
    member = get_object_or_404(ScrapedMember, pk=member_id)
    member.is_active = not member.is_active
    member.save()
    return JsonResponse({'status': 'success', 'is_active': member.is_active})


def export_members_csv(request, session_id):
    """Export scraped members to CSV"""
    session = get_object_or_404(ScrapingSession, pk=session_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="members_{session.group.name}_{session.started_at.strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
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
    
    return response


# Message Template Views
def template_list(request):
    """List message templates"""
    templates = MessageTemplate.objects.filter(is_active=True).order_by('name')
    return render(request, 'scraper/templates/list.html', {'templates': templates})


def template_create(request):
    """Create message template"""
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Template {template.name} created successfully!')
            return redirect('template_list')
    else:
        form = MessageTemplateForm()
    return render(request, 'scraper/templates/form.html', {'form': form, 'title': 'Add Template'})


def template_edit(request, pk):
    """Edit message template"""
    template = get_object_or_404(MessageTemplate, pk=pk)
    if request.method == 'POST':
        form = MessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f'Template {template.name} updated successfully!')
            return redirect('template_list')
    else:
        form = MessageTemplateForm(instance=template)
    return render(request, 'scraper/templates/form.html', {
        'form': form, 
        'template': template, 
        'title': 'Edit Template'
    })


# Invite/DM Views
def invite_dm_interface(request):
    """Main invite/DM interface"""
    if request.method == 'POST':
        # Handle CSV upload and processing
        pass
    
    accounts = Account.objects.filter(is_active=True)
    target_groups = Group.objects.filter(is_active=True)
    templates = MessageTemplate.objects.filter(is_active=True)
    
    return render(request, 'scraper/invite_dm/interface.html', {
        'accounts': accounts,
        'target_groups': target_groups,
        'templates': templates
    })


def invite_logs(request):
    """View invite logs"""
    logs = InviteLog.objects.select_related('account', 'target_group', 'member').order_by('-attempted_at')
    return render(request, 'scraper/logs/invites.html', {'logs': logs})


def dm_logs(request):
    """View DM logs"""
    logs = DMLog.objects.select_related('account', 'member', 'message_template').order_by('-sent_at')
    return render(request, 'scraper/logs/dms.html', {'logs': logs})


# Settings Views
def settings_view(request):
    """Application settings"""
    if request.method == 'POST':
        # Handle settings updates
        pass
    
    # Get current settings
    settings_dict = {}
    for setting in Settings.objects.all():
        settings_dict[setting.key] = setting.value
    
    return render(request, 'scraper/settings.html', {'settings': settings_dict})
