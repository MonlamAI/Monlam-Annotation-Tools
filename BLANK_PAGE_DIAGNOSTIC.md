# 🔍 **Diagnostic Guide: Blank Annotation Page**

## 🚨 **Issue:**

User clicks "Annotate" button → Page navigates to correct URL → BUT page is **completely blank**

**URL:** `https://annotate.monlam.ai/projects/9/speech-to-text?page=0&q&isChecked`

**What's visible:**
- ✅ Left menu sidebar
- ❌ Nothing else (blank white/grey area)

---

## 🔧 **Step 1: Check Browser Console (MOST IMPORTANT!)**

### **How to Open Console:**

**Windows/Linux:** Press `F12` or `Ctrl + Shift + I`
**Mac:** Press `Cmd + Option + I`

### **What to Look For:**

Click on the **Console** tab and look for **RED error messages**.

### **Common Errors:**

**Error 1: Vue Not Loaded**
```
Uncaught ReferenceError: Vue is not defined
```
**Solution:** JavaScript files not loading. Check network tab.

**Error 2: API Errors**
```
GET /v1/projects/9/examples 403 Forbidden
GET /v1/projects/9/examples 404 Not Found
```
**Solution:** User doesn't have access or examples don't exist.

**Error 3: Route Not Found**
```
[Vue warn]: Failed to mount app
[Vue Router] No match for /speech-to-text
```
**Solution:** Routing issue with Doccano.

**Error 4: CORS Errors**
```
Access blocked by CORS policy
```
**Solution:** S3 CORS configuration needed.

### **Send Me:**
- Screenshot of Console tab
- Copy-paste ALL red error messages

---

## 🔧 **Step 2: Check Network Tab**

### **In DevTools:**

1. Click **Network** tab
2. Refresh the page (`Ctrl + R` or `Cmd + R`)
3. Look for failed requests (red text)

### **Check These:**

**JavaScript Files:**
- Do you see files like `app.js`, `chunk-vendors.js`, `9e09696.js`?
- Are they loading (green 200 status)?
- Or failing (red 404/403/500)?

**API Calls:**
- Do you see `/v1/projects/9/examples`?
- What status code? 200 (good), 403/404/500 (bad)?

### **Send Me:**
- Screenshot of Network tab showing all requests
- Highlight any RED (failed) requests

---

## 🔧 **Step 3: Try "Start Annotation" Button**

### **What to Do:**

1. I see a blue **"Start Annotation"** button at top left
2. Click that button
3. What happens?

### **If It Works:**
- ✅ Annotation interface appears
- **Problem:** The "Annotate" button navigation is wrong
- **Solution:** We need to match how "Start Annotation" works

### **If It Doesn't Work:**
- ❌ Still blank or error
- **Problem:** Something fundamental with Doccano's annotation route
- **Solution:** Check console errors first

---

## 🔧 **Step 4: Check Enhanced Dataset Page**

### **Go Back To:**

`https://annotate.monlam.ai/monlam/9/dataset-enhanced/`

### **Check:**

1. How many rows in the table?
2. Do you see any examples with data?
3. Do you see status badges (pending, in-progress, etc.)?
4. Does the table look normal?

### **Send Me:**
- Screenshot of the enhanced dataset page
- Tell me how many examples are shown

---

## 🔧 **Step 5: Try Direct URL**

### **Type This Directly in Browser:**

```
https://annotate.monlam.ai/projects/9/speech-to-text
```

(No parameters like `?page=0&q&isChecked`)

### **What Happens?**

**If It Works:**
- ✅ Annotation interface loads
- **Problem:** The URL parameters are breaking it
- **Solution:** Already fixed (simplified navigation pushed to GitHub)

**If Still Blank:**
- ❌ Same blank page
- **Problem:** Deeper issue with Doccano's annotation route
- **Solution:** Check console for errors

---

## 🔧 **Step 6: Check If You Have Examples**

### **Via API (In Browser Console):**

1. Open Console (F12)
2. Paste this code and press Enter:

```javascript
fetch('/v1/projects/9/examples')
  .then(r => r.json())
  .then(data => console.log('Examples:', data))
  .catch(err => console.error('Error:', err));
```

### **Expected Output:**

```javascript
{
  count: 2446,
  next: "...",
  previous: null,
  results: [
    { id: 1, text: "...", ... },
    { id: 2, text: "...", ... },
    ...
  ]
}
```

### **If You See:**

**"Error: 403 Forbidden"**
- ❌ User doesn't have permission
- Solution: Check project roles

**"Error: 404 Not Found"**
- ❌ Project doesn't exist or examples don't exist
- Solution: Upload examples first

**Empty results array**
- ❌ No examples in project
- Solution: Upload examples via dataset page

---

## 🔧 **Step 7: Check Your Role**

### **Via API (In Browser Console):**

```javascript
fetch('/v1/me')
  .then(r => r.json())
  .then(data => console.log('My user:', data))
  .catch(err => console.error('Error:', err));
```

### **Then Check Project Membership:**

```javascript
fetch('/v1/projects/9/members')
  .then(r => r.json())
  .then(data => console.log('Project members:', data))
  .catch(err => console.error('Error:', err));
```

### **Look For:**
- Is your user ID in the members list?
- What's your role? (annotator=1, approver=2, admin=3)

---

## 📊 **Common Scenarios:**

### **Scenario 1: No JavaScript Errors, Page Still Blank**

**Possible causes:**
- Vue app mounted but no content rendered
- CSS hiding everything
- Examples not loading from API

**Check:**
1. Network tab for API calls
2. Console for Vue warnings (yellow text)
3. Right-click blank area → Inspect → Check HTML structure

### **Scenario 2: JavaScript Errors Present**

**Most likely cause:**
- Doccano's Vue app failed to initialize
- Missing dependency or configuration

**Solution:**
- Send me the error messages
- I'll diagnose and fix

### **Scenario 3: "Start Annotation" Works, Annotate Button Doesn't**

**Cause:**
- URL construction is wrong
- Parameters breaking the route

**Solution:**
- Already deployed simplified navigation
- Wait for Render deployment
- Try again

---

## ✅ **What I Need From You:**

Please send me:

1. **Browser Console screenshot** (F12 → Console tab) ⚠️ MOST IMPORTANT
2. **Network tab screenshot** (F12 → Network tab → refresh page)
3. **Enhanced dataset page screenshot** (the table with examples)
4. **What happens when you click "Start Annotation" button?**
5. **Result of API test** (fetch examples from console)

---

## 🚀 **What I Just Deployed:**

**Simplified Annotate Button:**
- Now just navigates to `/projects/9/speech-to-text`
- No complex page calculation
- Let Doccano handle the rest

**Wait for Render deployment (5-10 minutes), then try again!**

---

## 🆘 **Quick Troubleshooting:**

### **Try These (In Order):**

1. **Hard refresh:** `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
2. **Clear cache:** Browser settings → Clear browsing data
3. **Try incognito/private window**
4. **Try different browser** (Chrome vs Firefox vs Safari)
5. **Check console for errors** (F12)

---

**Send me the diagnostic information above and I'll fix it!** 🔍



