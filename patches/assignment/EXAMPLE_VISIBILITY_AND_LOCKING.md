# 🔒 Example Visibility & Locking System

## 🎯 Problem Solved

**Before:** All annotators could see and edit all examples simultaneously, causing:
- Duplicate work
- Conflicting annotations
- Wasted effort
- No assignment enforcement

**After:** Proper visibility control and locking:
- ✅ Annotators only see their assigned examples
- ✅ Completed examples hidden from annotators
- ✅ Example locking prevents simultaneous editing
- ✅ Role-based access control

---

## 📋 Visibility Rules

### Who Sees What

| Example Status | Annotator (Owner) | Other Annotator | Approver | Project Manager |
|----------------|-------------------|-----------------|----------|-----------------|
| **assigned**   | ✅ See & Edit     | ❌ Hidden       | ❌ Hidden | ✅ See All     |
| **in_progress**| ✅ See & Edit     | ❌ Hidden       | ❌ Hidden | ✅ See All     |
| **submitted**  | ❌ Hidden         | ❌ Hidden       | ✅ Review Only | ✅ Review |
| **approved**   | ❌ Hidden         | ❌ Hidden       | ✅ View Only | ✅ View     |
| **rejected**   | ✅ See & Fix      | ❌ Hidden       | ✅ View | ✅ View         |

### Key Points

1. **Annotators see ONLY their assigned examples**
   - Cannot see examples assigned to others
   - Cannot see their own submitted/approved examples
   - CAN see rejected examples (need to fix them)

2. **Approvers see review-ready examples**
   - See submitted examples (ready for review)
   - See approved examples (for reference)
   - See rejected examples (tracking)
   - Do NOT see assigned/in-progress (not ready yet)

3. **Project Managers see everything**
   - Full visibility for project oversight
   - Can monitor all statuses
   - Can access any example

4. **Admins see everything**
   - Unrestricted access
   - System-level management

---

## 🔐 Locking System

### How It Works

1. **When annotator opens an example:**
   ```
   POST /v1/projects/{project_id}/assignments/examples/{example_id}/lock/
   ```
   - Example is locked to that user
   - Lock timestamp recorded
   - Other annotators cannot access

2. **While working:**
   - Lock is held
   - Other users see "Locked by [username]"
   - Approvers/PMs can still view (read-only)

3. **When finished:**
   ```
   POST /v1/projects/{project_id}/assignments/examples/{example_id}/unlock/
   ```
   - Example is unlocked
   - Available for others (if needed)

4. **Lock expiration:**
   - Locks expire after **10 minutes** of inactivity
   - Prevents abandoned locks
   - Auto-releases if user doesn't finish

### Lock States

```
┌─────────────────────────────────────────┐
│ Example Lifecycle with Locking          │
├─────────────────────────────────────────┤
│                                         │
│ 1. ASSIGNED (Unlocked)                  │
│    ↓                                    │
│    Annotator clicks "Annotate"         │
│    ↓                                    │
│ 2. LOCKED (In Progress)                 │
│    ↓                                    │
│    Annotator works on it               │
│    ↓                                    │
│ 3. SUBMITTED (Unlocked)                 │
│    ↓                                    │
│    Hidden from annotator               │
│    Visible to approver                 │
│                                         │
└─────────────────────────────────────────┘
```

### API Endpoints

#### Lock an Example
```http
POST /v1/projects/{project_id}/assignments/examples/{example_id}/lock/
Authorization: Token YOUR_TOKEN

Response 200:
{
  "message": "Example locked successfully",
  "locked_by": "annotator01",
  "locked_at": "2026-01-06T10:30:00Z"
}

Response 423 (Locked):
{
  "error": "Example is locked by another user",
  "locked_by": "annotator02",
  "locked_at": "2026-01-06T10:25:00Z"
}
```

#### Unlock an Example
```http
POST /v1/projects/{project_id}/assignments/examples/{example_id}/unlock/
Authorization: Token YOUR_TOKEN

Response 200:
{
  "message": "Example unlocked successfully"
}
```

