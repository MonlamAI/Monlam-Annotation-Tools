#!/bin/bash
# Diagnostic script to check what's on Render server
# Run this via Render Shell

echo "🔍 Monlam Files Diagnostic on Render"
echo "====================================="
echo ""

echo "1. Checking if staticfiles/_nuxt directory exists:"
ls -la /doccano/backend/staticfiles/_nuxt/ | head -20
echo ""

echo "2. Looking for our JS files in staticfiles/_nuxt:"
ls -la /doccano/backend/staticfiles/_nuxt/*.js 2>/dev/null | grep -E "(audio-loop|enhance|dataset)" || echo "❌ NOT FOUND in staticfiles/_nuxt"
echo ""

echo "3. Checking client/dist/static/_nuxt:"
ls -la /doccano/backend/client/dist/static/_nuxt/*.js 2>/dev/null | grep -E "(audio-loop|enhance|dataset)" || echo "❌ NOT FOUND in client/dist/static/_nuxt"
echo ""

echo "4. Searching entire backend for our JS files:"
find /doccano/backend -name "audio-loop-enhanced.js" 2>/dev/null || echo "❌ NOT FOUND anywhere"
echo ""

echo "5. Checking index.html for script tags:"
grep -n "audio-loop-enhanced" /doccano/backend/client/dist/index.html || echo "❌ Script tag NOT in index.html"
echo ""

echo "6. Checking Django STATIC_ROOT setting:"
grep -r "STATIC_ROOT" /doccano/backend/config/settings/ 2>/dev/null
echo ""

echo "7. Checking Django STATICFILES_DIRS:"
grep -r "STATICFILES_DIRS" /doccano/backend/config/settings/ 2>/dev/null
echo ""

echo "8. Testing if URL path exists:"
curl -I http://localhost:8000/static/_nuxt/audio-loop-enhanced.js 2>/dev/null || echo "❌ Cannot reach URL"
echo ""

echo "✅ Diagnostic complete!"

