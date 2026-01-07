# 🗄️ Database Reset & Setup Commands

## 🎯 **Use Case**
You deleted everything in PostgreSQL or need to start fresh.

---

## 📍 **Step 1: Wait for Deployment** ⏳

First, let commit `d84fc37` deploy successfully. Watch for:
```
✅ 🔍 DATABASE_URL: postgres://...
✅ 🐍 Django Settings: config.settings.production
✅ Running migrations...
```

If you still see "settings.DATABASES is improperly configured", go to **Emergency Fix** below.

---

## 📍 **Step 2: Access Render Shell** 🖥️

1. Go to Render Dashboard → Your Web Service
2. Click **Shell** tab (top right)
3. Wait for shell to connect

---

## 📍 **Step 3: Reset Database (Option A - Complete Wipe)** 💣

**⚠️ WARNING: This DELETES EVERYTHING in the database!**

```bash
# In Render Shell:
cd /doccano/backend

# Drop ALL tables (including django_migrations)
python manage.py dbshell << 'EOF'
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    -- Drop all tables
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    -- Drop all sequences
    FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
    END LOOP;
END $$;
EOF

echo "✅ All tables dropped!"
```

---

## 📍 **Step 4: Run Fresh Migrations** 🔄

```bash
# In Render Shell (after Step 3):
cd /doccano/backend

# Run all migrations from scratch
python manage.py migrate --noinput

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, assignment, auth, contenttypes, ...
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
#   Applying assignment.0003_example_locking... OK
#   Applying assignment.0006_annotation_tracking_simple... OK
#   ...

echo "✅ Migrations complete!"
```

---

## 📍 **Step 5: Create Admin User** 👤

```bash
# In Render Shell:
cd /doccano/backend

python manage.py create_admin \
  --username admin \
  --password MonlamAI2024 \
  --email admin@monlam.ai \
  --noinput

# If command not found, use createsuperuser:
python manage.py createsuperuser \
  --username admin \
  --email admin@monlam.ai \
  --noinput

# Then set password manually:
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
u = User.objects.get(username='admin');
u.set_password('MonlamAI2024');
u.save();
print('✅ Admin password set!')
"
```

---

## 📍 **Step 6: Verify Database** ✅

```bash
# In Render Shell:
cd /doccano/backend

# Check migrations applied:
python manage.py showmigrations

# Should show [X] for all migrations:
# assignment
#  [X] 0001_initial
#  [X] 0002_alter_example_assignment
#  [X] 0003_example_locking
#  [X] 0006_annotation_tracking_simple
# ...

# Check tables exist:
python manage.py dbshell -c "\dt"

# Should show:
#   public | annotation_tracking | table | ...
#   public | assignment_example  | table | ...
#   public | auth_user           | table | ...
#   ...

echo "✅ Database verified!"
```

---

## 🚨 **Emergency Fix: DATABASE_URL Still Not Working**

If deployment still fails with database error:

### **Option 1: Check Environment Variables**
```bash
# In Render Shell:
env | grep DATABASE

# Should show:
# DATABASE_URL=postgres://user:pass@host:5432/dbname
```

If missing, go to Render Dashboard → Environment → Add `DATABASE_URL`

### **Option 2: Manually Set in Dockerfile**
```dockerfile
# Add before CMD:
ENV DATABASE_URL=${DATABASE_URL}
```

### **Option 3: Check Render Database Connection**
1. Render Dashboard → PostgreSQL Database
2. Check **Status** = "Available"
3. Copy **Internal Database URL**
4. Paste into Web Service → Environment → `DATABASE_URL`

---

## 📍 **Step 7: Test the Application** 🧪

```bash
# After everything is set up:

# 1. Visit: https://annotate.monlam.ai
# 2. Login with admin credentials
# 3. Create a test project
# 4. Upload some examples
# 5. Check dataset table for custom columns
```

---

## 🔄 **Alternative: Reset Just One App (assignment)**

If you only want to reset the `assignment` app:

```bash
# In Render Shell:
cd /doccano/backend

# Drop assignment tables only:
python manage.py dbshell << 'EOF'
DROP TABLE IF EXISTS annotation_tracking CASCADE;
DROP TABLE IF EXISTS assignment_example CASCADE;
DROP TABLE IF EXISTS assignment_assignment CASCADE;
-- Add any other assignment tables
EOF

# Remove assignment migrations from django_migrations:
python manage.py dbshell << 'EOF'
DELETE FROM django_migrations WHERE app = 'assignment';
EOF

# Re-run assignment migrations:
python manage.py migrate assignment --fake-initial

echo "✅ Assignment app reset!"
```

---

## 📊 **Summary of Commands**

| Action | Command |
|--------|---------|
| **Access Shell** | Render Dashboard → Shell |
| **Drop All Tables** | `python manage.py dbshell` + SQL |
| **Run Migrations** | `python manage.py migrate --noinput` |
| **Create Admin** | `python manage.py create_admin ...` |
| **Verify DB** | `python manage.py showmigrations` |
| **Check Tables** | `python manage.py dbshell -c "\dt"` |

---

## ✅ **After Database Reset**

Your database will have:
- ✅ All Django core tables (auth, contenttypes, etc.)
- ✅ Doccano tables (projects, examples, labels, etc.)
- ✅ Custom assignment tables (assignment_example, annotation_tracking)
- ✅ Admin user ready to login

---

## 🆘 **If You Get Stuck**

Run this diagnostic command:
```bash
# In Render Shell:
cd /doccano/backend
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()
from django.conf import settings
print('✅ Database Engine:', settings.DATABASES['default']['ENGINE'])
print('✅ Database Name:', settings.DATABASES['default']['NAME'])
print('✅ Database Host:', settings.DATABASES['default']['HOST'])
"
```

This will show if Django can read the database configuration.

---

**Created:** 2026-01-07  
**Commit:** `d84fc37`  
**Status:** Ready to use after deployment ✅

