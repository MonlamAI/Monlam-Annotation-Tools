# 🔍 Why Am I Not Seeing Changes? - Debug Checklist

## Quick Checks

### 1️⃣ Has Render Actually Deployed?

**Check Render Dashboard:**
- Go to: https://dashboard.render.com
- Find your service
- Look at **Events** tab
- Do you see "Deploy live" with today's timestamp?

**If NOT deployed yet:**
- ⏳ Wait 5-10 minutes for build to complete
- 🔄 Refresh Render dashboard
- Check "Logs" tab for build progress

**If build FAILED:**
- Check "Logs" for error messages
- Look for red error text
- Common issues:
  - Missing files
  - Syntax errors in Dockerfile
  - Migration failures

---

### 2️⃣ Clear Browser Cache

**Your browser might be showing OLD version:**

```bash
# Hard refresh (clears cache)
Windows/Linux: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

**Or completely clear cache:**
- Chrome: Settings → Privacy → Clear browsing data → Cached images and files
- Firefox: Settings → Privacy → Clear Data → Cached Web Content

---

### 3️⃣ Check Page Source

**View page source to verify scripts are injected:**

1. Go to your Doccano URL
2. Right-click → View Page Source
3. Search for (Ctrl+F): `enhance-members-progress.js`

**Should see:**
```html
<script src="/js/audio-loop-enhanced.js"></script>
<script src="/js/enhance-members-progress.js"></script>
<script src="/js/dataset-completion-columns.js"></script>
</body>
```

**If NOT there:**
- Dockerfile didn't run the sed command correctly
- Need to fix Dockerfile and redeploy

---

### 4️⃣ Check Browser Console

**Open Developer Tools (F12):**

1. Go to your Doccano site
2. Press `F12`
3. Click **Console** tab
4. Look for Monlam messages

**Should see:**
```
[Monlam] Enhanced Audio Loop Patch loaded
[Monlam] Enhanced Members Progress Patch loaded
[Monlam] Dataset Completion Columns Patch loaded
```

**If you see errors:**
- Red errors? → JavaScript syntax issue
- "Failed to fetch"? → API not available
- "404 Not Found"? → Scripts not copied correctly

---

### 5️⃣ Check Network Tab

**In Developer Tools (F12):**

1. Click **Network** tab
2. Reload page (F5)
3. Filter by "js"
4. Look for:
   - `enhance-members-progress.js`
   - `dataset-completion-columns.js`
   - `audio-loop-enhanced.js`

**Each should show:**
- Status: **200** ✅
- Size: ~15-20 KB

**If you see 404:**
- Scripts weren't copied to Docker image
- Check Render build logs
- Dockerfile copy commands may have failed

---

## 🔧 Detailed Diagnostics

### Test 1: Check if Scripts Are on Server

**If you have SSH access to Render:**

```bash
# SSH into your Render service
render ssh

# Check if JavaScript files exist
ls -la /doccano/backend/client/dist/js/

# Should see:
# enhance-members-progress.js
# dataset-completion-columns.js
# audio-loop-enhanced.js
```

**If files are MISSING:**
- Dockerfile COPY commands didn't work
- Files might not be in the right location in repo
- Need to fix Dockerfile

---

### Test 2: Check if index.html Was Modified

**SSH into Render:**

```bash
# Check if script tags were added
grep "enhance-members-progress" /doccano/backend/client/dist/index.html

# Should return the script tag line
```

**If NOT found:**
- The `sed` command in Dockerfile didn't run
- Need to fix the sed command

---

### Test 3: Check API Availability

**In browser console (F12):**

```javascript
// Test if completion API is available
fetch('/v1/projects/1/assignments/completion-matrix/summary/')
  .then(r => {
    console.log('API Status:', r.status);
    return r.json();
  })
  .then(data => console.log('API Data:', data))
  .catch(err => console.error('API Error:', err));
```

**Expected:** Status 200, data object
**If 404:** Assignment URLs not registered (see below)

---

## 🚨 Common Issues & Fixes

### Issue 1: Render Hasn't Deployed Yet

**Symptoms:**
- No "Deploy live" event in Render dashboard
- Build still in progress
- Old version still running

**Fix:**
- ⏳ **Wait!** Builds take 5-10 minutes
- Watch Render logs for progress
- Don't refresh the page until deploy completes

---

### Issue 2: Build Failed

**Symptoms:**
- "Build failed" in Render events
- Red errors in build logs
- Service not updating

**Common causes:**
- Syntax error in Dockerfile
- Missing files
- Migration errors

**Fix:**
```bash
# Check Render build logs for specific error
# Look for lines starting with "Error:" or "Failed:"
# Fix the specific issue and push again
```

---

### Issue 3: Scripts Not Copied

**Symptoms:**
- 404 errors for .js files in Network tab
- No console messages
- Features don't work

**Fix - Update Dockerfile:**

Check these lines exist in Dockerfile:
```dockerfile
# Copy UI enhancement scripts
COPY patches/frontend/enhance-members-progress.js /doccano/backend/client/dist/js/
COPY patches/frontend/dataset-completion-columns.js /doccano/backend/client/dist/js/
```

**If missing, add them and push again.**

---

### Issue 4: Scripts Not Injected into HTML

**Symptoms:**
- Scripts exist (200 in Network)
- But not loaded by page
- View Source doesn't show script tags

**Fix - Update Dockerfile:**

Check this line exists:
```dockerfile
RUN sed -i 's|</body>|  <script src="/js/enhance-members-progress.js"></script>\n  <script src="/js/dataset-completion-columns.js"></script>\n</body>|' /doccano/backend/client/dist/index.html
```

**If missing or wrong, fix and push again.**

---

### Issue 5: Assignment URLs Not Registered

**Symptoms:**
- Scripts load fine
- But API returns 404
- "Failed to fetch" in console

**Fix - Manual URL Registration:**

This requires editing Doccano's main `urls.py`:

**Option A: Add to Dockerfile (automated):**
```dockerfile
# Add at end of Dockerfile, before USER doccano
RUN echo "from django.urls import path, include" >> /doccano/backend/config/urls.py && \
    echo "urlpatterns += [path('v1/projects/<int:project_id>/assignments/', include('assignment.urls'))]" >> /doccano/backend/config/urls.py
