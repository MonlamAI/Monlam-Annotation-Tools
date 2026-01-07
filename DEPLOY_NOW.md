# 🚀 DEPLOY NOW - Quick Guide

**Status:** ✅ **Ready for Deployment**  
**Commit:** `12bdf90` - Vue.js Expert Fixes  
**Date:** January 7, 2026

---

## 📦 **What's Being Deployed**

### **Frontend Fixes (JavaScript):**
1. ✅ **Dataset Table Enhancement** - Proper field names, no duplicates, Vue-aware
2. ✅ **Metrics Redirect** - Works on first click, Vue Router intercepted

### **Backend Enhancements:**
1. ✅ **Tracking Fields in API** - `annotated_by_username`, `reviewed_by_username`, `tracking_status`
2. ✅ **Visibility Filtering** - Server-side DRF filter (automatic)
3. ✅ **Auto-Tracking** - Django signals (automatic)

### **What's NOT Changed:**
- ✅ Audio auto-loop (still working)
- ✅ Approve/reject buttons (still working)
- ✅ Existing Doccano features (untouched)

---

## 🎯 **Deployment Steps**

### **1. Render Will Auto-Deploy** (5-10 min)

Render is watching your `main` branch. After the push, it will:
1. Pull latest code
2. Build Docker image
3. Deploy new version
4. Show "Live" status

**Watch:** https://dashboard.render.com → Your service

---

### **2. Wait for "Live" Status**

**Expected logs:**
```
==> Building...
==> Copying patches/backend/serializers.py
==> Copying patches/frontend/index.html
==> Copying patches/monlam_tracking
==> Build complete
==> Deploying...
==> Live ✅
```

---

### **3. Run Migration (Optional but Recommended)**

**Why?** Creates the `annotation_tracking` table for full tracking features.

**In Render Shell:**
```bash
python manage.py migrate assignment --noinput
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: assignment
Running migrations:
  Applying assignment.0006_annotation_tracking_simple... OK ✅
```

**Note:** If table already exists, you'll see:
```
No migrations to apply. ✅
```

---

## ✅ **Post-Deployment Testing**

### **Test 1: Dataset Table Columns** (30 seconds)

**Steps:**
1. Go to any project → Dataset
2. Hard refresh: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)
3. Wait 1-2 seconds

**Expected:**
```
Column 1: [Checkbox]
Column 2: ID
Column 3: Text/Audio
Column 4: Annotated By  ← NEW (shows username or "—")
Column 5: Reviewed By   ← NEW (shows username or "—")
Column 6: Status        ← NEW (colored badge)
Column 7+: Other columns (shifted right)
```

**✅ PASS if:** Columns appear at positions 4, 5, 6 with correct data

**❌ FAIL if:** Columns missing, duplicated, or misaligned

---

### **Test 2: Metrics Redirect** (10 seconds)

**Steps:**
1. Open any project
2. Click "Metrics" (གཞི་གྲངས།) in left menu

**Expected:**
- **Immediate** redirect to `/monlam/{id}/completion/`
- No loading delay
- Completion dashboard appears

**✅ PASS if:** Redirects on first click without refresh

**❌ FAIL if:** Shows old metrics page or requires refresh

---

### **Test 3: API Tracking Fields** (1 minute)

**Steps:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Go to dataset page
4. Find request: `/v1/projects/9/examples?limit=10`
5. Click on it → Preview/Response

