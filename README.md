# Telegram Web Scraper & Adder

A comprehensive Django web application for managing Telegram accounts, scraping group members, and conducting invite/DM campaigns. This project has evolved from standalone command-line scripts (`scrape_by_chat.py` and `adder.py`) into a full-featured web interface.

## 🌟 Features

### 🔐 Account Management
- Add, edit, and delete multiple Telegram accounts
- Secure storage of API credentials (api_id, api_hash)
- Automated session file management
- Account status tracking and validation
- Support for multiple phone numbers

### 👥 Group Management
- Attach multiple groups/channels to each account
- Support for channels, groups, supergroups, and broadcast channels
- Group information tracking (member count, type, metadata)
- Flexible identifier support (username, invite link, or direct ID)
- Group status monitoring

### 🔍 Member Scraping
- **Direct member list extraction** - Get members directly from group participant lists
- **Message history analysis** - Extract members from message history (useful for restricted groups)
- Real-time progress tracking with detailed status updates
- Configurable scraping limits and options
- CSV export functionality with member filtering
- Bot detection and verification status tracking
- Active/inactive member management for targeted campaigns

### 📧 Invite/DM Campaigns
- **CSV-based member targeting** - Upload member lists for targeted campaigns
- **Message template system** - Create reusable templates with placeholders
- **Invite campaigns** - Automatically invite users to target groups
- **Direct message campaigns** - Send personalized DMs to users
- Rate limiting and flood protection with intelligent delays
- Comprehensive logging of all campaign activities
- Success/failure tracking with detailed error messages
- Skip already processed users automatically

### 📊 Analytics & Logging
- Detailed campaign logs with filterable views
- Success rate statistics and performance metrics
- Error tracking and analysis for troubleshooting
- Export capabilities for reporting
- Real-time campaign monitoring
- Historical data retention

### ⚙️ Configuration Management
- Web-based settings management
- Configurable rate limits and delays
- Message template editor with placeholder support
- Bulk data management tools
- Database cleanup utilities

## 📋 Prerequisites

Before setting up the application, ensure you have:

