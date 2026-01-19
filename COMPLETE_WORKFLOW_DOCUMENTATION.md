# Complete Workflow, Metrics, Analytics & Dashboard Documentation

## Table of Contents
1. [Overview](#overview)
2. [Roles and Hierarchy](#roles-and-hierarchy)
3. [Complete Workflow](#complete-workflow)
4. [Status Definitions](#status-definitions)
5. [Completion Metrics](#completion-metrics)
6. [Analytics & Reporting](#analytics--reporting)
7. [Dashboard Features](#dashboard-features)
8. [API Endpoints](#api-endpoints)
9. [Data Models](#data-models)
10. [Technical Implementation](#technical-implementation)

---

## Overview

This system implements a **two-level approval workflow** for annotation projects with comprehensive tracking, metrics, and analytics. The workflow ensures quality control through multiple review stages while maintaining clear role separation and accountability.

**Key Features:**
- Role-based access control
- Two-level approval (Annotation Approver → Project Admin)
- Real-time completion tracking
- Comprehensive analytics dashboard
- Per-user performance metrics
- Multi-level approval tracking

---

## Roles and Hierarchy

### Role Hierarchy (from lowest to highest permissions)

| Role | Level | Permissions |
|------|-------|-------------|
| **Annotator** | 1 | Can annotate and submit examples only |
| **Annotation Approver** | 2 | Can review and approve/reject submitted examples |
| **Project Manager** | 3 | Can review/approve/reject at any stage (bypasses workflow) |
| **Project Admin** | 4 | Can review/approve/reject after approver approval (final approval) |

### Detailed Role Permissions

#### 1. Annotator (`annotator`)
**Can:**
- ✅ Annotate examples
- ✅ Confirm/submit examples (tick mark ✓ or Enter key)
- ✅ View their own assigned examples
- ✅ Resubmit rejected examples

**Cannot:**
- ❌ Approve or reject examples
- ❌ View examples assigned to others (unless privileged)
- ❌ Access completion dashboard (limited view)

**Restrictions:**
- Only annotators can confirm/submit examples
- Tick mark and Enter key are blocked for non-annotators
- Backend enforces this restriction via role checks

#### 2. Annotation Approver (`annotation_approver`)
**Can:**
- ✅ View all submitted examples
- ✅ Approve/reject examples (first-level review)
- ✅ View completion metrics
- ✅ See approval chain

**Cannot:**
- ❌ Confirm/submit examples (tick mark/Enter disabled)
- ❌ Approve examples that aren't submitted/confirmed
- ❌ Approve before annotator submits

**Restrictions:**
- Can only approve/reject if example is `submitted` or `confirmed`
- Must wait for annotator to submit before reviewing

#### 3. Project Manager (`project_manager`)
**Can:**
- ✅ View all examples
- ✅ Approve/reject at any stage (bypasses workflow restrictions)
- ✅ Access full completion dashboard
- ✅ Export completion data

**Cannot:**
- ❌ Confirm/submit examples (tick mark/Enter disabled)

**Special Privileges:**
- Can approve/reject without waiting for submission
- Can approve/reject without waiting for approver approval
- Full access to all analytics

#### 4. Project Admin (`project_admin`)
**Can:**
- ✅ View all examples
- ✅ Approve/reject examples (second-level review)
- ✅ Access full completion dashboard
- ✅ Export completion data
- ✅ Sync completion tracking

**Cannot:**
- ❌ Confirm/submit examples (tick mark/Enter disabled)
- ❌ Approve before Annotation Approver approves

**Restrictions:**
- Can only approve/reject after Annotation Approver has approved
- Must wait for first-level approval before final approval

---

## Complete Workflow

### Workflow Diagram

```
┌─────────────┐
│   PENDING   │  (Example assigned, not started)
└──────┬──────┘
       │ Annotator annotates
       ▼
┌─────────────┐
│ IN_PROGRESS │  (Annotator working)
└──────┬──────┘
       │ Annotator confirms/submits (✓ or Enter)
       │ ✅ ONLY ANNOTATORS CAN DO THIS
       ▼
┌─────────────┐
│  SUBMITTED  │  (Ready for review)
│  CONFIRMED  │  (Same as submitted)
└──────┬──────┘
       │ Annotation Approver reviews
       ├──────────────┐
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│  REVIEWED   │  │  REJECTED   │
│  (Approved) │  │              │
└──────┬──────┘  └──────┬───────┘
       │                │
       │                │ Annotator fixes
       │                │
       │                ▼
       │          ┌─────────────┐
       │          │  SUBMITTED  │ (Resubmitted)
       │          └──────┬──────┘
       │                 │
       │                 └───┐
       │                     │
       ▼                     │
┌─────────────┐              │
│   FINAL     │              │
│  APPROVED   │◄─────────────┘
│ (by Admin)  │
└─────────────┘
```

### Stage-by-Stage Workflow

#### Stage 1: Annotation (Annotator Only)

**What Happens:**
1. Annotator opens an example
2. Annotator creates annotations (labels, spans, etc.)
3. Annotator confirms/submits:
   - **Option A:** Click tick mark (✓) in toolbar
   - **Option B:** Press Enter key after annotation

**Technical Details:**
- Creates `ExampleState` with `confirmed_by = annotator`
- Creates/updates `AnnotationTracking` with:
  - `status = 'submitted'`
  - `annotated_by = annotator`
  - `annotated_at = timestamp`
- Updates `Assignment` status to `'submitted'` if exists

**Restrictions:**
- ✅ **Only annotators can confirm/submit**
- ❌ Reviewers/admins cannot use tick mark or Enter key
- ❌ Backend blocks non-annotators from creating `ExampleState`

**Status Transition:** `pending` → `submitted` / `confirmed`

---

#### Stage 2: First-Level Review (Annotation Approver)

**Prerequisites:**
- Example must be **submitted** or **confirmed** by an annotator
- System checks:
  - `AnnotationTracking.status == 'submitted'` OR
  - `Assignment.status == 'submitted'` OR
  - `ExampleState.confirmed_by` exists (tick mark clicked)

**What Happens:**
1. Annotation Approver opens the example
2. Sees "Submitted" status with annotator name and timestamp
3. Can approve or reject:
   - **Approve:** Creates `ApproverCompletionStatus` with `status='approved'`
   - **Reject:** Creates `ApproverCompletionStatus` with `status='rejected'`

**Technical Details:**
- Updates `AnnotationTracking`:
  - `status = 'reviewed'` (if approved) or `'rejected'`
  - `reviewed_by = approver`
  - `reviewed_at = timestamp`
- Creates `ApproverCompletionStatus` record
- Tracks approver role for analytics

**Restrictions:**
- ❌ Cannot approve/reject if example not submitted
- ❌ Cannot confirm/submit examples
- Buttons disabled until example is submitted

**Status Transition:** `submitted` → `reviewed` (approved) or `rejected`

---

#### Stage 3: Second-Level Review (Project Admin)

**Prerequisites:**
- Annotation Approver **must have already approved**
- System checks for `ApproverCompletionStatus` with:
  - `approver_role == 'annotation_approver'`
  - `status == 'approved'`

**What Happens:**
1. Project Admin opens the example
2. Sees "Approved by [Approver Name]" status
3. Can approve or reject (final approval):
   - **Approve:** Creates `ApproverCompletionStatus` with `status='approved'`
   - **Reject:** Creates `ApproverCompletionStatus` with `status='rejected'`

**Technical Details:**
- Creates separate `ApproverCompletionStatus` record (multi-level approval)
- Updates `AnnotationTracking` with final review info
- Both approver and admin approvals are tracked separately
- Final approval tracked for metrics

**Restrictions:**
- ❌ Cannot approve/reject until Annotation Approver has approved
- ❌ Cannot confirm/submit examples
- Buttons disabled until approver has approved

**Status Transition:** `reviewed` → Final approval (or rejection)

---

#### Stage 4: Rejection Flow (Back to Annotator)

**What Happens:**
1. If rejected (by Approver or Admin):
   - `AnnotationTracking.status = 'rejected'`
   - Example becomes available to original annotator again
2. Annotator fixes and resubmits:
   - Status changes from `'rejected'` → `'submitted'`
   - Workflow restarts from Stage 1

**Technical Details:**
- Rejected examples are visible to original annotator
- Resubmission updates `annotated_at` timestamp
- Creates new approval records (previous approvals remain in history)
- Tracks rejection reason and reviewer

**Status Transition:** `rejected` → `submitted` (resubmission)

---

## Status Definitions

### Status Types

#### 1. ExampleState Status (Doccano Native)
- **Confirmed:** Example has `ExampleState` with `confirmed_by` set
- **Unconfirmed:** No `ExampleState` record exists

**Note:** Confirmed = Submitted (they are functionally the same)

#### 2. AnnotationTracking Status
- **`pending`:** Example assigned but not yet annotated
- **`submitted`:** Example annotated and submitted for review
- **`reviewed`:** Example approved by reviewer (first-level approval)
- **`rejected`:** Example rejected and needs revision

#### 3. Assignment Status
- **`assigned`:** Example assigned to annotator
- **`in_progress`:** Annotator has started working
- **`submitted`:** Example submitted for review
- **`approved`:** Example approved
- **`rejected`:** Example rejected

#### 4. ApproverCompletionStatus Status
- **`pending`:** Not yet reviewed
- **`approved`:** Approved by this approver
- **`rejected`:** Rejected by this approver

### Status Equivalency

**Submitted = Confirmed:**
- When annotator clicks tick mark → Creates `ExampleState` (confirmed) AND `AnnotationTracking` (submitted)
- When annotator presses Enter → Creates `AnnotationTracking` (submitted) AND `ExampleState` (confirmed)
- Both mean: "Annotator has finished and submitted for review"

---

## Completion Metrics

### Project-Level Metrics

#### Summary Statistics
- **Total Examples:** Total number of examples in project
- **Confirmed:** Examples confirmed by annotators (ExampleState records)
- **Pending:** Examples not yet confirmed
- **Submitted:** Examples awaiting review (confirmed - approved - rejected)
- **Approved:** Examples approved by reviewers (all approvals)
- **Final Approved:** Examples approved by Project Admin (final approval)
- **Rejected:** Examples rejected by reviewers

#### Calculation Formulas

```
Pending = Total Examples - Confirmed
Submitted = Confirmed - Approved - Rejected
Completion Rate = (Confirmed / Total Examples) × 100
Approval Rate = (Approved / Total Examples) × 100
Final Approval Rate = (Final Approved / Total Examples) × 100
```

### Per-Annotator Metrics

#### Annotator Statistics
- **Total Annotated:** Number of examples confirmed by this annotator
- **Submitted:** Examples submitted but not yet reviewed
- **Approved:** Examples approved by reviewers
- **Rejected:** Examples rejected by reviewers
- **Approval Rate:** (Approved / Total Annotated) × 100

**Formula:**
```
Total Annotated = Submitted + Approved + Rejected
```

### Per-Approver Metrics

#### Approver Statistics
- **Total Reviewed:** Total examples reviewed by this approver
- **Approved:** Examples approved by this approver
- **Final Approved:** Examples approved by this approver (if Project Admin)
- **Rejected:** Examples rejected by this approver
- **Role:** Role of the approver (annotation_approver or project_admin)

**Note:** Each approver's decisions are tracked separately for multi-level approval.

---

## Analytics & Reporting

### Completion Dashboard

**Access:** `/monlam/{project_id}/completion-dashboard/`

**Features:**
- Real-time completion statistics
- Per-annotator progress tracking
- Per-approver review statistics
- Visual progress indicators
- Export to CSV functionality

### Dashboard Sections

#### 1. Summary Cards
Displays key metrics at a glance:
- Total Examples
- Confirmed (with percentage)
- Pending
- Awaiting Review (Submitted)
- Approved
- Final Approved (with percentage)
- Rejected

#### 2. Annotator Progress Table
Shows per-annotator statistics:
- Annotator username
- Total Annotated
- Submitted count
- Approved count
- Rejected count
- Approval Rate (progress bar)

**Sortable columns** for easy analysis

#### 3. Approver Statistics Table
Shows per-approver review statistics:
- Approver username
- Role (Annotation Approver or Project Admin)
- Total Reviewed
- Approved count
- Final Approved count (for Project Admins)
- Rejected count

**Sortable columns** for review analysis

### Completion Matrix API

**Endpoint:** `/v1/projects/{project_id}/completion-matrix/`

**Features:**
- Complete matrix view for Project Managers
- Annotator completion matrix
- Approver completion matrix
- Summary statistics
- Export to CSV

**Access:** Project Managers and Admins only

### Personal Stats API

**Endpoint:** `/v1/projects/{project_id}/completion-matrix/my/`

**Features:**
- Current user's annotator stats
- Current user's approver stats
- Role information

**Access:** All authenticated project members

---

## Dashboard Features

### Real-Time Updates
- Dashboard refreshes automatically
- Shows current completion status
- Updates when examples are submitted/approved/rejected

### Data Export
- Export completion matrix as CSV
- Export annotator statistics
- Export approver statistics
- Includes all metrics and timestamps

### Filtering & Sorting
- Sort by any column
- Filter by annotator/approver
- Filter by status
- Search functionality

### Visual Indicators
- Color-coded status cards
- Progress bars for completion rates
- Percentage calculations
- Icon indicators for different statuses

### Access Control
- **Annotators:** Limited view (own stats only)
- **Annotation Approvers:** Can view all stats
- **Project Managers:** Full access + export
- **Project Admins:** Full access + export + sync

---

## API Endpoints

### Completion Tracking APIs

#### 1. Get Completion Summary
```
GET /v1/projects/{project_id}/completion-matrix/summary/
```
Returns project-wide summary statistics.

#### 2. Get Annotator Matrix
```
GET /v1/projects/{project_id}/completion-matrix/annotators/
```
Returns per-annotator completion statistics.

#### 3. Get Approver Matrix
```
GET /v1/projects/{project_id}/completion-matrix/approvers/
```
Returns per-approver review statistics.

#### 4. Get Complete Matrix
```
GET /v1/projects/{project_id}/completion-matrix/
```
Returns complete matrix with all data.

#### 5. Get Personal Stats
```
GET /v1/projects/{project_id}/completion-matrix/my/
```
Returns current user's stats (as annotator and approver).

#### 6. Sync Completion Data
```
POST /v1/projects/{project_id}/completion-matrix/sync/
```
Syncs completion tracking from assignments (Admin only).

#### 7. Export to CSV
```
GET /v1/projects/{project_id}/completion-matrix/export/
```
Exports completion matrix as CSV (Manager/Admin only).

### Completion Stats API (Dashboard)

#### Get Completion Statistics
```
GET /monlam/{project_id}/api/completion-stats/
```
Returns comprehensive statistics for dashboard:
- Summary statistics
- Per-annotator stats
- Per-approver stats

**Response Format:**
```json
{
  "summary": {
    "total_examples": 1000,
    "confirmed": 850,
    "pending": 150,
    "submitted": 200,
    "approved": 500,
    "final_approved": 450,
    "rejected": 150
  },
  "annotators": [
    {
      "annotated_by__id": 1,
      "annotated_by__username": "john",
      "total_annotated": 100,
      "submitted": 20,
      "approved": 60,
      "rejected": 20
    }
  ],
  "approvers": [
    {
      "reviewed_by__id": 2,
      "reviewed_by__username": "mary",
      "role": "annotation_approver",
      "total_reviewed": 300,
      "approved": 250,
      "final_approved": 0,
      "rejected": 50
    }
  ]
}
```

---

## Data Models

### 1. ExampleState (Doccano Native)
**Purpose:** Marks example as confirmed (tick mark)

**Fields:**
- `example`: ForeignKey to Example
- `confirmed_by`: User who confirmed (annotator)
- `confirmed_at`: Timestamp of confirmation

**Created By:** Annotator only (via tick mark or Enter key)

### 2. AnnotationTracking (Custom Tracking)
**Purpose:** Tracks submission and review status

**Fields:**
- `project`: ForeignKey to Project
- `example`: ForeignKey to Example
- `status`: `'pending'`, `'submitted'`, `'reviewed'`, `'rejected'`
- `annotated_by`: User who submitted (annotator)
- `reviewed_by`: User who reviewed (approver/admin)
- `annotated_at`: Timestamp of submission
- `reviewed_at`: Timestamp of review
- `review_notes`: Notes from reviewer
- `started_at`: When annotation started
- `time_spent_seconds`: Time spent annotating

**Status Flow:**
```
pending → submitted → reviewed/rejected
```

### 3. Assignment (Assignment Tracking)
**Purpose:** Tracks assignment to annotator

**Fields:**
- `example`: ForeignKey to Example
- `project`: ForeignKey to Project
- `assigned_to`: User assigned (annotator)
- `assigned_by`: User who made assignment
- `status`: `'assigned'`, `'in_progress'`, `'submitted'`, `'approved'`, `'rejected'`
- `started_at`: When annotation started
- `submitted_at`: When submitted
- `reviewed_by`: User who reviewed
- `reviewed_at`: When reviewed
- `is_active`: Boolean (current assignment)

### 4. AnnotatorCompletionStatus (Completion Tracking)
**Purpose:** Tracks individual annotator's completion status

**Fields:**
- `example`: ForeignKey to Example
- `project`: ForeignKey to Project
- `annotator`: User (annotator)
- `is_completed`: Boolean
- `completed_at`: Timestamp
- `annotation_count`: Number of annotations
- `assignment`: Link to Assignment (optional)

**Unique Constraint:** `(example, annotator)`

### 5. ApproverCompletionStatus (Multi-Level Approval)
**Purpose:** Tracks each approver's decision separately

**Fields:**
- `example`: ForeignKey to Example
- `project`: ForeignKey to Project
- `approver`: User (approver/admin)
- `status`: `'pending'`, `'approved'`, `'rejected'`
- `reviewed_at`: Timestamp
- `review_notes`: Notes from reviewer
- `assignment`: Link to Assignment (optional)

**Unique Constraint:** `(example, approver)`

**Multi-Level Support:**
- Multiple approvers can review the same example
- Each approver maintains their own approval record
- Tracks approver role for analytics

---

## Technical Implementation

### Workflow Enforcement

#### Backend Checks

1. **Tick Mark (ExampleState creation):**
   ```python
   # Signal: track_example_state_saved
   if not _is_annotator_only(user, project):
       instance.delete()  # Delete if non-annotator
   ```

2. **Enter Key (mark-submitted API):**
   ```python
   # API: mark_submitted
   if not _is_annotator_only(user, project):
       return 403 error
   ```

3. **Approve/Reject (approver-completion API):**
   ```python
   # For Annotation Approver:
   if not is_submitted and not is_confirmed:
       return 403 error
   
   # For Project Admin:
   if not annotation_approver_approved:
       return 403 error
   ```

#### Frontend Checks

1. Buttons disabled based on `canReviewNow` flag
2. Status display shows who did what
3. Validation prevents missing example IDs
4. Role-based UI elements (tick mark hidden for non-annotators)

### Role Checking Function

```python
def _is_annotator_only(user, project):
    """
    Check if user is ONLY an annotator (not approver/admin/manager).
    Uses exact role name matching: role == 'annotator'
    """
    if user.is_superuser:
        return False
    
    role = _get_user_role(user, project)
    if not role:
        return False
    
    role = role.lower().strip().replace(' ', '_')
    return role == 'annotator'  # Exact match
```

### Status Checking Logic

```python
# Check if example is submitted or confirmed
is_submitted = False

# Check AnnotationTracking status
if tracking.status == 'submitted':
    is_submitted = True
# Check Assignment status
elif assignment.status == 'submitted':
    is_submitted = True
# Check ExampleState (confirmed via checkmark)
elif ExampleState.confirmed_by exists:
    is_submitted = True  # Confirmed = Submitted
```

### Metrics Calculation

#### Project Summary
```python
total_examples = Example.objects.filter(project=project).count()
confirmed = ExampleState.objects.filter(example__project=project).count()
approved = AnnotationTracking.objects.filter(
    project=project, 
    status='reviewed'
).count()
rejected = AnnotationTracking.objects.filter(
    project=project, 
    status='rejected'
).count()
submitted = confirmed - approved - rejected
pending = total_examples - confirmed
```

#### Per-Annotator Stats
```python
# Group by confirmed_by from ExampleState
annotator_stats = {}
for state in ExampleState.objects.filter(example__project=project):
    annotator = state.confirmed_by
    annotator_stats[annotator.username] = {
        'total_annotated': count(confirmed by this annotator),
        'submitted': count(submitted but not reviewed),
        'approved': count(approved),
        'rejected': count(rejected)
    }
```

#### Per-Approver Stats
```python
# Group by approver from ApproverCompletionStatus
approver_stats = {}
for approval in ApproverCompletionStatus.objects.filter(project=project):
    approver = approval.approver
    approver_stats[approver.username] = {
        'total_reviewed': count(reviewed by this approver),
        'approved': count(approved by this approver),
        'final_approved': count(approved if role == project_admin),
        'rejected': count(rejected by this approver)
    }
```

---

## Permission Matrix

| Action | Annotator | Annotation Approver | Project Manager | Project Admin |
|--------|-----------|---------------------|-----------------|---------------|
| Annotate examples | ✅ | ✅ | ✅ | ✅ |
| Confirm/Submit (✓ or Enter) | ✅ | ❌ | ❌ | ❌ |
| Approve (if submitted) | ❌ | ✅ | ✅ | ❌* |
| Approve (if approver approved) | ❌ | ❌ | ✅ | ✅ |
| Reject (if submitted) | ❌ | ✅ | ✅ | ❌* |
| Reject (if approver approved) | ❌ | ❌ | ✅ | ✅ |
| View all examples | ❌ | ✅ | ✅ | ✅ |
| View completion dashboard | Limited | ✅ | ✅ | ✅ |
| Export completion data | ❌ | ❌ | ✅ | ✅ |
| Sync completion data | ❌ | ❌ | ❌ | ✅ |

*Project Admin can only approve/reject after Annotation Approver has approved

---

## Example Scenarios

### Scenario 1: Successful Approval Flow
1. **Annotator "john"** annotates Example #123
2. **John** clicks tick mark → Status: `submitted` / `confirmed`
3. **Approver "mary"** reviews → Clicks Approve → Status: `reviewed`
4. **Admin "admin"** reviews → Clicks Approve → Status: `final_approved`
5. **Result:** Example fully approved by both approver and admin

**Metrics Impact:**
- John's stats: `total_annotated: +1`, `approved: +1`
- Mary's stats: `total_reviewed: +1`, `approved: +1`
- Admin's stats: `total_reviewed: +1`, `final_approved: +1`
- Project stats: `approved: +1`, `final_approved: +1`

### Scenario 2: Rejection and Resubmission
1. **Annotator "john"** submits Example #456
2. **Approver "mary"** reviews → Clicks Reject → Status: `rejected`
3. **John** sees rejection, fixes annotations
4. **John** clicks tick mark again → Status: `submitted` (resubmitted)
5. **Mary** reviews again → Clicks Approve → Status: `reviewed`
6. **Admin** reviews → Clicks Approve → Status: `final_approved`

**Metrics Impact:**
- John's stats: `total_annotated: +1`, `rejected: +1` (then `approved: +1`)
- Mary's stats: `total_reviewed: +2`, `rejected: +1`, `approved: +1`
- Admin's stats: `total_reviewed: +1`, `final_approved: +1`

### Scenario 3: Admin Tries to Approve Early
1. **Annotator "john"** submits Example #789
2. **Admin "admin"** tries to approve → **Error:** "Project admins can only approve examples that have been approved by an annotation approver first"
3. **Approver "mary"** must approve first
4. After mary approves, admin can then approve

**Metrics Impact:**
- No change until approver approves
- After approver approves: Mary's stats updated
- Then admin can approve: Admin's stats updated

---

## Key Points Summary

### Workflow Rules
1. ✅ **Two-level approval:** Annotation Approver → Project Admin
2. ✅ **Role-based restrictions:** Only annotators can submit; approvers/admins cannot
3. ✅ **Status tracking:** Multiple models track different aspects
4. ✅ **User attribution:** Shows who submitted and who reviewed
5. ✅ **Rejection flow:** Rejected examples go back to annotator for fixes
6. ✅ **Multi-level records:** Each approver's decision tracked separately

### Status Equivalency
- **Submitted = Confirmed:** They are functionally the same
- Both mean: "Annotator has finished and submitted for review"
- System checks for both to ensure flexibility

### Metrics Accuracy
- Uses both `ExampleState` and `AnnotationTracking` for accuracy
- Matches records by `example_id` to ensure consistency
- Handles edge cases (missing records, mismatched data)
- Calculates submitted as: `total_annotated - approved - rejected`

### Analytics Features
- Real-time completion tracking
- Per-user performance metrics
- Multi-level approval tracking
- Export capabilities
- Visual progress indicators

---

## Troubleshooting

### Common Issues

#### 1. Metrics Not Updating
**Solution:** Run sync command:
```python
CompletionMatrixUpdater.sync_from_assignments(project)
```

#### 2. Submitted Count Incorrect
**Check:**
- ExampleState records exist (confirmed_by set)
- AnnotationTracking status is 'submitted'
- Formula: `submitted = confirmed - approved - rejected`

#### 3. Approval Not Working
**Check:**
- Example is submitted/confirmed
- User has correct role
- Workflow prerequisites met (for Project Admin)

#### 4. Non-Annotator Can Confirm
**Check:**
- Role check function `_is_annotator_only()` working
- Signal handler deleting ExampleState for non-annotators
- API endpoint checking role before allowing submission

---

## Best Practices

1. **Regular Sync:** Run sync command after bulk operations
2. **Role Verification:** Always verify user roles before actions
3. **Status Consistency:** Ensure ExampleState and AnnotationTracking stay in sync
4. **Metrics Validation:** Verify `total_annotated = submitted + approved + rejected`
5. **Error Handling:** Log errors but don't fail entire operations
6. **User Feedback:** Show clear error messages when restrictions apply

---

## Future Enhancements

Potential improvements:
- Batch approval/rejection
- Approval deadlines and reminders
- Advanced filtering in dashboard
- Custom report generation
- Email notifications for status changes
- Time tracking and productivity metrics
- Quality score tracking
- Inter-annotator agreement metrics

---

**Last Updated:** 2024
**Version:** 1.0
**Maintained By:** Monlam AI Team