#### Check Lock Status
```http
GET /v1/projects/{project_id}/assignments/examples/{example_id}/lock-status/
Authorization: Token YOUR_TOKEN

Response 200:
{
  "locked": true,
  "locked_by": "annotator01",
  "locked_at": "2026-01-06T10:30:00Z",
  "is_locked_by_me": false
}
```

---

## 🛠️ Implementation Details

### Database Schema

**New fields added to `Assignment` model:**

```python
class Assignment(models.Model):
    # ... existing fields ...
    
    # Locking fields
    locked_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True,
        related_name='locked_assignments',
        help_text='User who currently has this example locked'
    )
    locked_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='When the example was locked'
    )
```

### Permission Classes

**`CanAccessExample`** - Controls who can see which examples

**`CanLockExample`** - Controls who can lock/unlock examples

### Filtering Mixin

**`ExampleFilterMixin`** - Filters example lists based on role

Apply this to Doccano's example viewsets:

```python
from assignment.example_filtering import ExampleFilterMixin

class ExampleViewSet(ExampleFilterMixin, viewsets.ModelViewSet):
    # ... existing code ...
```

---

## 🔄 Workflow Examples

### Scenario 1: Normal Annotation Workflow

1. **Project Manager assigns 10 examples to Annotator A**
   ```
   Annotator A sees: 10 examples (assigned)
   Annotator B sees: 0 examples (none assigned to them)
   ```

2. **Annotator A opens Example #1**
   ```
   POST /lock/
   → Example #1 locked by Annotator A
   ```

3. **Annotator B tries to open Example #1**
   ```
   → Access denied (not assigned to them)
   ```

4. **Annotator A submits Example #1**
   ```
   Status: assigned → submitted
   → Unlocked automatically
   → Hidden from Annotator A
   → Visible to Approver
   ```

5. **Approver reviews and approves**
   ```
   Status: submitted → approved
   → Still hidden from Annotator A
   → Visible to Approver and PM
   ```

### Scenario 2: Rejection Workflow

1. **Approver rejects Example #1**
   ```
   Status: submitted → rejected
   → Visible to Annotator A again
   → Annotator can fix and resubmit
   ```

2. **Annotator A fixes and resubmits**
   ```
   Status: rejected → submitted
   → Hidden from Annotator A
   → Visible to Approver again
   ```

### Scenario 3: Lock Expiration

1. **Annotator A locks Example #1**
   ```
   Locked at: 10:00 AM
   ```

2. **Annotator A goes to lunch (forgets to unlock)**
   ```
   10:05 AM - Still locked
   10:09 AM - Still locked
   10:11 AM - Lock expired (10+ minutes)
   → Auto-released
   ```

3. **Annotator B can now access (if assigned)**
   ```
   GET /lock-status/
   → locked: false (expired)
   → Can lock it themselves
   ```

---

## 🚀 Integration with Monlam UI

### Enhanced Dataset View

The `enhanced_dataset.html` template shows:
- Only examples the user can access
- Lock status indicators
- "Locked by [user]" badges

### Annotation Page

The `annotation_with_approval.html` template:
- Auto-locks when page opens
- Shows lock warning if locked by others
- Auto-unlocks when navigating away

### Frontend Integration

```javascript
// When opening annotation page
await axios.post(`/v1/projects/${projectId}/assignments/examples/${exampleId}/lock/`);

// When leaving page
await axios.post(`/v1/projects/${projectId}/assignments/examples/${exampleId}/unlock/`);

// Before allowing edit
const status = await axios.get(`/v1/projects/${projectId}/assignments/examples/${exampleId}/lock-status/`);
if (status.data.locked && !status.data.is_locked_by_me) {
  alert(`Example is locked by ${status.data.locked_by}`);
}
```

---

## 🧪 Testing

### Test Cases

