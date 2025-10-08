"""Debug test to understand the database issue."""

from sqlalchemy import create_engine, text

from askui.chat.api.db.base import Base

# Import all models


def test_debug_database():
    """Debug test to check database table creation."""
    engine = create_engine("sqlite:///:memory:")

    # Create tables
    Base.metadata.create_all(engine)

    # Check if tables exist
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        print(f"Tables created: {tables}")

        # Check if assistants table exists
        if "assistants" in tables:
            print("✅ assistants table exists")
        else:
            print("❌ assistants table missing")

        # Try to query assistants table
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM assistants"))
            count = result.scalar()
            print(f"✅ Query successful, count: {count}")
        except Exception as e:
            print(f"❌ Query failed: {e}")


if __name__ == "__main__":
    test_debug_database()
