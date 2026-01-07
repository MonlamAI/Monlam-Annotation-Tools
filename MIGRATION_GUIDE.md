# 🗄️ Database Migration Guide

## ⚠️ IMPORTANT: Migrations Must Be Run Manually!

Django migrations **DO NOT** run automatically. After deploying to Render, you **MUST** manually run migrations to update the PostgreSQL database schema.

---

## 📋 What Migrations Need to Run?

We created **3 migration files** that add new database tables and fields:

### **Migration 1: `0001_initial.py`**
**Creates:**
- ✅ `assignment_assignment` table
- ✅ `assignment_assignmentbatch` table

**What it does:**
- Creates the Assignment model (assigns examples to users)
- Creates the AssignmentBatch model (bulk assignments)

**Fields added:**
- `project`, `example`, `assigned_to`, `assigned_by`
- `status` (assigned/in_progress/submitted/approved/rejected)
- `assigned_at`, `completed_at`, etc.

---

### **Migration 2: `0002_completion_tracking.py`**
**Creates:**
- ✅ `assignment_annotatorcompletionstatus` table
- ✅ `assignment_approvercompletionstatus` table

**What it does:**
- Tracks per-example completion by annotators
- Tracks per-example approval by approvers

**Fields added:**
- Annotator completion status per example
- Approver approval status per example
- Review notes, timestamps, etc.

---

### **Migration 3: `0003_example_locking.py`** 🔒 **NEW!**
**Adds to `assignment_assignment` table:**
- ✅ `locked_by` column (Foreign Key to User)
- ✅ `locked_at` column (DateTime)

**What it does:**
- Enables example locking
- Prevents multiple annotators from editing same example simultaneously
- Tracks who locked the example and when

**SQL equivalent:**
```sql
ALTER TABLE assignment_assignment 
ADD COLUMN locked_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL;

ALTER TABLE assignment_assignment 
ADD COLUMN locked_at TIMESTAMP WITH TIME ZONE;
```

---

## 🚀 How to Run Migrations on Render

### **Step 1: Access Render Shell**

1. Go to Render Dashboard: https://dashboard.render.com/
2. Select your service: `monlam-doccano` (or whatever you named it)
3. Click **"Shell"** tab in the top navigation
4. Wait for shell to connect (30 seconds)

### **Step 2: Navigate to Backend Directory**

```bash
cd /doccano/backend
```

### **Step 3: Check Current Migration Status**

```bash
python manage.py showmigrations assignment
```

**Expected output:**
```
assignment
 [ ] 0001_initial
 [ ] 0002_completion_tracking
 [ ] 0003_example_locking
```

If you see `[X]` instead of `[ ]`, that migration is already applied.

### **Step 4: Run Migrations**

```bash
python manage.py migrate assignment
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: assignment
Running migrations:
  Applying assignment.0001_initial... OK
  Applying assignment.0002_completion_tracking... OK
  Applying assignment.0003_example_locking... OK
```

### **Step 5: Verify Migrations Applied**

```bash
python manage.py showmigrations assignment
```

**Expected output:**
```
assignment
 [X] 0001_initial
 [X] 0002_completion_tracking
 [X] 0003_example_locking
```

All should have `[X]` now!

---

## ✅ Success Indicators

After running migrations, you should see:

1. **No errors in Render logs**
2. **API endpoints work:**
   ```bash
   # Test in browser
   https://annotate.monlam.ai/v1/projects/9/assignments/
   
   # Should return data, not "relation does not exist" error
   ```

3. **Locking works:**
   - When annotator opens example, it locks
   - Other annotators can't access locked examples

---

## 🚨 Common Errors and Fixes

### **Error 1: `relation "assignment_assignment" does not exist`**

**Cause:** Migrations not run yet.

**Fix:**
```bash
python manage.py migrate assignment
```

---

### **Error 2: `Migration assignment.0001_initial is applied before its dependency`**

**Cause:** Migration order issue.

**Fix:**
```bash
# Run all migrations
python manage.py migrate
```

---

### **Error 3: `column "locked_by_id" of relation "assignment_assignment" does not exist`**

**Cause:** Migration 0003 not applied.

**Fix:**
```bash
python manage.py migrate assignment 0003
```

---

### **Error 4: `FATAL: password authentication failed`**

**Cause:** Database connection issue.

**Fix:** Check Render environment variables (DATABASE_URL).

---

## 📝 Migration Checklist

Use this checklist after each deployment:

- [ ] **Step 1:** Render deployment finished successfully
- [ ] **Step 2:** Access Render Shell
- [ ] **Step 3:** Run `cd /doccano/backend`
- [ ] **Step 4:** Run `python manage.py showmigrations assignment`
- [ ] **Step 5:** Run `python manage.py migrate assignment`
- [ ] **Step 6:** Verify all migrations have `[X]`
- [ ] **Step 7:** Test API endpoints (no "relation does not exist" errors)
- [ ] **Step 8:** Test locking feature
- [ ] **Step 9:** Clear CloudFlare cache (if using)