```

**Option B: Manual edit (if SSH access):**
```bash
# SSH into Render
render ssh

# Edit urls.py
nano /doccano/backend/config/urls.py

# Add at bottom:
from django.urls import path, include
urlpatterns += [
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
]

# Restart service
```

---

## 🎯 Quick Diagnosis Script

**Paste this in browser console (F12) to diagnose:**

```javascript
console.log('🔍 Monlam Deployment Diagnostics\n');

// 1. Check if scripts are loaded
console.log('1. Scripts Loaded:');
console.log('   Audio Loop:', typeof window.MonlamAudioLoop !== 'undefined' ? '✅ Yes' : '❌ No');
console.log('   Members:', document.querySelector('.monlam-stats-button') ? '✅ Yes' : '❌ No');
console.log('   Dataset:', document.querySelector('.monlam-completion-cell') ? '✅ Yes' : '⚠️  Not on dataset page or not loaded');

// 2. Check script files
console.log('\n2. Script Files:');
['enhance-members-progress.js', 'dataset-completion-columns.js', 'audio-loop-enhanced.js'].forEach(script => {
    fetch(`/js/${script}`)
        .then(r => console.log(`   ${script}: ${r.status === 200 ? '✅ Found' : '❌ Missing ('+r.status+')'}`))
        .catch(() => console.log(`   ${script}: ❌ Error loading`));
});

// 3. Check API
console.log('\n3. API Endpoints:');
fetch('/v1/projects/1/assignments/completion-matrix/summary/')
    .then(r => console.log('   Completion Matrix:', r.status === 200 ? '✅ Working' : '❌ Not found ('+r.status+')'))
    .catch(() => console.log('   Completion Matrix: ❌ Error'));

// 4. Check current page
console.log('\n4. Current Page:', window.location.pathname);

console.log('\n✅ Diagnostics complete. Check results above.');
```

---

## 📋 Step-by-Step Troubleshooting

### Start Here:

**1. Check Render Dashboard**
- [ ] Is deployment complete? ("Deploy live" status)
- [ ] Any errors in Events tab?
- [ ] Check build logs for errors

**2. Clear Browser Cache**
- [ ] Hard refresh: Ctrl+Shift+R
- [ ] Or clear all cache in browser settings

**3. Check Page Source**
- [ ] View page source (right-click → View Source)
- [ ] Search for: `enhance-members-progress.js`
- [ ] Are script tags present?

**4. Check Browser Console**
- [ ] Press F12
- [ ] Go to Console tab
- [ ] Do you see "[Monlam] ..." messages?
- [ ] Any red errors?

**5. Check Network Tab**
- [ ] Press F12 → Network tab
- [ ] Reload page
- [ ] Are .js files loading (200 status)?

**6. Run Diagnostic Script**
- [ ] Copy script above
- [ ] Paste in console (F12)
- [ ] Check results

---

## 🆘 Still Not Working?

If you've tried everything above and it's still not working:

### Share This Info:

1. **Render Status:**
   - Screenshot of Render Events tab
   - Last 50 lines of build logs

2. **Browser Info:**
   - View Source → Is `enhance-members-progress.js` there?
   - Console (F12) → Any messages or errors?
   - Network tab → Status of .js files?

3. **Diagnostic Script Results:**
   - Run the script above
   - Share the console output

4. **Current Page:**
   - What URL are you on?
   - Members page or Dataset page?

---

## ✅ Success Indicators

You'll know it's working when:

### Console Shows:
```
[Monlam] Enhanced Audio Loop Patch loaded
[Monlam] Enhanced Members Progress Patch loaded
[Monlam] Dataset Completion Columns Patch loaded
```

### Network Tab Shows:
```
enhance-members-progress.js    200  ✅
dataset-completion-columns.js   200  ✅
audio-loop-enhanced.js          200  ✅
```

### Page Shows:
- Members page: Color-coded progress bars
- Dataset page: Two new columns with badges
- STT page: Audio loops automatically

---

**Start with Step 1 (Render Dashboard) and work through the checklist!**

