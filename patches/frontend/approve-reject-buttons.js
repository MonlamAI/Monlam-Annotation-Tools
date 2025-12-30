/**
 * Approve/Reject Buttons for Annotation Page
 * Adds approval workflow buttons for approvers and project managers
 * 
 * Features:
 * - Approve/Reject buttons on annotation page
 * - Only visible to approvers and project managers
 * - Updates completion status via API
 * - Syncs with dataset table and metrics page
 * 
 * Author: Monlam AI
 * Date: December 30, 2025
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Approve/Reject Buttons Patch loaded');
    
    let projectId = null;
    let exampleId = null;
    let currentUserRole = null;
    let buttonsAdded = false;
    
    /**
     * Check if we're on an annotation page
     */
    function isAnnotationPage() {
        const path = window.location.pathname;
        return path.includes('/annotation') || path.match(/\/projects\/\d+\/\d+/);
    }
    
    /**
     * Extract project ID from URL
     */
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Extract example ID from URL
     */
    function getExampleId() {
        // Look for pattern: /projects/{project_id}/{example_id}
        const match = window.location.pathname.match(/\/projects\/\d+\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Get current user's role in the project
     */
    async function getUserRole() {
        if (!projectId) return null;
        
        try {
            // Try to fetch project members to determine role
            const response = await fetch(`/v1/projects/${projectId}/members`);
            if (response.ok) {
                const members = await response.json();
                // Find current user (usually the API returns current user info)
                // For now, we'll check if user has permission to access approver endpoints
                return await checkApproverPermission();
            }
        } catch (error) {
            console.log('[Monlam] Could not fetch user role:', error);
        }
        return null;
    }
    
    /**
     * Check if user has approver permission by testing the API
     */
    async function checkApproverPermission() {
        try {
            // Try to access the completion matrix (only approvers+ can access)
            const response = await fetch(`/v1/projects/${projectId}/assignments/completion-matrix/my/`);
            if (response.ok || response.status === 200) {
                return 'approver'; // Has approver or higher permission
            }
        } catch (error) {
            console.log('[Monlam] Not an approver:', error);
        }
        return null;
    }
    
    /**
     * Call approve API
     */
    async function approveExample() {
        if (!projectId || !exampleId) {
            alert('Cannot approve: Missing project or example ID');
            return;
        }
        
        try {
            const response = await fetch(
                `/v1/projects/${projectId}/assignments/approver-completion/${exampleId}/approve/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        review_notes: '' // Optional: Could add a notes input
                    })
                }
            );
            
            if (response.ok) {
                showNotification('✓ Approved successfully!', 'success');
                updateButtonState('approved');
                console.log('[Monlam] Example approved:', exampleId);
            } else {
                const error = await response.json();
                showNotification(`Failed to approve: ${error.error || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('[Monlam] Error approving:', error);
            showNotification('Error approving example', 'error');
        }
    }
    
    /**
     * Call reject API
     */
    async function rejectExample() {
        if (!projectId || !exampleId) {
            alert('Cannot reject: Missing project or example ID');
            return;
        }
        
        const notes = prompt('Rejection reason (optional):');
        if (notes === null) return; // User cancelled
        
        try {
            const response = await fetch(
                `/v1/projects/${projectId}/assignments/approver-completion/${exampleId}/reject/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify({
                        review_notes: notes || ''
                    })
                }
            );
            
            if (response.ok) {
                showNotification('✗ Rejected', 'warning');
                updateButtonState('rejected');
                console.log('[Monlam] Example rejected:', exampleId);
            } else {
                const error = await response.json();
                showNotification(`Failed to reject: ${error.error || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('[Monlam] Error rejecting:', error);
            showNotification('Error rejecting example', 'error');
        }
    }
    
    /**
     * Get CSRF token from cookies
     */
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    /**
     * Show notification to user
     */
    function showNotification(message, type = 'info') {
        // Try to use Vuetify snackbar if available
        const existingNotif = document.querySelector('.monlam-notification');
        if (existingNotif) {
            existingNotif.remove();
        }
        
        const colors = {
            success: '#4CAF50',
            error: '#F44336',
            warning: '#FF9800',
            info: '#2196F3'
        };
        
        const notification = document.createElement('div');
        notification.className = 'monlam-notification';
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            font-size: 16px;
            font-weight: 500;
            animation: slideIn 0.3s ease-out;
            font-family: MonlamTBslim, 'Noto Sans Tibetan', sans-serif;
        `;
        notification.textContent = message;
        
        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    /**
     * Update button states after action
     */
    function updateButtonState(status) {
        const approveBtn = document.querySelector('.monlam-approve-btn');
        const rejectBtn = document.querySelector('.monlam-reject-btn');
        
        if (status === 'approved') {
            if (approveBtn) {
                approveBtn.style.opacity = '0.5';
                approveBtn.style.pointerEvents = 'none';
                approveBtn.innerHTML = '✓ Approved';
            }
            if (rejectBtn) {
                rejectBtn.style.opacity = '0.3';
            }
        } else if (status === 'rejected') {
            if (rejectBtn) {
                rejectBtn.style.opacity = '0.5';
                rejectBtn.style.pointerEvents = 'none';
                rejectBtn.innerHTML = '✗ Rejected';
            }
            if (approveBtn) {
                approveBtn.style.opacity = '0.3';
            }
        }
    }
    
    /**
     * Check current approval status
     */
    async function checkApprovalStatus() {
        if (!projectId || !exampleId) return null;
        
        try {
            const response = await fetch(
                `/v1/projects/${projectId}/assignments/approver-completion/${exampleId}/`
            );
            
            if (response.ok) {
                const data = await response.json();
                console.log('[Monlam] Current approval status:', data);
                return data.status;
            }
        } catch (error) {
            console.log('[Monlam] Could not check approval status:', error);
        }
        return null;
    }
    
    /**
     * Create and inject approve/reject buttons
     */
    async function injectApprovalButtons() {
        if (buttonsAdded) return;
        if (!isAnnotationPage()) return;
        
        projectId = getProjectId();
        exampleId = getExampleId();
        
        if (!projectId || !exampleId) {
            console.log('[Monlam] Missing project or example ID');
            return;
        }
        
        // Check if user has approver role
        currentUserRole = await getUserRole();
        if (!currentUserRole) {
            console.log('[Monlam] User does not have approver permission');
            return;
        }
        
        console.log('[Monlam] User has approver permission, adding buttons');
        
        // Find a good place to inject buttons (top toolbar area)
        let toolbar = document.querySelector('.v-toolbar, .toolbar, header');
        
        // If no toolbar, create a floating button container
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 1000;
                display: flex;
                gap: 12px;
            `;
            document.body.appendChild(toolbar);
        }
        
        // Check current status
        const currentStatus = await checkApprovalStatus();
        
        // Create button container
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'monlam-approval-buttons';
        buttonContainer.style.cssText = `
            display: flex;
            gap: 12px;
            align-items: center;
            margin-left: auto;
            padding: 8px;
        `;
        
        // Approve button
        const approveBtn = document.createElement('button');
        approveBtn.className = 'monlam-approve-btn';
        approveBtn.innerHTML = currentStatus === 'approved' ? '✓ Approved' : '✓ Approve';
        approveBtn.style.cssText = `
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            font-family: MonlamTBslim, 'Noto Sans Tibetan', sans-serif;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
            ${currentStatus === 'approved' ? 'opacity: 0.5; pointer-events: none;' : ''}
        `;
        approveBtn.onmouseover = () => {
            if (currentStatus !== 'approved') {
                approveBtn.style.background = '#45a049';
                approveBtn.style.transform = 'translateY(-2px)';
                approveBtn.style.boxShadow = '0 4px 12px rgba(76, 175, 80, 0.4)';
            }
        };
        approveBtn.onmouseout = () => {
            if (currentStatus !== 'approved') {
                approveBtn.style.background = '#4CAF50';
                approveBtn.style.transform = 'translateY(0)';
                approveBtn.style.boxShadow = '0 2px 8px rgba(76, 175, 80, 0.3)';
            }
        };
        approveBtn.onclick = approveExample;
        
        // Reject button
        const rejectBtn = document.createElement('button');
        rejectBtn.className = 'monlam-reject-btn';
        rejectBtn.innerHTML = currentStatus === 'rejected' ? '✗ Rejected' : '✗ Reject';
        rejectBtn.style.cssText = `
            background: #F44336;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            font-family: MonlamTBslim, 'Noto Sans Tibetan', sans-serif;
            box-shadow: 0 2px 8px rgba(244, 67, 54, 0.3);
            ${currentStatus === 'rejected' ? 'opacity: 0.5; pointer-events: none;' : ''}
        `;
        rejectBtn.onmouseover = () => {
            if (currentStatus !== 'rejected') {
                rejectBtn.style.background = '#da190b';
                rejectBtn.style.transform = 'translateY(-2px)';
                rejectBtn.style.boxShadow = '0 4px 12px rgba(244, 67, 54, 0.4)';
            }
        };
        rejectBtn.onmouseout = () => {
            if (currentStatus !== 'rejected') {
                rejectBtn.style.background = '#F44336';
                rejectBtn.style.transform = 'translateY(0)';
                rejectBtn.style.boxShadow = '0 2px 8px rgba(244, 67, 54, 0.3)';
            }
        };
        rejectBtn.onclick = rejectExample;
        
        // Add buttons to container
        buttonContainer.appendChild(approveBtn);
        buttonContainer.appendChild(rejectBtn);
        
        // Inject into toolbar
        if (toolbar.classList && (toolbar.classList.contains('v-toolbar') || toolbar.tagName === 'HEADER')) {
            // Insert into existing toolbar
            const toolbarContent = toolbar.querySelector('.v-toolbar__content');
            if (toolbarContent) {
                toolbarContent.appendChild(buttonContainer);
            } else {
                toolbar.appendChild(buttonContainer);
            }
        } else {
            // Use floating container
            toolbar.appendChild(buttonContainer);
        }
        
        buttonsAdded = true;
        console.log('[Monlam] Approval buttons added');
    }
    
    /**
     * Initialize
     */
    function init() {
        if (isAnnotationPage()) {
            console.log('[Monlam] On annotation page, will add approval buttons');
            
            // Wait a bit for page to fully render
            setTimeout(injectApprovalButtons, 1000);
            
            // Watch for navigation changes
            let lastUrl = window.location.href;
            let lastExampleId = getExampleId();
            
            const observer = new MutationObserver(() => {
                const newUrl = window.location.href;
                const newExampleId = getExampleId();
                
                if (newUrl !== lastUrl || newExampleId !== lastExampleId) {
                    lastUrl = newUrl;
                    lastExampleId = newExampleId;
                    buttonsAdded = false;
                    exampleId = newExampleId;
                    
                    if (isAnnotationPage()) {
                        setTimeout(injectApprovalButtons, 500);
                    }
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }
    
    // Wait for page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 1000);
    }
})();

