# 🔍 **Debug Migration Issue**

## Issue:
```
No migrations to apply.
Your models in app(s): 'assignment' have changes that are not yet reflected in a migration
```

## Run These Commands in Render Shell:

### **Step 1: Check Migration History**
```bash
python manage.py showmigrations assignment
```

**Expected output:**
```
assignment
 [X] 0001_initial
 [X] 0002_completion_tracking
 [X] 0003_example_locking
 [ ] 0005_annotation_tracking  ← Should be unchecked
```

### **Step 2: Check If Migration File Exists**
```bash
ls -la /doccano/backend/assignment/migrations/
```

**Expected output:**
```
0001_initial.py
0002_completion_tracking.py
0003_example_locking.py
0005_annotation_tracking.py  ← Should exist
```

### **Step 3: Check Migration File Content**
```bash
head -20 /doccano/backend/assignment/migrations/0005_annotation_tracking.py
```

**Should show:**
```python
dependencies = [
    ...
    ('assignment', '0003_example_locking'),
]
```

### **Step 4: Make Migrations (If Needed)**
```bash
python manage.py makemigrations assignment
```

**If it creates new migration:**
- Note the migration number
- Run `python manage.py migrate assignment`

---

## Possible Causes:

### **Cause 1: Migration File Not Copied**
- Dockerfile didn't copy migration to container
- Fix: Check if file exists in container

### **Cause 2: Migration Already Applied**
- Database already has the table
- Fix: Check with `\d annotation_tracking` in dbshell

### **Cause 3: Model Changed Since Migration**
- Models have additional changes
- Fix: Run `makemigrations` to create new one

---

## Please Run Step 1 First:

```bash
python manage.py showmigrations assignment
```

**Share the output with me!** 🔍

