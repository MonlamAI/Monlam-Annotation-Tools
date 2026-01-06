# 👁️ Approver Workflow Guide

## How Approvers See What Needs Review

This guide explains **exactly** how approvers and project managers see what annotations are ready for review and how to approve/reject them.

---

## 🎯 Quick Answer

**Where to go:** https://annotate.monlam.ai/monlam/{project_id}/dataset-enhanced/

**What you'll see:**
- 🟠 **Orange badges** = Examples submitted for review (**ACTION NEEDED**)
- Status tabs to filter by status
- Big warning alert: "⚠️ X examples awaiting your review!"

---

## 📊 The Enhanced Dataset View

### **1. Status Summary Dashboard** (Top of Page)

When you open the Enhanced Dataset View, you see this at the top:

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Quick Status Summary                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [⏱ Assigned: 100]  [🔵 In Progress: 45]                  │
│  [🟠 ⚠️ Needs Review: 25]  [✅ Approved: 20]  [❌ Rejected: 10] │
│                                                             │
│  ⚠️ Action Required: 25 example(s) submitted and awaiting  │
│     your review!  [Review Now →]                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**
- **Orange "Needs Review" badge** - Clickable! Shows count of submitted examples
- **Warning alert** - Shows if action is needed
- **"Review Now" button** - Automatically filters to show only submitted examples

---

### **2. Status Filter Tabs**

Below the summary, you see tabs:

```
┌─────────────────────────────────────────────────────────────┐
│ [All (200)] [Needs Review (25)] [In Progress (45)]         │
│ [Approved (20)] [Rejected (10)]                            │
└─────────────────────────────────────────────────────────────┘
```

**For Approvers, click:**
- **"Needs Review" tab** - Shows ONLY submitted examples ready for your review
- Count badge shows how many examples await review

---

### **3. Dataset Table with Status Indicators**

```
┌────┬──────────────┬───────────────┬──────────────┬─────────────┬─────────────┐
│ ID │ Content      │ Assigned To   │ Status       │ Approver    │ Actions     │
├────┼──────────────┼───────────────┼──────────────┼─────────────┼─────────────┤
│ 42 │ [Audio]      │ annotator01   │ 🟠 SUBMITTED │ Not reviewed│ [Review]    │ ← TAKE ACTION
│ 43 │ [Audio]      │ annotator01   │ 🔵 IN PROGRESS│ -           │ [Annotate]  │ ← Wait
│ 44 │ [Audio]      │ annotator02   │ 🟠 SUBMITTED │ Not reviewed│ [Review]    │ ← TAKE ACTION
│ 45 │ [Audio]      │ annotator02   │ ✅ APPROVED  │ approver01  │ [Annotate]  │ ← Done
│ 46 │ [Audio]      │ annotator01   │ ❌ REJECTED  │ approver01  │ [Annotate]  │ ← Wait for fix
└────┴──────────────┴───────────────┴──────────────┴─────────────┴─────────────┘
```

**Status Colors:**
- 🟠 **ORANGE "SUBMITTED"** = Ready for your review (**ACTION NEEDED**)
- 🔵 **BLUE "IN PROGRESS"** = Annotator still working (wait)
- ✅ **GREEN "APPROVED"** = Already reviewed by you or another approver
- ❌ **RED "REJECTED"** = Already reviewed and sent back to annotator
- ⚪ **GREY "ASSIGNED"** = Not started yet (wait)

**Actions Column:**
- Examples with status "SUBMITTED" show **orange "Review" button**
- All others show regular "Annotate" button

---

## 🔄 Complete Review Workflow

### **Step 1: Access the Enhanced Dataset View**

```
URL: https://annotate.monlam.ai/monlam/9/dataset-enhanced/
     (Replace 9 with your project ID)
```

### **Step 2: Check Status Summary**

Look at the top:
- **"Needs Review: 25"** - You have 25 examples to review
- If count is 0 → ✅ All caught up!

### **Step 3: Filter to Submitted Examples**

Click:
- **"Needs Review" tab**, OR
- **Orange badge** in summary, OR
- **"Review Now" button** in alert

Result: Table shows ONLY submitted examples.

### **Step 4: Review Each Example**

For each orange "SUBMITTED" row:

1. **Click the "Review" button** (orange button in Actions column)
2. Opens annotation page with approval interface
3. You'll see:

```
┌─────────────────────────────────────────────┐
│ 📝 Example #42                              │
├─────────────────────────────────────────────┤
│                                             │
│ 📋 Approval Status Chain:                  │
│                                             │
│ 👤 Annotator Status:                       │
│    ✅ SUBMITTED by annotator01             │
│    (Submitted on: 2025-01-06 10:00)        │
│                                             │
│ ✓ Approver Status:                         │
│    ⏳ PENDING REVIEW                       │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ 🔊 [Audio Player] (plays automatically)    │
│ 📝 Transcription: "དེ་རིང་གནམ་གཤིས་ཡག་པོ་འདུག"  │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│ [✅ Approve]  [❌ Reject]                   │
│                                             │
└─────────────────────────────────────────────┘
```

4. **Listen to audio** (auto-plays in loop)
5. **Check transcription accuracy**
6. **Make decision:**

---

### **Step 5A: If Annotation is Correct → Approve**

1. **Click [✅ Approve] button**
2. Confirmation: "Example approved!"
3. **Status changes:**
   - Annotator status: submitted → approved
   - Approver status: pending → approved
   - Your name appears as reviewer
