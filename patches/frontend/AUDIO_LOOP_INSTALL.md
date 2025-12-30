# Quick Install: Audio Loop for STT Projects

## ⚡ Fast Installation (2 minutes)

### Step 1: Copy the Script

```bash
# Copy the enhanced version (recommended)
cp patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/
```

### Step 2: Add to HTML

Edit `/doccano/backend/client/dist/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <!-- existing head -->
</head>
<body>
    <div id="app"></div>
    
    <!-- ADD THIS LINE -->
    <script src="/js/audio-loop-enhanced.js"></script>
    
    <!-- existing scripts -->
</body>
</html>
```

### Step 3: Restart Doccano

```bash
# If using Docker
docker-compose restart

# If using systemd
sudo systemctl restart doccano
```

Done! 🎉

## ✨ What You Get

- ✅ Audio automatically loops by default
- ✅ Press **L** key to toggle loop on/off
- ✅ Status indicator in top-right corner
- ✅ Per-audio toggle buttons
- ✅ Preference saved across sessions
- ✅ Keep all existing play/stop controls

## 🎮 How to Use

1. **Open any STT annotation page**
   - Audio will auto-loop by default

2. **Toggle loop:**
   - Press **L** key, or
   - Click the status indicator (top-right), or
   - Click the toggle button next to audio player

3. **Your preference is remembered**
   - Saved in browser
   - Persists across sessions

## 🔧 Verify Installation

1. Open browser console (F12)
2. Look for: `[Monlam] Enhanced Audio Loop Patch loaded`
3. Should see: `[Monlam] Loop is currently ENABLED`

## 📝 Notes

- Works with existing controls (play, pause, stop)
- Doesn't break any functionality
- Can be removed anytime by removing the script tag
- Each user's preference is independent

## 🎯 Alternative: Basic Version

If you want simple auto-loop without UI controls:

```bash
# Use the basic version instead
cp patches/frontend/audio-loop-patch.js /doccano/backend/client/dist/js/
```

```html
<script src="/js/audio-loop-patch.js"></script>
```

---

**Questions?** See `AUDIO_LOOP_README.md` for full documentation.

