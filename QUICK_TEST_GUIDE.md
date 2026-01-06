# 🧪 **Quick Test Guide**

## 📋 **What to Test (After Render Deployment)**

### **Test 1: Dataset Page**
```
1. Go to: https://annotate.monlam.ai/projects/9/dataset
2. Wait 2 seconds
3. Look for 3 NEW columns on the right:
   ✓ Annotated By
   ✓ Reviewed By  
   ✓ Status
```

**Expected Result:**
- ✅ 3 new columns appear
- ✅ Shows usernames in Annotated By / Reviewed By
- ✅ Shows colored badges in Status (e.g., ASSIGNED, SUBMITTED, APPROVED)

---

### **Test 2: Annotate Button**
```
1. On the dataset page
2. Click [Annotate] button on any row
```

**Expected Result:**
- ✅ Annotation page loads (NOT BLANK!)
- ✅ You can see the annotation interface
- ✅ Audio plays (for STT projects)
- ✅ Can annotate normally

---

### **Test 3: Audio Loop**
```
1. Open annotation page
2. Audio should auto-play and loop
3. Navigate away
4. Audio should stop
```

**Expected Result:**
- ✅ Audio plays automatically
- ✅ Audio loops continuously  
- ✅ Audio stops when you leave the page

---

## ✅ **Success Criteria:**

| Feature | Working? |
|---------|----------|
| Dataset page loads normally | ⬜ |
| 3 new columns appear (2 sec delay) | ⬜ |
| Annotated By shows usernames | ⬜ |
| Reviewed By shows usernames | ⬜ |
| Status shows colored badges | ⬜ |
| [Annotate] button works | ⬜ |
| Annotation page loads (not blank) | ⬜ |
| Audio loops on annotation pages | ⬜ |

---

## 🐛 **If Something Doesn't Work:**

### **Problem: No new columns**
```
Check browser console (F12):
- Look for: [Monlam Dataset] logs
- Should see: "Loaded X assignments"
- Should see: "✅ Headers added"
- Should see: "✅ Enhanced X rows"
```

### **Problem: Blank annotation page**
```
This shouldn't happen anymore!
We're using Doccano's original button.

If it does:
1. Check console for errors
2. Try different example
3. Report the specific URL
```

### **Problem: Audio doesn't loop**
```
Check console:
- Look for: [Monlam Audio] logs
- Should see: "Audio loop enabled"
```

---

## 📊 **Expected Console Logs:**

### **On Dataset Page:**
```
[Monlam] Initializing features...
[Monlam] Current path: /projects/9/dataset
[Monlam Dataset] Enhancing dataset table for project 9
[Monlam Dataset] Loaded 54 assignments
[Monlam Dataset] ✅ Headers added
[Monlam Dataset] ✅ Enhanced 54 rows
```

### **On Annotation Page:**
```
[Monlam] Initializing features...
[Monlam] Current path: /projects/9/speech-to-text
[Monlam Audio] Enabling audio loop...
[Monlam Audio] Found 1 audio elements
[Monlam Audio] ✅ Audio loop enabled
```

---

## 🎯 **Quick Summary:**

**What changed:**
- Dataset table now has 3 extra columns
- Shows who annotated, who reviewed, and status
- Everything else works as normal

**What to look for:**
- 3 new columns on dataset page ✓
- [Annotate] button works ✓
- No blank pages ✓

**That's it!** Simple and straightforward. 🚀

---

## 📞 **What to Report:**

If everything works:
- ✅ "Works! I see the 3 columns and Annotate button works!"

If something doesn't work:
- ❌ What doesn't work?
- ❌ Any console errors? (Copy/paste)
- ❌ Screenshot if helpful

---

**Ready for testing!** 🧪

