
/**
 * Monlam Tools - Frontend Overrides
 * 
 * This file contains all custom logic for Monlam Doccano, including:
 * - Tibetan Translations
 * - UI Branding & Font enforcement
 * - Review Workflow (Approve/Reject buttons)
 * - API Interception for robust ID detection
 * 
 * It is injected into index.html to prevent main thread freezing during parsing.
 */

// ========================================
// 1. GLOBAL STATE & CONFIG
// ========================================

// Tibetan translations map
const translations = {
  // Home page
  'Text Annotation for Humans': 'ཞུ་དག་བྱ་ཡུལ།',
  'Get Started': 'འགོ་བརྩམས།',
  'GET STARTED': 'འགོ་བརྩམས།',
  'The best features': 'དམིགས་བསལ་ཁྱད་ཆོས།',
  'Team Collaboration': 'ཚོགས་པའི་མཉམ་ལས།',
  'Annotation with your team mates': 'ཁྱོད་ཀྱི་ལས་རོགས་དང་མཉམ་དུ་མཆན་འགོད།',
  'Any Language': 'སྐད་རིགས་གང་ཡང་།',
  'Annotation with any language': 'སྐད་རིགས་གང་ཡང་རུང་བའི་མཆན་འགོད།',
  'Open Source': 'ལས་སླ་པོ།',
  'Annotation that is free and customizable': 'རིན་མེད་དང་རང་མོས་བཟོ་བཅོས་བྱེད་རུང་བའི་མཆན་འགོད།',
  'Realize your ideas quickly': 'ཁྱོད་ཀྱི་བསམ་བློ་མགྱོགས་པོར་དངོས་སུ་སྒྲུབ།',
  'Try Demo': 'ཚོད་ལྟ་བྱེད།',
  'TRY DEMO': 'ཚོད་ལྟ་བྱེད།',
  
  // Navigation
  'Login': 'ནང་འཛུལ།',
  'LOGIN': 'ནང་འཛུལ།',
  'Sign Out': 'ཕྱིར་འཐོན།',
  'Projects': 'ལས་གཞི།',
  'PROJECTS': 'ལས་གཞི།',
  
  // Project home
  'Home': 'མདུན་ངོས།',
  'Welcome to Doccano!': 'སྐུ་ཁམས་བཟང་།',
  'Welcome to Monlam Tools!': 'སྐུ་ཁམས་བཟང་།',
  'Import a dataset': 'གཞི་གྲངས་ནང་འདྲེན།',
  'Create labels for this project': 'ལས་གཞི་འདིའི་ཆེད་ཁ་བྱང་གསར་བཟོ།',
  'Add members for collaborative work': 'མཉམ་ལས་ཀྱི་ཆེད་ཚོགས་མི་སྣོན་པ།',
  'Define a guideline for the work': 'ལས་ཀའི་ལམ་སྟོན་གཏན་འཁེལ།',
  'Annotate the dataset': 'གཞི་གྲངས་ལ་མཆན་འགོད།',
  'View statistics': 'ཚད་གཞི་ལྟ་བ།',
  'Export the dataset': 'གཞི་གྲངས་ཕྱིར་འདྲེན།',
  
  // Common
  'Save': 'ཉར་ཚགས།',
  'Edit': 'རྩོམ་སྒྲིག',
  'Create': 'གསར་བཟོ།',
  'Cancel': 'འདོར་བ།',
  'Close': 'སྒོ་རྒྱག',
  'Delete': 'བསུབ་པ།',
  'Search': 'བཙལ་ཞིབ།',
  'Import': 'ནང་འདྲེན།',
  'Export': 'ཕྱིར་འདྲེན།',
  'Add': 'སྣོན་པ།',
  'Upload': 'སྐྱེལ་འཇུག',
  'Yes': 'ཡིན།',
  'No': 'མིན།',
  'Loading...': 'སྣན་བཞིན་པ།...',
  'Loading... Please wait': 'སྣན་བཞིན་པ། སྒུག་རོགས།',
  
  // Labels/Annotation
  'Labels': 'ཁ་བྱང་།',
  'Dataset': 'གཞི་གྲངས།',
  'Members': 'ཚོགས་མི།',
  'Guideline': 'ལམ་སྟོན།',
  'Statistics': 'ཚད་གཞི།',
  'Metrics': 'ཚད་གཞི།',
  'Settings': 'སྒྲིག་འགོད།',
  'Comments': 'མཆན།',
  
  // Demo types
  'Named Entity Recognition': 'མིང་ཚིག་དབྱེ་འབྱེད།',
  'Sentiment Analysis': 'སེམས་ཚོར་དབྱེ་ཞིབ།',
  'Translation': 'ཡིག་སྒྱུར།',
  'Text to SQL': 'ཡི་གེ་ནས་SQL',
  'Intent Detection and Slot Filling': 'དམིགས་བསལ་འཚོལ་ཞིབ།',
  'Image Classification': 'པར་རིས་དབྱེ་འབྱེད།',
  'Image Captioning': 'པར་རིས་འགྲེལ་བཤད།',
  'Object Detection': 'དངོས་པོ་འཚོལ་ཞིབ།',
  'Polygon Segmentation': 'མཐའ་རིས་དབྱེ་བཞག',
  'Speech to Text': 'སྐད་ཆ་ནས་ཡི་གེ།',
  
  // Project types
  'Text Classification': 'ཡི་གེ་དབྱེ་འབྱེད།',
  'Sequence Labeling': 'མཚམས་རིས་ཁ་བྱང་།',
  'Sequence to sequence': 'མཚམས་ནས་མཚམས།',
  
  // Doccano branding
  'doccano': 'Monlam Tools',
  'Doccano': 'Monlam Tools',
  'Monlam AI': 'Monlam Tools',
  
  // Copyright
  '© 2025 Monlam Tools': '© 2026 Monlam Tools',
  '© 2026 Monlam AI': '© 2026 Monlam Tools',
};

