#!/bin/bash
#
# Quick Deployment Script
# Deploys all features: Audio loop, Completion tracking, UI enhancements
#

set -e  # Exit on error

echo "🚀 Monlam Doccano - Complete System Deployment"
echo "=============================================="
echo ""

# Check we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Dockerfile not found. Are you in the monlam-doccano directory?"
    exit 1
fi

echo "✅ Found Dockerfile"
echo ""

# Show what will be deployed
echo "📦 Features to be deployed:"
echo "  ✅ Audio Loop for STT Projects"
echo "  ✅ Completion Tracking Backend"
echo "  ✅ Enhanced Members Progress Page"
echo "  ✅ Dataset Completion Columns"
echo "  ✅ Project Manager Role"
echo ""

# Stage all changes
echo "📝 Staging changes..."
git add Dockerfile \
  README.md \
  patches/assignment/ \
  patches/frontend/*.js \
  patches/frontend/UI_ENHANCEMENTS_README.md \
  patches/frontend/AUDIO_LOOP_README.md \
  patches/frontend/ADD_COMPLETION_MATRIX_TO_MENU.md \
  patches/frontend/FIX_AUDIO_LOOP.md \
  patches/backend/urls_patch.py \
  UI_INTEGRATION_SUMMARY.md \
  DEPLOYMENT_FIX_GUIDE.md \
  FINAL_DEPLOYMENT_GUIDE.md \
  DEPLOY_NOW.sh \
  2>/dev/null || true

echo "✅ Changes staged"
echo ""

# Show what will be committed
echo "📊 Files to be committed:"
git status --short
echo ""

# Commit
echo "💾 Creating commit..."
git commit -m "feat: Complete system deployment - audio loop, completion tracking, UI enhancements

Backend Features:
- Assignment system for example distribution
- Completion status tracking per annotator/approver
- Project Manager role with full visibility
- Comprehensive REST APIs for completion matrix
- PostgreSQL views for integrated data
- Database migrations for new tables

Frontend Features:
- Auto-loop audio with toggle controls (STT projects)
- Enhanced Members Progress page with color-coded bars
- Detailed stats modal with completion matrix
- Dataset table with Annotator/Approver status columns
- Color-coded status badges and usernames
- Real-time updates via MutationObserver

UI Integration:
- Members page: Progress bars + detailed modal
- Dataset table: 2 new columns with status badges
- Non-invasive JavaScript injection (no core mods)
- Graceful degradation if APIs unavailable

Technical Details:
- Dockerfile updated to copy and install all components
- Scripts auto-injected into index.html and 200.html
- Migrations run automatically on container startup
- All changes backward-compatible

Related: #audio-loop #completion-tracking #ui-enhancements"

echo "✅ Commit created"
echo ""

# Push
echo "🚢 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Push successful!"
echo ""
echo "🎉 Deployment initiated!"
echo ""
echo "📊 Next steps:"
echo "  1. Monitor Render dashboard for build progress"
echo "  2. Wait 5-10 minutes for deployment to complete"
echo "  3. Test features using FINAL_DEPLOYMENT_GUIDE.md"
echo ""
echo "📖 Documentation:"
echo "  - Full guide: FINAL_DEPLOYMENT_GUIDE.md"
echo "  - UI features: UI_INTEGRATION_SUMMARY.md"
echo "  - Troubleshooting: DEPLOYMENT_FIX_GUIDE.md"
echo ""
echo "✅ All done! Your features are deploying now. 🚀"

