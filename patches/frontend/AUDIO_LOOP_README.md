# Audio Loop Feature for Speech-to-Text Projects

Automatically loops audio in STT annotation projects while keeping all existing controls.

## Features

### Basic Version (`audio-loop-patch.js`)
- ✅ Auto-loop all audio by default
- ✅ Works with existing play/stop controls
- ✅ Automatically detects new audio elements
- ✅ Lightweight and simple

### Enhanced Version (`audio-loop-enhanced.js`) ⭐ Recommended
- ✅ All basic features
- ✅ **Toggle button** to enable/disable loop
- ✅ **Keyboard shortcut** (L key) to toggle
- ✅ **Visual indicators** for loop status
- ✅ **Remembers preference** across sessions
- ✅ **Status indicator** in top-right corner
- ✅ **Toast notifications** when toggling

## Installation

### Method 1: Add to Doccano's index.html (Recommended)

Edit `/doccano/backend/client/dist/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <!-- existing head content -->
</head>
<body>
    <div id="app"></div>
    
    <!-- MONLAM PATCH: Audio Loop -->
    <script src="/js/audio-loop-enhanced.js"></script>
    
    <!-- existing scripts -->
</body>
</html>
```

### Method 2: Copy to Static Directory

```bash
# Copy the enhanced version
cp patches/frontend/audio-loop-enhanced.js /doccano/backend/client/dist/js/

# Or copy the basic version
cp patches/frontend/audio-loop-patch.js /doccano/backend/client/dist/js/
```

### Method 3: Add to Your HTML Template

Add this to any page where audio players appear:

```html
<script src="/path/to/audio-loop-enhanced.js"></script>
```

## Usage

### Enhanced Version (Recommended)

Once installed, the enhanced version provides multiple ways to control audio looping:

#### 1. Status Indicator (Top-Right Corner)
- Shows current loop status: "🔁 Loop: ON" or "🔁 Loop: OFF"
- Click to toggle loop on/off
- Always visible for easy access

#### 2. Keyboard Shortcut
- Press **L** key to toggle loop (when not typing in input fields)
- Quick and convenient during annotation

#### 3. Per-Audio Toggle Buttons
- Each audio player gets a toggle button next to it
- Click to toggle loop for that specific session
- Button shows "🔁 Loop ON" (green) or "🔁 Loop OFF" (gray)

#### 4. Visual Feedback
- Toast notification appears when toggling
- Audio elements get green glow when loop is enabled
- Status indicator updates in real-time

#### 5. Persistent Preference
- Your preference is saved in browser localStorage
- Loop status persists across page refreshes and sessions
- Each user's preference is independent

### Basic Version

The basic version simply enables loop on all audio elements automatically. No UI controls, just auto-loop.

## API

### Enhanced Version

The enhanced version exposes a JavaScript API:

```javascript
// Check if loop is enabled
MonlamAudioLoop.enabled()  // returns true/false

// Toggle loop
MonlamAudioLoop.toggle()

// Enable loop
MonlamAudioLoop.enable()

// Disable loop
MonlamAudioLoop.disable()

// Manually apply to all audio elements
MonlamAudioLoop.applyToAll()

// Check version
MonlamAudioLoop.version  // "2.0.0"
```

### Basic Version

```javascript
// Enable loop on a specific audio element
MonlamAudioPatch.enableLoop(audioElement)

// Apply to all audio elements
MonlamAudioPatch.applyToAll()

// Check version
MonlamAudioPatch.version  // "1.0.0"
```

## How It Works

### Detection
1. Automatically detects audio elements on page load
2. Uses MutationObserver to detect dynamically added audio elements
3. Fallback periodic check every 2-3 seconds

### Loop Application
- Sets the `loop` attribute on audio elements
- Adds visual indicators (enhanced version only)
- Creates toggle buttons (enhanced version only)
- Doesn't interfere with existing controls

### Compatibility
- ✅ Works with HTML5 `<audio>` elements
- ✅ Works with Doccano's audio player
- ✅ Works with dynamically loaded content
- ✅ Works with Vue.js/React SPAs
- ✅ All modern browsers

## Customization

### Change Keyboard Shortcut

Edit `audio-loop-enhanced.js`, line ~182:

```javascript
// Change from L to another key
if (e.key === 'l' || e.key === 'L') {
    // Change to, for example, 'r' for repeat:
    if (e.key === 'r' || e.key === 'R') {
```