// Global variable to store currently viewed Example ID
window.monlamCurrentExampleId = null;

// ========================================
// 2. API INTERCEPTOR
// ========================================
(function() {
  // 1. Intercept Fetch API
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);
    
    try {
      // Only inspect relevant endpoints to save resources
      const url = response.url;
      if (url.includes('/projects/') && 
         (url.includes('/next') || url.includes('/examples/') || url.includes('/auto-labeling'))) {
        
        // Clone response to read without consuming stream
        // Verify Content-Type is JSON before cloning to avoid errors on blob/image responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const clone = response.clone();
            clone.json().then(data => {
              if (data && data.id) {
                // Must have content fields to be a valid Annotation Example
                if (data.text !== undefined || data.filename !== undefined || data.meta !== undefined) {
                  console.debug('Monlam Tools: Captured Example ID from API:', data.id);
                  window.monlamCurrentExampleId = data.id;
                  
                  // Update UI container if present
                  const container = document.querySelector('.monlam-review-container');
                  if (container) {
                    container.dataset.exampleId = data.id;
                  }
                }
              }
            }).catch(() => {});
        }
      }
    } catch (e) {
      console.warn('Monlam Tools: Fetch interceptor warning:', e);
    }
    
    return response;
  };
  
  // 2. Intercept XMLHttpRequest
  const originalOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url) {
    this._url = url;
    return originalOpen.apply(this, arguments);
  };
  
  const originalSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function() {
    this.addEventListener('load', function() {
      try {
        if (this._url && this._url.includes('/projects/') && 
           (this._url.includes('/next') || this._url.includes('/examples/'))) {
          // Check response text is valid JSON
          const data = JSON.parse(this.responseText);
          if (data && data.id && (data.text !== undefined || data.filename !== undefined)) {
            console.debug('Monlam Tools: Captured Example ID from XHR:', data.id);
            window.monlamCurrentExampleId = data.id;
          }
        }
      } catch (e) {}
    });
    return originalSend.apply(this, arguments);
  };
})();

// ========================================
// 3. CORE LOGIC - Handle Nuxt Dynamic Rendering
// ========================================
let monlamInitialized = false;

function initMonlamTools() {
  if (monlamInitialized) return;
  
  console.log('Monlam Tools: initializing...');
  
  // Initial setup (can run immediately)
  document.title = 'Monlam Tools';
  setFavicon();
  forceMonlamFont();
  
  // Start Translation System (will catch Nuxt content)
  initTranslationSystem();
  
  // Start UI Tweaks
  initUITweaks();
  
  monlamInitialized = true;
}

