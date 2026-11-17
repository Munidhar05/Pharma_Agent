import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import init_db, engine
from backend.app.models import Base

def main():
    print("Initializing Pharma Job Hunter AI Database Schema...")
    init_db()
    print("Database tables created successfully!")
    print(f"Total tables managed: {len(Base.metadata.tables)}")
    for table_name in sorted(Base.metadata.tables.keys()):
        print(f" - {table_name}")

if __name__ == "__main__":
    main()

