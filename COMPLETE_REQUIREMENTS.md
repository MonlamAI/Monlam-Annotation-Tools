# 📋 COMPLETE REQUIREMENTS - Monlam Doccano Customization

**Project:** Monlam Annotation Tools (Custom Doccano)  
**Goal:** Production-grade annotation tracking with Tibetan language support  
**Tech Stack:** Django (backend), Vue.js (frontend), PostgreSQL (database)

---

## 🎯 CORE REQUIREMENTS

### **1. ANNOTATION TRACKING SYSTEM**

#### **1.1 Database Model: `AnnotationTracking`**

**Location:** Django model in `backend/`

**Fields:**
```python
class AnnotationTracking(models.Model):
    project = ForeignKey('projects.Project')
    example = ForeignKey('examples.Example')
    
    # Tracking fields
    annotated_by = ForeignKey(User, related_name='annotations_tracked', null=True)
    annotated_at = DateTimeField(null=True)
    reviewed_by = ForeignKey(User, related_name='reviews_tracked', null=True)
    reviewed_at = DateTimeField(null=True)
    
    # Status tracking
    status = CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    
    # Review notes
    review_notes = TextField(blank=True, default='')
    
    # Example locking (prevent simultaneous editing)
    locked_by = ForeignKey(User, related_name='locked_examples', null=True)
    locked_at = DateTimeField(null=True)
    
    class Meta:
        unique_together = ('project', 'example')
        indexes = [
            Index(fields=['project', 'example']),
            Index(fields=['project', 'status']),
            Index(fields=['annotated_by']),
            Index(fields=['reviewed_by']),
            Index(fields=['locked_by']),
        ]
```

**Requirements:**
- ✅ One tracking record per (project, example) pair
- ✅ Tracks who annotated and who reviewed
- ✅ Tracks timestamps for both actions
- ✅ Stores review notes (especially for rejections)
- ✅ Supports example locking to prevent conflicts

---

### **2. ROLE-BASED ACCESS CONTROL**

#### **2.1 User Roles**

| Role | Can Annotate | Can Review | Can See All | Can Manage |
|------|--------------|------------|-------------|------------|
| **Annotator** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Approver** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Project Manager** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Limited |
| **Project Admin** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Full |

**Note:** Project Manager is essentially Approver + visibility of completion matrix.

#### **2.2 Permissions**

**Annotators:**
- Can annotate examples that are:
  - `pending` (not yet annotated by anyone)
  - `rejected` AND annotated by them (for revision)
- **Cannot see** examples annotated by others
- **Cannot see** examples that are `submitted`, `approved`, or rejected by others

**Approvers & Project Managers:**
- Can see **ALL** examples regardless of status
- Can approve or reject any submitted annotation
- Can add review notes

**Project Admins:**
- Full access to everything
- Can upload/download datasets
- Can manage project settings

---

### **3. VISIBILITY FILTERING (CRITICAL)**

#### **3.1 Annotator Visibility Rules**

**Rule:** Annotators should ONLY see:
1. Examples that are `pending` (unannotated)
2. Examples that are `rejected` AND annotated by them (for re-work)

**Rule:** Annotators should NOT see:
- Examples annotated by other annotators (prevents double-editing)
- Examples with status `submitted`, `approved`
- Examples with status `rejected` but annotated by someone else

**Implementation:** DRF Filter Backend on `ExampleListAPI`

```python
class AnnotationVisibilityFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        user = request.user
        project_id = view.kwargs.get('project_id')
        
        # Superusers/Admins see everything
        if user.is_superuser:
            return queryset
        
        # Get user's role in project
        role = get_user_role(user, project_id)
        
        # Project Managers and Reviewers see all examples
        if role in ['project_manager', 'approver']:
            return queryset
        
        # Annotators: filtered visibility
        if role == 'annotator':
            return queryset.filter(
                Q(id__in=get_pending_examples(project_id)) |
                Q(id__in=get_rejected_by_user(project_id, user))
            )
        
        return queryset.none()
```

#### **3.2 Example Locking**

**Purpose:** Prevent two annotators from editing the same example simultaneously.

**Workflow:**
1. User opens an example → Lock it (`locked_by` = user, `locked_at` = now)
2. Other users see "Locked by [username]" or cannot open it
3. User saves/closes → Release lock (`locked_by` = NULL, `locked_at` = NULL)
4. Optional: Auto-release lock after timeout (e.g., 15 minutes of inactivity)

