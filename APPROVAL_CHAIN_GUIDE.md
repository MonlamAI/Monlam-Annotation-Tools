# 👑 Approval Chain: Approver vs Project Manager

## Clear Distinction Between Two-Level Approval

This guide explains how Project Managers can clearly see which examples are approved by **Approvers** vs **Final Approved by PM**.

---

## 🎯 **Your Question:**
> "is there clear indication between approver approved for project manager"

**Answer:** YES! We now have **clear visual indicators** that distinguish:
- 🟡 **Approved by Approver** (needs PM final review)
- 🟢 **Final Approved by PM** (complete!)

---

## 📊 **Two-Level Approval Workflow:**

```
┌──────────────────────────────────────────────────────┐
│ LEVEL 1: APPROVER REVIEW                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Annotator submits → Approver reviews                │
│                  → Approver approves/rejects        │
│                                                      │
│ Status: APPROVED (🟡 By Approver)                   │
│ Badge: Orange "✓ Approver"                          │
│ Meaning: Needs PM final review                      │
│                                                      │
└──────────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│ LEVEL 2: PROJECT MANAGER FINAL REVIEW               │
├──────────────────────────────────────────────────────┤
│                                                      │
│ PM reviews approver's work → PM final approves      │
│                                                      │
│ Status: APPROVED (🟢 By PM)                         │
│ Badge: Purple "👑 PM FINAL"                         │
│ Meaning: Complete! Ready for production             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 🎨 **Visual Indicators in Enhanced Dataset View**

### **Status Summary Dashboard** (Top of Page)

```
┌────────────────────────────────────────────────────────┐
│ 📊 Quick Status Summary                               │
├────────────────────────────────────────────────────────┤
│                                                        │
│  [⏱ Assigned: 100]                                    │
│  [🔵 In Progress: 45]                                 │
│  [🟠 ⚠️ Needs Review: 25]          ← Approver          │
│  [🟣 👑 PM Review: 10]              ← PM FINAL!        │
│  [🟢 ✅ Final: 20]                  ← Completed!       │
│  [❌ Rejected: 5]                                      │
│                                                        │
│  ℹ️ Action Required (Project Manager):                 │
│     10 example(s) approved by approver and awaiting   │
│     PM final review!  [Review Now →]                  │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Key Indicators:**
- 🟣 **PURPLE Badge "👑 PM Review"** - Approved by approver, needs YOUR (PM) review
- 🟢 **GREEN Badge "✅ Final"** - Final approved by PM (you or another PM)
- ℹ️ **Info Alert** - Shows count of examples awaiting PM review

---

### **Filter Tabs**

```
[All] [Needs Approver Review (25)] [👑 Needs PM Final Review (10)] [Final Approved (20)] [In Progress] [Rejected]
        ↑                                      ↑                          ↑
   Approver's work                    PM's work (YOU!)           Completed!
```

**For Project Managers:**
- Click **"👑 Needs PM Final Review"** tab
- Shows ONLY examples approved by approver but not yet by PM
- Count badge shows how many need YOUR attention

---

### **Table Column: "Reviewed By"**

Each row shows **who approved it** and **their role**:

```
┌─────┬────────────┬──────────────────────────────────┬─────────┐
│ ID  │ Status     │ Reviewed By                      │ Actions │
├─────┼────────────┼──────────────────────────────────┼─────────┤
│ 42  │ 🟠 SUBMITTED│ ⏱ Awaiting review               │[Review] │← Approver needed
│ 43  │ ✅ APPROVED │ 🔵 approver01 [✓ Approver]       │[Review] │← PM needed!
│ 44  │ ✅ APPROVED │ 🟢 manager01 [👑 PM FINAL]       │[View]   │← Done!
│ 45  │ ❌ REJECTED │ 🔴 approver01 [✓ Approver]       │[View]   │← Sent back
└─────┴────────────┴──────────────────────────────────┴─────────┘
```

**Color Coding:**
- 🔵 **Blue chip + Orange "✓ Approver" badge** = Approved by approver (needs PM)
- 🟢 **Green chip + Purple "👑 PM FINAL" badge** = Approved by PM (done!)

**Badge Meanings:**
- [✓ Approver] - Level 1 approval done, needs level 2
- [👑 PM FINAL] - Level 2 approval done, complete!

---

## 🔄 **Complete Two-Level Workflow**

### **Step 1: Annotator Submits**
```
Status: SUBMITTED (🟠)
Visible to: Approver
Reviewed by: (None yet)
```

### **Step 2: Approver Reviews & Approves**
```
Status: APPROVED (🟡)
Visible to: Project Manager
Reviewed by: approver01 [✓ Approver]
Badge color: Blue + Orange badge
Tab: "👑 Needs PM Final Review"
Alert: "Action Required (Project Manager)"
```

### **Step 3: Project Manager Final Approval**
```
Status: APPROVED (🟢)
Visible to: All (for reference)
Reviewed by: manager01 [👑 PM FINAL]
Badge color: Green + Purple badge
Tab: "Final Approved"
Alert: (None - complete!)
```

