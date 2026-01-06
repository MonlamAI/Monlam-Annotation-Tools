# 🧭 Navigation Options for New Monlam Pages

## Current Situation

**Standard Doccano Menu (Left Sidebar):**
- གཞི་གྲངས། (Dataset) → `/projects/9/dataset` (standard)
- སྤྱི་འཐུས། (Members) → `/projects/9/members` (standard)
- Metrics → `/projects/9/metrics` (standard)

**New Monlam Pages:**
- Landing → `/monlam/9/`
- Enhanced Dataset → `/monlam/9/dataset-enhanced/`
- Completion Dashboard → `/monlam/9/completion/`
- Annotation with Approval → `/monlam/9/annotate/{id}/`

**Problem:** New pages are not in the left menu!

---

## 🎯 **Option 1: Redirect Standard Pages** (Recommended)

**Intercept standard menu clicks and redirect to new pages.**

### Implementation:

Add redirects in `monlam_ui/views.py`:

```python
from django.shortcuts import redirect
from django.views import View

class DatasetRedirectView(View):
    """Redirect /projects/{id}/dataset to /monlam/{id}/dataset-enhanced/"""
    def get(self, request, project_id):
        return redirect(f'/monlam/{project_id}/dataset-enhanced/')

class MetricsRedirectView(View):
    """Redirect /projects/{id}/metrics to /monlam/{id}/completion/"""
    def get(self, request, project_id):
        # Only for project managers/admins
        return redirect(f'/monlam/{project_id}/completion/')
```

Update `config/urls.py` to intercept:

```python
# Before Doccano's URLs
urlpatterns = [
    path('projects/<int:project_id>/dataset/', 
         DatasetRedirectView.as_view(), 
         name='dataset-redirect'),
    path('projects/<int:project_id>/metrics/', 
         MetricsRedirectView.as_view(), 
         name='metrics-redirect'),
    # ... rest of Doccano URLs
]
```

**Result:**
- Click "གཞི་གྲངས།" (Dataset) → Auto-redirects to `/monlam/9/dataset-enhanced/` ✅
- Click "Metrics" → Auto-redirects to `/monlam/9/completion/` ✅

**Pros:**
- ✅ Seamless user experience
- ✅ No need to modify Doccano's frontend
- ✅ Users use existing menu

**Cons:**
- ⚠️ Users can't access standard pages anymore
- ⚠️ Might confuse if they expect standard interface

---

## 🎯 **Option 2: Add Floating Button** (Easy)

**Add a floating "Monlam Tools" button on project pages.**

### Implementation:

Create a script that adds a floating button:

```javascript
// In base template or inline script
if (window.location.pathname.match(/\/projects\/\d+/)) {
    const projectId = window.location.pathname.match(/\/projects\/(\d+)/)[1];
    
    // Create floating button
    const btn = document.createElement('a');
    btn.href = `/monlam/${projectId}/`;
    btn.innerHTML = '🌟 Monlam Tools';
    btn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 30px;
        text-decoration: none;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 9999;
        font-weight: 600;
        font-size: 16px;
        transition: transform 0.2s;
    `;
    
    btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'scale(1.05)';
    });
    btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'scale(1)';
    });
    
    document.body.appendChild(btn);
}
```

**Result:**
- Standard Doccano interface (unchanged)
- Floating "🌟 Monlam Tools" button in bottom-right
- Click → Goes to `/monlam/9/` landing page

**Pros:**
- ✅ Non-invasive (doesn't change Doccano)
- ✅ Easy to implement
- ✅ Users can access both systems

**Cons:**
- ⚠️ Extra click needed
- ⚠️ Button might be overlooked

---

## 🎯 **Option 3: Bookmark/Direct Access** (Current)

**Users bookmark the landing page.**

### Implementation:

**For Users:**
1. Go to: `https://annotate.monlam.ai/monlam/9/`
2. Bookmark it
3. Use bookmark to access Monlam Tools

**For Admins:**
- Send users the link
- Add to project description
- Email/documentation

**Result:**
- Users manually go to `/monlam/9/`
- From there, access all features

