# Telegram Web Scraper

A comprehensive Django web application for managing Telegram accounts, scraping group members, and conducting invite/DM campaigns.

## Features

### 🔐 Account Management
- Add, edit, and delete Telegram accounts
- Secure storage of API credentials
- Session file management
- Account status tracking

### 👥 Group Management
- Attach groups to accounts
- Support for channels, groups, and supergroups
- Group information tracking
- Identifier validation

### 🔍 Member Scraping
- Direct member list extraction
- Message history analysis
- Flexible scraping options
- Real-time progress tracking
- CSV export functionality

### 📧 Invite/DM Campaigns
- CSV-based member targeting
- Message template system
- Rate limiting and flood protection
- Comprehensive logging
- Success/failure tracking

### 📊 Analytics & Logging
- Detailed campaign logs
- Success rate statistics
- Error tracking and analysis
- Export capabilities

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tg_scapper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start the server**
   ```bash
   python manage.py runserver
   ```

## Configuration

### Telegram API Setup

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Navigate to "API development tools"
4. Create a new application
5. Note down your `api_id` and `api_hash`

### Account Setup

1. Navigate to the Accounts section
2. Click "Add Account"
3. Enter your phone number, API ID, and API Hash
4. The system will create session files automatically

## Usage

### Adding Groups

1. Go to Groups section
2. Click "Add Group"
3. Select an account
4. Enter group identifier (username, invite link, or ID)

### Scraping Members

1. Navigate to Scraping section
2. Click "Start New Session"
3. Select account and group
4. Configure scraping options
5. Monitor progress on sessions page

### Running Campaigns

1. Go to Invite/DM interface
2. Upload CSV file with member data
3. Select account and action type
4. Choose message template
5. Configure campaign settings
6. Start campaign

## File Structure

```
tg_scapper/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── tg_web_scraper/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── scraper/                 # Main application
│   ├── models.py            # Database models
│   ├── views.py             # Web views
│   ├── forms.py             # Django forms
│   ├── admin.py             # Admin interface
│   ├── urls.py              # URL routing
│   ├── telegram_utils.py    # Telegram scraping utilities
│   ├── invite_utils.py      # Invite/DM utilities
│   └── templates/           # HTML templates
├── static/                  # Static files (CSS, JS)
├── media/                   # Uploaded files
├── csv_exports/             # CSV export files
└── telegram_sessions/       # Telegram session files
```

## Database Models

### Account
- Phone number
- API credentials
- Display name
- Status tracking

### Group
- Account association
- Group identifier
- Type and metadata
- Member count

### ScrapingSession
- Account and group references
- Configuration options
- Status and progress
- Results and errors

### ScrapedMember
- Telegram user data
- Username, names, phone
- Bot/verification status
- Active status for filtering

### MessageTemplate
- Template name and content
- Placeholder support
- Active status

### InviteLog / DMLog
- Campaign tracking
- Success/failure status
- Error messages
- Timestamps

### Settings
- Application configuration
- Default values
- Rate limits

## Security Features

### Data Protection
- API credentials stored securely
- Session files isolated per account
- No hardcoded secrets
- CSRF protection enabled

### Rate Limiting
- Configurable intervals between actions
- Flood wait handling
- Maximum action limits
- Random delays for natural behavior

### Privacy
- User data only stored temporarily
- Optional data cleanup
- Respect for Telegram's terms
- Privacy-conscious design

## API Endpoints

- `/` - Dashboard
- `/accounts/` - Account management
- `/groups/` - Group management
- `/scraping/` - Scraping sessions
- `/templates/` - Message templates
- `/invite-dm/` - Campaign interface
- `/logs/invites/` - Invite logs
- `/logs/dms/` - DM logs
- `/settings/` - Application settings
- `/admin/` - Django admin panel

## CSV Format

### Member Export Format
```csv
ID,Username,First Name,Last Name,Phone,Access Hash,Is Bot,Is Active
123456789,johndoe,John,Doe,+1234567890,123456789,False,True
```

### Required Fields for Import
- `ID` (required) - Telegram user ID
- `Username` (optional) - Telegram username
- `First Name` (optional) - User's first name
- `Last Name` (optional) - User's last name
- `Phone` (optional) - Phone number
- `Access Hash` (optional) - Telegram access hash

## Message Templates

Templates support the following placeholders:
- `{name}` - Recipient's name (first name or username)
- `{first_name}` - First name
- `{last_name}` - Last name
- `{username}` - Username
- `{group_link}` - Target group link

### Example Template
```
Hi {name},

We've created a new Telegram group for discussions:
👉 {group_link}

You're welcome to join us!
```

## Troubleshooting

### Common Issues

1. **Session Authentication Errors**
   - Ensure API credentials are correct
   - Check phone number format
   - Verify account permissions

2. **Scraping Limitations**
   - Large groups may have restricted visibility
   - Try message history scraping
   - Account must be group member

3. **Rate Limits**
   - Increase interval between actions
   - Reduce batch sizes
   - Monitor error logs

4. **Template Errors**
   - Check placeholder syntax
   - Verify template is active
   - Test with sample data

## Best Practices

### Responsible Usage
- Respect Telegram's terms of service
- Use appropriate rate limits
- Avoid spam-like behavior
- Respect user privacy

### Performance
- Monitor session status regularly
- Clean up old logs periodically
- Use message scraping for restricted groups
- Batch operations appropriately

### Security
- Keep API credentials secure
- Regularly update dependencies
- Use strong admin passwords
- Monitor access logs

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Django admin logs
3. Monitor application logs
4. Check Telegram API documentation

## License

This project is provided for educational and legitimate use cases only. Users are responsible for compliance with Telegram's terms of service and applicable laws.