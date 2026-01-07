# 🔄 Database Migration Guide - After Changes

**Date:** January 7, 2026  
**Situation:** You made database changes while testing  
**Solution:** Clean migration strategy

---

## 🎯 **Two Scenarios**

### **Scenario A: Local Testing (Your Computer)**
You tried something locally and the database might be in an inconsistent state.

### **Scenario B: Production (Render)**
The production database on Render needs to be updated.

---

## 📋 **Option 1: Fresh Start (Recommended for Local)**

If you were just testing locally and can reset your local database:

### **Step 1: Check Current State**

```bash
cd /Users/tseringwangchuk/Documents/monlam-doccano

# Check what migrations Django thinks exist
# (This would need to be run in Docker, but we can check files locally)
ls -la patches/assignment/migrations/
```

**Current migrations:**
```
0001_initial.py
0002_completion_tracking.py
0003_example_locking.py
0006_annotation_tracking_simple.py  ← Current one
```

### **Step 2: Create Clean Migration (If Model Changed)**

```bash
# If you changed the model in simple_tracking.py, create new migration
# This needs to be run in Docker/Render environment:

python manage.py makemigrations assignment
```

**It will create:** `0007_<description>.py`

### **Step 3: Apply Migration**

```bash
python manage.py migrate assignment
```

---

## 📋 **Option 2: Fix Production Database (Render)**

If the production database on Render has issues:

### **Step 1: Check Migration Status on Render**

```bash
# In Render Shell:
python manage.py showmigrations assignment
```

**Expected output:**
```
assignment
 [X] 0001_initial
 [X] 0002_completion_tracking
 [X] 0003_example_locking
 [ ] 0006_annotation_tracking_simple  ← If not checked, needs to run
```

### **Step 2: Check if Table Exists**

```bash
# In Render Shell:
python manage.py dbshell
```

```sql
-- Check if table exists
\dt annotation_tracking

-- If it exists, check structure
\d annotation_tracking

-- Check for records
SELECT COUNT(*) FROM annotation_tracking;

-- Exit
\q
```

### **Step 3: Choose Fix Based on What You Find**

**Case A: Table exists, migration not marked**
```bash
# Fake the migration (tell Django it's already done)
python manage.py migrate assignment 0006_annotation_tracking_simple --fake
```

**Case B: Table doesn't exist**
```bash
# Run migration normally
python manage.py migrate assignment
```

**Case C: Table exists but columns are different**
```bash
# Option 1: Drop and recreate (⚠️ LOSES DATA)
python manage.py dbshell
DROP TABLE IF EXISTS annotation_tracking CASCADE;
\q

python manage.py migrate assignment

# Option 2: Manual ALTER (keeps data)
python manage.py dbshell
-- Add missing columns manually (see below)
\q

python manage.py migrate assignment 0006_annotation_tracking_simple --fake
```

---

## 🔧 **Manual Column Fixes**

If your table exists but is missing columns:

```sql
-- Connect to database
python manage.py dbshell

-- Check current columns
\d annotation_tracking

-- Add missing columns (if any)
ALTER TABLE annotation_tracking ADD COLUMN IF NOT EXISTS locked_by_id INTEGER;
ALTER TABLE annotation_tracking ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP;
ALTER TABLE annotation_tracking ADD COLUMN IF NOT EXISTS review_notes TEXT DEFAULT '';

-- Add foreign key constraints (if needed)
ALTER TABLE annotation_tracking 
  ADD CONSTRAINT annotation_tracking_locked_by_fkey 
  FOREIGN KEY (locked_by_id) 
  REFERENCES auth_user(id) 
  ON DELETE SET NULL;

-- Add indexes (if needed)
CREATE INDEX IF NOT EXISTS anno_track_locked_idx ON annotation_tracking(locked_by_id);

-- Verify
\d annotation_tracking

-- Exit
\q
```

Then fake the migration:
```bash
python manage.py migrate assignment 0006_annotation_tracking_simple --fake
```

---

## 🆕 **If You Changed the Model**

If you modified `patches/assignment/simple_tracking.py`:

### **Step 1: Create New Migration**

```bash
# This generates a new migration file
python manage.py makemigrations assignment --name "update_tracking_model"
```

**This creates:** `patches/assignment/migrations/0007_update_tracking_model.py`

### **Step 2: Review the Migration**

```bash
# Check what it will do
cat patches/assignment/migrations/0007_update_tracking_model.py
```

### **Step 3: Commit the New Migration**

```bash
git add patches/assignment/migrations/0007_update_tracking_model.py
git commit -m "Add migration for tracking model updates"
git push origin main
```

### **Step 4: Deploy & Run on Render**

After Render deploys:
```bash
# In Render Shell:
python manage.py migrate assignment
```

---

## ✅ **Verification Commands**

### **Check Migration Status**
```bash
python manage.py showmigrations assignment
```

