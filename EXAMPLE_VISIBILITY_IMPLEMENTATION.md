# ✅ Example Visibility & Locking - Implementation Summary

## 🎯 What Was Built

A complete system to control **who sees what examples** and prevent **simultaneous editing**.

---

## 🚀 New Features

### 1. **Visibility Control** ✅

**Rules:**
- 👤 **Annotators** see ONLY their assigned examples
- ✓ **Approvers** see submitted/approved/rejected examples
- 👑 **Project Managers** see ALL examples

**Result:** No more confusion about what to work on!

### 2. **Example Locking** ✅

**How it works:**
- When annotator opens an example → **Locked**
- Other annotators see "Locked by [user]"
- When done → **Unlocked**
- Locks expire after 10 minutes (abandoned locks)

**Result:** No duplicate work!

### 3. **Status-Based Hiding** ✅

**Workflow:**
```
Annotator works → Submits → Example HIDDEN from them
                           → Visible to Approver
Approver reviews → Approves → Still hidden from annotator
                → Rejects  → Visible to annotator (to fix)
```

**Result:** Clean workflow, no confusion!

---

## 📦 Files Created

```
patches/assignment/
├── permissions.py                     # NEW: Permission classes
├── example_filtering.py               # NEW: Filtering & locking logic
├── migrations/
│   └── 0003_example_locking.py        # NEW: Database migration
└── EXAMPLE_VISIBILITY_AND_LOCKING.md  # NEW: Full documentation

Also:
└── EXAMPLE_VISIBILITY_IMPLEMENTATION.md  # This file
```

---

## 🗄️ Database Changes

**New fields in `Assignment` model:**
- `locked_by` - User who locked the example
- `locked_at` - When it was locked

**Migration:** `0003_example_locking.py`

---

## 🔌 API Endpoints

### Lock an Example
```
POST /v1/projects/{id}/assignments/examples/{id}/lock/
→ Locks example to current user
```

### Unlock an Example
```
POST /v1/projects/{id}/assignments/examples/{id}/unlock/
→ Releases the lock
```

### Check Lock Status
```
GET /v1/projects/{id}/assignments/examples/{id}/lock-status/
→ Returns who locked it and when
```

---

## 📊 Visibility Matrix

| Status | Annotator (Owner) | Other Annotator | Approver | PM |
|--------|-------------------|-----------------|----------|-----|
| assigned | ✅ | ❌ | ❌ | ✅ |
| in_progress | ✅ | ❌ | ❌ | ✅ |
| submitted | ❌ | ❌ | ✅ | ✅ |
| approved | ❌ | ❌ | ✅ | ✅ |
| rejected | ✅ | ❌ | ✅ | ✅ |

---

## 🔧 Integration Steps

### Step 1: Run Migration

```bash
# After deployment to Render
python manage.py migrate assignment
```

This adds the `locked_by` and `locked_at` fields.

### Step 2: Apply Filtering (Optional)

To automatically filter examples in Doccano's UI, apply the mixin:

**Edit**: `/doccano/backend/examples/views.py` (Doccano core file)

```python
from assignment.example_filtering import ExampleFilterMixin

class ExampleViewSet(ExampleFilterMixin, viewsets.ModelViewSet):
    # ... existing code ...
```

**Note:** This modifies Doccano's core, so it's optional. The APIs work without it.

### Step 3: Frontend Integration

Add locking to the annotation page:

```javascript
// When opening example
axios.post(`/v1/projects/${projectId}/assignments/examples/${exampleId}/lock/`);

// When leaving example
axios.post(`/v1/projects/${projectId}/assignments/examples/${exampleId}/unlock/`);
```

---

## 🧪 Testing Checklist

### Test 1: Visibility
- [ ] Login as annotator
- [ ] See only your assigned examples
- [ ] Submit an example
- [ ] Verify it disappears from your list
- [ ] Login as approver
- [ ] Verify submitted example is visible

### Test 2: Locking
- [ ] Login as annotator1
- [ ] Lock an example
- [ ] In another browser, login as annotator2
- [ ] Try to access same example
- [ ] Verify locked message

