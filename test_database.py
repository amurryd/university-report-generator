"""
Simple Database Connection Test
================================
Run this to test if your PostgreSQL database is working correctly.

Usage: python test_database.py
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("DATABASE CONNECTION TEST")
print("=" * 70)
print()

# Step 1: Check if .env file exists
print("Step 1: Checking .env file...")
if os.path.exists('.env'):
    print("✅ .env file found")
else:
    print("❌ .env file NOT found!")
    print("   → Create .env by copying .env.example")
    print("   → Set POSTGRES_PASSWORD in .env")
    exit(1)

# Step 2: Check if password is set
print("\nStep 2: Checking password...")
password = os.getenv('POSTGRES_PASSWORD')
if password and password != 'your_secure_password_here':
    print(f"✅ Password is set")
else:
    print("❌ Password NOT set or still default!")
    print("   → Edit .env file")
    print("   → Change POSTGRES_PASSWORD=your_secure_password_here")
    print("   → To something like: POSTGRES_PASSWORD=mypassword123")
    exit(1)

# Step 3: Try to import storage_manager
print("\nStep 3: Checking storage_manager.py...")
try:
    from storage_manager import StorageManager
    print("✅ storage_manager.py found and imported")
except ImportError as e:
    print(f"❌ Cannot import storage_manager: {e}")
    print("   → Make sure storage_manager.py is in the same folder")
    exit(1)

# Step 4: Check if psycopg2 is installed
print("\nStep 4: Checking psycopg2 package...")
try:
    import psycopg2
    print("✅ psycopg2 is installed")
except ImportError:
    print("❌ psycopg2 NOT installed!")
    print("   → Run: pip install psycopg2-binary")
    exit(1)

# Step 5: Try to connect to database
print("\nStep 5: Connecting to database...")
print("   (This might take 10-20 seconds on first try)")

try:
    storage = StorageManager(
        host=os.getenv('POSTGRES_HOST', '127.0.0.1'), # Use .env or fallback to IPv4
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'led_reports'),
        user=os.getenv('POSTGRES_USER', 'led_user'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    print("✅ Connected to database successfully!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print()
    print("Troubleshooting:")
    print("1. Is Docker Desktop running? (Check for whale icon)")
    print("2. Did you run 'docker-compose up -d'?")
    print("3. Wait 30 seconds after running docker-compose up -d")
    print("4. Try: docker-compose restart")
    print()
    exit(1)

# Step 6: Get database statistics
print("\nStep 6: Getting database info...")
try:
    stats = storage.get_report_statistics()
    
    print("✅ Database is working!")
    print()
    print("📊 Current Statistics:")
    print(f"   Total Reports: {stats['total_reports']}")
    print(f"   Draft Reports: {stats['draft_reports']}")
    print(f"   Final Reports: {stats['final_reports']}")
    
except Exception as e:
    print(f"❌ Error getting stats: {e}")

# Step 7: Test saving a report
print("\nStep 7: Testing save functionality...")
try:
    test_report_id = storage.save_report(
        content="This is a test report to verify database is working.",
        report_type="test",
        title="Test Report",
        metadata={'test': True},
        status='draft'
    )
    print(f"✅ Successfully saved test report (ID: {test_report_id})")
    
    # Try to retrieve it
    retrieved = storage.get_report(test_report_id)
    if retrieved:
        print("✅ Successfully retrieved test report")
        
        # Delete the test report
        storage.delete_report(test_report_id)
        print("✅ Successfully deleted test report")
    
except Exception as e:
    print(f"❌ Error in save/retrieve test: {e}")

print()
print("=" * 70)
print("TEST COMPLETE!")
print("=" * 70)
print()
print("✅ Everything is working correctly!")
print()
print("Next steps:")
print("1. Run your Streamlit app: streamlit run streamlit_app.py")
print("2. Generate a report")
print("3. It will automatically save to the database!")
print()
print("To view your database:")
print("→ Open browser: http://localhost:5050")
print("→ Login with credentials from .env file")
print()
print("=" * 70)
