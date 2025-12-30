# 🚀 Deployment Fix Guide - Audio Loop & Completion Matrix

## Overview
Two features weren't deployed yet:
1. ✅ **Audio Loop** - Code ready, needs deployment
2. ✅ **Completion Matrix** - Backend ready, API working, UI access needed

---

## ⚡ Quick Fix - Deploy in 5 Minutes

### Step 1: Verify Files Are in Repo

Check these files exist in your GitHub repo:

```bash
# Audio loop
git ls-files | grep "audio-loop-enhanced.js"
# Should show: patches/frontend/audio-loop-enhanced.js

# Assignment app
git ls-files | grep "patches/assignment"
# Should show multiple files in patches/assignment/

# Dockerfile updated
git diff main Dockerfile
# Should show new sections for audio loop and assignment
```

### Step 2: Update Dockerfile (Already Done! ✅)

Your Dockerfile now includes:
- ✅ Audio loop script copied to `/doccano/backend/client/dist/js/`
- ✅ Script tag injected into `index.html` and `200.html`
- ✅ Assignment app copied to `/doccano/backend/assignment/`
- ✅ Migrations will run automatically

### Step 3: Register URLs in Doccano

**Manual step required:** Add assignment URLs to Doccano's main `urls.py`

**File:** In your Doccano installation, find `backend/config/urls.py` or `backend/api/urls.py`

**Add this line:**

```python
from django.urls import path, include

urlpatterns = [
    # ... existing URLs ...
    
    # Monlam: Assignment and Completion Tracking
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
]
```

**Or create a patch file:**

```bash
# Create url patch
cat > patches/backend/urls_main.py << 'EOF'
# Add to the end of the main urls.py

from django.urls import path, include

# Monlam: Assignment and Completion Tracking
urlpatterns += [
    path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),
]
EOF

# Update Dockerfile to apply this patch
echo "COPY patches/backend/urls_main.py /doccano/backend/config/urls_patch.py" >> Dockerfile
echo "RUN cat /doccano/backend/config/urls_patch.py >> /doccano/backend/config/urls.py" >> Dockerfile
```

### Step 4: Commit and Push

```bash
cd /Users/tseringwangchuk/Documents/monlam-doccano

# Add all changes
git add Dockerfile patches/

# Commit
git commit -m "fix: Deploy audio loop and completion matrix

- Add audio loop script to static files
- Inject audio loop into index.html
- Include assignment app in Docker image
- Run migrations automatically
- Register assignment URLs

Fixes: Audio not looping, completion matrix not accessible"

# Push
git push origin main
```

### Step 5: Render Will Auto-Deploy

Render will automatically:
1. Detect the git push
2. Rebuild the Docker image with new Dockerfile
3. Deploy the new image
4. Run migrations (assignment tables created)
5. Start the service

**Estimated time:** 5-10 minutes

---

## 🧪 Verification After Deployment

### Test 1: Check Audio Loop

1. Go to STT annotation page
2. Open browser console (F12)
3. Look for:
   ```
   [Monlam] Enhanced Audio Loop Patch loaded
   [Monlam] Applied loop to X audio elements
   ```
4. Play audio
5. Verify it loops automatically ✅

### Test 2: Check Completion Matrix API

```bash
# Get your project ID (e.g., 1)
PROJECT_ID=1

# Test API endpoints
curl https://your-app.onrender.com/v1/projects/$PROJECT_ID/assignments/completion-matrix/summary/ \
  -H "Authorization: Token YOUR_TOKEN"
```

Should return JSON with completion statistics.

### Test 3: Check Database Tables

```bash
# SSH into Render (if you have access)
render ssh

# Check tables exist
python manage.py dbshell
\dt assignment_*

# Should show:
# assignment_assignment
# assignment_assignmentbatch
# assignment_annotatorcompletionstatus
# assignment_approvercompletionstatus
```

---

## 🎯 How to Access Completion Matrix

### Option 1: Direct API Call (Easiest)

Use Postman, Insomnia, or curl:

```bash
# Get auth token
TOKEN=$(curl -X POST https://your-app.onrender.com/v1/auth-token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}' \
  | jq -r '.token')

# Get completion matrix
curl https://your-app.onrender.com/v1/projects/1/assignments/completion-matrix/ \
  -H "Authorization: Token $TOKEN" \
  | jq
```

### Option 2: Browser Console

1. Log into Doccano
2. Go to any project page
3. Open console (F12)
4. Paste:

```javascript
fetch('/v1/projects/1/assignments/completion-matrix/summary/')
  .then(r => r.json())
  .then(data => {
    console.table(data.annotators);
    console.table(data.approvers);
  });
```

### Option 3: Custom Dashboard HTML (Future)

Copy the dashboard to static files:

```bash
# In Dockerfile, add:
COPY patches/frontend/completion-matrix.html /doccano/backend/client/dist/
```

Then access at:
```
https://your-app.onrender.com/completion-matrix.html
```

### Option 4: Integrate into Doccano Menu (Advanced)

