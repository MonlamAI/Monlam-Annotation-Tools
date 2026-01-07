#!/usr/bin/env python
"""
Emergency database reset script for Render Shell
Drops and recreates public schema to fix migration inconsistencies
"""
import os
import sys
import django

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.db import connection

print("🔧 Resetting database schema...")

try:
    with connection.cursor() as cursor:
        # Drop and recreate public schema
        cursor.execute("DROP SCHEMA IF EXISTS public CASCADE;")
        print("✅ Dropped public schema")
        
        cursor.execute("CREATE SCHEMA public;")
        print("✅ Created public schema")
        
        cursor.execute("GRANT ALL ON SCHEMA public TO PUBLIC;")
        print("✅ Granted permissions")
        
    print("\n🎉 Database reset complete!")
    print("📝 Now run: python manage.py migrate --noinput")
    print("👤 Then create admin: python manage.py create_admin --username admin --password MonlamAI2024 --email admin@monlam.ai --noinput")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Alternative: Ask Render to provision a new PostgreSQL database")
    sys.exit(1)