4. **Result:**
   - Example HIDDEN from annotator
   - Example visible to Project Manager for final check
   - You return to dataset view
   - Example disappears from "Needs Review" tab

---

### **Step 5B: If Annotation Needs Fixing → Reject**

1. **Click [❌ Reject] button**
2. **Popup asks: "Please provide a reason for rejection:"**
3. **Type reason:** e.g., "Wrong punctuation in line 2"
4. **Click OK**
5. Confirmation: "Example rejected!"
6. **Status changes:**
   - Annotator status: submitted → rejected
   - Approver status: pending → rejected
   - Your name appears as reviewer
   - Your notes visible to annotator
7. **Result:**
   - Example VISIBLE to annotator again (they can see it)
   - Annotator sees your rejection notes
   - Annotator fixes and resubmits
   - Example stays in "Rejected" tab until resubmitted

---

### **Step 6: Continue Reviewing**

After approve/reject:
- Automatically returns to dataset view
- Next submitted example still visible in "Needs Review" tab
- Repeat steps 4-5 for each example
- "Needs Review" count decreases as you work

---

## 🎨 Visual Indicators Summary

| Indicator | Meaning | Action |
|-----------|---------|--------|
| 🟠 Orange badge "SUBMITTED" | Ready for review | Review NOW |
| 🟠 Orange "Review" button | Click to review | Click it |
| ⚠️ Warning alert at top | Examples waiting | Review them |
| Count in tab badge | How many to review | Track progress |
| ✅ Green "APPROVED" | Already done | Skip it |
| ❌ Red "REJECTED" | Sent back to annotator | Wait for resubmit |
| 🔵 Blue "IN PROGRESS" | Annotator working | Wait |

---

## 📊 For Project Managers

Project Managers see **everything** + additional overview:

### **Completion Dashboard**

```
URL: https://annotate.monlam.ai/monlam/9/completion/
```

Shows:
- Overall project completion percentage
- Per-annotator progress (who submitted how many)
- Per-approver activity (who approved how many)
- Matrix of all examples with all statuses

**Use this to:**
- Monitor team progress
- See who's behind schedule
- Track approval rates
- Final approval after approvers review

---

## 🔄 Example Lifecycle (Approver's Perspective)

```
1. Annotator working:
   Status: IN PROGRESS (🔵)
   Visibility: You DON'T see it yet
   Action: Wait
   
2. Annotator submits:
   Status: SUBMITTED (🟠)
   Visibility: YOU SEE IT NOW! In "Needs Review" tab
   Action: REVIEW IT!
   Alert: "⚠️ 1 new example awaiting review"
   
3. You approve:
   Status: APPROVED (✅)
   Visibility: Moves to "Approved" tab
   Action: Done! (PM may do final check)
   
   OR
   
3. You reject:
   Status: REJECTED (❌)
   Visibility: Moves to "Rejected" tab, annotator sees it again
   Action: Wait for annotator to fix and resubmit
   
4. Annotator resubmits (if rejected):
   Status: SUBMITTED (🟠) again
   Visibility: Back in "Needs Review" tab
   Action: Review again
```

---

## 🆘 Common Questions

### **Q: I don't see any submitted examples, but I know annotators are working.**

**A:** They haven't submitted yet. Examples must be:
1. Assigned to annotator
2. Annotator completes work
3. **Annotator clicks "Submit for Review"** ← CRITICAL
4. Only then you see it

Check "In Progress" tab - those are still being worked on.

---

### **Q: After I approve, where does the example go?**

**A:** 
- Disappears from "Needs Review" tab
- Appears in "Approved" tab
- Hidden from annotator (they can't see it anymore)
- Visible to Project Manager for final review
- Counted in "Approved" statistics

---

### **Q: If I reject, can the annotator see why?**

**A:** YES! When you reject, you MUST provide notes. Annotator sees:
- Status: "REJECTED"
- Your name as reviewer
- Your rejection notes: "Wrong punctuation in line 2"
- They can fix and resubmit

---

### **Q: Can multiple approvers review the same example?**

**A:** Currently, first approver to review "wins". If you approve/reject, status changes immediately. Other approvers see it's already reviewed.

For **double-review workflow**, Project Manager can do second review.

---

### **Q: How do I know which examples need my urgent attention?**

**A:** Look for:
1. **Orange badge count** at top
2. **Warning alert**: "Action Required"
3. **"Needs Review" tab** with count
4. Examples sorted by submission date (oldest first)

---

## 🎯 Quick Action Checklist

Every time you login as approver:

- [ ] Go to: `/monlam/{project_id}/dataset-enhanced/`
- [ ] Check orange badge: "Needs Review: X"
- [ ] If X > 0 → Click "Review Now" or "Needs Review" tab
- [ ] For each orange "SUBMITTED" row:
  - [ ] Click "Review" button
  - [ ] Listen to audio
  - [ ] Check transcription
  - [ ] Click "Approve" or "Reject" (with notes)
- [ ] When orange count = 0 → All done! ✅

---

## 📚 Related Guides

- **ASSIGNMENT_WORKFLOW_GUIDE.md** - How assignments work overall
- **MONLAM_UI_USER_GUIDE.md** - Complete UI feature guide
- **MIGRATION_GUIDE.md** - Database setup (for admins)

---

## 🚨 IMPORTANT: Run Migrations First!

If you just deployed, **you MUST run migrations** before any of this works:

```bash
# In Render Shell
cd /doccano/backend
python manage.py migrate assignment
```

Without this, you'll get database errors!

---

**Version:** 1.0  
**Last Updated:** 2025-01-06  
**For:** Approvers, Project Managers

