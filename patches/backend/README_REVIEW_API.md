# Review API Integration Guide

## Overview

The Review API provides a backend-only solution for approve/reject functionality. The frontend makes a simple API call, and the backend automatically finds the current example.

## Backend Endpoint

**Endpoint:** `POST /v1/projects/{project_id}/review-current/`

**Request Body:**
```json
{
  "action": "approve" | "reject",
  "notes": "optional notes"
}
```

**Response:**
```json
{
  "status": "success",
  "action": "approve",
  "example_id": 123,
  "reviewed_by": "approver01",
  "message": "Successfully approved example 123"
}
```

## How It Works

1. **Frontend:** Makes simple POST request with only `project_id` and `action`
2. **Backend:** Automatically finds the current example using Doccano's logic:
   - Checks for unconfirmed examples
   - Respects collaborative vs individual mode
   - Falls back to last example if all confirmed
3. **Backend:** Updates database (ExampleState, Comment, annotations_approved_by)
4. **Frontend:** Reloads page to show updated state

## URL Integration

To make this endpoint accessible, you need to add it to Doccano's URL configuration.

### Option 1: Patch Doccano's main urls.py

Add to `/doccano/backend/config/urls.py`:

```python
from examples.review_api import review_current_example_simple

urlpatterns = [
    # ... existing patterns ...
    path('v1/projects/<int:project_id>/review-current/', review_current_example_simple, name='review-current'),
]
```

### Option 2: Use Django REST Framework Router

If Doccano uses DRF routers, add as a custom action to the examples router.

### Option 3: Middleware Approach (Advanced)

Create middleware that intercepts requests to `/v1/projects/*/review-current/` and routes them to the review function.

## Frontend Changes

The frontend HTML now contains:
- **Minimal code:** Just one `fetch()` call
- **No DOM parsing:** Backend handles everything
- **No API interceptors:** Simple direct call
- **No periodic checks:** Backend finds current example

## Benefits

✅ **No complex HTML changes** - Just one API call  
✅ **Backend handles logic** - More reliable  
✅ **No example ID needed** - Backend finds it automatically  
✅ **Works with Doccano's workflow** - Uses existing ExampleState logic  
✅ **Database-backed** - All reviews saved to PostgreSQL  

## Testing

```bash
# Test approve
curl -X POST https://monlam-annotate.onrender.com/v1/projects/1/review-current/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"action": "approve", "notes": "Looks good"}'

# Test reject
curl -X POST https://monlam-annotate.onrender.com/v1/projects/1/review-current/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"action": "reject", "notes": "Needs revision"}'
```

