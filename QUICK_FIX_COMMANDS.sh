#!/bin/bash
# Quick Fix Commands - Copy/Paste into Render Shell
# DO NOT RUN THIS FILE DIRECTLY - Copy commands one by one

echo "======================================================================"
echo "MONLAM DOCCANO - QUICK FIX COMMANDS"
echo "======================================================================"
echo ""
echo "Copy these commands ONE BY ONE into Render Shell:"
echo ""

echo "----------------------------------------------------------------------"
echo "STEP 1: Run Migrations (Creates Database Tables)"
echo "----------------------------------------------------------------------"
cat << 'EOF'
python manage.py migrate assignment --noinput
EOF
echo ""
echo "Expected: Should see 'Applying assignment.0001_initial... OK'"
echo ""

echo "----------------------------------------------------------------------"
echo "STEP 2: Verify Tables Created"
echo "----------------------------------------------------------------------"
cat << 'EOF'
python manage.py shell -c "from assignment.models_separate import Assignment; print(f'✅ Assignment model loaded: {Assignment}'); print(f'Total assignments: {Assignment.objects.count()}')"
EOF
echo ""
echo "Expected: Should see '✅ Assignment model loaded' and '0' assignments"
echo ""

echo "----------------------------------------------------------------------"
echo "STEP 3: Create Test Assignments (10 examples)"
echo "----------------------------------------------------------------------"
cat << 'EOF'
python manage.py shell << 'PYTHON_SCRIPT'
from examples.models import Example
from django.contrib.auth import get_user_model
from projects.models import Project
from assignment.models_separate import Assignment

User = get_user_model()

# Get project 9
project = Project.objects.get(id=9)
print(f"📁 Project: {project.name}")

# Get first 10 examples
examples = Example.objects.filter(project=project)[:10]
print(f"📋 Found {examples.count()} examples")

# Get project_manager user (or change to any username)
try:
    annotator = User.objects.get(username='project_manager')
    print(f"👤 Annotator: {annotator.username}")
except User.DoesNotExist:
    # Fallback to first user
    annotator = User.objects.first()
    print(f"👤 Using user: {annotator.username}")

# Create assignments
count = 0
for example in examples:
    assignment, created = Assignment.objects.get_or_create(
        project=project,
        example=example,
        defaults={
            'assigned_to': annotator,
            'assigned_by': annotator,
            'status': 'assigned'
        }
    )
    if created:
        count += 1
        print(f"✓ Assigned example {example.id}")
    else:
        print(f"⊙ Example {example.id} already assigned")

print(f"\n✅ Created {count} new assignments")
print(f"📊 Total assignments: {Assignment.objects.filter(project=project).count()}")
PYTHON_SCRIPT
EOF
echo ""
echo "Expected: Should see '✓ Assigned example X' for each example"
echo ""

echo "----------------------------------------------------------------------"
echo "STEP 4: Test API Endpoints"
echo "----------------------------------------------------------------------"
echo "Open browser console on https://annotate.monlam.ai/projects/9/metrics"
echo "Paste this:"
echo ""
cat << 'EOF'
// Test completion matrix API
fetch('/v1/projects/9/assignments/completion-matrix/summary/')
  .then(r => r.json())
  .then(d => console.log('✅ Summary API works!', d))
  .catch(e => console.error('❌ API failed:', e));

// Test comprehensive examples API
setTimeout(() => {
  fetch('/v1/projects/9/assignments/examples-comprehensive/')
    .then(r => r.json())
    .then(d => console.log('✅ Examples API works!', d.results?.length || 0, 'examples'))
    .catch(e => console.error('❌ Examples API failed:', e));
}, 1000);
EOF
echo ""
echo "Expected: Both should return ✅ with data"
echo ""

echo "----------------------------------------------------------------------"
echo "STEP 5: Hard Refresh & Test Features"
echo "----------------------------------------------------------------------"
echo "1. Press Ctrl+Shift+R (or Cmd+Shift+R on Mac) to hard refresh"
echo "2. Check metrics page: Should show completion matrix with data"
echo "3. Check dataset page: Should show Annotator/Approver columns"
echo "4. Click an example: Audio should auto-loop"
echo "5. If you're an approver: Should see Approve/Reject buttons"
echo ""

echo "======================================================================"
echo "TROUBLESHOOTING"
echo "======================================================================"
echo ""
echo "If migrations fail with 'already exists':"
cat << 'EOF'
python manage.py migrate assignment --fake
EOF
echo ""
echo "If need to reset migrations (DANGER - loses data):"
cat << 'EOF'
python manage.py migrate assignment zero
python manage.py migrate assignment
EOF
echo ""
echo "If need to check what migrations are applied:"
cat << 'EOF'
python manage.py showmigrations assignment
EOF
echo ""

echo "======================================================================"
echo "ALL DONE! 🎉"
echo "======================================================================"
echo "After running these commands, all features should work:"
echo "  ✅ Metrics completion matrix"
echo "  ✅ Dataset status columns"
echo "  ✅ Audio auto-loop"
echo "  ✅ Approve/Reject buttons"
echo "  ✅ Members progress tracking"
echo ""

