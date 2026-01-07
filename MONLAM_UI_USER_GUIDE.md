# 📘 Monlam UI - User Guide

## 🎯 What Is Monlam UI?

Monlam UI is a **professional extension** to Doccano that provides enhanced features for:
- 📊 **Project Managers** - Complete visibility into project progress
- ✓ **Approvers** - Easy review and approval interface
- 👤 **Annotators** - Better workflow tracking

---

## 🚀 Getting Started

### Access Your Features

All Monlam UI features are accessed through special URLs:

```
Base URL: https://annotate.monlam.ai
```

| Feature | URL | Who Can Access |
|---------|-----|----------------|
| **Completion Dashboard** | `/monlam/<project_id>/completion/` | Project Managers, Admins |
| **Enhanced Dataset** | `/monlam/<project_id>/dataset-enhanced/` | All project members |
| **Annotation with Approval** | `/monlam/<project_id>/annotate/<example_id>/` | All project members |

**Example:**
- If your project ID is `9`, access the dashboard at:
  ```
  https://annotate.monlam.ai/monlam/9/completion/
  ```

---

## 📊 Feature 1: Completion Dashboard

### What It Shows

**For Project Managers** - Get a complete overview of project progress:

```
┌─────────────────────────────────────────────┐
│ 📊 Project Completion Dashboard             │
├─────────────────────────────────────────────┤
│                                             │
│ Summary Cards:                              │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│ │  54  │ │  54  │ │   5  │ │   2  │        │
│ │Total │ │Assign│ │Submit│ │Approv│        │
│ └──────┘ └──────┘ └──────┘ └──────┘        │
│                                             │
│ Annotator Progress Table:                  │
│ ┌──────────┬──────────┬──────────┬──────┐  │
│ │ User     │ Assigned │ Complete │ %    │  │
│ ├──────────┼──────────┼──────────┼──────┤  │
│ │ ann01    │ 54       │ 5        │ 9%   │  │
│ │ ann02    │ 30       │ 30       │ 100% │  │
│ └──────────┴──────────┴──────────┴──────┘  │
│                                             │
│ Approver Activity Table:                   │
│ ┌──────────┬──────────┬──────────┐         │
│ │ User     │ Reviewed │ Approved │         │
│ ├──────────┼──────────┼──────────┤         │
│ │ app01    │ 5        │ 2        │         │
│ └──────────┴──────────┴──────────┘         │
└─────────────────────────────────────────────┘
```

### How to Use

1. **Navigate** to `/monlam/<project_id>/completion/`
2. **View** the summary cards at the top
3. **Check** the annotator progress table
   - See who's assigned what
   - View completion percentages
   - Identify bottlenecks
4. **Review** the approver activity table
   - See who's reviewing
   - Track approval rates
5. **Click Refresh** to update data in real-time

### Key Metrics

- **Total Examples** - Total number of examples in project
- **Assigned** - How many examples are assigned to annotators
- **Submitted** - How many are waiting for review
- **Approved** - How many are completed and approved

---

## 📋 Feature 2: Enhanced Dataset View

### What It Shows

**For All Users** - See the dataset with assignment information:

```
┌────────────────────────────────────────────────────────────┐
│ Dataset: My STT Project                                    │
│ Search: [________] 🔍                        [Refresh]     │
├────────────────────────────────────────────────────────────┤
│ ID  │ Content       │ Assigned To│ Status      │ Approver │
├─────┼───────────────┼────────────┼─────────────┼──────────┤
│2446 │ 🔊 Audio...   │ ann01      │ ✅ APPROVED │ app01    │
│2447 │ 🔊 Audio...   │ ann01      │ 🔄 IN PROG  │ -        │
│2448 │ 🔊 Audio...   │ ann02      │ 📤 SUBMITTED│ -        │
│2449 │ 🔊 Audio...   │ -          │ ⏳ Not Asgnd│ -        │
└────────────────────────────────────────────────────────────┘
```

### How to Use

1. **Navigate** to `/monlam/<project_id>/dataset-enhanced/`
2. **Browse** the table to see all examples
3. **Use Search** to filter by text
4. **Check Status**:
   - ⏳ **ASSIGNED** - Just assigned, not started
   - 🔄 **IN PROGRESS** - Annotator is working on it
   - 📤 **SUBMITTED** - Ready for review
   - ✅ **APPROVED** - Completed and approved
   - ❌ **REJECTED** - Needs revision
5. **Click Annotate** button to work on any example
6. **View Assigned To** - See who's working on each example
7. **View Approver** - See who reviewed it and when

### Features

- **Search** - Filter examples by content
- **Sort** - Click column headers to sort
- **Audio Preview** - Play audio directly in table (STT projects)
- **Direct Links** - Click "Annotate" to jump to annotation interface

---

## ✅ Feature 3: Annotation with Approval

### What It Shows

**For Everyone** - Enhanced annotation page with approval workflow:

```
┌───────────────────────────────────────────────────┐
│ 📋 Approval Status Chain                          │
├───────────────────────────────────────────────────┤
│ 👤 Annotator          │ ✓ Approver                │
│ 📤 SUBMITTED          │ ⏳ PENDING REVIEW         │
│ By: ann01             │ By: Not reviewed          │
│ Submitted: 2026-01-06 │                           │
└───────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────┐
│ 🔍 Review Actions (For Approvers/PMs Only)        │
├───────────────────────────────────────────────────┤
│ This example is ready for review.                │
│                                                   │
│ [✅ Approve]          [❌ Reject]                 │
└───────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────┐
│ 🔊 Audio                                          │
├───────────────────────────────────────────────────┤
│ [▶ Play] ────────●──── [Volume]                  │
│ ℹ️ Audio will loop automatically                  │
└───────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────┐
│ ✏️ Annotation                                      │
├───────────────────────────────────────────────────┤
│ [Standard Doccano annotation interface loads here]│
└───────────────────────────────────────────────────┘
```