// Strategy 1: Run immediately if DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMonlamTools);
} else {
  // DOM already loaded
  initMonlamTools();
}

// Strategy 2: Wait for Nuxt to mount (check for Nuxt app)
function waitForNuxt() {
  // Check if Nuxt app is mounted
  const nuxtApp = document.querySelector('#__nuxt');
  if (nuxtApp && nuxtApp.__vue__) {
    console.log('Monlam Tools: Nuxt detected, applying translations');
    initMonlamTools();
    // Run translations again after Nuxt renders
    setTimeout(() => {
      if (document.body) {
        replaceText(document.body);
      }
    }, 500);
  } else {
    // Retry after a short delay
    setTimeout(waitForNuxt, 100);
  }
}

// Start checking for Nuxt after DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', waitForNuxt);
} else {
  waitForNuxt();
}

// Strategy 3: Run after delays to catch late-rendered content
setTimeout(initMonlamTools, 1000);
setTimeout(initMonlamTools, 3000);
setTimeout(initMonlamTools, 5000);

// ========================================
// 4. TRANSLATION & TEXT REPLACEMENT
// ========================================
function initTranslationSystem() {
  // Initial pass - wait for body if not ready
  if (document.body) {
    replaceText(document.body);
  } else {
    // Wait for body
    const bodyObserver = new MutationObserver(function() {
      if (document.body) {
        replaceText(document.body);
        bodyObserver.disconnect();
      }
    });
    bodyObserver.observe(document.documentElement, { childList: true });
  }
  
  // MutationObserver for dynamic content (Nuxt SPA)
  // Debounced to prevent freezing on large DOM updates
  let timeout;
  const observer = new MutationObserver(function(mutations) {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => {
      mutations.forEach(function(mutation) {
        if (mutation.type === 'childList') {
            mutation.addedNodes.forEach(function(node) {
              if (node.nodeType === Node.ELEMENT_NODE) {
                // Ignore script/style tags to be safe
                if (node.tagName !== 'SCRIPT' && node.tagName !== 'STYLE') {
                    replaceText(node);
                }
              } else if (node.nodeType === Node.TEXT_NODE) {
                // Handle text nodes directly
                replaceText(node.parentElement || document.body);
              }
            });
        }
        // Also handle text content changes
        if (mutation.type === 'characterData') {
          replaceText(mutation.target.parentElement || document.body);
        }
      });
      
      // Also re-apply GitHub hiding
      hideGithub();
    }, 50); // Reduced debounce to 50ms for faster updates
  });
  
  // Observe body when it's available
  if (document.body) {
    observer.observe(document.body, { 
      childList: true, 
      subtree: true,
      characterData: true
    });
  } else {
    // Wait for body, then observe
    document.addEventListener('DOMContentLoaded', function() {
      if (document.body) {
        observer.observe(document.body, { 
          childList: true, 
          subtree: true,
          characterData: true
        });
      }
    });
  }
  
  // Also observe document root for early content
  observer.observe(document.documentElement, { 
    childList: true, 
    subtree: true 
  });
  
  // Periodic refresh to catch any missed Nuxt content
  setInterval(function() {
    if (document.body) {
      replaceText(document.body);
    }
  }, 2000);
}

function replaceText(element) {
  // Safety check
  if (!element || !element.nodeType) {
    return;
  }
  
  // Update title dynamically
  if (document.title && document.title.includes('doccano')) {
    document.title = 'Monlam Tools';
  }
  
  try {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    let node;
    while (node = walker.nextNode()) {
      let text = node.nodeValue;
      // Fast fail check
      if (!text || text.trim().length === 0) continue;
      
      let changed = false;
      for (const [eng, tib] of Object.entries(translations)) {
        if (text.includes(eng)) {
          text = text.replace(new RegExp(eng.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), tib);
          changed = true;
        }
      }
      
      if (changed) {
        node.nodeValue = text;
      }
    }
  } catch (e) {
    // Silently fail if element is not ready
    console.debug('Monlam Tools: replaceText skipped for element:', e);
  }
}

// ========================================
// 5. UI TWEAKS & BRANDING
// ========================================
function initUITweaks() {
  // Periodic checks
  setInterval(function() {
    styleReviewButtons(); // icons
    hideGithub();
    
    // Check for approver rights and inject buttons
    checkAndInjectApproverButtons();
  }, 1000);
  
  // Font enforcement
  window.addEventListener('load', function() {
    forceMonlamFont();
    setTimeout(forceMonlamFont, 500);
  });
}

