# 🧪 **Testing Checklist After Render Deployment**

## ⏰ **Wait for Render Deployment**

1. Go to Render dashboard: https://dashboard.render.com/
2. Check build logs for your service
3. Wait for: **"Deploy succeeded"** ✅
4. Note the deployment time

---

## 🔍 **Test 1: As Approver or Project Manager**

### **Step 1: Enhanced Dataset Page**

1. Sign in as **Approver** or **Project Manager** (NOT Project Admin)
2. Go to your project: `https://annotate.monlam.ai/projects/9`
3. Click **གཞི་གྲངས། (Dataset)** in left menu

**Expected:**
- ✅ Automatically redirected to: `/monlam/9/dataset-enhanced/`
- ✅ See enhanced dataset table with status columns
- ✅ See "Annotate" buttons for each example

### **Step 2: Click Annotate Button**

1. Find an example in the table
2. Click the **"Annotate"** button

**Expected:**
- ✅ Navigate to: `/projects/9/speech-to-text?page=N`
- ✅ Page loads (not blank, not just buttons)

### **Step 3: Check Annotation Interface**

**Expected to SEE:**
- ✅ **Full Doccano interface** (header, toolbar, example list)
- ✅ **Audio player** with play/pause controls
- ✅ **Transcription text field** (if already transcribed)
- ✅ **Text input area** for annotation
- ✅ **Navigation buttons** (prev/next example)
- ✅ **Save button**

**Expected to HEAR:**
- ✅ Audio plays automatically
- ✅ Audio loops when it ends

**Should NOT see:**
- ❌ Only approve/reject buttons
- ❌ Buttons covering the interface
- ❌ Blank page

**Browser Console (Press F12):**
```
Expected logs:
✅ [Monlam Audio] Enabling audio loop...
✅ [Monlam Audio] Loop enabled

Should NOT see:
❌ [Monlam Approve] Buttons added
❌ [Monlam Approve] Failed after 20 attempts
```

### **Step 4: Annotate an Example**

1. Listen to the audio
2. Type transcription in the text field
3. Click **Save**

**Expected:**
- ✅ Annotation saves successfully
- ✅ Can navigate to next example
- ✅ Audio plays for next example

---

## 🔍 **Test 2: As Project Admin**

### **Step 1: Original Dataset Page**

1. Sign in as **Project Admin** (role_id = 3)
2. Go to your project: `https://annotate.monlam.ai/projects/9`
3. Click **གཞི་གྲངས། (Dataset)** in left menu

**Expected:**
- ✅ Stay on: `/projects/9/dataset?limit=10&offset=0` (original page)
- ✅ NOT redirected to `/monlam/9/dataset-enhanced/`
- ✅ See the standard Doccano dataset table

**Browser Console (Press F12):**
```
Expected logs:
✅ [Monlam] Project Admin detected. Skipping redirect for dataset.

Or no redirect happens at all (good!).
```

### **Step 2: Check Upload/Download Features**

1. Look for **"Upload"** button at top of page
2. Look for **"Download"** button
3. Look for **"Import"** or **"Export"** options

**Expected:**
- ✅ All buttons visible and clickable
- ✅ No ERROR 500
- ✅ Page loads completely

### **Step 3: Test Upload (Optional)**

1. Click **Upload** button
2. Try to upload a file (or just open the dialog)

**Expected:**
- ✅ Upload dialog opens
- ✅ No errors
- ✅ Can close dialog

---

## 🔍 **Test 3: Metrics Page (All Roles)**

### **Step 1: Click Metrics in Menu**

1. Sign in as **any role**
2. Go to your project
3. Click **གྲུབ་འབྲས། (Metrics)** in left menu

**Expected:**
- ✅ Automatically redirected to: `/monlam/9/completion/`
- ✅ See completion dashboard
- ✅ See "Back to Project" button

### **Step 2: Check Dashboard Content**

**Expected to see:**
- ✅ **Summary Section** (total examples, completed, approved, etc.)
- ✅ **Annotator Progress** (table with names and completion %)
- ✅ **Approver Progress** (table with review stats)
- ✅ **"Back to Project"** button at top
- ✅ **"Enhanced Dataset"** button at top

**Should NOT see:**
- ❌ "Could not load completion data"
- ❌ Empty tables
- ❌ 404 error

---

## 🔍 **Test 4: Navigation Flow**

### **Test Full Workflow:**

1. Start at **Project Dashboard**
2. Click **གཞི་གྲངས། (Dataset)** → Should go to enhanced view (non-admins)
3. Click **"Annotate"** on an example → Should show full annotation interface
4. Annotate and save
5. Click **"Back to Project"** button (if added)
6. Click **གྲུབ་འབྲས། (Metrics)** → Should go to completion dashboard
7. Check progress is updated

**Expected:**
- ✅ All navigation works smoothly
- ✅ No 404 errors
- ✅ No blank pages
- ✅ No 500 errors

---

## 🚨 **If Something Goes Wrong:**

### **Issue: Still See Only Approve Buttons**

**Check:**
1. Hard refresh page: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
2. Clear browser cache
3. Check browser console for errors
4. Check Render deployment succeeded

### **Issue: Project Admin Still Gets Redirected**

**Check:**
1. Confirm user has `role_id = 3` (Project Admin)
2. Check browser console: Does it say "Project Admin detected"?
3. Try in incognito/private window
4. Check Render logs for errors

### **Issue: Audio Doesn't Play**

**Check:**
1. S3 CORS settings (see `S3_CORS_FIX.md`)
2. Browser console for CORS errors
3. Check audio file URL is correct
4. Try opening audio URL directly in browser

### **Issue: 404 or 500 Errors**

**Check:**
1. Render deployment logs
2. Check if migrations ran: `python manage.py showmigrations`
3. Check Render shell: `python manage.py runserver` for errors
4. Send me the error logs

---

## ✅ **Success Criteria:**

After all tests pass, you should have:

```
✅ Enhanced Dataset Page
   - Shows for non-admins
   - Annotate button works
   - Status tracking visible

✅ Annotation Interface
   - FULL Doccano UI visible
   - NOT just approve buttons
   - Audio auto-loops
   - Can annotate and save

✅ Project Admin Access
   - Original dataset page loads
   - Upload/Download available
   - No 500 errors

✅ Metrics Dashboard
   - Completion stats show
   - Per-user progress visible
   - No loading errors

✅ Navigation
   - Menu clicks work
   - Back buttons work
   - No redirects for admins
   - Redirects for non-admins
```

---

## 📸 **Take Screenshots:**

If possible, take screenshots of:

1. Enhanced dataset page (showing status columns)
2. Annotation interface (showing FULL UI, not just buttons)
3. Project Admin's original dataset page (with upload/download)
4. Completion dashboard (with stats)

This will help me verify everything works! 📷

---

**Test all scenarios and report back!** 🚀



