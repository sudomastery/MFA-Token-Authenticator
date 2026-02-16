# Quick test to create tables
from database import init_db, engine
from sqlalchemy import inspect

print("Testing database connection...")
print(f"Database URL: {engine.url}")

print("\nCreating tables...")
init_db()

print("\nChecking created tables...")
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables created: {tables}")

print("\n✅ Success! Database setup complete!")