**Expected JSON:**
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "text": "སངས་རྒྱས།",
      "annotated_by_username": "john",    ← Should exist
      "reviewed_by_username": null,       ← Should exist
      "tracking_status": "submitted",     ← Should exist
      ...
    }
  ]
}
```

**✅ PASS if:** All three fields exist in response

**❌ FAIL if:** Fields missing or API error

---

## 🐛 **Troubleshooting**

### **Issue: Columns don't appear**

**Solution:**
1. Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
2. Clear browser cache
3. Check console for `[Monlam Dataset]` logs
4. Try incognito/private window

### **Issue: Metrics redirect loops**

**Solution:**
1. Clear browser cache and cookies
2. Try different browser
3. Check console for `[Monlam Metrics]` logs

### **Issue: API returns null for tracking fields**

**Solution:**
1. Run migration: `python manage.py migrate assignment`
2. Check database: `\d annotation_tracking` in psql
3. Restart Django server (Render will auto-restart)

### **Issue: "Table already exists" error**

**Solution:**
```bash
# This is OK! It means table was created before
# Just fake the migration:
python manage.py migrate assignment 0006_annotation_tracking_simple --fake
```

---

## 📊 **Expected Console Logs**

### **Browser Console (F12):**

**On Dataset Page:**
```
[Monlam] 🚀 Initializing features...
[Monlam Dataset] ✨ Starting table enhancement for project 9
[Monlam Dataset] ✅ Loaded 100 tracking records
[Monlam Dataset] ✅ Headers inserted at positions 4, 5, 6
[Monlam Dataset] ✅ Enhanced 10 rows
[Monlam Dataset] ✅ Enhancement complete after 2 attempts
```

**On Metrics Click:**
```
[Monlam Metrics] Setting up redirect interception...
[Monlam Metrics] ✅ Redirect system initialized
[Monlam Metrics] ⚡ Click intercepted, redirecting to: /monlam/9/completion/
```

### **Server Logs (Render):**

**On Startup:**
```
[Monlam Tracking] App initializing...
[Monlam Tracking] ✅ Visibility filter registered
[Monlam Signals] ✅ Connected tracking for Category
[Monlam Signals] ✅ Connected tracking for Span
[Monlam Signals] ✅ Connected tracking for TextLabel
[Monlam Tracking] ✅ Auto-tracking signals connected
```

---

## 🎉 **Success Indicators**

**You'll know it's working when:**

✅ **Dataset table** shows 3 new columns at positions 4, 5, 6  
✅ **Metrics redirect** works on first click  
✅ **API response** includes tracking fields  
✅ **Console logs** show successful initialization  
✅ **No errors** in browser console or server logs  

---

## 🔍 **Verification Commands**

### **Check Migration Status:**
```bash
python manage.py showmigrations assignment
```

**Expected:**
```
assignment
 [X] 0001_initial
 [X] 0002_completion_tracking
 [X] 0003_example_locking
 [X] 0006_annotation_tracking_simple  ← This should be [X]
```

### **Check Table Exists:**
```bash
python manage.py dbshell
```
```sql
\d annotation_tracking

-- Should show table structure with columns:
-- id, project_id, example_id, annotated_by_id, reviewed_by_id, status, etc.
```

### **Check Tracking Records:**
```sql
SELECT COUNT(*) FROM annotation_tracking;

-- Should show number of tracking records
-- (0 if fresh install, >0 if data exists)
```

---

## 📞 **If Something Breaks**

### **Rollback Plan:**

**Option 1: Rollback to previous commit**
```bash
# In Render Dashboard:
# 1. Go to "Manual Deploy"
# 2. Select commit: 3b9b625 (before Vue fixes)
# 3. Click "Deploy"
```

**Option 2: Quick fix**
```bash
# If specific feature is broken, disable it:
# Edit index.html and comment out the problematic function
```

### **Get Help:**

1. **Check VUE_EXPERT_FIXES.md** - Comprehensive troubleshooting
2. **Check console logs** - Browser + Server
3. **Check database** - Migration status, table structure
4. **Share error logs** - Post in support channel

---

## 🎯 **Next Steps After Deployment**

1. ✅ Test all 3 features (dataset, metrics, API)
2. ✅ Monitor console logs for errors
3. ✅ Check server performance (should be same as before)
4. ✅ Have users test workflow
5. ✅ Monitor for issues over 24-48 hours

---

## 📝 **Deployment Checklist**

- [ ] Code pushed to GitHub ✅ (commit `12bdf90`)
- [ ] Render shows "Live" status
- [ ] Migration run (if needed)
- [ ] Test 1: Dataset table columns
- [ ] Test 2: Metrics redirect
- [ ] Test 3: API tracking fields
- [ ] Console logs check
- [ ] No errors reported
- [ ] Users can annotate normally
- [ ] Audio loop still works
- [ ] Approve/reject buttons still work

---

## ✨ **What Makes This Deployment Safe**

1. **Backward Compatible** - Works with or without migration
2. **Graceful Degradation** - Features fail silently if not ready
3. **No Breaking Changes** - Existing features untouched
4. **Error Handling** - Try/except everywhere
5. **Rollback Ready** - Can revert to previous commit anytime

---

**🚀 Ready to deploy! Just wait for Render to finish, then test!**

**⏱️ Expected deployment time: 5-10 minutes**

**✅ Expected result: All features working smoothly!**

---

**Document Version:** 1.0  
**Deployment Commit:** `12bdf90`  
**Last Updated:** January 7, 2026  
**Status:** Production-ready ✅
