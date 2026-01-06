# 🔧 **Manual Migration Fix**

## Problem:
Auto-generated migration tries to remove constraints that don't exist.

## Quick Fix (Run in Render Shell):

### **Step 1: Delete the Bad Migration**
```bash
rm /doccano/backend/assignment/migrations/0006_remove_annotatorcompletionstatus_unique_annotator_completion_and_more.py
```

### **Step 2: Create Table Manually with SQL**
```bash
python manage.py dbshell
```

Then paste this SQL:

```sql
-- Create annotation_tracking table
CREATE TABLE IF NOT EXISTS annotation_tracking (
    id BIGSERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects_project(id) ON DELETE CASCADE,
    example_id INTEGER NOT NULL REFERENCES examples_example(id) ON DELETE CASCADE,
    annotated_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    annotated_at TIMESTAMP WITH TIME ZONE,
    reviewed_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending',
    review_notes TEXT DEFAULT '',
    locked_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    locked_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(project_id, example_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS anno_track_proj_ex_idx ON annotation_tracking(project_id, example_id);
CREATE INDEX IF NOT EXISTS anno_track_proj_status_idx ON annotation_tracking(project_id, status);
CREATE INDEX IF NOT EXISTS anno_track_annotated_idx ON annotation_tracking(annotated_by_id);
CREATE INDEX IF NOT EXISTS anno_track_reviewed_idx ON annotation_tracking(reviewed_by_id);
CREATE INDEX IF NOT EXISTS anno_track_locked_idx ON annotation_tracking(locked_by_id);

-- Verify table created
\d annotation_tracking

-- Exit
\q
```

### **Step 3: Mark Migration as Applied (Fake)**
```bash
# Tell Django the migration is applied without running it
python manage.py migrate assignment --fake
```

### **Step 4: Verify Everything Works**
```bash
# Check migration status
python manage.py showmigrations assignment

# Should show all checked ✅
```

---

## Alternative: Wait for Clean Migration

I've created a clean migration file (`0006_annotation_tracking_simple.py`).

I can:
1. Delete the bad auto-generated one locally
2. Push the clean version
3. Render redeploys
4. You run: `python manage.py migrate assignment`

**Which do you prefer?**
- **Option A:** Manual SQL (5 minutes, works now)
- **Option B:** Wait for redeploy (10 minutes, cleaner)

Let me know! 🔧

