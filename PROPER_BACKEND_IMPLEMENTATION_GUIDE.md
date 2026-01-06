# 🎯 **Proper Backend Implementation Guide**

## 📋 **What This System Does:**

### **Simple Annotation Tracking (No Assignments)**

1. **Members annotate** any unannotated example
2. **System tracks** who annotated it automatically
3. **Reviewers approve/reject** using buttons on annotation page
4. **Dataset columns** show this data from database
5. **Everything** stored in PostgreSQL

---

## 🏗️ **Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Vue.js + JavaScript)                             │
│  - Dataset table (auto-populated from API)                  │
│  - Approve/Reject buttons on annotation page                │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Django REST API                                            │
│  - GET /v1/projects/{id}/examples                           │
│    → Returns examples WITH tracking data                    │
│  - POST /v1/projects/{id}/tracking/{ex_id}/approve/        │
│  - POST /v1/projects/{id}/tracking/{ex_id}/reject/         │
│  - GET /v1/projects/{id}/tracking/{ex_id}/status/          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL Database                                        │
│                                                             │
│  annotation_tracking table:                                 │
│  - id                                                       │
│  - project_id                                               │
│  - example_id                                               │
│  - annotated_by (user_id)                                   │
│  - annotated_at (timestamp)                                 │
│  - reviewed_by (user_id)                                    │
│  - reviewed_at (timestamp)                                  │
│  - status (pending/submitted/approved/rejected)             │
│  - review_notes (text)                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 **Files Created:**

### **Backend Files:**

| File | Purpose |
|------|---------|
| `patches/assignment/simple_tracking.py` | Django model for tracking |
| `patches/assignment/tracking_api.py` | REST API endpoints |
| `patches/assignment/tracking_urls.py` | URL configuration |
| `patches/assignment/migrations/0005_annotation_tracking.py` | Database migration |
| `patches/backend/examples_serializer_patch.py` | Extend examples API (UPDATED) |

### **Frontend Files:**

| File | Purpose |
|------|---------|
| `patches/frontend/approve-reject-buttons-proper.js` | Buttons on annotation page |

---

## 🚀 **Implementation Steps:**

### **Step 1: Update Dockerfile**

Add these lines to apply the tracking system:

```dockerfile
# Copy tracking files
COPY patches/assignment/simple_tracking.py /doccano/backend/assignment/
COPY patches/assignment/tracking_api.py /doccano/backend/assignment/
COPY patches/assignment/tracking_urls.py /doccano/backend/assignment/
COPY patches/assignment/migrations/0005_annotation_tracking.py /doccano/backend/assignment/migrations/

# Patch examples serializer to include tracking data
COPY patches/backend/examples_serializer_patch.py /doccano/backend/examples/serializers.py

# Register tracking API URLs
RUN if ! grep -q "tracking.urls" /doccano/backend/config/urls.py; then \
        sed -i "s|path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),|path('v1/projects/<int:project_id>/assignments/', include('assignment.urls')),\n    path('v1/projects/<int:project_id>/tracking/', include('assignment.tracking_urls')),|" /doccano/backend/config/urls.py; \
    fi
```

### **Step 2: Add Frontend Integration**

Update `patches/frontend/index.html` to include approve/reject buttons:

```html
<!-- After audio loop script -->
<script src="/static/approve-reject-buttons-proper.js"></script>
```

OR inline the script (better for reliability):

```javascript
// Add the contents of approve-reject-buttons-proper.js inline
```

### **Step 3: Run Migration**

After deployment to Render:

```bash
# SSH into Render shell
python manage.py migrate assignment

# Should create annotation_tracking table
```

### **Step 4: Test**

1. Go to dataset page - columns should show tracking data
2. Annotate an example - should auto-track
3. Click approve button - should save to database
4. Refresh dataset - should see updated status

---

## 🔄 **How It Works:**

### **1. Dataset Columns (Automatic)**

When user visits dataset page:

```javascript
// Old approach (CURRENT):
1. Fetch examples: GET /v1/projects/9/examples
2. Fetch tracking separately: GET /v1/projects/9/assignments/
3. Manually match and insert columns

// New approach (AFTER BACKEND PATCH):
1. Fetch examples: GET /v1/projects/9/examples
   → Response includes tracking data:
   {
     "id": 1,
     "text": "...",
     "annotated_by_username": "john_doe",
     "reviewed_by_username": "jane_admin",
     "tracking_status": "approved"
   }
2. Vue automatically displays columns ✅
```

### **2. Approve/Reject Buttons**

On annotation page:

```javascript
// User clicks "Approve"
1. POST /v1/projects/9/tracking/123/approve/
2. Backend saves to annotation_tracking table
3. Button shows success
4. Auto-advances to next example

// User clicks "Reject"
1. Prompt for reason
2. POST /v1/projects/9/tracking/123/reject/
   Body: { "review_notes": "Needs correction" }
3. Backend saves to database
4. Button shows success
5. Auto-advances to next example
```

