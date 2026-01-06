# 🎯 **Proper Vue SPA Integration - Implementation Plan**

## ❌ **Why Current Approach Fails:**

```
Enhanced Dataset (Django view)
  → Separate HTML page
  → Own Vue instance
  → Uses window.location.href to navigate
  → Full page reload
  → Vue Router state lost
  → Blank page
```

## ✅ **Proper Solution: Integrate with Doccano's Nuxt App:**

### **Challenge:**
- Doccano uses Nuxt.js (pre-built in Docker image)
- Can't rebuild from source
- Need to inject route AFTER build

### **Solution: Dynamic Route Registration**

```javascript
// Wait for Nuxt to load
// Register new route: /monlam/:id/dataset-enhanced
// Component fetches data and renders using Vue
// Uses $router.push() for navigation (no reload!)
```

## 📋 **Implementation Steps:**

### **Step 1: Create Vue Component (JavaScript)**

File: `patches/frontend/enhanced-dataset-spa-component.js`

```javascript
// Enhanced Dataset as a Nuxt/Vue component
// Registers itself dynamically after Nuxt loads

(function() {
    // Wait for Nuxt
    const checkNuxt = setInterval(() => {
        if (!window.$nuxt) return;
        
        clearInterval(checkNuxt);
        
        // Define component
        const EnhancedDataset = {
            template: `<div>Enhanced Dataset for {{ $route.params.id }}</div>`,
            async asyncData({ $axios, params }) {
                // Fetch examples
                const examples = await $axios.get(\`/v1/projects/\${params.id}/examples\`);
                return { examples: examples.data.results };
            },
            methods: {
                goToAnnotation(exampleId) {
                    // Use Vue Router - NO PAGE RELOAD!
                    const index = this.examples.findIndex(ex => ex.id === exampleId);
                    const page = Math.floor(index / 10);
                    this.$router.push(\`/projects/\${this.$route.params.id}/speech-to-text?page=\${page}\`);
                }
            }
        };
        
        // Register route
        window.$nuxt.$router.addRoute({
            path: '/monlam/:id/dataset-enhanced',
            component: EnhancedDataset
        });
        
        console.log('[Monlam] ✅ Enhanced Dataset registered in Vue SPA!');
    }, 100);
})();
```

### **Step 2: Copy Script to Docker Image**

Update `Dockerfile`:
```dockerfile
# Copy Enhanced Dataset SPA component
COPY patches/frontend/enhanced-dataset-spa-component.js /doccano/backend/client/dist/static/enhanced-dataset.js
```

### **Step 3: Inject Script into index.html**

Add script tag before `</body>`:
```html
<script src="/static/enhanced-dataset.js"></script>
```

### **Step 4: Update Menu Redirect**

In `patches/frontend/index.html`:
```javascript
// Instead of intercepting and redirecting
// Just let the link work naturally
// Nuxt router will handle /monlam/:id/dataset-enhanced
```

## ✅ **Benefits:**

- ✅ No page reload
- ✅ Vue Router handles navigation
- ✅ Can use $router.push() from enhanced dataset
- ✅ Annotation page loads properly
- ✅ Goes to specific example page

## 🚀 **User Experience:**

```
1. Click "Dataset" menu
   → Vue Router navigates to /monlam/9/dataset-enhanced
   → No reload, SPA navigation ✅

2. Click "Annotate" on example #2446
   → Component calls: this.$router.push('/projects/9/speech-to-text?page=24')
   → Vue Router navigates (no reload) ✅

3. Annotation interface loads
   → Shows page 24 with example #2446 ✅
```

## ⏱️ **Implementation Time:**

- Create component JavaScript: 30 min
- Test dynamic registration: 30 min
- Full template with data fetching: 2 hours
- Total: ~3 hours

## 🔧 **Alternative: Simpler Hybrid Approach**

If full SPA integration is complex, use this hybrid:

1. Keep enhanced dataset as Django view
2. Add button: "Open in Annotation Mode"
3. Button navigates to: `/projects/9/speech-to-text`
4. User is now in Vue SPA
5. They navigate within annotation interface

Trade-off:
- Enhanced dataset NOT in SPA
- But annotation navigation WORKS
- User can review and approve

---

**Which approach do you want?**

A) Full SPA integration (3 hours work, proper solution)
B) Hybrid approach (30 minutes, works but not perfect)
C) Current workaround (already deployed, functional but clunky)