---

## 🔄 Why Migrations Don't Run Automatically

### **In Development (Local Docker):**
```dockerfile
# In Dockerfile
RUN python manage.py migrate  # ❌ Won't work - no database during build
```

**Problem:** Database doesn't exist during Docker image build.

**Solution:** Run migrations after container starts.

### **In Production (Render):**
```yaml
# In render.yaml
buildCommand: docker build -t myapp .
```

**Problem:** Build phase has no database access.

**Solution:** Run migrations manually in Shell after deployment.

---

## 🎯 Best Practices

### ✅ DO:
- Run migrations immediately after deployment
- Check migration status before and after
- Test API endpoints after migrations
- Keep migration files in version control (Git)
- Document what each migration does

### ❌ DON'T:
- Delete migration files
- Edit migration files after they're committed
- Skip migrations
- Run migrations on production without testing locally first
- Modify database schema directly with SQL (use migrations)

---

## 🧪 Testing Migrations Locally

Before deploying to production, test migrations locally:

```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# Access backend container
docker-compose exec backend bash

# Run migrations
cd /doccano/backend
python manage.py migrate assignment

# Check status
python manage.py showmigrations assignment
```

---

## 📚 Additional Resources

- **Django Migrations Docs:** https://docs.djangoproject.com/en/3.2/topics/migrations/
- **Our Migration Files:** `/patches/assignment/migrations/`
- **Assignment Models:** `/patches/assignment/models_separate.py`
- **Locking Documentation:** `/patches/assignment/EXAMPLE_VISIBILITY_AND_LOCKING.md`

---

## 🆘 Need Help?

If migrations fail:

1. **Check Render logs:**
   - Go to Render dashboard
   - Click "Logs" tab
   - Look for errors

2. **Check database connection:**
   ```bash
   python manage.py dbshell
   # Should connect to PostgreSQL
   \dt assignment_*
   # Should list assignment tables
   ```

3. **Try running all migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Check migration dependencies:**
   ```bash
   python manage.py showmigrations
   ```

---

## 📊 What Happens When You Run Migrations

```
Before Migration:
┌────────────────────────────────┐
│ PostgreSQL Database            │
├────────────────────────────────┤
│ ✅ examples_example            │
│ ✅ projects_project            │
│ ✅ auth_user                   │
│ ❌ assignment_assignment       │  <- MISSING!
│ ❌ assignment_*completion*     │  <- MISSING!
└────────────────────────────────┘

After Migration:
┌────────────────────────────────┐
│ PostgreSQL Database            │
├────────────────────────────────┤
│ ✅ examples_example            │
│ ✅ projects_project            │
│ ✅ auth_user                   │
│ ✅ assignment_assignment       │  <- CREATED!
│ ✅ assignment_annotatorcompletionstatus  <- CREATED!
│ ✅ assignment_approvercompletionstatus   <- CREATED!
│ ✅ assignment_assignmentbatch  │  <- CREATED!
└────────────────────────────────┘

Columns in assignment_assignment:
┌────────────────────────────────┐
│ id (PRIMARY KEY)               │
│ project_id (FOREIGN KEY)       │
│ example_id (FOREIGN KEY)       │
│ assigned_to_id (FOREIGN KEY)   │
│ assigned_by_id (FOREIGN KEY)   │
│ status (VARCHAR)               │
│ assigned_at (TIMESTAMP)        │
│ completed_at (TIMESTAMP)       │
│ is_active (BOOLEAN)            │
│ locked_by_id (FOREIGN KEY)     │  <- NEW in 0003!
│ locked_at (TIMESTAMP)          │  <- NEW in 0003!
└────────────────────────────────┘
```

---

## ⏱️ Timeline

```
1. Code change → Push to GitHub (Done ✅)
2. Render detects change → Rebuilds image (5-10 min)
3. Render deploys new image (2-3 min)
4. YOU run migrations manually ⚠️ (1 min)
5. Database updated → Features work! (Done ✅)
```

**Current Status:** Waiting for Step 4 (YOU need to run migrations)

---

## 🎯 Quick Command Reference

```bash
# Check migration status
python manage.py showmigrations assignment

# Run migrations
python manage.py migrate assignment

# Run specific migration
python manage.py migrate assignment 0003

# Rollback migration
python manage.py migrate assignment 0002

# Show SQL for migration (don't apply)
python manage.py sqlmigrate assignment 0003

# List all tables in database
python manage.py dbshell
\dt

# Check assignment tables specifically
\dt assignment_*
```

---

**Remember: Migrations = Schema Changes = Manual Step Required!** 🚨

**After every deployment with model changes, run migrations!**

---

**Version:** 1.0  
**Last Updated:** 2025-01-06