### **3. Database Tracking**

When annotation is saved (auto-tracked):

```python
# Hook into Doccano's save annotation logic
# (Add this to tracking_api.py or use Django signals)

from django.db.models.signals import post_save
from examples.models import Example

@receiver(post_save, sender=Example)
def track_annotation(sender, instance, created, **kwargs):
    if created or instance.is_confirmed:
        AnnotationTracking.objects.update_or_create(
            project=instance.project,
            example=instance,
            defaults={
                'annotated_by': instance.user,
                'annotated_at': timezone.now(),
                'status': 'submitted'
            }
        )
```

---

## ✅ **Benefits:**

### **For Users:**
- ✅ Simple workflow (no assignments needed)
- ✅ Any member can annotate any unannotated example
- ✅ Clear visibility of who did what
- ✅ Easy approve/reject interface

### **For System:**
- ✅ Efficient (single API call for examples + tracking)
- ✅ Fast (database JOIN instead of separate queries)
- ✅ Scalable (proper indexing)
- ✅ Maintainable (proper Django models and API)

### **For Developers:**
- ✅ Clean architecture
- ✅ Standard Django patterns
- ✅ RESTful API
- ✅ Easy to extend

---

## 🧪 **Testing Checklist:**

### **Test 1: Dataset Columns**
```
- [ ] Go to dataset page
- [ ] Columns show at positions 4, 5, 6
- [ ] "Annotated By" shows username
- [ ] "Reviewed By" shows username  
- [ ] "Status" shows colored badge
- [ ] Data comes from database (not hardcoded)
```

### **Test 2: Approve Buttons**
```
- [ ] Go to annotation page
- [ ] See approve/reject buttons underneath label box
- [ ] Click "Approve" - saves successfully
- [ ] Auto-advances to next example
- [ ] Check database - status is "approved"
```

### **Test 3: Reject Buttons**
```
- [ ] Go to annotation page with submitted example
- [ ] Click "Reject"
- [ ] Prompted for reason
- [ ] Enter reason, submit
- [ ] Saves successfully
- [ ] Auto-advances to next example
- [ ] Check database - status is "rejected" with notes
```

### **Test 4: Data Persistence**
```
- [ ] Approve an example
- [ ] Refresh dataset page
- [ ] Status shows "APPROVED"
- [ ] Reviewed By shows your username
- [ ] Data persists after page reload
```

---

## 🎯 **Current Status:**

### **Files Ready:**
✅ Backend models  
✅ REST API endpoints  
✅ Database migration  
✅ Examples serializer patch  
✅ Frontend buttons  
✅ URL configuration  

### **Next Steps:**
1. Update Dockerfile to include all files
2. Deploy to Render
3. Run migration
4. Test!

---

## 🔧 **Troubleshooting:**

### **Problem: Columns don't show data**
**Solution:** Check if examples serializer patch is applied correctly
```bash
# Verify patch
cat /doccano/backend/examples/serializers.py | grep tracking_status
```

### **Problem: Approve button doesn't work**
**Solution:** Check API endpoint is registered
```bash
# Verify URL
cat /doccano/backend/config/urls.py | grep tracking
```

### **Problem: Migration fails**
**Solution:** Check if table already exists
```bash
python manage.py dbshell
\d annotation_tracking
```

---

## 📊 **Database Schema:**

```sql
CREATE TABLE annotation_tracking (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects_project(id),
    example_id INTEGER NOT NULL REFERENCES examples_example(id),
    annotated_by_id INTEGER REFERENCES auth_user(id),
    annotated_at TIMESTAMP,
    reviewed_by_id INTEGER REFERENCES auth_user(id),
    reviewed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    review_notes TEXT DEFAULT '',
    UNIQUE(project_id, example_id)
);

CREATE INDEX annotation_project_example_idx ON annotation_tracking(project_id, example_id);
CREATE INDEX annotation_project_status_idx ON annotation_tracking(project_id, status);
CREATE INDEX annotation_annotated_by_idx ON annotation_tracking(annotated_by_id);
CREATE INDEX annotation_reviewed_by_idx ON annotation_tracking(reviewed_by_id);
```

---

## 🎉 **Summary:**

**Simple System:**
- No complex assignments
- Anyone can annotate unannotated examples
- Approve/reject buttons on annotation page
- Everything tracked in database
- Dataset columns auto-populated from API

**Proper Implementation:**
- Backend: Django models + REST API
- Frontend: Vue-aware, efficient
- Database: Proper schema with indexes
- Clean, maintainable, scalable

**Ready to deploy!** 🚀