This requires modifying Doccano's Vue.js frontend navigation - beyond scope of current patches.

---

## 📊 Available API Endpoints

After deployment, these endpoints will be available:

### Completion Matrix

```
GET /v1/projects/{project_id}/assignments/completion-matrix/
GET /v1/projects/{project_id}/assignments/completion-matrix/summary/
GET /v1/projects/{project_id}/assignments/completion-matrix/annotator/{user_id}/
GET /v1/projects/{project_id}/assignments/completion-matrix/approver/{user_id}/
```

### Comprehensive Examples

```
GET /v1/projects/{project_id}/assignments/comprehensive-examples/
GET /v1/projects/{project_id}/assignments/comprehensive-examples/export-csv/
```

### Assignments (existing)

```
GET /v1/projects/{project_id}/assignments/
POST /v1/projects/{project_id}/assignments/bulk-assign/
POST /v1/projects/{project_id}/assignments/{id}/start/
POST /v1/projects/{project_id}/assignments/{id}/submit/
POST /v1/projects/{project_id}/assignments/{id}/approve/
POST /v1/projects/{project_id}/assignments/{id}/reject/
```

---

## 🐛 Troubleshooting

### Issue: Audio Still Not Looping

**Check 1:** Is script loaded?
```javascript
// In browser console
window.MonlamAudioLoop
// Should return object with methods
```

**Check 2:** View page source
```
View → Developer → View Source
```
Look for:
```html
<script src="/js/audio-loop-enhanced.js"></script>
```

**Check 3:** Check network tab
```
F12 → Network → Reload page
Look for: audio-loop-enhanced.js (should be 200 OK)
```

**Fix:**
- Clear browser cache (Ctrl+Shift+R)
- Verify Render deployed new image (check build logs)
- SSH into Render and verify file exists:
  ```bash
  ls -la /doccano/backend/client/dist/js/audio-loop-enhanced.js
  ```

### Issue: Completion Matrix 404

**Check 1:** URLs registered?
```python
# SSH into Render
python manage.py show_urls | grep assignment
```

**Check 2:** App installed?
```python
# In Django shell
from django.apps import apps
apps.get_app_config('assignment')
```

**Fix:**
- Verify `INSTALLED_APPS += ['assignment']` in settings
- Verify URL patch was applied
- Rerun migrations: `python manage.py migrate assignment`

### Issue: Database Tables Don't Exist

```bash
# SSH into Render
python manage.py migrate assignment --plan

# If no migrations found:
python manage.py makemigrations assignment
python manage.py migrate assignment
```

---

## ✅ Final Checklist

Before considering deployment complete:

- [ ] Dockerfile updated with audio loop script
- [ ] Dockerfile updated with assignment app
- [ ] URLs registered in main urls.py
- [ ] Code pushed to GitHub
- [ ] Render build completed successfully
- [ ] Audio loops in STT projects
- [ ] Completion matrix API returns data
- [ ] Database tables exist
- [ ] No errors in Render logs

---

## 📝 Quick Commands Reference

```bash
# Check deployment status on Render
# (via Render dashboard)

# Test audio loop
# (open STT page, check F12 console)

# Test completion matrix API
curl https://your-app.onrender.com/v1/projects/1/assignments/completion-matrix/summary/ \
  -H "Authorization: Token YOUR_TOKEN"

# View Render logs
# (via Render dashboard → Logs)

# Restart Render service
# (via Render dashboard → Manual Deploy → Clear cache & deploy)
```

---

## 🎉 Success Criteria

You'll know it's working when:

1. **Audio Loop:**
   - Audio plays
   - Reaches end
   - Automatically restarts
   - Console shows "[Monlam] Applied loop to 1 audio elements"

2. **Completion Matrix:**
   - API returns JSON with completion stats
   - No 404 errors
   - Data reflects actual assignments

3. **No Errors:**
   - Render logs show no errors
   - Database migrations successful
   - Static files served correctly

---

## 🆘 Need Help?

If issues persist after deployment:

1. **Check Render build logs:**
   - Render Dashboard → Your Service → Logs → Build
   - Look for errors during Docker build

2. **Check Render runtime logs:**
   - Render Dashboard → Your Service → Logs → Runtime
   - Look for errors after deployment

3. **Verify files in deployment:**
   - SSH into Render (if you have shell access)
   - Check files exist:
     ```bash
     ls -la /doccano/backend/client/dist/js/audio-loop-enhanced.js
     ls -la /doccano/backend/assignment/
     ```

4. **Manual fixes:**
   - Add files manually via SSH
   - Restart service: `render restart`

---

## 📚 Documentation

- Audio Loop: `patches/frontend/AUDIO_LOOP_README.md`
- Completion Tracking: `patches/assignment/COMPLETION_TRACKING_README.md`
- Installation: `patches/assignment/INSTALLATION_GUIDE.md`
- Architecture: `patches/assignment/ARCHITECTURE.md`

---

**Last Updated:** December 30, 2025  
**Status:** Ready to deploy ✅