**Pros:**
- ✅ No code changes needed (already done)
- ✅ Clean separation
- ✅ Works immediately

**Cons:**
- ⚠️ Users need to know the URL
- ⚠️ Extra step to access

---

## 🎯 **Option 4: Home Page Redirect** (Most Seamless)

**Redirect project home to Monlam landing page.**

### Implementation:

```python
class ProjectHomeRedirectView(View):
    """Redirect /projects/{id}/ to /monlam/{id}/"""
    def get(self, request, project_id):
        return redirect(f'/monlam/{project_id}/')
```

```python
# In config/urls.py
urlpatterns = [
    path('projects/<int:project_id>/', 
         ProjectHomeRedirectView.as_view(), 
         name='project-home-redirect'),
    # ... rest
]
```

**Result:**
- Click on project → Goes to `/monlam/9/` landing page automatically
- Landing page has cards for:
  - Enhanced Dataset
  - Completion Dashboard
  - Standard Doccano (for those who need it)

**Pros:**
- ✅ Most seamless experience
- ✅ Monlam Tools is the default
- ✅ Still can access standard via card

**Cons:**
- ⚠️ Changes default behavior
- ⚠️ Users who want standard need extra click

---

## 📊 **Comparison Table**

| Option | Ease | User Experience | Invasiveness | Recommended For |
|--------|------|-----------------|--------------|-----------------|
| **1. Redirect Menu** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Users who ONLY use Monlam tools |
| **2. Floating Button** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | Mixed usage (both systems) |
| **3. Bookmark** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | Tech-savvy users |
| **4. Home Redirect** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Full Monlam adoption |

---

## ✅ **Recommended Approach**

**For now (Immediate):**
- **Option 3:** Bookmark `/monlam/9/`
- Users can access immediately
- No code changes needed

**For better UX (After testing):**
- **Option 2:** Add floating button
- Or **Option 4:** Redirect project home to landing page

**For full integration (If needed):**
- **Option 1:** Redirect menu items

---

## 🚀 **Quick Implementation: Floating Button**

Want to add the floating button? Here's the code:

```html
<!-- Add to base template or as inline script -->
<script>
(function() {
    // Only on project pages
    const match = window.location.pathname.match(/\/projects\/(\d+)/);
    if (!match) return;
    
    const projectId = match[1];
    
    // Create floating button
    const btn = document.createElement('a');
    btn.href = `/monlam/${projectId}/`;
    btn.innerHTML = `
        <svg style="width:20px;height:20px;margin-right:8px;vertical-align:middle;" viewBox="0 0 24 24">
            <path fill="currentColor" d="M12,17.27L18.18,21L16.54,13.97L22,9.24L14.81,8.62L12,2L9.19,8.62L2,9.24L7.45,13.97L5.82,21L12,17.27Z" />
        </svg>
        Monlam Tools
    `;
    btn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 14px 22px;
        border-radius: 28px;
        text-decoration: none;
        box-shadow: 0 4px 16px rgba(102,126,234,0.4);
        z-index: 9999;
        font-weight: 600;
        font-size: 15px;
        display: flex;
        align-items: center;
        transition: all 0.2s ease;
    `;
    
    btn.onmouseenter = () => {
        btn.style.transform = 'translateY(-2px) scale(1.05)';
        btn.style.boxShadow = '0 6px 24px rgba(102,126,234,0.5)';
    };
    btn.onmouseleave = () => {
        btn.style.transform = 'translateY(0) scale(1)';
        btn.style.boxShadow = '0 4px 16px rgba(102,126,234,0.4)';
    };
    
    document.body.appendChild(btn);
})();
</script>
```

Save this in `patches/frontend/monlam-floating-button.html` and inject it!

---

## 🎯 **Decision Time**

Which option do you prefer?

1. **Redirect menu items** → གཞི་གྲངས། goes to enhanced dataset
2. **Floating button** → Easy access from any page
3. **Bookmark** → Users manually go to `/monlam/9/`
4. **Home redirect** → Project home = Monlam landing page

Let me know and I'll implement it!

