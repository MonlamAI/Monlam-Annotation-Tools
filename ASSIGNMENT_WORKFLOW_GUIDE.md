# 📋 Complete Assignment Workflow Guide

## Table of Contents
1. [What is Assignment?](#what-is-assignment)
2. [How Assignment Works](#how-assignment-works)
3. [Creating Assignments](#creating-assignments)
4. [Assignment Lifecycle](#assignment-lifecycle)
5. [Visibility Rules](#visibility-rules)
6. [Example Locking](#example-locking)
7. [Practical Examples](#practical-examples)

---

## What is Assignment?

**Assignment** is how you distribute work to annotators in Doccano.

### **Without Assignment:**
❌ All annotators see all examples  
❌ People work on same examples (duplicate work)  
❌ No accountability  
❌ Chaos!

### **With Assignment:**
✅ Each example assigned to specific annotator  
✅ Annotators see only their work  
✅ No duplicate work  
✅ Clear accountability  
✅ Professional workflow!

---

## How Assignment Works

### **Step-by-Step Process:**

```
┌─────────────────────────────────────────────────────┐
│ 1. PROJECT CREATION                                 │
│    Admin creates STT project with 1000 audio files │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 2. ADD MEMBERS                                      │
│    - annotator01 (role: annotator)                 │
│    - annotator02 (role: annotator)                 │
│    - approver01 (role: approver)                   │
│    - manager01 (role: project_manager)             │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 3. CREATE ASSIGNMENTS                               │
│    - Examples 1-500 → annotator01                  │
│    - Examples 501-1000 → annotator02               │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 4. ANNOTATORS WORK                                  │
│    annotator01:                                     │
│      - Sees only examples 1-500                    │
│      - Locks example when working                  │
│      - Submits when done                           │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 5. APPROVAL WORKFLOW                                │
│    approver01:                                      │
│      - Sees submitted examples                     │
│      - Reviews & approves/rejects                  │
│      - If rejected → back to annotator             │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 6. PROJECT MANAGER OVERSIGHT                        │
│    manager01:                                       │
│      - Sees all examples (all statuses)            │
│      - Monitors completion matrix                  │
│      - Final approval                              │
└─────────────────────────────────────────────────────┘
```

---

## Creating Assignments

### **Method 1: API Call (Bulk Assignment)**

Best for creating many assignments at once.

```bash
# Assign examples 1-500 to annotator01
curl -X POST https://annotate.monlam.ai/v1/projects/9/assignments/bulk/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assigned_to_username": "annotator01",
    "example_ids": [1, 2, 3, ... 500]
  }'
```

### **Method 2: Python Script**

Use the script I just created:

```bash
# In Render Shell or local Docker
cd /doccano/backend

# Assign all unassigned examples to annotator01
python scripts/create_assignments.py \
  --project 9 \
  --user annotator01 \
  --all

# Assign specific range (examples 1-500)
python scripts/create_assignments.py \
  --project 9 \
  --user annotator01 \
  --examples 1-500

# Assign specific examples
python scripts/create_assignments.py \
  --project 9 \
  --user annotator02 \
  --examples 501,502,503,504,505
```

### **Method 3: Django Shell (Manual)**

For one-off assignments or debugging:

```python
# In Render Shell or Docker
python manage.py shell

# Then in Python shell:
from django.contrib.auth import get_user_model
from projects.models import Project
from examples.models import Example
from assignment.models_separate import Assignment

User = get_user_model()

# Get project and user
project = Project.objects.get(pk=9)
user = User.objects.get(username='annotator01')

# Get examples (first 100)
examples = Example.objects.filter(project=project)[:100]

# Create assignments
for example in examples:
    Assignment.objects.create(
        project=project,
        example=example,
        assigned_to=user,
        assigned_by=user,  # Or admin user
        status='assigned'
    )
    print(f"✓ Assigned example {example.id}")

print(f"✅ Created {examples.count()} assignments")
```

---

## Assignment Lifecycle

### **Assignment Status Flow:**

```
assigned
   ↓
in_progress (annotator working)
   ↓
submitted (annotator done)
   ↓
approved (approver approved)  OR  rejected (needs fixing)
   ↓                                  ↓
COMPLETE                           assigned (back to annotator)
```

### **Status Definitions:**

| Status | Meaning | Who Can See | Actions Available |
|--------|---------|-------------|-------------------|
| `assigned` | Waiting for annotator | Annotator, PM | Start work |
| `in_progress` | Annotator working | Annotator, PM | Submit when done |
| `submitted` | Ready for review | Approver, PM | Approve/Reject |
| `approved` | Annotation approved | PM | Export/Use |
| `rejected` | Needs revision | Annotator, Approver, PM | Fix & resubmit |

---

## Visibility Rules

### **What Each Role Sees:**

#### **👤 Annotator (Owner of Assignment):**
```
✅ Can see:
   - assigned (their own)
   - in_progress (their own)
   - rejected (their own, needs fixing)

❌ Cannot see:
   - submitted (hidden after submit!)
   - approved (hidden!)
   - Other annotators' examples
```

**Why?** Once submitted, it's out of their hands!

#### **✓ Approver:**
```
✅ Can see:
   - submitted (ready for review)
   - approved (already reviewed)
   - rejected (reviewed, sent back)

❌ Cannot see:
   - assigned (not ready yet)
   - in_progress (not ready yet)
```

**Why?** Only work on examples ready for review!

#### **👑 Project Manager:**
```
✅ Can see:
   - EVERYTHING (all statuses, all users)
```

**Why?** Need full oversight of project!

---

## Example Locking

### **How Locking Works:**

```
1. annotator01 opens Example #42
   → Assignment locked_by = annotator01
   → Assignment locked_at = 2025-01-06 10:00:00

2. annotator02 tries to open Example #42
   → ❌ "This example is locked by annotator01"
   → ❌ Access denied

3. annotator01 finishes or closes browser
   → Lock remains for 10 minutes
   → After 10 minutes: Auto-unlock

4. If annotator01 submits example
   → Lock released immediately
```

### **Lock API Endpoints:**

```bash
# Lock an example (when opening it)
POST /v1/projects/9/assignments/examples/42/lock/

# Unlock an example (when closing it)
POST /v1/projects/9/assignments/examples/42/unlock/

# Check lock status
GET /v1/projects/9/assignments/examples/42/lock-status/

# Response:
{
  "is_locked": true,
  "locked_by": "annotator01",
  "locked_at": "2025-01-06T10:00:00Z",
  "lock_expires_at": "2025-01-06T10:10:00Z"
}
```

### **Lock Expiration:**

- **Duration:** 10 minutes
- **Reason:** Prevents abandoned locks
- **Example:** Annotator's browser crashes → lock expires → others can work

---

## Practical Examples

### **Scenario 1: Distributing Work Evenly**

**Project:** 1000 STT audio files  
**Team:** 5 annotators

```bash
# Annotator 1: Examples 1-200
python scripts/create_assignments.py \
  --project 9 --user annotator01 --examples 1-200

# Annotator 2: Examples 201-400
python scripts/create_assignments.py \
  --project 9 --user annotator02 --examples 201-400

# Annotator 3: Examples 401-600
python scripts/create_assignments.py \
  --project 9 --user annotator03 --examples 401-600

# ... and so on
```

**Result:**
- Each annotator sees exactly 200 examples
- No overlap
- Clear accountability

---

### **Scenario 2: Reassigning Rejected Work**

**Situation:** Approver rejected Example #42, needs fixing

```python
# In Django shell
assignment = Assignment.objects.get(
    project_id=9,
    example_id=42
)

# Already set to 'rejected' by approver
print(assignment.status)  # 'rejected'

# Annotator can now see it again
# (because rejected examples are visible to owner)

# Annotator fixes it and resubmits
assignment.status = 'submitted'
assignment.save()
```

---

### **Scenario 3: Checking Progress**

```python
# In Django shell
from assignment.models_separate import Assignment

project_id = 9

# Total assignments
total = Assignment.objects.filter(
    project_id=project_id,
    is_active=True
).count()

# By status
assigned = Assignment.objects.filter(
    project_id=project_id,
    status='assigned',
    is_active=True
).count()

in_progress = Assignment.objects.filter(
    project_id=project_id,
    status='in_progress',
    is_active=True
).count()

submitted = Assignment.objects.filter(
    project_id=project_id,
    status='submitted',
    is_active=True
).count()

approved = Assignment.objects.filter(
    project_id=project_id,
    status='approved',
    is_active=True
).count()

print(f"""
Project {project_id} Progress:
─────────────────────────────
Total:       {total}
Assigned:    {assigned}
In Progress: {in_progress}
Submitted:   {submitted}
Approved:    {approved}
─────────────────────────────
Completion:  {(approved/total)*100:.1f}%
""")
```

---

### **Scenario 4: Bulk Reassignment**

**Situation:** Annotator left, need to reassign their work

```python
# In Django shell
from django.contrib.auth import get_user_model
from assignment.models_separate import Assignment

User = get_user_model()

old_user = User.objects.get(username='annotator_left')
new_user = User.objects.get(username='annotator_new')

# Find all incomplete assignments
assignments = Assignment.objects.filter(
    project_id=9,
    assigned_to=old_user,
    status__in=['assigned', 'in_progress'],
    is_active=True
)

# Reassign
count = 0
for assignment in assignments:
    assignment.assigned_to = new_user
    assignment.status = 'assigned'  # Reset to assigned
    assignment.save()
    count += 1

print(f"✅ Reassigned {count} examples to {new_user.username}")
```

---

## Summary

### **Key Concepts:**

1. **Assignment = Task Distribution**
   - Each example assigned to one annotator
   - Clear ownership

2. **Status = Workflow Stage**
   - `assigned` → `in_progress` → `submitted` → `approved`
   - Status determines visibility

3. **Visibility = Access Control**
   - Annotators see only their assigned work
   - Approvers see submitted work
   - PMs see everything

4. **Locking = Prevents Conflicts**
   - One person works at a time
   - 10-minute expiration
   - Auto-unlock on submit

### **Best Practices:**

✅ **DO:**
- Distribute work evenly
- Create assignments BEFORE annotators start
- Use bulk assignment API for large projects
- Monitor completion matrix regularly

❌ **DON'T:**
- Assign same example to multiple annotators (unless intentional for quality check)
- Forget to run migrations after deployment
- Skip lock implementation (leads to conflicts)

---

## Quick Reference Commands

```bash
# Create assignments (Python script)
python scripts/create_assignments.py --project 9 --user annotator01 --all

# Check assignments (Django shell)
python manage.py shell
>>> from assignment.models_separate import Assignment
>>> Assignment.objects.filter(project_id=9).count()

# View specific user's assignments
>>> Assignment.objects.filter(assigned_to__username='annotator01').count()

# Check project completion
>>> total = Assignment.objects.filter(project_id=9).count()
>>> approved = Assignment.objects.filter(project_id=9, status='approved').count()
>>> print(f"Progress: {(approved/total)*100:.1f}%")
```

---

## Need Help?

- **API Documentation:** `/patches/assignment/COMPLETION_TRACKING_README.md`
- **Visibility Rules:** `/patches/assignment/EXAMPLE_VISIBILITY_AND_LOCKING.md`
- **Monlam UI:** `/MONLAM_UI_USER_GUIDE.md`

---

**Version:** 1.0  
**Last Updated:** 2025-01-06  
**Author:** Monlam AI Team