**Should show:**
```
assignment
 [X] 0001_initial
 [X] 0002_completion_tracking
 [X] 0003_example_locking
 [X] 0006_annotation_tracking_simple
 [X] 0007_update_tracking_model  ← If you created new one
```

### **Check Table Structure**
```bash
python manage.py dbshell
```
```sql
\d annotation_tracking
```

**Should show:**
```
                                Table "public.annotation_tracking"
      Column      |           Type           | Nullable |           Default
------------------+--------------------------+----------+---------------------------
 id               | bigint                   | not null | nextval('...')
 annotated_at     | timestamp with time zone | yes      |
 reviewed_at      | timestamp with time zone | yes      |
 status           | character varying(20)    | not null | 'pending'
 review_notes     | text                     | not null | ''
 locked_at        | timestamp with time zone | yes      |
 annotated_by_id  | integer                  | yes      |
 example_id       | bigint                   | not null |
 locked_by_id     | integer                  | yes      |
 project_id       | bigint                   | not null |
 reviewed_by_id   | integer                  | yes      |
```

### **Check Indexes**
```sql
\di annotation_tracking*
```

**Should show:**
```
anno_track_proj_ex_idx       (project_id, example_id)
anno_track_proj_status_idx   (project_id, status)
anno_track_annotated_idx     (annotated_by_id)
anno_track_reviewed_idx      (reviewed_by_id)
anno_track_locked_idx        (locked_by_id)
```

### **Check Constraints**
```sql
SELECT conname FROM pg_constraint 
WHERE conrelid = 'annotation_tracking'::regclass;
```

**Should show:**
```
annotation_tracking_pkey
annotation_tracking_project_example_unique
annotation_tracking_annotated_by_fkey
annotation_tracking_example_fkey
annotation_tracking_locked_by_fkey
annotation_tracking_project_fkey
annotation_tracking_reviewed_by_fkey
```

---

## 🚨 **Common Issues**

### **Issue 1: "Table already exists"**

```
django.db.utils.ProgrammingError: relation "annotation_tracking" already exists
```

**Solution:**
```bash
python manage.py migrate assignment 0006_annotation_tracking_simple --fake
```

### **Issue 2: "Column already exists"**

```
django.db.utils.ProgrammingError: column "locked_by_id" of relation "annotation_tracking" already exists
```

**Solution:**
```bash
# Drop the failed migration from django_migrations
python manage.py dbshell
```
```sql
DELETE FROM django_migrations 
WHERE app = 'assignment' 
  AND name = '0007_update_tracking_model';
\q
```
```bash
# Then fake it
python manage.py migrate assignment 0007_update_tracking_model --fake
```

### **Issue 3: "Migration inconsistency"**

```
Migration assignment.0007_update_tracking_model is applied before its dependency
```

**Solution:**
```bash
# Reset migrations
python manage.py migrate assignment zero --fake
python manage.py migrate assignment --fake
```

---

## 🎯 **Recommended Path for Your Situation**

Since you mentioned you "changed it a little trying something else":

### **Path A: If You're Happy with Current Code**

1. **Check if model in `simple_tracking.py` matches migration `0006`** ✅ (I checked - they match!)
2. **On Render, just run:**
   ```bash
   python manage.py migrate assignment
   ```
3. **If it says "already applied" or table exists:**
   ```bash
   python manage.py migrate assignment 0006_annotation_tracking_simple --fake
   ```

### **Path B: If You Modified the Model**

1. **Commit your model changes** (if not already committed)
2. **Locally create migration:**
   ```bash
   # Would need to run in Docker environment
   python manage.py makemigrations assignment
   ```
3. **Commit new migration file**
4. **Deploy to Render**
5. **Run migration on Render:**
   ```bash
   python manage.py migrate assignment
   ```

---

## 📝 **Quick Reference**

| Command | Purpose |
|---------|---------|
| `showmigrations` | See what's applied |
| `migrate assignment` | Apply all pending |
| `migrate assignment 0006 --fake` | Mark as done without running |
| `makemigrations assignment` | Create new migration |
| `dbshell` | Access database SQL |
| `\d annotation_tracking` | Show table structure |
| `\di annotation_tracking*` | Show indexes |

---

## ✅ **Final Checklist**

After migration:
- [ ] Run `python manage.py showmigrations assignment` - All should be `[X]`
- [ ] Check table exists: `\dt annotation_tracking`
- [ ] Check columns match model: `\d annotation_tracking`
- [ ] Test API: `/v1/projects/9/examples` shows tracking fields
- [ ] Test frontend: Dataset table shows columns 4, 5, 6
- [ ] No errors in server logs

---

## 🆘 **Need Help?**

**Current Status Check:**
```bash
# Tell me the output of these commands:
python manage.py showmigrations assignment
python manage.py dbshell -c "\d annotation_tracking"
```

**I can help fix any migration issues!**

---

**Quick Start:** Just run `python manage.py migrate assignment` on Render and see what happens. If it errors, check this guide for the solution!