function setFavicon() {
  document.querySelectorAll('link[rel*="icon"]').forEach(function(link) {
    if (!link.href.includes('favicon.ico') && !link.href.includes('favicon.png')) {
      link.remove();
    }
  });
  
  const head = document.head;
  const existingIco = document.querySelector('link[href="/favicon.ico"]');
  if (!existingIco) {
    const ico = document.createElement('link');
    ico.rel = 'icon';
    ico.type = 'image/x-icon';
    ico.href = '/favicon.ico';
    head.appendChild(ico);
  }
}

function hideGithub() {
  document.querySelectorAll('a[href*="github"], button').forEach(function(el) {
    if (el.textContent && el.textContent.toLowerCase().includes('github')) {
      el.style.display = 'none';
    }
  });
}

function forceMonlamFont() {
  const MONLAM_FONT = "'MonlamTBslim', 'Noto Sans Tibetan', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  document.documentElement.style.setProperty('font-family', MONLAM_FONT, 'important');
  document.body.style.setProperty('font-family', MONLAM_FONT, 'important');
  
  document.querySelectorAll('.v-application').forEach(function(el) {
    el.style.setProperty('font-family', MONLAM_FONT, 'important');
  });
  
  // Target specific elements that might override base font
  const selectors = 'h1, h2, h3, h4, h5, h6, .v-btn, .v-card, .v-list-item, .v-tab, input, textarea';
  document.querySelectorAll(selectors).forEach(function(el) {
    el.style.setProperty('font-family', MONLAM_FONT, 'important');
    el.style.setProperty('line-height', '1.8', 'important');
  });
}

function styleReviewButtons() {
    const CLOSE_PATH = "M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z";
    const CHECK_PATH = "M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z";
    const CIRCLE_PATH = "M12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z";
    
    document.querySelectorAll('.v-btn--icon .v-icon svg path').forEach(function(path) {
      const d = path.getAttribute('d');
      if (d === CLOSE_PATH) {
        path.setAttribute('d', CIRCLE_PATH);
        path.style.fill = '#f44336';
      } else if (d === CHECK_PATH) {
        path.style.fill = '#4caf50';
      }
    });
}


// ========================================
// 6. APPROVER BUTTON LOGIC
// ========================================
let approverCheckDone = false;
let isUserApprover = false;

async function checkAndInjectApproverButtons() {
    // Basic route check
    if (!window.location.pathname.includes('/projects/')) return;
    if (window.location.pathname.includes('/dataset')) return;
    if (window.location.pathname.includes('/labels')) return;
    
    // Check user role (cached)
    if (!approverCheckDone) {
        isUserApprover = await isApprover();
        approverCheckDone = true;
        
        // Reset check on nav
        const currentPath = window.location.pathname;
        setTimeout(() => {
          if (window.location.pathname !== currentPath) {
            approverCheckDone = false;
          }
        }, 3000);
    }
    
    if (isUserApprover && !document.querySelector('.monlam-review-container')) {
        injectReviewButtons();
    }
}

async function isApprover() {
  try {
    const userInfo = await fetch('/v1/me').then(r => r.ok ? r.json() : null).catch(() => null);
    if (userInfo && userInfo.username) {
      return userInfo.username.toLowerCase().includes('approver') || 
             userInfo.is_staff === true ||
             (userInfo.groups && userInfo.groups.some(g => g.name && g.name.toLowerCase().includes('approver')));
    }
    return false;
  } catch (e) {
    return false;
  }
}

function injectReviewButtons() {
  const toolbar = document.querySelector('.v-card__actions') || 
                  document.querySelector('.v-toolbar__items');
  const mainContent = document.querySelector('.v-main__wrap');
  
  if (!mainContent && !toolbar) return;
  
  const exampleId = getCurrentExampleId();
  
  const container = document.createElement('div');
  container.className = 'monlam-review-container';
  if (exampleId) container.dataset.exampleId = exampleId;
  
  container.innerHTML = `
    <span class="monlam-review-status monlam-status-pending">📋 Pending Review</span>
    <input type="text" class="monlam-review-notes" placeholder="Review notes (optional)..." />
    <button class="monlam-approve-btn" onclick="window.monlamApprove()"><span>✅</span> Approve</button>
    <button class="monlam-reject-btn" onclick="window.monlamReject()"><span>❌</span> Reject</button>
  `;
  
  if (toolbar) {
    toolbar.parentNode.insertBefore(container, toolbar.nextSibling);
  } else if (mainContent) {
    // Try to find a good spot in main content
    const card = mainContent.querySelector('.v-card');
    if (card) card.appendChild(container);
  }
}

