#!/bin/bash
# Verify Frontend Features Are Deployed
# Run this in Render Shell after deployment

echo "🔍 Verifying Frontend Features..."
echo "=================================="
echo ""

echo "📍 1. Checking if index.html exists..."
if [ -f "/doccano/backend/client/dist/index.html" ]; then
    echo "   ✅ /doccano/backend/client/dist/index.html exists"
    ls -lh /doccano/backend/client/dist/index.html
else
    echo "   ❌ /doccano/backend/client/dist/index.html NOT FOUND"
fi
echo ""

if [ -f "/doccano/backend/staticfiles/index.html" ]; then
    echo "   ✅ /doccano/backend/staticfiles/index.html exists"
    ls -lh /doccano/backend/staticfiles/index.html
else
    echo "   ❌ /doccano/backend/staticfiles/index.html NOT FOUND"
fi
echo ""

echo "📍 2. Checking for custom JavaScript..."
audio_count=$(grep -c "Monlam Audio" /doccano/backend/client/dist/index.html 2>/dev/null || echo "0")
dataset_count=$(grep -c "Monlam Dataset" /doccano/backend/client/dist/index.html 2>/dev/null || echo "0")
metrics_count=$(grep -c "Monlam Metrics" /doccano/backend/client/dist/index.html 2>/dev/null || echo "0")
approve_count=$(grep -c "Monlam Approve" /doccano/backend/client/dist/index.html 2>/dev/null || echo "0")

echo "   Audio Loop: $audio_count occurrences $([ $audio_count -gt 0 ] && echo '✅' || echo '❌')"
echo "   Dataset Enhancement: $dataset_count occurrences $([ $dataset_count -gt 0 ] && echo '✅' || echo '❌')"
echo "   Metrics Redirect: $metrics_count occurrences $([ $metrics_count -gt 0 ] && echo '✅' || echo '❌')"
echo "   Approve/Reject: $approve_count occurrences $([ $approve_count -gt 0 ] && echo '✅' || echo '❌')"
echo ""

echo "📍 3. Checking file permissions..."
ls -l /doccano/backend/client/dist/index.html 2>/dev/null | awk '{print "   Owner: " $3 ", Group: " $4 ", Perms: " $1}'
echo ""

echo "📍 4. Checking file size..."
size=$(wc -c < /doccano/backend/client/dist/index.html 2>/dev/null || echo "0")
if [ $size -gt 100000 ]; then
    echo "   ✅ File size: $size bytes (looks good)"
else
    echo "   ⚠️  File size: $size bytes (seems small, might be wrong file)"
fi
echo ""

echo "=================================="
if [ $audio_count -gt 0 ] && [ $dataset_count -gt 0 ] && [ $metrics_count -gt 0 ] && [ $approve_count -gt 0 ]; then
    echo "🎉 ALL FEATURES DETECTED!"
    echo "If they don't work in browser, try:"
    echo "  1. Hard refresh (Ctrl+Shift+R)"
    echo "  2. Clear browser cache"
    echo "  3. Check browser console (F12) for errors"
else
    echo "❌ SOME FEATURES MISSING!"
    echo "The custom index.html might not be deployed correctly."
    echo "Try rebuilding and redeploying."
fi

