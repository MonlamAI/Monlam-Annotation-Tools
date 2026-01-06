# 🧪 **Test Plan: Hybrid Approach (New Tab Navigation)**

## 📋 **What Changed:**

Instead of trying to navigate within the same tab (which broke Vue Router), the "Annotate" button now **opens annotation in a NEW TAB**.

## ✅ **Expected Behavior:**

### **Scenario 1: Basic Annotation from Enhanced Dataset**

1. **Go to Enhanced Dataset:**
   - URL: `https://annotate.monlam.ai/monlam/9/dataset-enhanced/`
   - Should see: Table with all 54 examples and their status

2. **Click "Annotate" on any example:**
   - Example: Click on example #2446
   - **Expected:** NEW TAB opens
   - **New tab URL should be:** `/projects/9/speech-to-text?page=24`
   - **New tab should show:** Annotation interface with page 24 loaded
   - **Should see:** Example #2446 ready to annotate

3. **Work in annotation interface:**
   - Should be able to play audio
   - Should be able to annotate
   - Should be able to navigate between examples
   - Vue Router should work normally

### **Scenario 2: Review Submitted Annotations**

1. **Filter by "Submitted" status:**
   - In enhanced dataset, click "Submitted" filter badge
   - Should see only examples with "Submitted" status

2. **Click "Review" button on submitted example:**
   - **Expected:** NEW TAB opens
   - **New tab shows:** Annotation interface at correct page
   - Approver can review and approve

3. **Keep both tabs open:**
   - Tab 1: Enhanced dataset (reference)
   - Tab 2: Annotation interface (working)
   - Can switch between them

### **Scenario 3: Multiple Examples**

1. **Review multiple examples:**
   - Click "Annotate" on example A → New tab opens (Tab 2)
   - Switch back to enhanced dataset (Tab 1)
   - Click "Annotate" on example B
   - **Expected:** Either reuses Tab 2 OR opens Tab 3 (browser dependent)

## ❌ **If It Doesn't Work:**

### **Problem 1: New Tab is Blank**

**Symptoms:**
- New tab opens
- URL is correct: `/projects/9/speech-to-text?page=24`
- But page is completely white/blank

**Diagnosis:**
- Vue still not initializing
- Even with fresh page load

**Solution:**
- Try different entry point (project home)
- Or implement full SPA integration (Option A)

### **Problem 2: Wrong Page Number**

**Symptoms:**
- New tab opens and loads
- But shows wrong example (e.g., page 0 instead of page 24)

**Diagnosis:**
- Page calculation wrong
- Or pagination different in annotation view

**Solution:**
- Check filteredExamples order
- Verify itemsPerPage (currently 10)
- Adjust calculation

### **Problem 3: New Tab Shows 404**

**Symptoms:**
- New tab shows "Page Not Found"

**Diagnosis:**
- URL incorrect
- project_type_slug wrong

**Solution:**
- Check console logs for generated URL
- Verify {{ project_type }} template variable

## 🔍 **How to Debug:**

### **Step 1: Check Console Logs**

In enhanced dataset page (before clicking Annotate):
```
1. Open browser DevTools (F12)
2. Go to Console tab
3. Click "Annotate" button
4. Should see logs:
   📍 Opening annotation for example 2446
   Index: 244, Page: 24
   URL: /projects/9/speech-to-text?page=24&q=&isChecked=
   Opening in new tab...
```

### **Step 2: Check New Tab**

After new tab opens:
```
1. Check URL bar: Should be /projects/9/speech-to-text?page=24
2. Check console: Should see Vue initialization logs
3. Check page: Should see annotation interface (NOT blank)
```

### **Step 3: Network Tab**

If blank page in new tab:
```
1. Open DevTools → Network tab
2. Look for failed requests
3. Check if Vue bundle files loaded
4. Check if API calls succeeded
```

## 📊 **Success Criteria:**

✅ **Minimum Success:**
- New tab opens
- Annotation interface loads (not blank)
- User can annotate
- Audio plays

✅ **Full Success:**
- New tab opens
- Shows correct page number
- Example matches what user clicked
- Can navigate between examples
- Can approve/reject

## 🎯 **Test Cases:**

### **Test 1: First Example**
- Click Annotate on example ID 1
- Should open page 0

### **Test 2: Middle Example**
- Click Annotate on example ID 2446
- Should open page 244

### **Test 3: Last Example**
- Click Annotate on example ID 5400
- Should open page 540

### **Test 4: After Filtering**
- Filter by "Submitted" (e.g., 10 examples)
- Click on 5th submitted example
- Should calculate page based on FULL dataset (not filtered)

### **Test 5: Different Project Types**
- Test with Speech-to-Text project
- Test with Document Classification (if available)
- Verify project_type_slug works

## 📝 **Feedback Needed:**

After testing, please report:

1. **Did new tab open?** (Yes/No)
2. **Did annotation interface load?** (Yes/No/Blank)
3. **Was it the correct page?** (Yes/No/Wrong page)
4. **Can you annotate?** (Yes/No)
5. **Any console errors?** (Copy/paste)

## 🔄 **Rollback Plan:**

If this doesn't work, we have 3 options:

**Option 1:** Go back to auto-click "Start Annotation" workaround
**Option 2:** Try opening `/projects/9/` (home) in new tab, then auto-click
**Option 3:** Implement full SPA integration (3+ hours work)

---

**Current Version:** HYBRID_NEW_TAB_V1  
**Deployed:** Waiting for Render deployment  
**Status:** Ready for testing 🧪