---

### **4. AUTO-TRACKING WITH DJANGO SIGNALS**

#### **4.1 Automatic Status Updates**

**Trigger:** When an annotator saves an annotation

**Action:**
```python
@receiver(post_save, sender=Category)  # or Span, TextLabel, etc.
def track_annotation(sender, instance, created, **kwargs):
    if created:
        tracking, _ = AnnotationTracking.objects.get_or_create(
            project=instance.project,
            example=instance.example,
            defaults={
                'annotated_by': instance.user,
                'annotated_at': timezone.now(),
                'status': 'submitted'
            }
        )
```

**Requirements:**
- ✅ Automatically creates/updates tracking record when annotation is saved
- ✅ Sets `annotated_by` to current user
- ✅ Sets `annotated_at` to current timestamp
- ✅ Changes status from `pending` → `submitted`
- ✅ No manual intervention needed

---

### **5. DATASET TABLE ENHANCEMENTS**

#### **5.1 Additional Columns**

**Location:** Dataset page (`/projects/{id}/dataset`)

**Add 3 columns at positions 4, 5, 6:**

| Position | Column Name | Data Source | Format |
|----------|-------------|-------------|--------|
| 4 | **Annotated By** | `AnnotationTracking.annotated_by.username` | Text (username) or "—" |
| 5 | **Reviewed By** | `AnnotationTracking.reviewed_by.username` | Text (username) or "—" |
| 6 | **Status** | `AnnotationTracking.status` | Badge with color |

