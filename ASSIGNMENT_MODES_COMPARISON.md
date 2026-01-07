# 📋 Assignment Modes: Explicit vs Implicit

## Overview

There are two ways to distribute annotation work:

1. **Explicit Assignment** - Admin pre-assigns examples to specific annotators
2. **Implicit Assignment** - Annotators pick available examples (first-come-first-served)

---

## Mode Comparison

### **Explicit Assignment Mode**

```
┌─────────────────────────────────────────┐
│ Admin creates assignments:              │
│   - Example 1-500 → annotator01        │
│   - Example 501-1000 → annotator02     │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ Annotators see ONLY their examples:     │
│   - annotator01: sees 1-500            │
│   - annotator02: sees 501-1000         │
└─────────────────────────────────────────┘
```

**Pros:**
✅ Guaranteed workload distribution  
✅ Clear accountability (who's responsible for what)  
✅ Can assign by expertise (e.g., specialist for medical terms)  
✅ Pre-plan entire project  
✅ Track individual progress  

**Cons:**
❌ Requires assignment UI  
❌ More setup work for admin  
❌ Less flexible (can't easily swap)  
❌ Rigid workflow  

**Best for:**
- Large teams (10+ annotators)
- Quality control needs
- Specialized content
- Formal workflows
- Contract work (pay per example)

---

### **Implicit Assignment Mode** ⭐ **SIMPLER**

```
┌─────────────────────────────────────────┐
│ Admin just adds members to project      │
│   - No assignment needed!               │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ All annotators see all available work:  │
│   - annotator01: sees all 1000         │
│   - annotator02: sees all 1000         │
│   First-come-first-served!             │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ Locking prevents conflicts:             │
│   - annotator01 opens #42 → Locked     │
│   - annotator02 can't open #42         │
│   - annotator02 picks #43 instead      │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│ Completed work hidden:                  │
│   - annotator01 submits #42            │
│   - #42 hidden from all annotators     │
│   - Only approvers see it              │
└─────────────────────────────────────────┘
```

**Pros:**
✅ No assignment UI needed  
✅ Simple setup (just add members)  
✅ Flexible (annotators pick what they want)  
✅ Self-balancing (fast workers do more)  
✅ Easy to start  

**Cons:**
❌ No guaranteed distribution  
❌ Some annotators might do more than others  
❌ Less accountability (harder to track who should do what)  
❌ Can't pre-assign by expertise  

**Best for:**
- Small teams (2-5 annotators)
- Trusted team
- Simple content
- Flexible workflow
- Quick projects

---

## Implementation Options

### **Option 1: Pure Implicit Mode** ⭐ **Recommended for You**

Remove assignment completely, use only:
- Member management (add users to project)
- Example locking (prevent conflicts)
- Status-based hiding (completed examples hidden)

**Changes needed:**
```python
# In example_filtering.py - list_available method
def list_available(self, request, project_id):
    # If user is annotator:
    examples = Example.objects.filter(
        project=project_id,
        # NOT completed/submitted/approved
    ).exclude(
        status__in=['submitted', 'approved']
    ).exclude(
        # NOT locked by others (or expired lock)
        locked_by__isnull=False,
        locked_at__gt=timezone.now() - timedelta(minutes=10)
    )
    
    return examples
```

**Result:**
- No Assignment table needed (can keep for future)
- Members page is the only UI
- Locking ensures no conflicts
- Simple!

---

### **Option 2: Hybrid Mode** (Flexible)

Support BOTH modes with auto-detection:

```python
# Pseudo-code
def get_available_examples(user, project):
    # Check if explicit assignments exist
    has_assignments = Assignment.objects.filter(
        project=project,
        is_active=True
    ).exists()
    
    if has_assignments:
        # EXPLICIT MODE: Show only assigned examples
        return get_assigned_examples(user, project)
    else:
        # IMPLICIT MODE: Show all available examples
        return get_all_available_examples(project)
```

**Result:**
- Start without assignments → Implicit mode
- Create assignments later → Explicit mode
- Best of both worlds!

---

### **Option 3: Configurable Mode** (Most Flexible)

Add a project setting:

```python
# In Project model
class Project(models.Model):
    # ... existing fields ...
    assignment_mode = models.CharField(
        max_length=20,
        choices=[
            ('explicit', 'Explicit Assignment'),
            ('implicit', 'First-Come-First-Served'),
        ],
        default='implicit'
    )
```

**Result:**
- Admin chooses mode per project
- Full control
- Most complex

---

## Current System Status

**What we built:**
- ✅ Assignment model & database
- ✅ Example locking
- ✅ Status-based hiding
- ✅ API endpoints
- ❌ **NO UI for creating assignments**

**What's missing for Explicit Mode:**
- Assignment UI page
- Bulk assignment interface
- Reassignment tools

**What's missing for Implicit Mode:**
- Nothing! We have everything needed

---

## My Recommendation

Based on your question, I recommend:

### **🎯 Go with Hybrid Mode (Option 2)**

**Why?**
1. ✅ Works immediately without assignment UI
2. ✅ Members page is all you need
3. ✅ Can add explicit assignments later if needed
4. ✅ No code to delete (assignment system stays for future)
5. ✅ Flexible!

**Implementation:**
- Modify `example_filtering.py` to check for assignments
- If no assignments: Show all available examples
- If assignments exist: Show only assigned examples
- Keep locking and hiding as-is

**Benefits:**
- Start simple (implicit mode)
- Grow complex if needed (explicit mode)
- No wasted work

---

## Decision Time

**Question for you:**

Do you want me to:

**A)** Implement Hybrid Mode (recommended)
- Works without assignments now
- Can add assignments later
- Flexible

**B)** Pure Implicit Mode
- Simplify by removing assignment requirement
- First-come-first-served only
- Simpler code

**C)** Build Assignment UI
- Create assignment management page
- Enable explicit mode fully
- More work, more features

**Let me know and I'll implement it immediately!**

---

## Technical Details for Hybrid Mode

If you choose Hybrid Mode, here's what I'll do:

### 1. Modify `example_filtering.py`:

```python
def list_available(self, request, project_id):
    """
    List available examples based on project mode.
    - If assignments exist: Show assigned examples only
    - If no assignments: Show all available examples
    """
    project = self.get_project(project_id)
    user = request.user
    
    # Check for assignments
    has_assignments = Assignment.objects.filter(
        project=project,
        is_active=True
    ).exists()
    
    if has_assignments:
        # EXPLICIT MODE
        examples = self._get_assigned_examples(user, project)
    else:
        # IMPLICIT MODE
        examples = self._get_all_available_examples(user, project)
    
    return Response(examples)

def _get_assigned_examples(self, user, project):
    """Get examples explicitly assigned to user."""
    assignments = Assignment.objects.filter(
        project=project,
        assigned_to=user,
        is_active=True,
        status__in=['assigned', 'in_progress', 'rejected']
    ).exclude(
        # Exclude locked by others
        locked_by__isnull=False,
        ~Q(locked_by=user)
    )
    return assignments

def _get_all_available_examples(self, user, project):
    """Get all examples not yet completed (implicit mode)."""
    examples = Example.objects.filter(
        project=project
    ).exclude(
        # Exclude completed
        status__in=['submitted', 'approved']
    ).exclude(
        # Exclude locked by others
        locked_by__isnull=False,
        ~Q(locked_by=user),
        locked_at__gt=timezone.now() - timedelta(minutes=10)
    )
    return examples
```

### 2. Update Documentation

Add section explaining both modes.

### 3. Test Both Scenarios

- Without assignments (implicit)
- With assignments (explicit)

---

**Ready to implement when you decide!** 🚀



