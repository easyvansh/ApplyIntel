import random
import sqlite3
from datetime import date, timedelta, datetime

# Sample data pools
COMPANIES = [
    "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Uber", "Airbnb",
    "Stripe", "Shopify", "Salesforce", "Adobe", "Spotify", "Twitter", "LinkedIn",
    "Pinterest", "Dropbox", "Slack", "Zoom", "Snap", "Reddit", "Square", "PayPal",
    "Intel", "IBM", "Oracle", "VMware", "Cisco", "Tesla", "SpaceX", "Atlassian",
    "Canva", "Figma", "Notion", "Airtable", "Coinbase", "Robinhood", "GitHub",
    "Bloomberg", "Capital One", "JPMorgan", "Goldman Sachs", "Morgan Stanley"
]

ROLES = [
    "Software Engineer", "Frontend Developer", "Backend Developer", "Full Stack Developer",
    "DevOps Engineer", "Data Scientist", "Machine Learning Engineer", "Product Manager",
    "UX Designer", "UI Designer", "QA Engineer", "Technical Lead", "Engineering Manager",
    "Site Reliability Engineer", "Security Engineer", "Cloud Architect", "iOS Developer",
    "Android Developer", "Mobile Developer", "Database Administrator", "Systems Engineer",
    "Data Engineer", "ML Ops Engineer", "Platform Engineer", "Infrastructure Engineer"
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA",
    "Los Angeles, CA", "Chicago, IL", "Denver, CO", "Portland, OR", "Atlanta, GA",
    "Remote - US", "Remote - Global", "Remote - East Coast", "Remote - West Coast",
    "London, UK", "Berlin, Germany", "Toronto, Canada", "Vancouver, Canada",
    "Amsterdam, Netherlands", "Sydney, Australia", "Singapore", "Tokyo, Japan"
]

STATUSES = ["saved", "applied", "interview", "rejected", "offer"]

# Sample URLs
URLS = [
    "https://careers.google.com/jobs/123",
    "https://jobs.microsoft.com/job/456",
    "https://amazon.jobs/en/jobs/789",
    "https://boards.greenhouse.io/apple/jobs/101",
    "https://jobs.lever.co/meta/112",
    "https://www.linkedin.com/jobs/view/131",
    "https://wellfound.com/jobs/415",
    None  # 1/8 chance of no URL
]

# Sample notes
NOTES = [
    "Had initial screening call with HR. Went well, they seemed interested.",
    "Completed technical interview. Need to review algorithms more.",
    "Received rejection email. Will reapply after gaining more experience.",
    "Final round interview scheduled for next week.",
    "Applied through referral. Waiting to hear back.",
    "Received offer! Need to negotiate salary.",
    "Ghosted after 3 interviews.",
    "Hiring manager seemed impressed with my portfolio.",
    "Technical test completed. Waiting for feedback.",
    "Second round interview completed. Moving to final round!",
    "Great conversation with the team. Culture seems amazing.",
    "Salary expectations discussed. They said it's within range.",
    "System design interview went okay. Could have done better.",
    "Take-home project submitted. Now waiting.",
    "Recruiter reached out on LinkedIn.",
    "Networking event led to this application.",
    "Applied through company website.",
    "Referred by former colleague.",
    "Had coffee chat with team lead.",
    "Negotiating offer details.",
    None  # 1/4 chance of no notes
]

def create_database():
    """Create jobtrackr.db with dummy data"""
    
    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect('jobtrackr.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company VARCHAR(200) NOT NULL,
            role VARCHAR(200) NOT NULL,
            location VARCHAR(200),
            url VARCHAR(500),
            status VARCHAR(50) NOT NULL,
            date_applied DATE NOT NULL,
            next_action_date DATE,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME
        )
    ''')
    
    # Clear existing data
    cursor.execute('DELETE FROM applications')
    
    # Generate 150 dummy records
    today = date.today()
    applications = []
    
    for i in range(150):
        # Random date within last 6 months
        days_ago = random.randint(0, 180)
        date_applied = today - timedelta(days=days_ago)
        
        # Random next action date (30% chance)
        next_action_date = None
        if random.random() < 0.3:
            next_action_days = random.randint(1, 30)
            next_action_date = today + timedelta(days=next_action_days)
        
        # Status distribution
        if days_ago < 7:
            status_weights = [0.4, 0.4, 0.1, 0.05, 0.05]  # More saved/applied for recent
        elif days_ago < 30:
            status_weights = [0.2, 0.3, 0.3, 0.15, 0.05]
        else:
            status_weights = [0.05, 0.1, 0.3, 0.4, 0.15]  # Older more likely rejected/offer
        
        status = random.choices(STATUSES, weights=status_weights)[0]
        
        # Soft delete some records (10% chance)
        deleted_at = None
        if random.random() < 0.1:
            deleted_days_ago = random.randint(1, 30)
            deleted_at = (datetime.now() - timedelta(days=deleted_days_ago)).isoformat()
        
        # Generate created_at (slightly after date_applied)
        created_days_offset = random.randint(0, 2)
        created_at = datetime.combine(date_applied, datetime.min.time()) + timedelta(
            days=created_days_offset, 
            hours=random.randint(9, 17)
        )
        
        application = (
            random.choice(COMPANIES),
            random.choice(ROLES),
            random.choice(LOCATIONS),
            random.choice(URLS),
            status,
            date_applied.isoformat(),
            next_action_date.isoformat() if next_action_date else None,
            random.choice(NOTES),
            created_at.isoformat(),
            deleted_at
        )
        applications.append(application)
    
    # Insert data
    cursor.executemany('''
        INSERT INTO applications (
            company, role, location, url, status, 
            date_applied, next_action_date, notes, created_at, deleted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', applications)
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON applications(company)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON applications(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_applied ON applications(date_applied)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_deleted_at ON applications(deleted_at)')
    
    # Commit and close
    conn.commit()
    
    # Verify data
    cursor.execute('SELECT COUNT(*) FROM applications')
    count = cursor.fetchone()[0]
    print(f"✅ Created {count} records in jobtrackr.db")
    
    cursor.execute('SELECT status, COUNT(*) FROM applications GROUP BY status')
    status_counts = cursor.fetchall()
    print("\nStatus distribution:")
    for status, count in status_counts:
        print(f"  {status}: {count}")
    
    cursor.execute('SELECT COUNT(*) FROM applications WHERE deleted_at IS NOT NULL')
    deleted_count = cursor.fetchone()[0]
    print(f"\nSoft deleted records: {deleted_count}")
    
    conn.close()

if __name__ == "__main__":
    create_database()
    print("\n🎉 Database file 'jobtrackr.db' has been created successfully!")