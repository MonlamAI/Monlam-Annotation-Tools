# 🚨 **ACTION REQUIRED: Run Database Migrations**

## ⚠️ **Answer to Your Question:**

> "if we created any schema, should the postgres needs updated or it gets create automatically"

**Answer:** PostgreSQL **DOES NOT** get updated automatically. You **MUST** run migrations manually.

---

## 📋 **What We Changed:**

We added 2 new columns to the database:
- `locked_by` - Who locked the example
- `locked_at` - When it was locked

**These columns DON'T EXIST in your PostgreSQL database yet!**

---

## 🚀 **What You Need to Do RIGHT NOW:**

### **Step 1: Open Render Shell**
1. Go to https://dashboard.render.com/
2. Click on your service
3. Click "Shell" tab
4. Wait for shell to connect

### **Step 2: Run These Commands**

```bash
cd /doccano/backend

python manage.py migrate assignment
```

**That's it!**

---

## ✅ **Expected Output:**

```
Operations to perform:
  Apply all migrations: assignment
Running migrations:
  Applying assignment.0001_initial... OK
  Applying assignment.0002_completion_tracking... OK
  Applying assignment.0003_example_locking... OK
```

---

## 🔴 **If You DON'T Run Migrations:**

Your app will crash with errors like:

```
django.db.utils.ProgrammingError: 
relation "assignment_assignment" does not exist
```

or

```
django.db.utils.ProgrammingError:
column "locked_by_id" does not exist
```

**The locking feature WON'T WORK until you run migrations!**

---

## 📊 **Before vs After:**

### **Before Migration (Current State):**
```
PostgreSQL Database:
❌ assignment_assignment table - MISSING
❌ locked_by column - MISSING
❌ locked_at column - MISSING

Result:
🔴 Locking feature = BROKEN
🔴 Assignment APIs = ERROR 500
```

### **After Migration (After You Run Commands):**
```
PostgreSQL Database:
✅ assignment_assignment table - EXISTS
✅ locked_by column - EXISTS
✅ locked_at column - EXISTS

Result:
✅ Locking feature = WORKS
✅ Assignment APIs = WORKS
```

---

## 🎯 **Summary:**

| What | Status |
|------|--------|
| Code pushed to GitHub | ✅ Done |
| Render rebuilt Docker image | ✅ Done (or in progress) |
| Migrations run on PostgreSQL | ❌ **YOU NEED TO DO THIS** |

---

## 📞 **Quick Help:**

**Q: Where do I run these commands?**  
A: In Render Shell (not your local computer)

**Q: When should I run them?**  
A: Right now! As soon as Render finishes deploying

**Q: How long does it take?**  
A: Less than 1 minute

**Q: What if I forget?**  
A: Your app will show errors when accessing assignment features

**Q: Can I run them multiple times?**  
A: Yes, it's safe. Django knows which migrations already ran.

---

## 🚨 **ACTION REQUIRED:**

**→ Open Render Shell**  
**→ Run: `python manage.py migrate assignment`**  
**→ Done!**

That's all you need to do! 🎉

---

**Once you run migrations, tell me and I'll help you test the locking feature!**