**Status Badge Colors:**
- `pending`: Gray (#e0e0e0)
- `in_progress`: Blue (#2196f3)
- `submitted`: Orange (#ff9800)
- `approved`: Green (#4caf50)
- `rejected`: Red (#f44336)

#### **5.2 Data Source**

**Approach:** Extend Doccano's `ExampleSerializer` to include tracking data

```python
class EnhancedExampleSerializer(ExampleSerializer):
    annotated_by = SerializerMethodField()
    reviewed_by = SerializerMethodField()
    status = SerializerMethodField()
    
    class Meta(ExampleSerializer.Meta):
        fields = ExampleSerializer.Meta.fields + (
            'annotated_by', 'reviewed_by', 'status'
        )
    
    def get_annotated_by(self, obj):
        tracking = AnnotationTracking.objects.filter(example=obj).first()
        return tracking.annotated_by.username if tracking and tracking.annotated_by else None
    
    # Similar for reviewed_by and status
```

**Vue Component:** Modify the dataset table component to display these fields

---

### **6. APPROVE/REJECT WORKFLOW**

#### **6.1 UI Components**

**Location:** Annotation page (all types: STT, sequence labeling, etc.)

**For:** Approvers and Project Managers only

**Design:**
- Fixed position at bottom-right corner
- Floating card design with shadow
- Contains:
  1. **Status Display** (left): Shows current status and annotator
  2. **Approve Button** (middle): Green, "✓ Approve"
  3. **Reject Button** (right): Red, "✗ Reject"

**Example:**
```
┌─────────────────────────────────────────────────────┐
│ Status: SUBMITTED by john  [✓ Approve] [✗ Reject]  │
└─────────────────────────────────────────────────────┘
```

#### **6.2 Approve Workflow**

**Trigger:** Reviewer clicks "✓ Approve"

**Steps:**
1. Optional prompt: "Approval notes (optional):"
2. API call: `POST /v1/projects/{id}/tracking/{example_id}/approve/`
3. Update tracking:
   - `status` = 'approved'
   - `reviewed_by` = current user
   - `reviewed_at` = current timestamp
   - `review_notes` = user's notes
4. Success message: "✅ Example approved successfully!"
5. Status display updates to "APPROVED by [reviewer]"
6. Example becomes hidden from annotators

#### **6.3 Reject Workflow**

**Trigger:** Reviewer clicks "✗ Reject"

**Steps:**
1. **Required** prompt: "Rejection reason (required):"
2. Validate: Must provide reason (cannot be empty)
3. API call: `POST /v1/projects/{id}/tracking/{example_id}/reject/`
4. Update tracking:
   - `status` = 'rejected'
   - `reviewed_by` = current user
   - `reviewed_at` = current timestamp
   - `review_notes` = rejection reason
5. Success message: "✅ Example rejected. Annotator will see it again for revision."
6. Example becomes visible to **original annotator only** (not other annotators)
7. Annotator can re-annotate and re-submit

#### **6.4 Auto-Update**

**Requirement:** Status display should update automatically when:
- User navigates to next/previous example
- Another reviewer approves/rejects
- Polling or WebSocket updates

---

### **7. COMPLETION METRICS DASHBOARD**

#### **7.1 Redirect**

**Requirement:** When user clicks "Metrics" in left menu, redirect to custom completion dashboard.

**From:** `/projects/{id}/metrics`  
**To:** `/monlam/{id}/completion/`

**Implementation:** Client-side redirect or Vue Router configuration

#### **7.2 Dashboard Content**

**Display:**

**Section 1: Overall Progress**
```
Total Examples: 100
Pending: 20 (20%)
In Progress: 10 (10%)
Submitted: 30 (30%)
Approved: 35 (35%)
Rejected: 5 (5%)
```

**Section 2: Annotator Performance**
```
| Annotator | Completed | Approved | Rejected | Success Rate |
|-----------|-----------|----------|----------|--------------|
| john      | 25        | 23       | 2        | 92%          |
| mary      | 30        | 28       | 2        | 93%          |
| ...       |           |          |          |              |
```

**Section 3: Reviewer Performance**
```
| Reviewer | Reviewed | Approved | Rejected | Approval Rate |
|----------|----------|----------|----------|---------------|
| admin    | 40       | 35       | 5        | 87.5%         |
| ...      |          |          |          |               |
```

**Section 4: Timeline** (optional)
- Line chart showing daily completion rate
- Bar chart showing status distribution over time

---

### **8. AUDIO AUTO-LOOP (STT Projects)**

#### **8.1 Requirement**

**For:** Speech-to-Text annotation pages only

**Behavior:**
1. When user opens an example with audio → Audio plays automatically
2. Audio loops continuously (repeats when finished)
3. No visible loop button needed (automatic)
4. Audio plays ONLY on annotation pages
5. Audio does NOT play on dataset table page (would play all at once)

#### **8.2 Implementation**

**Vue Component:** Modify STT annotation component

```javascript
// In AudioPlayer component or similar
mounted() {
  if (this.$route.path.includes('/speech-to-text')) {
    this.$nextTick(() => {
      const audio = this.$refs.audioPlayer;
      if (audio) {
        audio.loop = true;
        audio.play().catch(e => {
          // Auto-play blocked, wait for user interaction
          document.addEventListener('click', () => audio.play(), { once: true });
        });
      }
    });
  }
}
```

**Requirements:**
- ✅ Auto-play on load (if browser allows)
- ✅ Loop continuously
- ✅ Handle browser auto-play restrictions gracefully
- ✅ Only on annotation pages, not dataset pages

---

### **9. TIBETAN LANGUAGE SUPPORT**

#### **9.1 Font**

**Font:** MonlamTBslim

**Requirement:**
- Replace Roboto font with MonlamTBslim throughout the application
- Ensure proper rendering of Tibetan script (དབུ་ཅན་)
- Font should be embedded/hosted locally (not CDN)

**Implementation:**
```css
@font-face {
  font-family: 'MonlamTBslim';
  src: url('/static/fonts/MonlamTBslim.woff2') format('woff2'),
       url('/static/fonts/MonlamTBslim.woff') format('woff'),
       url('/static/fonts/MonlamTBslim.ttf') format('truetype');
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}

body, * {
  font-family: 'MonlamTBslim', 'Noto Sans Tibetan', sans-serif !important;
}
```

#### **9.2 UI Text**

**Requirement:** Tibetan text in menus and labels

**Examples:**
- "གཞི་གྲངས།" (Dataset)
- Other Tibetan UI elements as specified

**Implementation:** Django i18n or direct template/component modification

---

### **10. BRANDING**

#### **10.1 Colors**

**Primary Colors:**
- Monlam Gold: `#B8963E`
- Monlam Gold Dark: `#9A7B32`
- Monlam Navy: `#1a1a2e`

**Apply to:**
- Navbar background: Navy
- Primary buttons: Gold
- Active menu items: Gold
- Links: Gold
- Progress bars: Gold

#### **10.2 Logo & Favicon**

**Requirement:**
- Replace Doccano branding with Monlam branding
- Custom favicon
- Logo in navbar

#### **10.3 Remove GitHub Links**

**Requirement:** Hide all GitHub-related buttons and links

```css
a[href*="github.com"],
button[class*="github"] {
  display: none !important;
}
```

---

## 🏗️ ARCHITECTURE REQUIREMENTS

### **11. BACKEND STRUCTURE**

#### **11.1 Django Apps**

**Create custom Django apps:**

1. **`monlam_tracking`** - Annotation tracking system
   - Models: `AnnotationTracking`
   - Views/ViewSets: Tracking API endpoints
   - Filters: `AnnotationVisibilityFilter`
   - Signals: Auto-tracking on annotation save

2. **`monlam_ui`** - Custom UI components
   - Views: Completion dashboard
   - Templates: Custom pages
   - Static files: Fonts, images

#### **11.2 API Endpoints**

**Base URL:** `/v1/projects/{project_id}/tracking/`

**Endpoints:**
```
GET    /v1/projects/{id}/tracking/                    # List all tracking records
GET    /v1/projects/{id}/tracking/{example_id}/       # Get specific tracking
GET    /v1/projects/{id}/tracking/{example_id}/status/ # Get status only
POST   /v1/projects/{id}/tracking/{example_id}/approve/ # Approve example
POST   /v1/projects/{id}/tracking/{example_id}/reject/  # Reject example
POST   /v1/projects/{id}/tracking/mark-submitted/      # Mark as submitted
POST   /v1/projects/{id}/tracking/{example_id}/lock/   # Lock example
POST   /v1/projects/{id}/tracking/{example_id}/unlock/ # Unlock example
```

**Completion Metrics:**
```
GET    /monlam/{id}/completion/  # Completion dashboard page
GET    /v1/projects/{id}/tracking/summary/  # Summary stats (JSON)
GET    /v1/projects/{id}/tracking/annotators/  # Annotator performance
GET    /v1/projects/{id}/tracking/approvers/   # Reviewer performance
```

---

### **12. FRONTEND STRUCTURE**

#### **12.1 Vue Components to Modify**

**Dataset Table:**
- File: `frontend/components/dataset/DatasetTable.vue` (or similar)
- Modify: Add columns for `annotated_by`, `reviewed_by`, `status`
- Fetch: Enhanced example data from API

**Annotation Pages:**
- Files: `frontend/components/annotation/*` (STT, sequence labeling, etc.)
- Add: Approve/Reject button component
- Add: Status display component
- Add: Audio auto-loop for STT

**Metrics Page:**
- File: `frontend/pages/projects/_id/metrics.vue` (or similar)
- Modify: Redirect to `/monlam/{id}/completion/`
- Or: Replace with custom completion dashboard

**Menu:**
- File: `frontend/components/layout/Menu.vue` (or similar)
- Modify: Tibetan labels
- Add: Custom menu items if needed

#### **12.2 New Vue Components**

**`ApproveRejectButtons.vue`:**
```vue
<template>
  <div class="approve-reject-container">
    <div class="status-display">
      Status: {{ status }} by {{ annotatedBy }}
    </div>
    <v-btn color="success" @click="approve">
      ✓ Approve
    </v-btn>
    <v-btn color="error" @click="reject">
      ✗ Reject
    </v-btn>
  </div>
</template>

<script>
export default {
  props: ['exampleId', 'projectId'],
  data() {
    return {
      status: 'loading',
      annotatedBy: null
    }
  },
  methods: {
    async approve() {
      // API call to approve
    },
    async reject() {
      // API call to reject
    },
    async fetchStatus() {
      // API call to get status
    }
  },
  mounted() {
    this.fetchStatus()
  }
}
</script>
```

**`CompletionDashboard.vue`:**
- Display overall progress
- Display annotator performance table
- Display reviewer performance table
- Charts (optional)

---

## 🧪 TESTING REQUIREMENTS

### **13. FUNCTIONAL TESTING**

#### **13.1 Annotator Workflow**

**Test Case 1: Basic Annotation**
```
1. Login as Annotator A
2. Go to project dataset
3. Should see only pending examples ✅
4. Click "Annotate" on Example #1
5. Add annotation (label/text/etc.)
6. Save
7. Go back to dataset
8. Example #1 should NOT be visible ✅
9. Status in tracking table should be "submitted" ✅
```

**Test Case 2: Visibility Isolation**
```
1. Login as Annotator A, annotate Example #5
2. Logout, login as Annotator B
3. Go to project dataset
4. Example #5 should NOT be visible to Annotator B ✅
5. Annotator B should only see unannotated examples ✅
```

**Test Case 3: Rejection & Re-work**
```
1. Annotator A submits Example #10
2. Login as Reviewer, reject Example #10 with notes
3. Login as Annotator A
4. Example #10 should NOW be visible ✅
5. Status shows "rejected" ✅
6. Can re-annotate and re-submit ✅
7. After re-submit, example disappears again ✅
```

#### **13.2 Reviewer Workflow**

**Test Case 4: Approve**
```
1. Login as Reviewer
2. Go to annotation page with submitted example
3. Approve/Reject buttons appear at bottom-right ✅
4. Status display shows "SUBMITTED by [username]" ✅
5. Click "Approve", add optional notes
6. Success message appears ✅
7. Status updates to "APPROVED" ✅
8. Example hidden from annotators ✅
```

**Test Case 5: Reject**
```
1. Login as Reviewer
2. Find submitted example
3. Click "Reject"
4. Prompt requires rejection reason ✅
5. Cannot submit empty reason ✅
6. After rejection, status = "REJECTED" ✅
7. Example visible to original annotator only ✅
```

#### **13.3 UI/UX Testing**

**Test Case 6: Dataset Table**
```
1. Go to dataset page
2. Verify columns:
   - Column 1, 2, 3: Original Doccano columns ✅
   - Column 4: "Annotated By" ✅
   - Column 5: "Reviewed By" ✅
   - Column 6: "Status" (colored badge) ✅
3. Verify data aligns with headers ✅
4. Verify status colors match specification ✅
```

**Test Case 7: Audio Loop**
```
1. Go to STT annotation page
2. Audio should play automatically (or after first click) ✅
3. Audio should loop continuously ✅
4. No visible loop button needed ✅
5. Go to dataset page
6. Audio should NOT play ✅
```

**Test Case 8: Metrics Redirect**
```
1. Go to project home
2. Click "Metrics" in left menu
3. Should redirect to /monlam/{id}/completion/ ✅
4. Should show completion dashboard ✅
5. No old metrics page ✅
```

---

## 🚀 DEPLOYMENT REQUIREMENTS

### **14. DOCKER & DOCKER COMPOSE**

**Requirement:** Maintain Docker-based deployment

**Files:**
- `Dockerfile` - Build instructions
- `docker-compose.yml` - Service orchestration
- `.dockerignore` - Exclude unnecessary files

**Services:**
- `backend` (Django/DRF)
- `frontend` (Vue.js, built into static files)
- `postgres` (Database)
- `nginx` (Reverse proxy, optional)

### **15. RENDER DEPLOYMENT**

**Platform:** Render.com

**Files:**
- `render.yaml` - Blueprint for Render services

**Services:**
- Web service (Docker-based)
- PostgreSQL database

**Environment Variables:**
- `DATABASE_URL`
- `SECRET_KEY`
- `DJANGO_SETTINGS_MODULE`
- AWS S3 credentials (for file storage)
- Other config as needed

**Post-Deploy:**
- Run migrations: `python manage.py migrate`
- Collect static files: `python manage.py collectstatic --noinput`
- Create superuser (if needed)

---

## 📊 DATA REQUIREMENTS

### **16. DATABASE MIGRATIONS**

**Requirement:** All schema changes must be versioned via Django migrations

**Process:**
1. Make model changes
2. Run `python manage.py makemigrations`
3. Review migration file
4. Test locally
5. Deploy
6. Run `python manage.py migrate` on server

**Critical Migrations:**
- `0001_initial` - Initial AnnotationTracking model
- `0002_add_locking` - Add locked_by, locked_at fields
- `0003_add_indexes` - Performance indexes

### **17. EXISTING DATA**

**Requirement:** Do not break existing annotations

**Approach:**
- New tracking system should work alongside existing annotations
- Backfill tracking data for existing annotations (optional)
- Gracefully handle examples without tracking records (show as "pending")

---

## 🎯 PERFORMANCE REQUIREMENTS

### **18. SCALABILITY**

**Requirements:**
- System should handle 1000+ examples per project
- System should handle 50+ concurrent users
- API responses < 500ms
- Page load times < 3s

**Optimizations:**
- Database indexes on frequently queried fields
- Pagination (default: 10-20 items per page)
- Caching (Redis, optional)
- Efficient queries (select_related, prefetch_related)

### **19. BROWSER SUPPORT**

**Requirements:**
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (optional)

---

## 🔐 SECURITY REQUIREMENTS

### **20. AUTHENTICATION & AUTHORIZATION**

**Requirements:**
- Use Doccano's existing auth system
- Enforce role-based permissions at API level
- Verify user permissions before every action
- Prevent privilege escalation

**Validation:**
- Annotators cannot approve/reject
- Users cannot modify other users' annotations
- Example locking prevents concurrent edits

### **21. DATA INTEGRITY**

**Requirements:**
- Unique constraint on (project, example) for tracking
- Foreign key constraints to prevent orphaned records
- Atomic transactions for approve/reject actions
- Validation on API inputs (e.g., rejection reason required)

---

## 📚 DOCUMENTATION REQUIREMENTS

### **22. CODE DOCUMENTATION**

**Requirements:**
- Docstrings for all models, views, serializers
- Comments for complex logic
- README files in each custom app directory
- API documentation (Swagger/OpenAPI, optional)

### **23. USER DOCUMENTATION**

**Requirements:**
- User guide for annotators
- User guide for reviewers
- Admin guide for project setup
- Troubleshooting guide

---

## ✅ SUCCESS CRITERIA

### **24. DEFINITION OF DONE**

**A feature is complete when:**
1. ✅ Code is written and tested
2. ✅ Unit tests pass (if applicable)
3. ✅ Manual testing confirms functionality
4. ✅ Code is reviewed
5. ✅ Documentation is updated
6. ✅ Deployed to staging
7. ✅ User acceptance testing passes
8. ✅ Deployed to production

**Overall project is complete when:**
1. ✅ All requirements implemented
2. ✅ All tests pass
3. ✅ No critical bugs
4. ✅ Performance requirements met
5. ✅ Documentation complete
6. ✅ User training complete (if needed)
7. ✅ Production deployment successful
8. ✅ Stakeholder sign-off

---

## 🔄 WORKFLOW SUMMARY

### **25. END-TO-END WORKFLOW**

**Annotator Journey:**
```
1. Login → Dashboard
2. Select project → See only pending examples
3. Click "Annotate" → Annotation page (audio loops if STT)
4. Add annotation → Save
5. Example disappears from view (status: submitted)
6. Move to next pending example
7. If reviewer rejects → Example reappears with notes
8. Fix and re-submit → Example disappears again
```

**Reviewer Journey:**
```
1. Login → Dashboard
2. Select project → See ALL examples
3. Filter by status: "submitted"
4. Click on submitted example → Annotation page
5. Review annotation → Buttons appear at bottom-right
6. Approve (with optional notes) OR Reject (with required notes)
7. Status updates → Example hidden from annotators (if approved)
8. Move to next submitted example
```

**Project Manager Journey:**
```
1. Login → Dashboard
2. Select project
3. Click "Metrics" → Redirects to completion dashboard
4. View overall progress
5. View annotator performance table
6. View reviewer performance table
7. Identify bottlenecks or issues
8. Can also review examples like Approver
```

**Project Admin Journey:**
```
1. All of the above +
2. Upload dataset
3. Download results
4. Manage project settings
5. Add/remove members
6. Assign roles
```

---

## 🎨 UI/UX WIREFRAMES (Conceptual)

### **26. DATASET TABLE**

```
┌────────────────────────────────────────────────────────────────┐
│  ID  │  Text/Data  │  ...  │ Annotated By │ Reviewed By │ Status │
├──────┼─────────────┼───────┼──────────────┼─────────────┼────────┤
│  1   │  སངས་རྒྱས...  │  ...  │  john        │  admin      │ ✅ APPROVED │
│  2   │  བྱང་ཆུབ...  │  ...  │  mary        │  —          │ 🟠 SUBMITTED │
│  3   │  སེམས་དཔའ... │  ...  │  —           │  —          │ ⚪ PENDING │
│  4   │  ཆོས་ཉིད...  │  ...  │  john        │  admin      │ ❌ REJECTED │
└──────┴─────────────┴───────┴──────────────┴─────────────┴────────┘
```

### **27. ANNOTATION PAGE (WITH APPROVE/REJECT)**

```
┌──────────────────────────────────────────────────────────────┐
│  ← Previous  |  Project Name  |  Next →                       │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  [Audio Player - plays automatically, loops]                  │
│  ▶ ━━━━━━━━━━━━━━━━━━ 0:45 / 1:30                          │
│                                                                │
│  Transcript:                                                   │
│  ┌────────────────────────────────────────────────────┐      │
│  │  སངས་རྒྱས་བསྟན་པ་རིན་པོ་ཆེ།                              │
│  │  བྱང་ཆུབ་སེམས་དཔའི་སེམས།                               │
│  └────────────────────────────────────────────────────┘      │
│                                                                │
│  Labels: [Category Dropdown] [Add Label Button]               │
│                                                                │
│                                                                │
│                   [Save & Next] [Skip]                         │
│                                                                │
│                                      ┌────────────────────┐   │
│                                      │ Status: SUBMITTED  │   │
│                                      │   by john          │   │
│                                      │                    │   │
│                                      │  [✓ Approve]       │   │
│                                      │  [✗ Reject]        │   │
│                                      └────────────────────┘   │
│                                      ↑ Bottom-right, fixed    │
└──────────────────────────────────────────────────────────────┘
```

### **28. COMPLETION DASHBOARD**

```
┌──────────────────────────────────────────────────────────────┐
│  Project: མོན་ལམ། - དཔེ་གྲངས།  |  Completion Matrix       │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  📊 Overall Progress                                          │
│  ━━━━━━━━━━━━━━━━━━ 75% Complete                            │
│                                                                │
│  Total: 100  |  Pending: 10  |  Submitted: 15  |  Approved: 75 │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Annotator Performance                               │    │
│  ├──────────┬──────────┬──────────┬──────────┬──────┤    │
│  │ Name     │ Completed│ Approved │ Rejected │ Rate │    │
│  ├──────────┼──────────┼──────────┼──────────┼──────┤    │
│  │ john     │    25    │    23    │     2    │ 92%  │    │
│  │ mary     │    30    │    28    │     2    │ 93%  │    │
│  │ tashi    │    20    │    19    │     1    │ 95%  │    │
│  └──────────┴──────────┴──────────┴──────────┴──────┘    │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Reviewer Performance                                │    │
│  ├──────────┬──────────┬──────────┬──────────┬──────┤    │
│  │ Name     │ Reviewed │ Approved │ Rejected │ Rate │    │
│  ├──────────┼──────────┼──────────┼──────────┼──────┤    │
│  │ admin    │    40    │    35    │     5    │ 87%  │    │
│  │ reviewer1│    35    │    33    │     2    │ 94%  │    │
│  └──────────┴──────────┴──────────┴──────────┴──────┘    │
│                                                                │
│  [Export Report] [Back to Project]                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚨 CRITICAL NOTES

### **29. THINGS THAT MUST NOT BREAK**

**Do NOT break:**
- ✅ Existing Doccano annotation functionality
- ✅ Existing project management
- ✅ Existing user authentication
- ✅ Existing data export/import
- ✅ Existing API endpoints (add new ones, don't modify existing)

**Approach:**
- Extend, don't replace
- Add features alongside existing ones
- Maintain backward compatibility
- Test thoroughly before deployment

### **30. THINGS THAT NEED SPECIAL ATTENTION**

**Critical Areas:**
1. **Visibility Filtering:** Most important feature, prevents double-editing
2. **Audio Loop:** Must work reliably on STT pages
3. **Dataset Table Columns:** Must align perfectly, no misalignment
4. **Approve/Reject Buttons:** Must appear reliably, must get correct example ID
5. **Metrics Redirect:** Must work on first click, no refresh needed

**Known Challenges:**
- JavaScript patching is fragile (that's why we're moving to Vue)
- Vue Router can intercept redirects
- Audio auto-play is restricted by browsers
- Getting current example ID from Vue state can be tricky
- Race conditions in table enhancement

---

## 🎓 TECHNICAL EXPERTISE REQUIRED

### **31. SKILLS NEEDED**

**Backend:**
- Django framework (models, views, serializers)
- Django REST Framework (viewsets, filters, permissions)
- PostgreSQL (indexes, constraints, queries)
- Django signals
- Python best practices

**Frontend:**
- Vue.js 2/3 (components, Vuex, Vue Router)
- JavaScript ES6+
- Vuetify (or whatever UI framework Doccano uses)
- CSS/SCSS
- Webpack/Vite (build tools)

**DevOps:**
- Docker & Docker Compose
- Render.com deployment
- Environment variables
- Static file serving
- Database migrations

**Understanding:**
- Doccano architecture
- SPA (Single Page Application) patterns
- RESTful API design
- Role-based access control
- Internationalization (i18n)

---

## 📞 HANDOFF INFORMATION

### **32. CURRENT STATE**

**Git Repository:** https://github.com/MonlamAI/Monlam-Annotation-Tools

**Current Live Commit:** `318f73b` (on Render)

**Latest Commit:** `b9b9311` (on GitHub, but broken)

**Reason for Rollback:**
- Commits after `318f73b` broke audio loop
- JavaScript patching approach is too fragile
- Need proper Vue.js implementation

**What Works at 318f73b:**
- ✅ Audio loop (confirmed working)
- ✅ Approve/reject buttons (confirmed working)
- ❓ Dataset table columns (need to test)
- ❓ Metrics redirect (need to test)

### **33. WHAT TO START WITH**

**Phase 1: Foundation (Week 1)**
1. Clone Doccano source code
2. Set up local development environment
3. Understand Doccano's Vue structure
4. Identify Vue components to modify
5. Create custom Django apps (`monlam_tracking`, `monlam_ui`)
6. Set up database models and migrations

**Phase 2: Backend (Week 2)**
1. Implement `AnnotationTracking` model
2. Create API endpoints (approve, reject, status)
3. Implement visibility filter
4. Set up Django signals for auto-tracking
5. Extend `ExampleSerializer`
6. Test API endpoints

**Phase 3: Frontend (Week 3)**
1. Modify dataset table component (add columns)
2. Create approve/reject buttons component
3. Implement audio auto-loop in STT component
4. Create completion dashboard component
5. Set up metrics redirect
6. Apply Tibetan font and branding

**Phase 4: Testing & Deployment (Week 4)**
1. Unit tests (backend)
2. Integration tests
3. Manual testing (all workflows)
4. Docker build and test
5. Deploy to staging
6. User acceptance testing
7. Deploy to production

---

## ✅ FINAL CHECKLIST

### **34. BEFORE HANDING OFF**

**Provide to New Agent:**
- ✅ This complete requirements document
- ✅ Access to GitHub repository
- ✅ Access to Render account (or credentials)
- ✅ Database credentials
- ✅ Current working commit (`318f73b`)
- ✅ Sample data or test project

**New Agent Should:**
1. ✅ Read this document thoroughly
2. ✅ Set up local development environment
3. ✅ Clone Doccano source code
4. ✅ Understand Doccano architecture
5. ✅ Create project plan with milestones
6. ✅ Start with Phase 1 (Foundation)
7. ✅ Communicate progress regularly
8. ✅ Test each feature thoroughly
9. ✅ Deploy incrementally
10. ✅ Document all changes

---

## 🎯 SUCCESS METRICS

### **35. HOW TO MEASURE SUCCESS**

**Technical Metrics:**
- ✅ All 34 requirements implemented
- ✅ All tests pass
- ✅ No critical bugs
- ✅ API response time < 500ms
- ✅ Page load time < 3s
- ✅ Zero data loss or corruption

**User Metrics:**
- ✅ Annotators can annotate without seeing others' work
- ✅ Reviewers can approve/reject easily
- ✅ Project managers have full visibility
- ✅ Audio loop works reliably
- ✅ Dataset table shows correct data
- ✅ System is intuitive and easy to use

**Business Metrics:**
- ✅ Annotation throughput increases
- ✅ Annotation quality improves
- ✅ Fewer conflicts and duplicate work
- ✅ Better project management visibility
- ✅ Stakeholder satisfaction

---

## 🚀 LET'S DO THIS RIGHT!

**This is a comprehensive specification for a production-grade Doccano customization.**

**Hand this to your new agent along with:**
- Current codebase at `318f73b`
- Access to development environment
- Any additional context or examples

**The new agent should have expertise in:**
- Django + DRF
- Vue.js
- PostgreSQL
- Docker
- Doccano architecture

**Good luck! 🎉**

---

**Document Version:** 1.0  
**Last Updated:** January 7, 2026  
**Author:** Comprehensive requirements compilation  
**Next Steps:** Hand off to new agent for proper Vue.js implementation

