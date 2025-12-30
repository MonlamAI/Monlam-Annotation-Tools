# Adding Completion Matrix to Project Manager Dashboard

## Quick Solution: Access via URL

**Immediate Access (No code changes needed):**

```
http://your-doccano-url/projects/{project_id}/assignments/completion-matrix/
```

Example:
```
http://localhost:8000/projects/1/assignments/completion-matrix/
```

This API endpoint returns the full completion matrix JSON that you can view directly.

---

## Proper Solution: Add to Navigation Menu

To add the Completion Matrix as a menu item in the left sidebar:

### Option 1: API Access (Current - Works Now!)

Use the API endpoints directly:

```bash
# Get completion matrix
GET /v1/projects/1/assignments/completion-matrix/

# Get summary
GET /v1/projects/1/assignments/completion-matrix/summary/

# Get your stats
GET /v1/projects/1/assignments/completion-matrix/my/

# Export CSV
GET /v1/projects/1/assignments/completion-matrix/export/
```

### Option 2: Add Menu Item to Doccano

**File to modify:** `/doccano/frontend/src/layouts/project/Index.vue` (or similar navigation component)

**Add this to the navigation items:**

```javascript
// In the navigation items array
{
  name: 'Completion Matrix',
  to: { 
    name: 'completion-matrix',
    params: { projectId: this.projectId }
  },
  icon: 'mdi-chart-box',
  // Show only for Project Managers and Admins
  visible: this.isProjectManager || this.isProjectAdmin
}
```

**Add Tibetan translation in `branding/i18n/bo/projects/home.js`:**

```javascript
export default {
  // ... existing translations
  completionMatrix: 'རྫོགས་སྐབས་རེའུ་མིག།', // Completion Matrix
}
```

### Option 3: Quick Access Page

Create a simple access page at:

**File:** `/doccano/backend/client/dist/completion-matrix.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Completion Matrix</title>
</head>
<body>
    <h1>Completion Matrix</h1>
    <div id="matrix-container"></div>
    
    <script>
        // Get project ID from URL
        const urlParams = new URLSearchParams(window.location.search);
        const projectId = urlParams.get('project') || 1;
        
        // Fetch and display matrix
        fetch(`/v1/projects/${projectId}/assignments/completion-matrix/`)
            .then(r => r.json())
            .then(data => {
                document.getElementById('matrix-container').innerHTML = 
                    JSON.stringify(data, null, 2);
            });
    </script>
</body>
</html>
```

Then access at:
```
http://localhost:8000/completion-matrix.html?project=1
```

---

## For Now: Use API Directly

**Best immediate solution:**

1. **Install a REST client** (Postman, Insomnia, or Thunder Client in VSCode)

2. **Or use curl:**
   ```bash
   # Get your auth token
   TOKEN=$(curl -X POST http://localhost:8000/v1/auth-token/ \
     -H "Content-Type: application/json" \
     -d '{"username":"your_username","password":"your_password"}' \
     | jq -r '.token')
   
   # Get completion matrix
   curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/ \
     -H "Authorization: Token $TOKEN" \
     | jq
   ```

3. **Or use browser console:**
   ```javascript
   // Open browser console (F12) on any Doccano page
   fetch('/v1/projects/1/assignments/completion-matrix/')
       .then(r => r.json())
       .then(data => console.table(data.annotators));
   ```

---

## Temporary Dashboard Integration

**Quick Fix:** Add a link in the existing guideline or overview page.

**File:** Create `/doccano/backend/client/dist/js/completion-matrix-link.js`

```javascript
// Add link to completion matrix in the UI
document.addEventListener('DOMContentLoaded', function() {
    // Find the navigation menu
    const nav = document.querySelector('.v-navigation-drawer');
    if (!nav) return;
    
    // Add completion matrix link
    const link = document.createElement('a');
    link.href = '#/completion-matrix';
    link.textContent = '📊 Completion Matrix';
    link.style.cssText = 'display: block; padding: 12px; color: #1976d2;';
    link.onclick = function(e) {
        e.preventDefault();
        // Open matrix in new tab
        const projectId = window.location.pathname.split('/')[2];
        window.open(`/v1/projects/${projectId}/assignments/completion-matrix/`, '_blank');
    };
    
    nav.appendChild(link);
});
```

Then add to `index.html`:
```html
<script src="/js/completion-matrix-link.js"></script>
```

---

## Best Practice: Use the Dashboard HTML

We already created `patches/frontend/completion-matrix.html`. 

**Copy it to Doccano:**
```bash
cp patches/frontend/completion-matrix.html /doccano/backend/client/dist/
```

**Access at:**
```
http://localhost:8000/completion-matrix.html
```

**Note:** You'll need to modify it to:
1. Get project ID from URL
2. Fetch data from API
3. Handle authentication

---

## Summary: 3 Ways to Access Right Now

### 1. Direct API Call ✅ Works Now
```bash
curl http://localhost:8000/v1/projects/1/assignments/completion-matrix/summary/
```

### 2. Browser Console ✅ Works Now
```javascript
fetch('/v1/projects/1/assignments/completion-matrix/summary/')
    .then(r => r.json())
    .then(console.log);
```

### 3. Copy Dashboard HTML ✅ 2 Minutes
```bash
cp patches/frontend/completion-matrix.html /doccano/backend/client/dist/
# Then open: http://localhost:8000/completion-matrix.html
```

---

## Next Steps

1. **Immediate:** Use API endpoints or browser console
2. **Short-term:** Copy dashboard HTML to static directory
3. **Long-term:** Integrate into Doccano's Vue.js navigation menu

The backend is fully working - it's just the frontend link that needs to be added!

