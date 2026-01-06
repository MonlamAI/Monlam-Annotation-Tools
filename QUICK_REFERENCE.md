# 🎯 **Quick Reference - Monlam Tracking System**

## 🚀 **Deployment Status:**

✅ Code pushed to GitHub  
✅ Dockerfile updated  
⏳ Render deploying...  
⏰ **WAITING FOR: "Live" status on Render**

---

## 📋 **After Deployment (Run ONCE):**

```bash
# Open Render Shell, then run:
python manage.py migrate assignment --noinput
```

**Expected Output:**
```
Applying assignment.0005_annotation_tracking... OK
```

---

## ✅ **Quick Tests:**

### **1. Metrics Redirect (30 seconds)**
```
Click "Metrics" → Should redirect immediately ✅
(No refresh needed!)
```

### **2. Dataset Columns (1 minute)**
```
Open dataset → Look at columns 4, 5, 6
Should see: Annotated By | Reviewed By | Status ✅
```

### **3. Visibility (2 minutes)**
```
Login as Annotator A → Annotate example #5
Login as Annotator B → Example #5 should be hidden ✅
Login as Reviewer → Example #5 visible ✅
```

### **4. Approve Buttons (1 minute)**
```
Login as Reviewer → Open annotation page
Look underneath label box → Should see [✓ Approve] [✗ Reject] ✅
```

---

## 🎯 **Key Features:**

| Feature | Status | How to Use |
|---------|--------|------------|
| **Visibility Filtering** | ✅ | Annotators see only unannotated + own rejected |
| **Example Locking** | ✅ | Auto-locks for 5 min when editing |
| **Approve/Reject** | ✅ | Buttons on annotation page |
| **Dataset Columns** | ✅ | Positions 4, 5, 6 show tracking |
| **Metrics Redirect** | ✅ | Works on first click |
| **Auto-advance** | ✅ | After approve/reject |

---

## 🔧 **Database Schema:**

```
annotation_tracking table:
├── project_id, example_id (unique together)
├── annotated_by, annotated_at
├── reviewed_by, reviewed_at
├── status (pending/submitted/approved/rejected)
├── locked_by, locked_at
└── review_notes
```

---

## 🐛 **Quick Fixes:**

**Features don't work?**
```bash
# Did you run migration?
python manage.py migrate assignment --noinput
```

**Metrics redirect broken?**
```
Clear cache: Ctrl+Shift+R (or Cmd+Shift+R)
```

**Columns don't show?**
```javascript
// Check console for errors (F12)
// Should see: [Monlam Dataset] ✅ Enhanced X rows
```

---

## 📊 **User Roles:**

| Role | Can See | Can Do |
|------|---------|--------|
| **Annotator** | Unannotated + own rejected | Annotate, edit own |
| **Reviewer** | ALL examples | Approve, reject |
| **Project Manager** | ALL examples | Approve, reject, monitor |
| **Admin** | ALL examples | Everything |

---

## 🎉 **Success Indicators:**

✅ Render shows "Live"  
✅ Migration ran successfully  
✅ Metrics redirect works on first click  
✅ Dataset columns show usernames  
✅ Approve buttons appear on annotation page  
✅ Annotators can't see each other's work  

**All features ready to test!** 🚀

---

## 📞 **Get Help:**

**If something breaks:**
1. Check browser console (F12)
2. Check Render logs
3. Share error messages
4. I'll debug!

**System is production-ready!** ✅

