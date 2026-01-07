# 📋 Adding Enhanced Dataset Menu Link

## 🎯 Goal

Add a menu item "གཞི་གྲངས།" (Dataset Statistics) to the left sidebar that links to the Enhanced Dataset View.

---

## 📍 Current State

**Left Menu (གཞི་གྲངས། - "Dataset"):**
- Currently shows: Standard Doccano dataset page
- URL: `/projects/9/dataset`

**We want to add:**
- New menu item: "📊 གཞི་གྲངས། (Enhanced)"
- URL: `/monlam/9/dataset-enhanced/`

---

## 🔧 Solution Options

### **Option 1: Browser Bookmark** (Quickest)

**For Users:**
1. Go to: `https://annotate.monlam.ai/monlam/9/dataset-enhanced/`
2. Bookmark it
3. Use bookmark to access

**Pros:** Immediate, no code changes
**Cons:** Not integrated into menu

---

### **Option 2: Add Link to Project Home** (Simple)

Add a card/button on the project home page that links to enhanced dataset.

**File to modify:** Doccano's project home template (complex)

---

### **Option 3: Use Existing Dataset Menu** (Recommended)

**Redirect the existing "གཞི་གྲངས།" menu to enhanced view:**

**In Doccano's URL config:**
```python
# Intercept /projects/<id>/dataset and redirect
# to /monlam/<id>/dataset-enhanced/
```

**Implementation:**
1. Add a view that intercepts `/projects/<id>/dataset`
2. Checks if enhanced view is available
3. Redirects to `/monlam/<id>/dataset-enhanced/`

---

### **Option 4: Custom Navigation Component** (Most Complex)

Modify Doccano's Vue.js frontend to add custom menu items.

**Requires:**
- Rebuilding Doccano's frontend
- Modifying Vue components
- Recompiling assets

**Not recommended** for non-invasive approach.

---

## ✅ **Recommended: Add Redirect**

Let's make the existing "གཞི་གྲངས།" button redirect to enhanced view:

```python
# In monlam_ui/views.py

from django.shortcuts import redirect
from django.views import View

class DatasetRedirectView(View):
    """
    Intercept standard dataset view and redirect to enhanced version.
    """
    def get(self, request, project_id):
        return redirect(f'/monlam/{project_id}/dataset-enhanced/')
```

```python
# In monlam_ui/urls.py

urlpatterns = [
    # Intercept dataset view
    path('<int:project_id>/dataset/', 
         DatasetRedirectView.as_view(), 
         name='dataset-redirect'),
    # ... other URLs
]
```

**Problem:** This would conflict with Doccano's main URLs.

---

## 🎯 **Best Solution: Direct Access Pattern**

**Current workflow:**
1. Users go to project page: `/projects/9/`
2. Click "གཞི་གྲངས།" (Dataset) in sidebar
3. See standard Doccano dataset

**Enhanced workflow:**
1. Users go to: `/monlam/9/dataset-enhanced/` directly
2. Bookmark it
3. Or create a custom landing page

**Alternative:** Add a floating button on standard dataset page that says:
"📊 View Enhanced Dataset →"

---

## 📊 **Floating Button Implementation**

Add a button that appears on the standard dataset page:

```html
<!-- In a custom script loaded on dataset page -->
<script>
if (window.location.pathname.includes('/projects/') && 
    window.location.pathname.includes('/dataset')) {
    
    const projectId = window.location.pathname.match(/projects\/(\d+)/)[1];
    
    // Create floating button
    const btn = document.createElement('a');
    btn.href = `/monlam/${projectId}/dataset-enhanced/`;
    btn.innerHTML = '📊 Enhanced View';
    btn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #1976d2;
        color: white;
        padding: 12px 24px;
        border-radius: 24px;
        text-decoration: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        font-weight: 500;
    `;
    
    document.body.appendChild(btn);
}
</script>
```

**Where to add this:** In Doccano's base template or via browser extension.

---

## 🚀 **Simplest Solution for Now**

**Direct URL Access:**

Users should access via direct URL:
```
https://annotate.monlam.ai/monlam/9/dataset-enhanced/
```

**To make it easier:**
1. Create a landing page at `/monlam/9/` that shows:
   - Link to Enhanced Dataset
   - Link to Completion Dashboard
   - Link to standard project
2. Users bookmark this landing page

---

## 📋 **Implementation: Project Landing Page**

Let's create a landing page!

```python
# In monlam_ui/views.py

@login_required
def project_landing(request, project_id):
    """Landing page for Monlam custom features."""
    project = get_object_or_404(Project, pk=project_id)
    
    context = {
        'project': project,
        'project_id': project_id,
    }
    
    return render(request, 'monlam_ui/project_landing.html', context)
```

```python
# In monlam_ui/urls.py

urlpatterns = [
    path('<int:project_id>/', 
         views.project_landing, 
         name='project-landing'),
    # ... other URLs
]
```

**Template: project_landing.html**

Show a dashboard with big cards:
- 📊 Enhanced Dataset View
- 📈 Completion Dashboard
- 📝 Annotations
- ← Back to Project

This gives users a clear entry point!

---

## ✅ **Action Items**

1. **Immediate:** Use direct URL for enhanced dataset
2. **Short-term:** Create project landing page
3. **Long-term:** Consider frontend integration

**For now, users should:**
- Bookmark: `https://annotate.monlam.ai/monlam/9/dataset-enhanced/`
- Or use: `https://annotate.monlam.ai/monlam/9/` (landing page)



