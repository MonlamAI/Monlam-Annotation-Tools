/**
 * Skip Button for Annotation Toolbar
 * 
 * Adds a "Skip Permanently" button to the annotation toolbar
 * Allows annotators to permanently skip examples with a reason
 */

(function() {
    'use strict';
    
    console.log('[Monlam Skip] Initializing skip button...');
    
    function isAnnotationPage() {
        const path = window.location.pathname;
        return path.includes('/speech-to-text') || 
               path.includes('/document-classification') ||
               path.includes('/sequence-labeling') ||
               path.includes('/sequence-to-sequence') ||
               path.includes('/image-classification') ||
               path.includes('/image-captioning') ||
               path.includes('/seq2seq') ||
               path.includes('/intent-detection-and-slot-filling') ||
               path.includes('/bounding-box') ||
               path.includes('/segmentation') ||
               path.includes('/image-captioning');
    }
    
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }
    
    async function getCurrentExampleId() {
        // Wait for Vue to be ready and example to be loaded
        return new Promise((resolve) => {
            let attempts = 0;
            const maxAttempts = 50; // 10 seconds
            
            const checkInterval = setInterval(() => {
                attempts++;
                
                // Try to get from Vue instance
                if (window.$nuxt && window.$nuxt.$route && window.$nuxt.$route.query) {
                    const app = window.$nuxt.$children[0];
                    if (app && app.example && app.example.id) {
                        clearInterval(checkInterval);
                        resolve(app.example.id);
                        return;
                    }
                }
                
                // Try to find example ID in DOM
                const exampleText = document.body.textContent;
                const idMatch = exampleText.match(/Example\s+ID:\s*(\d+)/i);
                if (idMatch) {
                    clearInterval(checkInterval);
                    resolve(parseInt(idMatch[1]));
                    return;
                }
                
                if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    resolve(null);
                }
            }, 200);
        });
    }
    
    function waitForElement(selector, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return;
            }
            
            const observer = new MutationObserver((mutations, obs) => {
                const element = document.querySelector(selector);
                if (element) {
                    obs.disconnect();
                    resolve(element);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Element ${selector} not found within ${timeout}ms`));
            }, timeout);
        });
    }
    
    function getCsrfToken() {
        const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieMatch ? cookieMatch[1] : '';
    }
    
    function checkUserRole(projectId) {
        // Check if user is annotator (not approver/admin/manager)
        // This is a simple check - in production, you might want to fetch from API
        // For now, we'll show the button and let the backend handle permission checks
        return true; // Show button, backend will validate
    }
    
    async function addSkipButton() {
        if (!isAnnotationPage()) return;
        
        const projectId = getProjectId();
        if (!projectId) {
            console.log('[Monlam Skip] No project ID found');
            return;
        }
        
        // Check if user is annotator (skip button only for annotators)
        if (!checkUserRole(projectId)) {
            console.log('[Monlam Skip] User is not an annotator, skipping button');
            return;
        }
        
        console.log('[Monlam Skip] Waiting for example to load...');
        const exampleId = await getCurrentExampleId();
        
        if (!exampleId) {
            console.log('[Monlam Skip] Could not get example ID');
            return;
        }
        
        console.log('[Monlam Skip] Example ID:', exampleId, 'Project ID:', projectId);
        
        // Wait for toolbar to appear
        try {
            await waitForElement('.v-toolbar, header, [role="toolbar"]', 5000);
        } catch (e) {
            console.log('[Monlam Skip] Toolbar not found, trying alternative locations...');
        }
        
        // Check if button already added
        if (document.querySelector('.monlam-skip-button')) {
            console.log('[Monlam Skip] Button already added');
            return;
        }
        
        // Find toolbar or header element
        const toolbar = document.querySelector('.v-toolbar') || 
                       document.querySelector('header') || 
                       document.querySelector('[role="toolbar"]') ||
                       document.querySelector('.toolbar-laptop') ||
                       document.querySelector('.v-app-bar');
        
        if (!toolbar) {
            console.log('[Monlam Skip] Could not find toolbar');
            // Try again after a delay
            setTimeout(addSkipButton, 1000);
            return;
        }
        
        // Create skip button
        const skipButton = document.createElement('button');
        skipButton.className = 'monlam-skip-button';
        skipButton.innerHTML = '⏭️ Skip Permanently';
        skipButton.style.cssText = `
            margin-left: 12px;
            padding: 8px 16px;
            background: #ff9800;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: background 0.2s;
        `;
        
        skipButton.onmouseover = () => {
            skipButton.style.background = '#f57c00';
        };
        skipButton.onmouseout = () => {
            skipButton.style.background = '#ff9800';
        };
        
        skipButton.onclick = async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Show dialog for reason
            const reason = prompt('Please provide a reason for skipping this example (optional):\n\nExamples: "Poor audio quality", "Not relevant", "Corrupted file", etc.');
            
            if (reason === null) {
                // User cancelled
                return;
            }
            
            skipButton.disabled = true;
            skipButton.style.opacity = '0.7';
            skipButton.textContent = '⏳ Skipping...';
            
            try {
                const response = await fetch(`/v1/projects/${projectId}/tracking/${exampleId}/skip/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({ reason: reason || '' })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    skipButton.textContent = '✅ Skipped';
                    skipButton.style.background = '#4caf50';
                    
                    // Show success message
                    alert('Example skipped successfully. You will not see this example anymore.');
                    
                    // Navigate to next example after 1 second
                    setTimeout(() => {
                        const nextBtn = document.querySelector('button[aria-label="next"], .v-btn:has([class*="next"]), button:contains("Next")');
                        if (nextBtn) {
                            nextBtn.click();
                        } else {
                            // Try to navigate using keyboard or URL
                            const urlParams = new URLSearchParams(window.location.search);
                            const currentPage = parseInt(urlParams.get('page') || '1');
                            const newUrl = window.location.pathname + '?page=' + (currentPage + 1);
                            window.location.href = newUrl;
                        }
                    }, 1000);
                } else {
                    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                    throw new Error(errorData.error || 'Failed to skip example');
                }
            } catch (error) {
                console.error('[Monlam Skip] Error:', error);
                skipButton.textContent = '❌ Error';
                skipButton.style.background = '#f44336';
                alert('Error skipping example: ' + error.message);
                
                setTimeout(() => {
                    skipButton.disabled = false;
                    skipButton.style.opacity = '1';
                    skipButton.textContent = '⏭️ Skip Permanently';
                    skipButton.style.background = '#ff9800';
                }, 2000);
            }
        };
        
        // Find a good place to insert the button
        // Try to find existing buttons in toolbar
        const existingButtons = toolbar.querySelectorAll('button, .v-btn');
        if (existingButtons.length > 0) {
            // Insert after last button
            existingButtons[existingButtons.length - 1].parentNode.insertBefore(
                skipButton,
                existingButtons[existingButtons.length - 1].nextSibling
            );
        } else {
            // Append to toolbar
            toolbar.appendChild(skipButton);
        }
        
        console.log('[Monlam Skip] ✅ Skip button added to toolbar');
    }
    
    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(addSkipButton, 1000);
        });
    } else {
        setTimeout(addSkipButton, 1000);
    }
    
    // Also run when navigating (for SPA)
    let lastUrl = location.href;
    new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            setTimeout(addSkipButton, 1000);
        }
    }).observe(document, { subtree: true, childList: true });
    
})();

