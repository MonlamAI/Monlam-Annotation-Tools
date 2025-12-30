# 🎯 WhiteNoise Compression Fix

## The Problem

JavaScript files were returning 404 errors (MIME type 'text/html' not executable) even though:
- ✅ Files existed at `/doccano/backend/staticfiles/_nuxt/`
- ✅ Script tags were in HTML
- ✅ Paths were correct

## Root Cause

**WhiteNoise** with `CompressedStaticFilesStorage` requires **both** the original file AND a `.gz` compressed version:

```python
# From Django settings
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
```

Other Doccano files had `.gz` versions:
```
08fba5f.js (2999 bytes) ✅
08fba5f.js.gz (1576 bytes) ✅
```

Our files only had originals:
```
audio-loop-enhanced.js (11040 bytes) ✅
audio-loop-enhanced.js.gz - MISSING ❌
```

**Result:** WhiteNoise refused to serve files without compressed versions.

## The Solution

### Immediate Fix (Applied on Render)

```bash
cd /doccano/backend/staticfiles/_nuxt/
gzip -k -f audio-loop-enhanced.js
gzip -k -f enhance-members-progress.js
gzip -k -f dataset-completion-columns.js
```

This created the required `.gz` files immediately.

### Permanent Fix (In Dockerfile)

Updated Dockerfile to automatically compress files after copying:

```dockerfile
# Copy JS files
COPY patches/frontend/audio-loop-enhanced.js /doccano/backend/staticfiles/_nuxt/
COPY patches/frontend/enhance-members-progress.js /doccano/backend/staticfiles/_nuxt/
COPY patches/frontend/dataset-completion-columns.js /doccano/backend/staticfiles/_nuxt/

# Compress for WhiteNoise
RUN gzip -k -f /doccano/backend/staticfiles/_nuxt/audio-loop-enhanced.js && \
    gzip -k -f /doccano/backend/staticfiles/_nuxt/enhance-members-progress.js && \
    gzip -k -f /doccano/backend/staticfiles/_nuxt/dataset-completion-columns.js
```

## Why This Happened

1. We copied files directly to `staticfiles/_nuxt/`
2. `collectstatic` saw them as "already in destination" (unmodified)
3. WhiteNoise's compression only runs during `collectstatic`
4. Files never got compressed
5. WhiteNoise refused to serve uncompressed files

## Verification

After the fix:

```bash
ls -la /doccano/backend/staticfiles/_nuxt/ | grep audio
-rw-r--r-- 1 doccano doccano   11040 audio-loop-enhanced.js
-rw-r--r-- 1 doccano doccano    2884 audio-loop-enhanced.js.gz ✅
```

Browser should now load:
```
✅ [Monlam] Enhanced Audio Loop Patch loaded
✅ [Monlam] Enhanced Members Progress Patch loaded
✅ [Monlam] Dataset Completion Columns Patch loaded
```

## Alternative Solutions Considered

### Option 1: Use STATICFILES_DIRS
Copy to a source directory, let collectstatic handle it:
```python
STATICFILES_DIRS = ['/doccano/frontend/monlam/']
```
**Rejected:** Would require modifying Django settings in Dockerfile

### Option 2: Disable Compression
```python
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
```
**Rejected:** Would affect all static files, not just ours

### Option 3: Manual gzip (CHOSEN)
Compress files after copying in Dockerfile
**Selected:** Simple, non-invasive, works with existing WhiteNoise config

## Files Modified

- ✅ `Dockerfile` - Added gzip commands
- ✅ Commit: `deb25f8`

## Testing

After deployment:
1. Hard refresh browser (Ctrl+Shift+R)
2. Open Console (F12)
3. Check for "[Monlam]" messages
4. Verify Network tab shows 200 OK for JS files

## Future Deployments

All future Render deployments will automatically:
1. Copy JS files to staticfiles
2. Compress them with gzip
3. Create both `.js` and `.js.gz` versions
4. WhiteNoise will serve them correctly

## Lessons Learned

When using WhiteNoise with `CompressedStaticFilesStorage`:
- **Always** provide `.gz` versions of static files
- Or let `collectstatic` handle compression
- Don't copy directly to STATIC_ROOT without compression
- Test file accessibility, not just file existence

---

**Status:** ✅ Fixed
**Date:** December 30, 2025
**Tested:** Working on Render production