### How to Use (As Annotator)

1. **Navigate** to example from dataset
2. **See Status Chain** - Check what stage the example is at
3. **Play Audio** (STT projects) - Audio loops automatically
4. **Annotate** - Use standard Doccano interface
5. **Submit** - When done, mark as complete

### How to Use (As Approver/PM)

1. **Navigate** to submitted example
2. **Check Status Chain**:
   - See who annotated it
   - See when it was submitted
3. **Listen/Read** the content
4. **Review** the annotation
5. **Take Action**:
   - **✅ Approve** - If annotation is good
   - **❌ Reject** - If needs work (provide feedback!)

### Rejection Workflow

When rejecting:
1. Click **❌ Reject**
2. **Dialog appears** - You must provide a reason
3. **Type feedback** - Explain what needs fixing
4. **Submit** - Annotator sees your notes

### Status Progression

```
Annotator Flow:
ASSIGNED → IN PROGRESS → SUBMITTED

Approver Flow:
SUBMITTED → APPROVED ✅
         → REJECTED ❌ (back to annotator)
```

---

## 🎨 Visual Guide

### Status Colors

| Status | Color | Icon | Meaning |
|--------|-------|------|---------|
| **Assigned** | Grey | ⏳ | Just assigned |
| **In Progress** | Blue | 🔄 | Being worked on |
| **Submitted** | Orange | 📤 | Waiting for review |
| **Approved** | Green | ✅ | Completed! |
| **Rejected** | Red | ❌ | Needs revision |

### Role Badges

| Role | Badge Color | Access Level |
|------|-------------|--------------|
| **Annotator** | Blue | Can annotate examples |
| **Approver** | Purple | Can approve/reject |
| **Project Manager** | Gold | See everything + approve |
| **Admin** | Red | Full access |

---

## 📱 Tips & Best Practices

### For Annotators

1. ✅ **Check Status** - Know what stage your work is at
2. ✅ **Read Feedback** - If rejected, check the notes
3. ✅ **Submit When Done** - Don't leave work un-submitted
4. ✅ **Use Audio Loop** - It auto-loops for efficiency

### For Approvers

1. ✅ **Provide Clear Feedback** - When rejecting, be specific
2. ✅ **Be Consistent** - Apply same standards to all
3. ✅ **Check Timestamps** - Prioritize older submissions
4. ✅ **Use Dashboard** - Track your review throughput

### For Project Managers

1. ✅ **Monitor Dashboard Daily** - Catch bottlenecks early
2. ✅ **Check Completion Rates** - Identify slow annotators
3. ✅ **Review Approval Rates** - Ensure quality standards
4. ✅ **Reassign if Needed** - Balance workload

---

## 🔐 Permissions

### Who Can Do What

| Action | Annotator | Approver | Project Manager | Admin |
|--------|-----------|----------|-----------------|-------|
| View Dashboard | ❌ | ✅ | ✅ | ✅ |
| View Enhanced Dataset | ✅ | ✅ | ✅ | ✅ |
| Annotate Examples | ✅ | ✅ | ✅ | ✅ |
| Approve/Reject | ❌ | ✅ | ✅ | ✅ |
| Reassign Tasks | ❌ | ❌ | ✅ | ✅ |

---

## ❓ Troubleshooting

### Dashboard Not Loading

**Problem:** Blank page or loading forever

**Solution:**
1. Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
2. Check your internet connection
3. Verify you're logged in
4. Confirm you have permission (Project Manager role)

### Dataset Shows No Assignments

**Problem:** "Not assigned" for all examples

**Solution:**
1. Assignments may not be created yet
2. Ask project admin to assign examples
3. Check if you're viewing the correct project

### Approve Button Not Showing

**Problem:** Can't see approve/reject buttons

**Solution:**
1. Check if example is **SUBMITTED** status
2. Verify you have **Approver** or **Project Manager** role
3. You can't approve your own annotations

### Audio Not Playing

**Problem:** Audio doesn't auto-play

**Solution:**
1. Click anywhere on the page first (browser security)
2. Check browser allows auto-play
3. Verify audio URL is valid
4. Try clicking the play button manually

---

## 🆘 Support

If you encounter issues:

1. **Check This Guide** - Most common issues are covered
2. **Check Browser Console** - Press F12, look for errors
3. **Contact Support** - Provide:
   - Your username
   - Project ID
   - What you were trying to do
   - Error message (if any)
   - Screenshot

---

## 🎓 Quick Reference

### Essential URLs

Replace `<project_id>` with your actual project ID:

```
Dashboard:    /monlam/<project_id>/completion/
Dataset:      /monlam/<project_id>/dataset-enhanced/
Annotate:     /monlam/<project_id>/annotate/<example_id>/
```

### Keyboard Shortcuts

(In annotation interface)
- `Space` - Play/Pause audio
- `←/→` - Navigate examples
- `Enter` - Submit annotation

### Status Quick Reference

- **Grey** = Not started
- **Blue** = In progress
- **Orange** = Needs review
- **Green** = Approved ✅
- **Red** = Rejected ❌

---

**Happy Annotating!** 🎉

Built with ❤️ by Monlam AI