---

## 🎯 **How Project Manager Uses This:**

### **Daily Workflow:**

1. **Open Enhanced Dataset View:**
   ```
   https://annotate.monlam.ai/monlam/9/dataset-enhanced/
   ```

2. **Check Purple Badge:**
   ```
   🟣 👑 PM Review: 10
   ```
   Meaning: **10 examples need YOUR final approval**

3. **Click "👑 Needs PM Final Review" Tab:**
   - Table filters to show ONLY examples approved by approver
   - All rows have:
     - Status: APPROVED
     - Reviewed by: [approver_name] [✓ Approver]
     - Badge: Blue chip + Orange badge

4. **Review Each Example:**
   - Click "Review" button
   - Opens annotation page
   - See what approver approved
   - Verify quality

5. **Final Approve or Send Back:**
   - ✅ Click [Approve] → Your name appears as "👑 PM FINAL"
   - ❌ Click [Reject] → Goes back to annotator

6. **Track Progress:**
   - Purple badge count decreases as you work
   - Green "✅ Final" count increases
   - When purple = 0 → All caught up!

---

## 📊 **Status Meanings for PM:**

| Visual | Status | Meaning | Action |
|--------|--------|---------|--------|
| 🟠 Orange badge "Needs Review" | Submitted | Needs approver review | Wait (approver's job) |
| 🟣 Purple badge "👑 PM Review" | Approved by Approver | **Needs YOUR final review** | **REVIEW NOW!** |
| 🟢 Green badge "✅ Final" | Approved by PM | Final approval done | Done! |
| ❌ Red badge "Rejected" | Rejected | Sent back to annotator | Wait for resubmit |

---

## 🎨 **Badge Color System:**

### **In "Reviewed By" Column:**

```
Approver Approval:
┌──────────────────────────────────┐
│ 🔵 approver01  [✓ Approver]     │
│    Blue chip   Orange badge      │
└──────────────────────────────────┘
Meaning: Needs PM review

PM Final Approval:
┌──────────────────────────────────┐
│ 🟢 manager01  [👑 PM FINAL]     │
│    Dark Green  Purple badge      │
└──────────────────────────────────┘
Meaning: Complete!
```

---

## 🔍 **Quick Checks:**

### **Q: How do I see only examples that need MY (PM) review?**
**A:** Click the purple badge or "👑 Needs PM Final Review" tab.

### **Q: How do I know if an example is fully done?**
**A:** Look for:
- Green chip in "Reviewed By" column
- Purple "👑 PM FINAL" badge
- Listed in "Final Approved" tab

### **Q: Can approvers do final approval?**
**A:** No. Only Project Managers can do final approval. Approvers see orange "✓ Approver" badge on their approvals.

### **Q: What if PM rejects?**
**A:** It goes back to annotator with status "REJECTED". Needs annotator to fix and resubmit. Then approver reviews again, then PM again.

### **Q: Can I see who did the first approval?**
**A:** YES! The "Reviewed By" column shows the approver's name even after PM final approval. (Future enhancement: show full approval history)

---

## 📈 **Progress Tracking:**

Project Manager can track:

1. **Submission Progress:**
   - 🟠 Needs Review count (approver's queue)

2. **Review Progress:**
   - 🟣 PM Review count (YOUR queue)

3. **Completion:**
   - 🟢 Final Approved count (completed work)

**Formula:**
```
Project Completion = (Final Approved / Total Examples) × 100%
```

---

## 🚀 **Technical Implementation:**

### **How It Works:**

1. **Database tracks `reviewed_by` user + their role:**
   ```python
   assignment.reviewed_by = approver01
   assignment.reviewed_by_role = "approver"
   ```

2. **When PM approves, it updates:**
   ```python
   assignment.reviewed_by = manager01
   assignment.reviewed_by_role = "project_manager"
   ```

3. **Frontend filters by role:**
   ```javascript
   // Show only approved by approver (needs PM)
   examples.filter(ex => 
     ex.status === 'approved' && 
     ex.reviewed_by_role === 'approver'
   )
   ```

---

## ✅ **Summary:**

**Before this update:**
- ❌ All approvals looked the same
- ❌ PM couldn't tell what needs final review
- ❌ No clear indication of completion

**After this update:**
- ✅ Clear visual distinction (blue vs green chips)
- ✅ Role badges (✓ Approver vs 👑 PM FINAL)
- ✅ Separate filter tab for PM review
- ✅ Purple badge shows PM's queue count
- ✅ Clear alerts for PM action needed

**Result:**
**Project Managers can instantly see exactly what needs their final approval!** 🎉

---

## 📚 **Related Guides:**

- **APPROVER_WORKFLOW_GUIDE.md** - For approvers
- **ASSIGNMENT_WORKFLOW_GUIDE.md** - Overall workflow
- **MONLAM_UI_USER_GUIDE.md** - Complete UI guide

---

**Version:** 1.0  
**Last Updated:** 2025-01-06  
**For:** Project Managers

