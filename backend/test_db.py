import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 50)
print("Testing Database Connection")
print("=" * 50)

try:
    from app.models.database import engine, init_db, Company
    from sqlalchemy import text
    
    # Test connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT @@VERSION"))
        version = result.fetchone()
        print("\n✓ Database connection successful!")
        print(f"\nSQL Server Version:\n{version[0]}")
    
    # Create tables
    print("\nCreating database tables...")
    init_db()
    print("✓ All tables created successfully!")
    
    print("\n" + "=" * 50)
    print("Database setup completed!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nPlease check:")
    print("  1. SQL Server is running")
    print("  2. Database 'FotoAnaliz' exists")
    print("  3. Credentials in .env file are correct")
    print("  4. ODBC Driver 18 for SQL Server is installed")
