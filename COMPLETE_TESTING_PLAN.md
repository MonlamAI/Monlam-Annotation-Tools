# Complete Testing Plan - All Features

## After Deployment (Wait 5-10 mins for commit 485853d)

---

## ✅ **PART 1: Create Test Data**

### **In Render Shell:**

```python
python manage.py shell
```

```python
from examples.models import Example
from django.contrib.auth import get_user_model
from projects.models import Project
from assignment.models_separate import Assignment

User = get_user_model()

# Get your project
project = Project.objects.get(id=9)
print(f"Project: {project.name}")

# Get examples
examples = Example.objects.filter(project=project)[:10]
print(f"Found {examples.count()} examples")

# Get user
annotator = User.objects.get(username='project_manager')
print(f"Annotator: {annotator.username}")

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

print(f"\n✅ Created {count} new assignments")
print(f"Total assignments: {Assignment.objects.filter(project=project).count()}")

exit()
```

---

## 🧪 **PART 2: Test Each Feature**

### **Feature 1: Metrics Page** 📊

**URL:** `https://annotate.monlam.ai/projects/9/metrics`

**Expected:**
- Original Doccano metrics at TOP
- Completion Matrix section BELOW with:
  - 4 colorful stat cards
  - Annotators Progress table (1 row: project_manager)
  - Approvers Activity table (empty - no approvals yet)

**Console Check:**
```javascript
console.log('Script version:', document.querySelector('script[src*="metrics"]').src);
// Should show: ?v=FIXED1
```

**Status:** ✅ Should work perfectly now

---

### **Feature 2: Dataset Completion Columns** 📋

**URL:** `https://annotate.monlam.ai/projects/9/dataset`

**Expected:**
- Normal dataset table
- Extra columns added:
  - 👤 **Annotator** (shows status badge + username)
  - ✓ **Approver** (shows "—" if not reviewed)

**Console Debug:**
```javascript
console.log('[DEBUG] Table rows:', document.querySelectorAll('tbody tr').length);
console.log('[DEBUG] Monlam columns:', document.querySelectorAll('.monlam-completion-cell').length);
```

**If not working:**
- Script loads but doesn't add columns
- Likely: API not returning data for examples
- Fix: Check if comprehensive examples API works

**Status:** ⚠️ Needs testing after assignments created

---

### **Feature 3: Audio Auto-Loop** 🎵

**URL:** Click any example in dataset (opens annotation page)

**Expected:**
- Audio starts playing AUTOMATICALLY
- When audio ends, loops back to start
- No visible button

**Console Debug:**
```javascript
console.log('[DEBUG] Audio elements:', document.querySelectorAll('audio').length);
console.log('[DEBUG] Audio loop applied:', document.querySelectorAll('audio[data-loop-applied]').length);
```

**If not working:**
- Check Console for: `[Monlam] Is annotation page?`
- Should show: `true`
- If false, page detection is wrong

**Status:** ⚠️ Needs testing on annotation page

---

### **Feature 4: Approve/Reject Buttons** ✅❌

**URL:** Same annotation page as above

**Expected:**
- Green **✓ Approve** button (top-right or floating)
- Red **✗ Reject** button next to it
- Only visible if you have approver/manager role

**Console Debug:**
```javascript
console.log('[DEBUG] Buttons found:', document.querySelectorAll('.monlam-approve-btn, .monlam-reject-btn').length);
console.log('[DEBUG] User has approver permission:', !!document.querySelector('.monlam-approve-btn'));
```

**If not working:**
- Script checking user role
- Might need to verify role assignment
- Or buttons not injecting into DOM

**Status:** ⚠️ Needs testing with proper role

---

## 📝 **Quick Test Script (Run in Browser Console)**

After deployment, paste this on `/projects/9/metrics`:

```javascript
// Comprehensive feature test
console.log('=== MONLAM FEATURE CHECK ===');

// 1. Check script versions
console.log('1. Script Versions:');
document.querySelectorAll('script[src*="monlam"], script[src*="metrics"], script[src*="audio"], script[src*="dataset"], script[src*="approve"]').forEach(s => {
  const name = s.src.split('/').pop().split('?')[0];
  const version = s.src.split('?v=')[1];
  console.log(`   ${name}: v=${version}`);
});

// 2. Check if metrics loaded
console.log('2. Metrics Matrix:');
console.log('   Injected:', !!document.querySelector('.monlam-completion-section'));

// 3. Test API
console.log('3. Testing API:');
fetch('/v1/projects/9/assignments/completion-matrix/summary/')
  .then(r => r.json())
  .then(d => console.log('   Summary API:', d))
  .catch(e => console.error('   Summary API failed:', e));

setTimeout(() => {
  fetch('/v1/projects/9/assignments/completion-matrix/annotators/')
    .then(r => r.json())
    .then(d => console.log('   Annotators API:', d))
    .catch(e => console.error('   Annotators API failed:', e));
}, 1000);

console.log('\n=== Check results above ===');
```

---

## 🎯 **Expected Timeline**

1. **Now → +5 mins:** Render deploying commit 485853d
2. **+5 mins:** Hard refresh, test metrics page
3. **+10 mins:** Create assignments in Render Shell
4. **+15 mins:** Test all 4 features
5. **+20 mins:** Debug any that don't work

---

## 🐛 **If Issues Remain**

For each broken feature, run its specific debug commands above and send me:
- Console output
- Network tab (any failed API calls)
- What you see vs what you expect

I'll fix each one individually with the same best practices! 🔧