### Test 3: Lock Expiration
- [ ] Lock an example
- [ ] Wait 11 minutes
- [ ] Check lock status
- [ ] Verify lock expired

---

## 🎯 Solves Your Problem

### Before ❌
- All annotators see all examples
- Multiple people edit same example
- Completed examples still visible
- Confusion about what to work on

### After ✅
- Annotators see ONLY assigned examples
- Locking prevents simultaneous editing
- Completed examples hidden
- Clear workflow

---

## 🚀 Deployment

### Commit & Push

```bash
cd /Users/tseringwangchuk/Documents/monlam-doccano

git add patches/assignment/permissions.py
git add patches/assignment/example_filtering.py
git add patches/assignment/migrations/0003_example_locking.py
git add patches/assignment/EXAMPLE_VISIBILITY_AND_LOCKING.md
git add patches/assignment/urls.py
git add EXAMPLE_VISIBILITY_IMPLEMENTATION.md

git commit -m "FEAT: Example Visibility & Locking System

Prevents duplicate work and enforces assignment-based visibility.

Features:
- Annotators see only their assigned examples
- Example locking (prevents simultaneous editing)
- Completed examples hidden from annotators
- Lock expiration (10 minutes)
- API endpoints for lock/unlock

Files:
- permissions.py (access control)
- example_filtering.py (filtering & locking logic)
- migrations/0003_example_locking.py (database changes)
- EXAMPLE_VISIBILITY_AND_LOCKING.md (documentation)

Solves: Annotators editing same example, seeing completed work"

git push origin main
```

### After Render Deploys

```bash
# SSH into Render shell
python manage.py migrate assignment
```

This creates the `locked_by` and `locked_at` fields.

---

## 📝 Usage

### For Annotators

1. Login
2. Go to dataset view
3. **You only see your assigned examples**
4. Click "Annotate"
5. Example is **locked to you**
6. Work on it
7. Submit when done
8. **Example disappears** from your view

### For Approvers

1. Login
2. Go to dataset view
3. **You see submitted examples only**
4. Review and approve/reject
5. If rejected → **visible to annotator again**

### For Project Managers

1. Login
2. Go to completion dashboard
3. **See all examples and statuses**
4. Monitor progress
5. Reassign if needed

---

## 🔒 Security

✅ **Permission-based** - Uses Django permissions  
✅ **Role-checked** - Validates user role in project  
✅ **Assignment-enforced** - Must be assigned to access  
✅ **Lock-protected** - Can't unlock others' locks  

---

## 💡 Key Benefits

1. **No Duplicate Work** - Locking prevents conflicts
2. **Clear Assignments** - Only see your work
3. **Clean Workflow** - Submitted → Approver → Done
4. **Accountability** - Know who's working on what
5. **Efficiency** - No confusion, focused work

---

## 🐛 Troubleshooting

### Annotator still sees all examples

**Cause:** Filtering not applied

**Solution:** 
- Check if assignments exist
- Verify user's role
- Apply `ExampleFilterMixin` to viewset

### Lock doesn't work

**Cause:** Migration not run

**Solution:**
```bash
python manage.py migrate assignment
```

### Lock never expires

**Cause:** Clock issue or timeout too long

**Solution:**
- Check server time
- Adjust timeout in `example_filtering.py`

---

## 📚 Documentation

Full docs: `patches/assignment/EXAMPLE_VISIBILITY_AND_LOCKING.md`

Includes:
- Detailed visibility rules
- API reference
- Integration guide
- Testing procedures
- Configuration options

---

## ✅ Status

```
✅ Permission classes created
✅ Filtering logic implemented
✅ Locking API built
✅ Database migration created
✅ URLs configured
✅ Documentation written
🔄 Ready for deployment
📝 Needs: Migration run on Render
```

---

## 🎉 Result

**Professional annotation workflow with:**
- ✅ Proper visibility control
- ✅ Example locking
- ✅ No duplicate work
- ✅ Clean hand-off to approvers
- ✅ Complete accountability

**This solves your exact problem!** 🚀

---

**Ready to deploy!** Push to GitHub and let Render rebuild.

Then run the migration and test! 🎯