### Change Status Indicator Position

Edit `audio-loop-enhanced.js`, line ~208:

```javascript
indicator.style.cssText = `
    position: fixed;
    top: 10px;      // Change to bottom: 10px
    right: 10px;    // Change to left: 10px
    // ... rest of styles
`;
```

### Change Colors

Edit the CSS in the script:

```javascript
// Green for enabled (line ~65)
background: '#4CAF50'  // Change to your color

// Gray for disabled
background: '#f0f0f0'  // Change to your color
```

### Disable Status Indicator

Comment out this line in `init()` function:

```javascript
// addStatusIndicator();  // Comment this out
```

## Troubleshooting

### Issue: Loop not working

**Check:**
1. Is the script loaded? Check browser console for "[Monlam] Audio Loop Patch loaded"
2. Are there audio elements? Check console for "Applied loop to X audio elements"
3. Try toggling loop off and on again (press L key)

**Fix:**
```javascript
// Open browser console and run:
MonlamAudioLoop.applyToAll()
```

### Issue: Button not appearing

**Cause:** Button is created dynamically when audio element is detected

**Fix:**
1. Wait a few seconds for detection
2. Or manually trigger: `MonlamAudioLoop.applyToAll()`

### Issue: Keyboard shortcut not working

**Cause:** You're typing in an input field

**Fix:** Click outside input fields before pressing L

### Issue: Loop resets after page navigation

**Cause:** SPA routing clears the page

**Fix:** The script automatically re-initializes. If not, you may need to add the script to your SPA's routing logic.

## Examples

### Example 1: Default Behavior

```html
<!-- User opens annotation page -->
<!-- Audio auto-plays and loops -->
<!-- User can pause/play normally -->
<!-- Audio continues looping -->
```

### Example 2: Toggle Off

```html
<!-- User presses L key -->
<!-- Toast shows "Audio loop disabled" -->
<!-- Audio stops looping but controls still work -->
<!-- User presses L again -->
<!-- Toast shows "Audio loop enabled" -->
<!-- Audio resumes looping -->
```

### Example 3: Multiple Audio Files

```html
<!-- Page has 3 audio elements -->
<!-- All 3 have loop enabled by default -->
<!-- Each gets a toggle button -->
<!-- Status indicator shows global state -->
<!-- User can control individually or globally -->
```

## Testing

### Test Basic Functionality

1. Open an STT annotation page
2. Audio should automatically loop
3. Try pause/play - loop should persist
4. Load new example - audio should still loop

### Test Enhanced Features

1. Check top-right for status indicator
2. Press L key - should toggle and show toast
3. Check console for log messages
4. Refresh page - preference should persist
5. Try in different browser - each has own preference

### Test in Different Scenarios

- ✅ Single audio file
- ✅ Multiple audio files on same page
- ✅ Dynamically loaded audio (SPA navigation)
- ✅ Audio in iframes
- ✅ Different audio formats (mp3, wav, ogg)

## Browser Console

Check these messages in browser console (F12):

```
[Monlam] Enhanced Audio Loop Patch loaded
[Monlam] Initializing Enhanced Audio Loop Patch...
[Monlam] Applied loop to 1 audio elements
[Monlam] Audio observer started
[Monlam] Keyboard shortcut registered (L key)
[Monlam] Enhanced Audio Loop Patch initialized
[Monlam] Loop is currently ENABLED
[Monlam] Press L key to toggle loop
```

## Performance

- ✅ Lightweight (<5KB)
- ✅ Minimal CPU usage
- ✅ No external dependencies
- ✅ Efficient MutationObserver
- ✅ Throttled periodic checks

## Future Enhancements

Possible future features:
- [ ] Per-project loop preferences
- [ ] Playback speed control
- [ ] Auto-advance to next example
- [ ] Keyboard shortcuts for skip forward/back
- [ ] Waveform visualization
- [ ] Bookmarking within audio

## Support

If you encounter issues:

1. Check browser console for error messages
2. Verify the script is loaded (check network tab)
3. Try the manual API commands
4. Check localStorage: `localStorage.getItem('monlam_audio_loop_enabled')`

## License

Part of Monlam Doccano. Same license as the main project.

---

**Recommendation:** Use the **Enhanced Version** (`audio-loop-enhanced.js`) for the best user experience!

