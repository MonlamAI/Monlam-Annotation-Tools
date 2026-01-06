# 🔧 Migration Fix Guide - Model Changes Detected

## ⚠️ Current Issue

```
Your models in app(s): 'assignment' have changes that are not yet reflected in a migration
```

This means there are model changes that need new migration files.

---

## ✅ **Solution: Create & Apply Migrations**

Run these commands in **Render Shell**:

```bash
# Step 1: Navigate to backend
cd /doccano/backend

# Step 2: Create new migrations (if model changes exist)
python manage.py makemigrations assignment

# Step 3: Apply all migrations
python manage.py migrate assignment

# Step 4: Verify all migrations are applied
python manage.py showmigrations assignment
```

---

## 📋 **Expected Output:**

### **After makemigrations:**

```
Migrations for 'assignment':
  assignment/migrations/0004_XXXXX.py
    - Add field reviewed_by_role to assignment
    OR
    - (whatever changes were detected)
```

### **After migrate:**

```
Operations to perform:
  Apply all migrations: assignment
Running migrations:
  Applying assignment.0004_XXXXX... OK
```

### **After showmigrations:**

```
assignment
 [X] 0001_initial
 [X] 0002_completion_tracking
 [X] 0003_example_locking
 [X] 0004_XXXXX (NEW)
```

All should have `[X]` (applied).

---

## 🔍 **What If No New Migrations Are Created?**

If `makemigrations` says:

```
No changes detected
```

But `migrate` still complains, then run:

```bash
# Force recreate migrations
python manage.py makemigrations assignment --empty

# Or check migration state
python manage.py showmigrations assignment
```

---

## 🚨 **Alternative: Fake the Migration**

If the models haven't actually changed (false positive):

```bash
# Mark current state as migrated
python manage.py migrate assignment --fake

# Verify
python manage.py showmigrations assignment
```

**⚠️ Only use `--fake` if you're SURE the database already matches the models!**

---

## ✅ **Full Command Sequence**

Copy-paste this entire block:

```bash
cd /doccano/backend
python manage.py makemigrations assignment
python manage.py migrate assignment
python manage.py showmigrations assignment
echo "✅ Migrations complete!"
```

---

## 📊 **After Migrations Complete**

Then test the menu redirects:

1. Go to: https://annotate.monlam.ai
2. Sign in
3. Click project
4. Click "གཞི་གྲངས།" (Dataset) in left menu
5. Should redirect to `/monlam/9/dataset-enhanced/`
6. Should see enhanced dataset view

---

## 🆘 **If Errors Occur**

**Error: "No such table: assignment_assignment"**
- Solution: Database needs to be created from scratch
- Run: `python manage.py migrate --run-syncdb`

**Error: "Column already exists"**
- Solution: Migration is trying to add existing column
- Run: `python manage.py migrate assignment --fake`

**Error: "Can't locate migration"**
- Solution: Migration files missing
- Check: `ls /doccano/backend/assignment/migrations/`
- Should see: `0001_initial.py`, `0002_*.py`, `0003_*.py`

---

## 📝 **What to Do Now**

**Run this command block in Render Shell:**

```bash
cd /doccano/backend
python manage.py makemigrations assignment
python manage.py migrate assignment
python manage.py showmigrations assignment
```

**Then paste the output here so I can verify!**