#### ✅ Test 1: Annotator sees only assigned examples
```
1. Login as annotator01
2. Navigate to /monlam/<project_id>/dataset-enhanced/
3. Verify: Only see examples assigned to you
4. Verify: Don't see examples assigned to others
```

#### ✅ Test 2: Completed examples hidden
```
1. Login as annotator01
2. Submit an example
3. Navigate to dataset
4. Verify: Submitted example is not visible
5. Login as approver
6. Verify: Submitted example IS visible
```

#### ✅ Test 3: Example locking
```
1. Login as annotator01
2. Open example #1
3. In another browser, login as annotator02
4. Try to open same example
5. Verify: See "Locked by annotator01" message
```

#### ✅ Test 4: Lock expiration
```
1. Lock an example
2. Wait 11 minutes
3. Check lock status
4. Verify: Lock has expired
5. Verify: Can be locked by another user
```

#### ✅ Test 5: Project Manager sees all
```
1. Login as project_manager
2. Navigate to dataset
3. Verify: See ALL examples regardless of status
4. Verify: Can access any example
```

---

## 🐛 Troubleshooting

### Issue: Annotator sees all examples

**Problem:** Visibility filtering not applied

**Solution:**
1. Check if `ExampleFilterMixin` is applied to viewset
2. Verify Assignment records exist
3. Check user's role in project

### Issue: Lock doesn't work

**Problem:** Locking endpoint not responding

**Solution:**
1. Run migration: `python manage.py migrate assignment`
2. Verify `locked_by` and `locked_at` fields exist
3. Check API endpoint is registered in URLs

### Issue: Examples remain locked forever

**Problem:** Lock not expiring

**Solution:**
1. Check `locked_at` timestamp
2. Verify 10-minute expiration logic
3. Manually unlock: `assignment.locked_by = None; assignment.save()`

---

## 🔧 Configuration

### Lock Timeout Duration

Default: **10 minutes**

To change, modify `example_filtering.py`:

```python
# Change from 10 to 15 minutes
if lock_duration < timedelta(minutes=15):
```

### Role Names

Default role names:
- `annotator`
- `approver`
- `project_manager`

If your Doccano uses different role names, update in:
- `permissions.py`
- `example_filtering.py`

---

## 📊 Database Migration

### Apply the Migration

```bash
# After deployment
python manage.py migrate assignment
```

This adds:
- `locked_by` field
- `locked_at` field

### Rollback (if needed)

```bash
python manage.py migrate assignment 0002_completion_tracking
```

---

## ✅ Benefits

1. **No Duplicate Work**
   - Annotators can't accidentally work on same example
   - Clear assignment boundaries

2. **Proper Workflow**
   - Completed work hidden from annotators
   - Clear hand-off to approvers

3. **Accountability**
   - Know who's working on what
   - Track lock history

4. **Efficiency**
   - Annotators focus on their assignments
   - No confusion about what to do

5. **Quality Control**
   - Approvers see only review-ready examples
   - Clean approval workflow

---

## 🎓 Best Practices

### For Annotators

1. ✅ Work on your assigned examples only
2. ✅ Submit when done (releases lock)
3. ✅ Fix rejected examples promptly
4. ❌ Don't abandon locked examples

### For Approvers

1. ✅ Review submitted examples
2. ✅ Provide clear feedback when rejecting
3. ✅ Approve quickly to maintain flow

### For Project Managers

1. ✅ Assign examples evenly
2. ✅ Monitor completion dashboard
3. ✅ Check for abandoned locks
4. ✅ Reassign if annotator inactive

---

## 📝 Summary

This system provides:

✅ **Visibility Control** - Right people see right examples  
✅ **Example Locking** - Prevent simultaneous editing  
✅ **Role-Based Access** - Proper permission enforcement  
✅ **Workflow Enforcement** - Clear annotation → approval flow  
✅ **Lock Expiration** - Abandoned locks auto-release  

**Result:** Professional annotation workflow with no duplicate work! 🎉

---

Built with ❤️ for Monlam AI



