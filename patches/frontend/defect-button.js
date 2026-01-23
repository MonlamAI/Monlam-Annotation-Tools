/**
 * Defect Button for Annotation Toolbar
 * 
 * Adds a "Defect" button to the annotation toolbar
 * Allows annotators to permanently mark examples as defects
 * Defect examples are hidden from annotator's view permanently
 */

(function() {
    'use strict';
    
    console.log('[Monlam Defect] Initializing defect button...');
    
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
               path.includes('/segmentation');
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
                
                // Try to get from URL query params
                const urlParams = new URLSearchParams(window.location.search);
                const page = urlParams.get('page');
                if (page && parseInt(page) > 0) {
                    // We're on a specific page, try to get example ID from API
                    const projectId = getProjectId();
                    if (projectId) {
                        fetch(`/v1/projects/${projectId}/examples?limit=1&offset=${(parseInt(page) - 1)}`)
                            .then(res => res.json())
                            .then(data => {
                                if (data.results && data.results.length > 0) {
                                    clearInterval(checkInterval);
                                    resolve(data.results[0].id);
                                }
                            })
                            .catch(() => {});
                    }
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
    
    async function checkUserRole(projectId) {
        // Check if user is annotator (not approver/admin/manager)
        try {
            const response = await fetch(`/v1/projects/${projectId}/my-role`);
            if (response.ok) {
                const roleData = await response.json();
                const roleName = (roleData.rolename || roleData.role || '').toLowerCase();
                
                // User is annotator if role includes 'annotator' but not admin/manager/approver
                return roleName.includes('annotator') && 
                       !roleName.includes('admin') && 
                       !roleName.includes('manager') && 
                       !roleName.includes('approver');
            }
        } catch (error) {
            console.error('[Monlam Defect] Error checking role:', error);
        }
        // Default to showing button, backend will validate
        return true;
    }
    
    function showNotification(message, type = 'success') {
        // Create a simple notification element
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#4caf50' : '#f44336';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 10000;
            font-size: 14px;
            max-width: 400px;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => {
            notification.style.transition = 'opacity 0.3s';
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    function navigateToNext() {
        // Try to find and click next button using pagination component
        const paginationButtons = document.querySelectorAll('.v-btn, button');
        for (const btn of paginationButtons) {
            const ariaLabel = btn.getAttribute('aria-label');
            const text = btn.textContent || '';
            const icon = btn.querySelector('i, .v-icon');
            const iconText = icon ? icon.textContent || icon.className : '';
            
            if (ariaLabel && ariaLabel.toLowerCase().includes('next')) {
                btn.click();
                return;
            }
            if (text.includes('Next') || iconText.includes('chevron_right') || iconText.includes('mdi-chevron-right')) {
                btn.click();
                return;
            }
        }
        
        // Fallback: navigate using URL
        const urlParams = new URLSearchParams(window.location.search);
        const currentPage = parseInt(urlParams.get('page') || '1', 10);
        urlParams.set('page', (currentPage + 1).toString());
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    }
    
    async function addDefectButton() {
        if (!isAnnotationPage()) return;
        
        const projectId = getProjectId();
        if (!projectId) {
            console.log('[Monlam Defect] No project ID found');
            return;
        }
        
        // Check if user is annotator (defect button only for annotators)
        const isAnnotator = await checkUserRole(projectId);
        if (!isAnnotator) {
            console.log('[Monlam Defect] User is not an annotator, skipping button');
            return;
        }
        
        console.log('[Monlam Defect] Waiting for example to load...');
        const exampleId = await getCurrentExampleId();
        
        if (!exampleId) {
            console.log('[Monlam Defect] Could not get example ID');
            // Retry after a delay
            setTimeout(addDefectButton, 2000);
            return;
        }
        
        console.log('[Monlam Defect] Example ID:', exampleId, 'Project ID:', projectId);
        
        // Wait for toolbar to appear
        try {
            await waitForElement('.v-toolbar, .toolbar-control, [role="toolbar"]', 5000);
        } catch (e) {
            console.log('[Monlam Defect] Toolbar not found, trying alternative locations...');
        }
        
        // Check if button already added
        if (document.querySelector('.monlam-defect-button')) {
            console.log('[Monlam Defect] Button already added');
            return;
        }
        
        // Find toolbar - look for the button group containing keyboard shortcut button
        const keyboardShortcutBtn = Array.from(document.querySelectorAll('button, .v-btn')).find(btn => {
            const icon = btn.querySelector('i, .v-icon');
            if (!icon) return false;
            const iconClass = icon.className || '';
            const ariaLabel = btn.getAttribute('aria-label') || '';
            const title = btn.getAttribute('title') || '';
            return iconClass.includes('keyboard') || 
                   iconClass.includes('mdi-keyboard') ||
                   ariaLabel.toLowerCase().includes('keyboard') ||
                   title.toLowerCase().includes('keyboard');
        });
        
        if (!keyboardShortcutBtn) {
            console.log('[Monlam Defect] Could not find keyboard shortcut button, retrying...');
            setTimeout(addDefectButton, 1000);
            return;
        }
        
        // Find the parent container (v-btn-toggle or toolbar)
        const toolbar = keyboardShortcutBtn.closest('.v-btn-toggle') || 
                       keyboardShortcutBtn.closest('.v-toolbar') ||
                       keyboardShortcutBtn.closest('.toolbar-control') ||
                       keyboardShortcutBtn.parentElement;
        
        if (!toolbar) {
            console.log('[Monlam Defect] Could not find toolbar container');
            setTimeout(addDefectButton, 1000);
            return;
        }
        
        // Create defect button (icon button style to match toolbar)
        const defectButton = document.createElement('button');
        defectButton.className = 'monlam-defect-button v-btn v-btn--icon v-btn--round theme--light';
        defectButton.setAttribute('type', 'button');
        defectButton.setAttribute('aria-label', 'Mark as Defect');
        defectButton.setAttribute('title', 'Mark as Defect');
        defectButton.style.cssText = `
            margin-left: 4px;
            width: 40px;
            height: 40px;
            min-width: 40px;
            padding: 0;
            color: #f44336 !important;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.2s;
        `;
        
        // Add icon (using Material Design Icons - alert-circle)
        defectButton.innerHTML = `
            <i class="v-icon notranslate mdi mdi-alert-circle theme--light" 
               style="font-size: 24px; color: #f44336;"></i>
        `;
        
        defectButton.onmouseover = () => {
            defectButton.style.backgroundColor = 'rgba(244, 67, 54, 0.1)';
        };
        defectButton.onmouseout = () => {
            defectButton.style.backgroundColor = 'transparent';
        };
        
        defectButton.onclick = async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Confirm action
            const confirmed = confirm(
                'Mark this example as a defect?\n\n' +
                'This will permanently hide this example from your view. ' +
                'You will not see it again.\n\n' +
                'Click OK to mark as defect, or Cancel to abort.'
            );
            
            if (!confirmed) return;
            
            defectButton.disabled = true;
            defectButton.style.opacity = '0.7';
            defectButton.style.cursor = 'not-allowed';
            
            // Change icon to loading
            const originalHTML = defectButton.innerHTML;
            defectButton.innerHTML = '<i class="v-icon notranslate mdi mdi-loading mdi-spin theme--light" style="font-size: 24px;"></i>';
            
            try {
                const response = await fetch(`/v1/projects/${projectId}/tracking/${exampleId}/skip/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        reason: 'Defect - Example has issues that prevent annotation'
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    
                    // Show success notification
                    showNotification('✅ Example marked as defect. You will not see it anymore.', 'success');
                    
                    // Change icon to success temporarily
                    defectButton.innerHTML = '<i class="v-icon notranslate mdi mdi-check-circle theme--light" style="font-size: 24px; color: #4caf50;"></i>';
                    
                    // Navigate to next example after a short delay
                    setTimeout(() => {
                        navigateToNext();
                    }, 1500);
                } else {
                    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                    throw new Error(errorData.error || 'Failed to mark as defect');
                }
            } catch (error) {
                console.error('[Monlam Defect] Error:', error);
                showNotification('❌ Error: ' + error.message, 'error');
                defectButton.innerHTML = originalHTML;
                defectButton.disabled = false;
                defectButton.style.opacity = '1';
                defectButton.style.cursor = 'pointer';
            }
        };
        
        // Insert button right after keyboard shortcut button
        if (keyboardShortcutBtn.nextSibling) {
            toolbar.insertBefore(defectButton, keyboardShortcutBtn.nextSibling);
        } else {
            toolbar.appendChild(defectButton);
        }
        
        console.log('[Monlam Defect] ✅ Defect button added to toolbar');
    }
    
    // Run on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(addDefectButton, 1000);
        });
    } else {
        setTimeout(addDefectButton, 1000);
    }
    
    // Also run when navigating (for SPA)
    let lastUrl = location.href;
    new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            // Remove old button if exists
            const oldButton = document.querySelector('.monlam-defect-button');
            if (oldButton) {
                oldButton.remove();
            }
            setTimeout(addDefectButton, 1000);
        }
    }).observe(document, { subtree: true, childList: true });
    
})();

