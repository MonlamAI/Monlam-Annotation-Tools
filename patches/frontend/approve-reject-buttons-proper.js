/**
 * Approve/Reject Buttons for Annotation Page
 * 
 * Adds buttons underneath the label box on annotation pages
 * Connected to proper backend API for tracking
 */

(function() {
    'use strict';
    
    console.log('[Monlam Approve] Initializing approve/reject buttons...');
    
    function isAnnotationPage() {
        const path = window.location.pathname;
        return path.includes('/speech-to-text') || 
               path.includes('/document-classification') ||
               path.includes('/sequence-labeling') ||
               path.includes('/sequence-to-sequence') ||
               path.includes('/image-classification') ||
               path.includes('/image-captioning');
    }
    
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }
    
    function getExampleIdFromPage() {
        // Try to get from URL query params (page number)
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page');
        
        // Note: This gives us the page number, not example ID
        // We'll need to get the actual example ID from Vue or wait for it to load
        return null; // Will be populated when example loads
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
                    // Check if we can access the current example from Vue
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
    
    async function addButtons() {
        if (!isAnnotationPage()) return;
        
        const projectId = getProjectId();
        if (!projectId) {
            console.log('[Monlam Approve] No project ID found');
            return;
        }
        
        console.log('[Monlam Approve] Waiting for example to load...');
        const exampleId = await getCurrentExampleId();
        
        if (!exampleId) {
            console.log('[Monlam Approve] Could not get example ID');
            return;
        }
        
        console.log('[Monlam Approve] Example ID:', exampleId, 'Project ID:', projectId);
        
        // Wait for the label box to appear
        await waitForElement('.v-card, .label-box, main');
        
        // Check if buttons already added
        if (document.querySelector('.monlam-approve-buttons')) {
            console.log('[Monlam Approve] Buttons already added');
            return;
        }
        
        // Fetch current status
        const currentStatus = await fetch Status(projectId, exampleId);
        
        // Create button container
        const container = createButtonContainer(projectId, exampleId, currentStatus);
        
        // Find injection point (underneath label box)
        const injectionPoint = findInjectionPoint();
        if (injectionPoint) {
            injectionPoint.appendChild(container);
            console.log('[Monlam Approve] ✅ Buttons added');
        } else {
            console.log('[Monlam Approve] Could not find injection point');
        }
    }
    
    async function fetchStatus(projectId, exampleId) {
        try {
            const response = await fetch(`/v1/projects/${projectId}/tracking/${exampleId}/status/`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('[Monlam Approve] Error fetching status:', error);
        }
        return { status: 'pending', annotated_by: null, reviewed_by: null };
    }
    
    function createButtonContainer(projectId, exampleId, statusData) {
        const container = document.createElement('div');
        container.className = 'monlam-approve-buttons';
        container.style.cssText = `
            margin: 16px 0;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        `;
        
        // Status display
        const statusColors = {
            'pending': { bg: '#e9ecef', color: '#495057', icon: '⏳' },
            'submitted': { bg: '#fff3cd', color: '#856404', icon: '📤' },
            'approved': { bg: '#d4edda', color: '#155724', icon: '✅' },
            'rejected': { bg: '#f8d7da', color: '#721c24', icon: '❌' }
        };
        
        const statusStyle = statusColors[statusData.status] || statusColors['pending'];
        
        container.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 600; margin-bottom: 8px; color: #495057;">
                        ${statusStyle.icon} Review Status
                    </div>
                    <div style="display: flex; gap: 16px; font-size: 13px; color: #6c757d;">
                        <div>
                            <span style="font-weight: 500;">Annotated by:</span>
                            <span>${statusData.annotated_by || 'Not yet'}</span>
                        </div>
                        <div>
                            <span style="font-weight: 500;">Reviewed by:</span>
                            <span>${statusData.reviewed_by || 'Not yet'}</span>
                        </div>
                        <div>
                            <span style="display: inline-block; padding: 4px 12px; border-radius: 12px; background: ${statusStyle.bg}; color: ${statusStyle.color}; font-weight: 500;">
                                ${statusData.status.toUpperCase()}
                            </span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 12px;">
                    <button class="approve-btn" style="
                        background: #28a745;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.2s;
                        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
                    ">
                        ✓ Approve
                    </button>
                    <button class="reject-btn" style="
                        background: #dc3545;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.2s;
                        box-shadow: 0 2px 4px rgba(220, 53, 69, 0.3);
                    ">
                        ✗ Reject
                    </button>
                </div>
            </div>
        `;
        
        // Add event listeners
        const approveBtn = container.querySelector('.approve-btn');
        const rejectBtn = container.querySelector('.reject-btn');
        
        approveBtn.addEventListener('click', () => handleApprove(projectId, exampleId, approveBtn, rejectBtn));
        rejectBtn.addEventListener('click', () => handleReject(projectId, exampleId, approveBtn, rejectBtn));
        
        // Hover effects
        approveBtn.addEventListener('mouseenter', () => {
            approveBtn.style.transform = 'translateY(-2px)';
            approveBtn.style.boxShadow = '0 4px 8px rgba(40, 167, 69, 0.4)';
        });
        approveBtn.addEventListener('mouseleave', () => {
            approveBtn.style.transform = 'translateY(0)';
            approveBtn.style.boxShadow = '0 2px 4px rgba(40, 167, 69, 0.3)';
        });
        
        rejectBtn.addEventListener('mouseenter', () => {
            rejectBtn.style.transform = 'translateY(-2px)';
            rejectBtn.style.boxShadow = '0 4px 8px rgba(220, 53, 69, 0.4)';
        });
        rejectBtn.addEventListener('mouseleave', () => {
            rejectBtn.style.transform = 'translateY(0)';
            rejectBtn.style.boxShadow = '0 2px 4px rgba(220, 53, 69, 0.3)';
        });
        
        return container;
    }
    
    async function handleApprove(projectId, exampleId, approveBtn, rejectBtn) {
        approveBtn.disabled = true;
        approveBtn.textContent = '⏳ Approving...';
        approveBtn.style.opacity = '0.7';
        
        try {
            const response = await fetch(`/v1/projects/${projectId}/tracking/${exampleId}/approve/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ review_notes: '' })
            });
            
            if (response.ok) {
                approveBtn.textContent = '✅ Approved!';
                approveBtn.style.background = '#5cb85c';
                rejectBtn.disabled = true;
                rejectBtn.style.opacity = '0.3';
                
                // Auto-advance to next example after 1 second
                setTimeout(() => {
                    const nextBtn = document.querySelector('button[aria-label="next"], .v-btn:has([class*="next"])');
                    if (nextBtn) nextBtn.click();
                }, 1000);
            } else {
                throw new Error('Approve failed');
            }
        } catch (error) {
            console.error('[Monlam Approve] Error:', error);
            approveBtn.textContent = '❌ Failed';
            approveBtn.disabled = false;
            approveBtn.style.opacity = '1';
        }
    }
    
    async function handleReject(projectId, exampleId, approveBtn, rejectBtn) {
        const notes = prompt('Please provide a reason for rejection:');
        if (!notes) return;
        
        rejectBtn.disabled = true;
        rejectBtn.textContent = '⏳ Rejecting...';
        rejectBtn.style.opacity = '0.7';
        
        try {
            const response = await fetch(`/v1/projects/${projectId}/tracking/${exampleId}/reject/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ review_notes: notes })
            });
            
            if (response.ok) {
                rejectBtn.textContent = '✗ Rejected';
                rejectBtn.style.background = '#d9534f';
                approveBtn.disabled = true;
                approveBtn.style.opacity = '0.3';
                
                // Auto-advance to next example after 1 second
                setTimeout(() => {
                    const nextBtn = document.querySelector('button[aria-label="next"], .v-btn:has([class*="next"])');
                    if (nextBtn) nextBtn.click();
                }, 1000);
            } else {
                throw new Error('Reject failed');
            }
        } catch (error) {
            console.error('[Monlam Approve] Error:', error);
            rejectBtn.textContent = '❌ Failed';
            rejectBtn.disabled = false;
            rejectBtn.style.opacity = '1';
        }
    }
    
    function findInjectionPoint() {
        // Look for the main content area
        const main = document.querySelector('main .v-card__text, main .container, main');
        return main;
    }
    
    function waitForElement(selector, timeout = 10000) {
        return new Promise((resolve) => {
            if (document.querySelector(selector)) {
                resolve(document.querySelector(selector));
                return;
            }
            
            const observer = new MutationObserver(() => {
                if (document.querySelector(selector)) {
                    observer.disconnect();
                    resolve(document.querySelector(selector));
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            setTimeout(() => {
                observer.disconnect();
                resolve(null);
            }, timeout);
        });
    }
    
    function getCsrfToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [key, value] = cookie.trim().split('=');
            if (key === name) return decodeURIComponent(value);
        }
        return '';
    }
    
    // Initialize
    function init() {
        console.log('[Monlam Approve] Initializing...');
        
        // Run on page load
        setTimeout(addButtons, 2000);
        
        // Re-run on navigation (SPA)
        let lastPath = window.location.pathname;
        setInterval(() => {
            if (window.location.pathname !== lastPath) {
                lastPath = window.location.pathname;
                console.log('[Monlam Approve] URL changed, re-initializing...');
                setTimeout(addButtons, 1000);
            }
        }, 500);
    }
    
    // Run after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

