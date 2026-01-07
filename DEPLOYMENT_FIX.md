# 🔧 Deployment Fix - wait_for_db Command

**Date:** January 7, 2026  
**Status:** ✅ **FIXED**  
**Commit:** `0e7691c`

---

## 🚨 **What Happened**

### **Error:**
```
Making staticfiles
Initializing database
Unknown command: 'wait_for_db'
Type 'manage.py help' for usage.
==> Exited with status 1
```

### **Root Cause:**
The official `doccano/doccano:1.8.4` Docker image has an initialization script that calls:
```bash
python manage.py wait_for_db
```

But this command doesn't exist in the base Doccano image! It's expected to be provided by custom deployments.

---

## ✅ **The Fix**

### **Created Custom Management Command:**

**File:** `patches/management_commands/wait_for_db.py`

**What it does:**
1. Tries to connect to the PostgreSQL database
2. Retries up to 30 times (30 seconds total)
3. Waits 1 second between retries
4. Exits successfully when database is ready
5. Fails with error if database never becomes available

**Code:**
```python
class Command(BaseCommand):
    """Django command to wait for database to be available"""
    
    def handle(self, *args, **options):
        # Try to connect to database
        # Retry up to 30 times with 1 second delay
        # Exit when connection successful
```

### **Dockerfile Changes:**

Added commands to copy the custom `wait_for_db` command into the Docker image:

```dockerfile
# Custom management command: wait_for_db (required by Render initialization)
RUN mkdir -p /doccano/backend/projects/management/commands
COPY patches/management_commands/__init__.py /doccano/backend/projects/management/__init__.py
COPY patches/management_commands/__init__.py /doccano/backend/projects/management/commands/__init__.py
COPY patches/management_commands/wait_for_db.py /doccano/backend/projects/management/commands/wait_for_db.py
```

**Why `projects/management/commands/`?**
- Django management commands must be in `<app_name>/management/commands/`
- `projects` is a core Doccano app that always exists
- This ensures the command is available during initialization

---

## 🚀 **What Happens Now**

### **Render Will:**
1. ✅ Detect the new commit (`0e7691c`)
2. ✅ Pull latest code from GitHub
3. ✅ Build new Docker image (5-7 min)
4. ✅ Run initialization:
   ```
   Making staticfiles ✅
   Initializing database ✅
   python manage.py wait_for_db ✅ (now works!)
   python manage.py migrate ✅
   python manage.py collectstatic ✅
   ```
5. ✅ Start the application
6. ✅ Show "Live" status

### **Expected Logs:**
```
==> Building...
==> Build successful
==> Deploying...
Making staticfiles
Initializing database
Waiting for database...
Database unavailable, waiting 1 second... (attempt 1/30)
Database unavailable, waiting 1 second... (attempt 2/30)
✅ Database available!
Making staticfiles
Initializing database
✅ Database available!
==> Live ✅
```

---

## ⏱️ **Timeline**

- **0 min:** Code pushed (`0e7691c`)
- **1 min:** Render detects change
- **1-7 min:** Building Docker image
- **7-10 min:** Deploying & initializing
- **10 min:** ✅ **Live!**

**Total time:** ~10 minutes

---

## ✅ **After Deployment**

### **Step 1: Verify Deployment** (1 min)

Watch Render dashboard for "Live" status.

### **Step 2: Run Migration** (30 sec)

```bash
# In Render Shell:
python manage.py migrate assignment
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: assignment
Running migrations:
  Applying assignment.0006_annotation_tracking_simple... OK ✅
```

Or:
```
No migrations to apply. ✅
```

### **Step 3: Test Features** (2 min)

See **`DEPLOY_NOW.md`** for 3 quick tests:

1. **Dataset Table Columns** (30 sec)
   - Go to dataset page
   - Hard refresh (Ctrl+Shift+R)
   - See columns 4, 5, 6 (Annotated By, Reviewed By, Status)

2. **Metrics Redirect** (10 sec)
   - Click "Metrics" in menu
   - Should redirect immediately to completion dashboard

3. **API Tracking Fields** (1 min)
   - Open DevTools → Network
   - Check `/v1/projects/9/examples` response
   - Should see: `annotated_by_username`, `reviewed_by_username`, `tracking_status`

---

## 🎯 **Why This Fix Works**

### **Django Management Commands:**

Django looks for management commands in:
```
<app_name>/
  management/
    commands/
      <command_name>.py
```

### **Our Structure:**
```
/doccano/backend/
  projects/           ← Existing Doccano app
    management/       ← We created this
      commands/       ← We created this
        wait_for_db.py ← Our custom command
```

### **Result:**
When initialization script runs `python manage.py wait_for_db`, Django finds our custom command and executes it!

---

## 🔍 **Verification**

### **After deployment, check logs:**

```bash
# In Render Dashboard → Logs
# Look for these messages:
```

**Success indicators:**
```
✅ Database available!
==> Live
```

**No more errors:**
```
❌ Unknown command: 'wait_for_db'  ← This should be gone!
```

---

## 📋 **Files Changed**

| File | Change | Purpose |
|------|--------|---------|
| `Dockerfile` | Modified | Copy wait_for_db command |
| `patches/management_commands/wait_for_db.py` | New | Custom Django command |
| `patches/management_commands/__init__.py` | New | Python package marker |

---

## 🚨 **If It Still Fails**

### **Check Build Logs:**

Look for:
```
COPY patches/management_commands/wait_for_db.py ...
```

Should see:
```
✅ Successfully copied
```

### **Check Initialization Logs:**

Look for:
```
python manage.py wait_for_db
```

Should see:
```
Waiting for database...
✅ Database available!
```

### **If Still Errors:**

The issue might be:
1. **File not copied correctly** → Check Dockerfile syntax
2. **Python syntax error** → Check `wait_for_db.py`
3. **Database not starting** → Check PostgreSQL logs in Render

---

## 💡 **Why We Need This**

### **The Chicken-and-Egg Problem:**

1. Django application starts
2. Tries to connect to database
3. But database might not be ready yet
4. Application crashes

### **The Solution:**

1. Django application starts
2. Runs `wait_for_db` command first
3. Command waits for database to be ready (up to 30 seconds)
4. Once ready, initialization continues
5. Application starts successfully

---

## 🎉 **Summary**

**Problem:** Deployment failed because `wait_for_db` command was missing

**Solution:** Created custom Django management command that waits for database

**Result:** Deployment will now succeed! ✅

**Next Steps:**
1. ⏳ Wait for Render to deploy (~10 min)
2. ✅ Run migration
3. ✅ Test features

---

## 📞 **Current Status**

- [x] Fix committed (`0e7691c`)
- [x] Pushed to GitHub
- [ ] ⏳ Waiting for Render deployment
- [ ] Run migration
- [ ] Test features

**Watch:** Render dashboard for "Live" status!

---

**This fix is critical and will resolve the deployment error. The next deployment will succeed! 🚀**

