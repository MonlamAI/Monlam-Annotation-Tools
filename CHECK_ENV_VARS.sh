#!/bin/bash
# 🔍 Diagnostic Script: Check Environment Variables
# Run this in Render Shell to see what's configured

echo "======================================"
echo "🔍 ENVIRONMENT VARIABLES DIAGNOSTIC"
echo "======================================"
echo ""

echo "📍 1. DJANGO_SETTINGS_MODULE"
echo "   Current: $DJANGO_SETTINGS_MODULE"
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    echo "   Status: ✅ CORRECT"
elif [ "$DJANGO_SETTINGS_MODULE" = "config.settings" ]; then
    echo "   Status: ❌ WRONG - Should be config.settings.production"
else
    echo "   Status: ⚠️  Not set (will use Dockerfile default)"
fi
echo ""

echo "📍 2. DATABASE_URL"
if [ -n "$DATABASE_URL" ]; then
    echo "   Status: ✅ SET"
    echo "   Value: ${DATABASE_URL:0:30}..."
else
    echo "   Status: ❌ NOT SET - This will cause errors!"
fi
echo ""

echo "📍 3. PORT"
echo "   Current: ${PORT:-Not set}"
echo "   Status: ${PORT:+✅ SET}"
echo ""

echo "📍 4. Admin Credentials"
echo "   ADMIN_USERNAME: ${ADMIN_USERNAME:-Not set}"
echo "   ADMIN_PASSWORD: ${ADMIN_PASSWORD:+***SET***}"
echo "   ADMIN_EMAIL: ${ADMIN_EMAIL:-Not set}"
echo ""

echo "======================================"
echo "🔧 RECOMMENDATION"
echo "======================================"
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings" ]; then
    echo "❌ DELETE DJANGO_SETTINGS_MODULE from Render Environment"
    echo "   Let Dockerfile set it to config.settings.production"
elif [ -z "$DATABASE_URL" ]; then
    echo "❌ ADD DATABASE_URL in Render Environment"
    echo "   Get it from PostgreSQL service → Internal Database URL"
else
    echo "✅ Environment looks good!"
fi
echo ""

echo "======================================"
echo "🐍 DJANGO CONFIGURATION TEST"
echo "======================================"
cd /doccano/backend
python -c "
import os
import sys

# Try to load Django settings
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    import django
    django.setup()
    from django.conf import settings
    
    print('✅ Django loaded successfully!')
    print('')
    print('Database Configuration:')
    print('  Engine:', settings.DATABASES['default']['ENGINE'])
    print('  Name:', settings.DATABASES['default']['NAME'])
    print('  Host:', settings.DATABASES['default']['HOST'][:30] + '...')
    print('  Port:', settings.DATABASES['default'].get('PORT', 5432))
    print('')
    print('✅ Database configuration looks good!')
    
except Exception as e:
    print('❌ Django failed to load!')
    print('Error:', str(e))
    print('')
    print('This usually means:')
    print('  1. DJANGO_SETTINGS_MODULE is set incorrectly')
    print('  2. DATABASE_URL is missing')
    sys.exit(1)
" 2>&1

echo ""
echo "======================================"
echo "Done! ✅"
echo "======================================"

