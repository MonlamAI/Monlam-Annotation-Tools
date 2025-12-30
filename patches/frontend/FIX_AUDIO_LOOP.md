# Fix: Audio Not Playing in Loop

## Issue
Audio in STT projects is not looping after deploying to Render.

## Root Cause
The `audio-loop-enhanced.js` script hasn't been deployed yet. It needs to be:
1. Copied to the static directory
2. Added to index.html
3. Doccano restarted

---

## Solution 1: Deploy via Dockerfile (Recommended for Render)

### Update Your Dockerfile

Add these lines to your Dockerfile to include the audio loop script:

```dockerfile
# ... existing Dockerfile content ...

# Copy Monlam patches
COPY patches/ /patches/

# Copy audio loop script to static directory
RUN cp /patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/ || true

# ... rest of Dockerfile ...
```

### Update index.html in Dockerfile

Add this to copy the modified index.html:

```dockerfile
# Modify index.html to include audio loop script
RUN sed -i 's|</body>|<script src="/js/audio-loop-enhanced.js"></script>\n</body>|' \
    /doccano/backend/client/dist/index.html || true
```

### Full Dockerfile Example

```dockerfile
FROM doccano/doccano:latest

# Copy Monlam customizations
COPY branding/ /doccano/branding/
COPY patches/ /doccano/patches/

# Install audio loop script
COPY patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/

# Add audio loop script to index.html
RUN sed -i 's|</body>|<script src="/js/audio-loop-enhanced.js"></script>\n</body>|' \
    /doccano/backend/client/dist/index.html

# Apply other patches
# ... your existing patch commands ...

# Run migrations
RUN python manage.py migrate assignment || true

CMD ["doccano"]
```

---

## Solution 2: Manual Deployment (SSH into Render)

If you have SSH access to your Render instance:

```bash
# SSH into Render
render ssh

# Copy audio loop script
cp /app/patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/

# Update index.html
cat >> /doccano/backend/client/dist/index.html << 'EOF'
<script src="/js/audio-loop-enhanced.js"></script>
EOF

# Restart the service
exit
# Then restart from Render dashboard
```

---

## Solution 3: Add to render.yaml

Update your `render.yaml` to include build commands:

```yaml
services:
  - type: web
    name: monlam-doccano
    env: docker
    
    # Add pre-deploy script
    preDeployCommand: |
      cp patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/
      sed -i 's|</body>|<script src="/js/audio-loop-enhanced.js"></script>\n</body>|' /doccano/backend/client/dist/index.html
    
    # ... rest of config ...
```

---

## Solution 4: Include in Git (Easiest)

Create a patched version of index.html in your repo:

```bash
# Create patches/frontend/index-with-audio-loop.html
cat > patches/frontend/index-with-audio-loop.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <!-- Doccano's existing head -->
</head>
<body>
    <div id="app"></div>
    
    <!-- Monlam: Audio Loop -->
    <script src="/js/audio-loop-enhanced.js"></script>
    
    <!-- Doccano's existing scripts -->
</body>
</html>
EOF
```

Then in Dockerfile:
```dockerfile
COPY patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/
COPY patches/frontend/index-with-audio-loop.html /doccano/backend/client/dist/index.html
```

---

## Quick Test: Manual Script Injection

**For immediate testing, add script via browser console:**

```javascript
// Open browser console (F12) on STT annotation page
const script = document.createElement('script');
script.src = 'https://raw.githubusercontent.com/MonlamAI/Monlam-Annotation-Tools/main/patches/frontend/audio-loop-enhanced.js';
document.body.appendChild(script);
```

Or paste the entire script content directly:

```javascript
// Copy entire content of audio-loop-enhanced.js
// Paste into browser console
// Audio should start looping immediately
```

---

## Verification

After deployment, verify audio loop is working:

### 1. Check Script is Loaded
```javascript
// In browser console (F12)
window.MonlamAudioLoop
// Should return: {enabled: ƒ, toggle: ƒ, enable: ƒ, ...}
```

### 2. Check for Console Messages
Look for in console:
```
[Monlam] Enhanced Audio Loop Patch loaded
[Monlam] Initializing Enhanced Audio Loop Patch...
[Monlam] Applied loop to 1 audio elements
```

### 3. Check Audio Element
```javascript
// In console
document.querySelector('audio').loop
// Should return: true
```

### 4. Manual Test
- Play audio
- Let it reach the end
- Should automatically restart ✅

---

## Troubleshooting

### Audio Still Not Looping?

**Check 1: Is script loaded?**
```javascript
console.log(window.MonlamAudioLoop);
```
If undefined → Script not loaded, check Dockerfile

**Check 2: Are there audio elements?**
```javascript
console.log(document.querySelectorAll('audio').length);
```
If 0 → You're not on an STT page

**Check 3: Check loop attribute**
```javascript
document.querySelector('audio').loop
```
If false → Script didn't run, check for errors

**Check 4: Manually enable**
```javascript
window.MonlamAudioLoop.enable();
```

### Script Loads but Doesn't Work?

**Clear Browser Cache:**
```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

**Check for JavaScript Errors:**
Open console (F12), look for red errors

**Try Basic Version:**
Use `audio-loop-patch.js` instead of enhanced version

---

## Files to Update

### 1. Update Dockerfile
```dockerfile
# Add these lines
COPY patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/
RUN sed -i 's|</body>|<script src="/js/audio-loop-enhanced.js"></script>\n</body>|' \
    /doccano/backend/client/dist/index.html
```

### 2. Rebuild Docker Image
```bash
docker build -t monlam-doccano .
```

### 3. Push to Render
```bash
git add Dockerfile
git commit -m "fix: Add audio loop script to Dockerfile"
git push origin main
```

Render will automatically rebuild and deploy!

---

## Summary

**The audio loop code is working** - it just needs to be deployed:

1. ✅ Code is in repo: `patches/frontend/audio-loop-enhanced.js`
2. ❌ Not copied to static directory yet
3. ❌ Not added to index.html yet
4. ❌ Render hasn't deployed it yet

**Fix:** Update Dockerfile to copy the script and modify index.html, then push to trigger Render rebuild.

**Estimated Time:** 5 minutes to update Dockerfile, 5-10 minutes for Render to rebuild.