- **Python 3.8+** (Python 3.10+ recommended)
- **Django 5.2+** (installed via requirements.txt)
- **Telethon 1.41+** (for Telegram API integration)
- **Pillow** (for image processing)
- **Telegram API credentials** (api_id and api_hash from https://my.telegram.org)
- **Active Telegram account(s)** with phone number access

### System Requirements
- Minimum 1GB RAM (2GB+ recommended for large groups)
- 500MB free disk space for session files and CSVs
- Stable internet connection for Telegram API access

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/mederhoo-script/tg_scapper.git
cd tg_scapper
```

### 2. Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Run initial migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 5. Initialize Default Settings (Optional)
```bash
# Load default application settings
python manage.py init_defaults
```

## ⚙️ Configuration

### Telegram API Setup

1. **Get API Credentials**:
   - Visit https://my.telegram.org
   - Log in with your phone number
   - Navigate to "API development tools"
   - Create a new application with any name/description
   - Note down your `api_id` (numeric) and `api_hash` (string)

2. **Security Notes**:
   - **Never share your API credentials** - they provide full access to your Telegram account
   - Store credentials securely - the app encrypts them in the database
   - Each account needs separate API credentials
   - API credentials are tied to your Telegram account, not phone numbers

### Environment Variables (Optional)

Create a `.env` file in the project root for additional configuration:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (if using PostgreSQL instead of SQLite)
DATABASE_URL=postgresql://user:password@localhost:5432/tg_scraper

# File Storage Paths
CSV_EXPORTS_DIR=/path/to/csv/exports
TELEGRAM_SESSIONS_DIR=/path/to/sessions
MEDIA_ROOT=/path/to/media

# Security
SECURE_SSL_REDIRECT=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
```

## 🎮 Running the Application

### Development Server
```bash
# Start the Django development server
python manage.py runserver

# Access the application at http://127.0.0.1:8000
```

### Background Tasks (If Using Celery)
If you've configured Celery for background processing:

```bash
# Start Celery worker (in a separate terminal)
celery -A tg_web_scraper worker --loglevel=info

# Start Celery beat for scheduled tasks (optional)
celery -A tg_web_scraper beat --loglevel=info
```

### Production Deployment
For production, consider using:
- **Gunicorn** or **uWSGI** as WSGI server
- **Nginx** as reverse proxy
- **PostgreSQL** or **MySQL** for database
- **Redis** for caching and Celery broker
- **Supervisor** for process management

## 📱 Using the Web Interface

### 1. Account Management (`/accounts/`)

**Adding Accounts**:
1. Click "Add Account" 
2. Enter phone number (with country code, e.g., +1234567890)
3. Enter your `api_id` and `api_hash`
4. Provide a display name for easy identification
5. Save - the system will create session files automatically

**Managing Accounts**:
- View all accounts with status indicators
- Edit account information and credentials
- Deactivate accounts without deleting data
- Monitor session file status

### 2. Group Management (`/groups/`)

**Adding Groups**:
1. Click "Add Group"
2. Select the account that has access to the group
3. Enter group identifier:
   - Username: `@groupusername`
   - Invite link: `https://t.me/joinchat/xxxxx`
   - Direct ID: `1234567890`
4. Provide a display name
5. Save - the system will validate group access

**Group Types Supported**:
- Public groups and channels
- Private groups (with invite links)
- Supergroups
- Broadcast channels

### 3. Member Scraping (`/scraping/`)

**Starting a Scraping Session**:
1. Click "Start New Session"
2. Select account and target group
3. Choose scraping method:
   - **Direct scraping**: Get members from participant list (faster, may be limited)
   - **Message scraping**: Extract members from message history (slower, works for restricted groups)
4. Set message limit (for message scraping)
5. Start session

**Monitoring Progress**:
- Real-time status updates on sessions page
- View detailed progress and member counts
- Access error logs and diagnostics
- Cancel running sessions if needed

**Managing Scraped Data**:
1. Click "View Members" on completed session
2. Filter members by username, name, or bot status
3. Toggle member active status to exclude from exports/campaigns
4. Bulk operations for managing large datasets
5. Export filtered data to CSV

### 4. CSV Downloads and Management

**Exporting Members**:
- Click "Export CSV" from scraping session or member list
- Files saved to `csv_exports/` directory
- Filename format: `members_{phone}_{group}_{timestamp}.csv`

**CSV Format**:
```csv
ID,Username,First Name,Last Name,Phone,Access Hash,Is Bot,Is Active
123456789,johndoe,John,Doe,+1234567890,123456789,False,True
```

**Editing Scraped Data**:
- Use member management interface to remove bots
- Filter out inactive/deleted accounts
- Exclude users based on criteria
- Bulk activate/deactivate members

### 5. Message Templates (`/templates/`)

**Creating Templates**:
1. Click "Create Template"
2. Enter template name and subject (optional)
3. Write message content with placeholders:
   - `{name}` - Recipient's name (first name or username)
   - `{first_name}` - First name only
   - `{last_name}` - Last name only
   - `{username}` - Username only
   - `{group_link}` - Target group link

**Example Template**:
```
Hi {name},

We've created a new Telegram group for discussions:
👉 {group_link}

You're welcome to join us!
```

### 6. Invite/DM Campaigns (`/invite-dm/`)

**Running Invite Campaigns**:
1. Upload CSV file with member data
2. Select account to use for inviting
3. Choose target group for invitations
4. Select message template (optional)
5. Configure settings:
   - Interval between invites (seconds)
   - Maximum invites per session
   - Group link for template
6. Start campaign

**Running DM Campaigns**:
1. Upload CSV file with member data
2. Select account for sending messages
3. Choose message template
4. Configure settings:
   - Interval between messages (seconds)
   - Maximum messages per session
   - Custom group link
5. Start campaign

**Campaign Settings**:
- **Rate Limiting**: 30-60 seconds between actions recommended
- **Flood Protection**: Automatic handling of Telegram rate limits
- **Skip Processed**: Automatically skip users already contacted
- **Error Handling**: Comprehensive error tracking and recovery

### 7. Campaign Logs and Monitoring

**Invite Logs** (`/logs/invites/`):
- View all invite attempts with status
- Filter by account, group, date, or status
- Export logs for analysis
- Retry failed invitations

**DM Logs** (`/logs/dms/`):
- Monitor direct message campaigns
- Track delivery status and errors
- View message content and responses
- Analyze success rates

**Log Statuses**:
- ✅ **Success**: Action completed successfully
- ❌ **Failed**: General failure
- 🔒 **Privacy Restricted**: User privacy settings prevent action
- ⏰ **Flood Wait**: Rate limited by Telegram
- 👤 **Already Member**: User already in target group
- ❓ **User Not Found**: User account deleted/invalid

### 8. Settings Management (`/settings/`)

**Configure Application**:
- Default rate limits and intervals
- Maximum action limits per session
- File storage locations
- Template defaults
- Cleanup schedules

**Bulk Operations**:
- Export all data
- Cleanup old logs
- Reset session statistics
- Database maintenance

## 🛡️ Django Admin Access (`/admin/`)

Access the Django admin panel for advanced management:

1. Navigate to `http://127.0.0.1:8000/admin/`
2. Login with superuser credentials
3. Manage all database records directly
4. Bulk operations and advanced filtering
5. User management and permissions
6. System logs and debugging

**Admin Features**:
- Direct database access to all models
- Bulk editing and deletion
- Advanced search and filtering
- Data export functionality
- User permission management

## 📁 File Locations

### Directory Structure
```
tg_scapper/
├── csv_exports/              # 📊 Exported CSV files
│   └── members_*.csv
├── telegram_sessions/        # 🔐 Telegram session files  
│   └── session_*.session
├── media/                    # 📎 Uploaded files
│   └── uploads/
├── static/                   # 🎨 Static assets (CSS, JS)
├── db.sqlite3               # 🗄️ SQLite database
└── logs/                    # 📝 Application logs
    ├── django.log
    ├── telegram.log
    └── campaigns.log
```

### Important Files
- **CSV Exports**: `csv_exports/members_{phone}_{group}_{timestamp}.csv`
- **Session Files**: `telegram_sessions/session_{phone}.session`
- **Database**: `db.sqlite3` (or configured database)
- **Logs**: `logs/` directory (if configured)
- **Uploaded CSVs**: `media/uploads/`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Auto-generated |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed host names | `[]` |
| `CSV_EXPORTS_DIR` | CSV export directory | `csv_exports/` |
| `TELEGRAM_SESSIONS_DIR` | Session files directory | `telegram_sessions/` |
| `MEDIA_ROOT` | Media files directory | `media/` |
| `DATABASE_URL` | Database connection string | SQLite default |

## 🔒 Security & Disclaimer

### Security Features
- **Encrypted API Storage**: API credentials stored securely in database
- **Session Isolation**: Each account has isolated session files
- **CSRF Protection**: Django CSRF protection enabled
- **Rate Limiting**: Built-in protection against Telegram rate limits
- **Access Control**: Admin panel with user authentication
- **Data Validation**: Input validation and sanitization

### Important Security Notes
1. **API Credentials**: Never share your Telegram API credentials
2. **Session Files**: Keep session files secure - they provide account access
3. **Network Security**: Use HTTPS in production
4. **Database Security**: Secure your database credentials
5. **Admin Access**: Use strong passwords for admin accounts

### Responsible Use Disclaimer

⚠️ **IMPORTANT**: This tool is provided for educational and legitimate use cases only.

**Users are responsible for**:
- Compliance with Telegram's Terms of Service
- Respecting user privacy and consent
- Following applicable laws and regulations
- Avoiding spam-like behavior
- Using appropriate rate limits

**Prohibited Uses**:
- Mass spamming or unsolicited messaging
- Harvesting data without consent
- Violating Telegram's anti-spam policies
- Any illegal activities

**The developers are not responsible for misuse of this tool.**

## 🔧 Troubleshooting

### Common Issues

#### Authentication Errors
```
Problem: "Session authentication failed"
Solution: 
- Verify API credentials are correct
- Check phone number format (+1234567890)
- Ensure account has API access enabled
- Delete and recreate session if corrupted
```

#### Scraping Limitations
```
Problem: "Cannot access group members"
Solution:
- Ensure account is a member of the group
- Try message scraping for restricted groups
- Check group privacy settings
- Verify group identifier is correct
```

#### Rate Limiting Issues
```
Problem: "FloodWaitError" or "Too many requests"
Solution:
- Increase interval between actions (60+ seconds)
- Reduce batch sizes
- Wait for flood restrictions to expire
- Use multiple accounts to distribute load
```

#### CSV Upload Errors
```
Problem: "Invalid CSV format"
Solution:
- Ensure CSV has required headers
- Check for encoding issues (use UTF-8)
- Verify data types are correct
- Remove empty rows and invalid characters
```

#### Database Issues
```
Problem: "Database locked" or migration errors
Solution:
- Stop all running processes
- Run: python manage.py migrate
- Check database permissions
- Consider switching to PostgreSQL for production
```

### Debug Mode
Enable debug mode for detailed error messages:
```bash
# In settings.py or .env
DEBUG = True

# View detailed logs
python manage.py runserver --verbosity=2
```

### Getting Help
1. Check application logs in Django admin
2. Enable debug mode for detailed errors
3. Review Telegram API documentation
4. Check GitHub issues for similar problems
5. Ensure all dependencies are up to date

## 🤝 Contributing

We welcome contributions to improve the Telegram Web Scraper!

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Ensure code follows Django best practices
5. Submit a pull request with clear description

### Code Style
- Follow PEP 8 for Python code
- Use Django conventions for models and views
- Add docstrings for new functions
- Include tests for new features
- Update documentation as needed

### Reporting Issues
- Use GitHub Issues for bug reports
- Include error messages and logs
- Provide steps to reproduce
- Specify environment details (Python version, OS, etc.)

### Feature Requests
- Open GitHub Issues with feature proposals
- Explain use case and benefits
- Consider implementation complexity
- Be open to discussion and feedback

---

## 📄 License

This project is provided for **educational and legitimate use cases only**. 

Users are responsible for compliance with:
- Telegram's Terms of Service
- Applicable laws and regulations  
- Privacy and data protection requirements
- Anti-spam policies

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.**

---

Made with ❤️ for the Telegram automation community. Use responsibly!