// Global button handlers
window.monlamApprove = function() {
    const notes = document.querySelector('.monlam-review-notes')?.value || '';
    reviewExample('approve', notes);
};
window.monlamReject = function() {
    const notes = document.querySelector('.monlam-review-notes')?.value || '';
    reviewExample('reject', notes);
};


// ========================================
// 7. REVIEW API LOGIC
// ========================================

function getCurrentExampleId() {
  // 1. API Interceptor (Authoritative)
  if (window.monlamCurrentExampleId) {
    return window.monlamCurrentExampleId;
  }
  
  // 2. DOM Attributes
  const exampleEl = document.querySelector('[data-example-id]') || 
                   document.querySelector('[data-id]');
  if (exampleEl) {
    return exampleEl.dataset.exampleId || exampleEl.dataset.id;
  }
  
  // 3. Vue State (Best effort)
  try {
     const nuxtEl = document.querySelector('#__nuxt');
     if (nuxtEl && nuxtEl.__vue__) {
       const state = nuxtEl.__vue__.$store.state;
       if (state.example?.id) return state.example.id;
       if (state.examples?.current?.id) return state.examples.current.id;
     }
  } catch(e) {}
  
  // 4. URL
  const pathMatch = window.location.pathname.match(/\/examples\/(\d+)/);
  if (pathMatch) return pathMatch[1];
  
  return null;
}

function getProjectId() {
  const match = window.location.pathname.match(/\/projects\/(\d+)/);
  return match ? match[1] : null;
}

function getCSRFToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}

async function reviewExample(action, notes = '') {
  const projectId = getProjectId();
  let exampleId = getCurrentExampleId();
  
  if (!exampleId) {
    // Check container override
    const container = document.querySelector('.monlam-review-container');
    if (container && container.dataset.exampleId) {
      exampleId = container.dataset.exampleId;
    }
  }
  
  if (!projectId) {
    showNotification('Cannot determine Project ID', 'error');
    return;
  }
  if (!exampleId) {
    showNotification('Cannot determine Example ID. Please verify you are viewing an example.', 'error');
    return;
  }
  
  try {
    const commentResponse = await fetch(`/v1/projects/${projectId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({
        example: parseInt(exampleId),
        text: `[REVIEW:${action.toUpperCase()}] ${notes || (action === 'approve' ? 'Approved' : 'Rejected')}`
      })
    });
    
    if (!commentResponse.ok) throw new Error('Failed to save comment');
    
    // State mgmt
    if (action === 'approve') {
       await fetch(`/v1/projects/${projectId}/examples/${exampleId}/states`, {
         method: 'POST',
         headers: {'X-CSRFToken': getCSRFToken()}
       });
    } else {
       await fetch(`/v1/projects/${projectId}/examples/${exampleId}/states`, {
         method: 'DELETE',
         headers: {'X-CSRFToken': getCSRFToken()}
       });
    }
    
    updateReviewStatus(action);
    showNotification(`${action === 'approve' ? 'Approved' : 'Rejected'} successfully!`, 'success');
  } catch(e) {
    console.error(e);
    showNotification('Error saving review', 'error');
  }
}

function showNotification(msg, type) {
    const notif = document.createElement('div');
    notif.style.cssText = `position:fixed;top:20px;right:20px;padding:16px 24px;border-radius:8px;color:white;font-weight:600;z-index:99999;
    background:${type==='success'?'#4caf50':'#f44336'};`;
    notif.textContent = msg;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}

function updateReviewStatus(action) {
    const statusEl = document.querySelector('.monlam-review-status');
    if (statusEl) {
        statusEl.textContent = action === 'approve' ? '✅ Approved' : '❌ Rejected';
        statusEl.className = `monlam-review-status ${action=='approve'?'monlam-status-approved':'monlam-status-rejected'}`;
    }
}
