# 🔧 **S3 CORS Configuration Fix**

## ⚠️ **Problem Identified:**

```
Access to fetch at 'https://monlam-ai-stt.s3.amazonaws.com/...' 
from origin 'https://annotate.monlam.ai' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**What this means:**
- The annotation page loads ✅
- But audio files from S3 can't load ❌
- S3 bucket doesn't allow requests from your domain

---

## ✅ **Solution: Update S3 CORS Settings**

### **Step 1: Go to AWS S3 Console**

1. Sign in to AWS Console
2. Go to **S3** service
3. Find and click on **`monlam-ai-stt`** bucket

### **Step 2: Navigate to CORS Settings**

1. Click on the bucket name
2. Go to **Permissions** tab
3. Scroll down to **Cross-origin resource sharing (CORS)**
4. Click **Edit** button

### **Step 3: Add CORS Configuration**

**Delete existing CORS rules (if any) and paste this:**

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "HEAD"
        ],
        "AllowedOrigins": [
            "https://annotate.monlam.ai",
            "http://localhost:8000",
            "http://localhost:3000"
        ],
        "ExposeHeaders": [
            "Content-Length",
            "Content-Type",
            "ETag"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

### **Step 4: Save Changes**

1. Click **Save changes**
2. Wait a few seconds for the changes to propagate

---

## 🧪 **Test the Fix**

After saving CORS settings:

1. **Go to annotation page:**
   ```
   https://annotate.monlam.ai/projects/9/speech-to-text?page=0
   ```

2. **Open browser console (F12)**

3. **Check for:**
   - ✅ **No CORS errors**
   - ✅ **Audio file loads successfully**
   - ✅ **You can hear the audio**

---

## 📋 **What the CORS Configuration Does:**

```json
"AllowedOrigins": [
    "https://annotate.monlam.ai",  // Your production site
    "http://localhost:8000",        // Local Django testing
    "http://localhost:3000"         // Local frontend testing
]
```

This tells S3: "Allow these domains to fetch files from this bucket"

```json
"AllowedMethods": [
    "GET",      // Read files
    "HEAD"      // Check if files exist
]
```

This allows reading files (GET) and checking metadata (HEAD).

```json
"AllowedHeaders": ["*"]
```

This allows any HTTP headers in the request.

---

## 🔍 **Common Issues:**

### **Issue 1: CORS Still Not Working**

**Try:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+F5)
3. Wait 5 minutes for S3 to propagate changes
4. Try in incognito/private browsing mode

### **Issue 2: Wrong Bucket**

**Make sure:**
- You're editing the correct bucket: `monlam-ai-stt`
- Your audio URLs use this bucket name
- Check the audio file URLs in your JSONL data

### **Issue 3: S3 Bucket is in Different Region**

**If bucket is not in us-east-1:**
- CORS settings are the same
- Make sure your audio URLs use the correct regional endpoint

---

## 🎯 **After CORS is Fixed:**

The annotation workflow will work perfectly:

1. ✅ User clicks "Annotate" in enhanced dataset
2. ✅ Navigation goes to correct page: `?page=N`
3. ✅ Doccano loads the example
4. ✅ Audio file loads from S3 (no CORS error)
5. ✅ User can listen and annotate
6. ✅ Approval buttons work (if example ID can be determined)

---

## 📸 **Screenshots:**

After applying CORS settings, your browser console should show:

```
✅ GET https://monlam-ai-stt.s3.amazonaws.com/...wav 200 OK
✅ [Monlam Audio] Loop enabled
```

Instead of:

```
❌ ERR_FAILED
❌ blocked by CORS policy
```

---

## 🆘 **Still Having Issues?**

If CORS is fixed but audio still doesn't play:

1. Check if audio file exists in S3
2. Check if file is public or requires authentication
3. Check if the URL in your JSONL is correct
4. Try opening the audio URL directly in browser

---

**Update S3 CORS settings and the audio will load!** 🎵



