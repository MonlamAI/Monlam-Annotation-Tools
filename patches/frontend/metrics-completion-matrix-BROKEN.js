/**
 * Completion Matrix for Metrics Page
 * Displays comprehensive completion tracking data on /projects/X/metrics
 * 
 * Features:
 * - Annotator completion matrix
 * - Approver approval matrix
 * - Project-wide statistics
 * - Real-time updates
 * 
 * Author: Monlam AI
 * Date: December 30, 2025
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Metrics Completion Matrix Patch loaded');
    
    /**
     * Check if we're on the metrics page
     */
    function isMetricsPage() {
        return window.location.pathname.includes('/metrics');
    }
    
    /**
     * Extract project ID from URL
     */
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Fetch completion matrix data
     * Uses separate API calls for summary, annotators, and approvers
     * These endpoints are available to all project members
     */
    async function fetchCompletionData(projectId) {
        try {
            // Fetch all three endpoints in parallel
            const [summaryRes, annotatorsRes, approversRes] = await Promise.all([
                fetch(`/v1/projects/${projectId}/assignments/completion-matrix/summary/`),
                fetch(`/v1/projects/${projectId}/assignments/completion-matrix/annotators/`),
                fetch(`/v1/projects/${projectId}/assignments/completion-matrix/approvers/`)
            ]);
            
            if (!summaryRes.ok) {
                console.error('[Monlam] Summary API failed:', summaryRes.status);
                return null;
            }
            
            const summary = await summaryRes.json();
            const annotators = annotatorsRes.ok ? await annotatorsRes.json() : [];
            const approvers = approversRes.ok ? await approversRes.json() : [];
            
            const data = {
                project_id: projectId,
                summary: summary,
                annotators: annotators,
                approvers: approvers
            };
            
            console.log('[Monlam] Completion matrix data fetched:', data);
            return data;
        } catch (error) {
            console.error('[Monlam] Error fetching completion data:', error);
        }
        return null;
    }
    
    /**
     * Create completion matrix HTML
     */
    function createCompletionMatrixHTML(data) {
        return `
            <div class="monlam-completion-matrix" style="padding: 24px; font-family: MonlamTBslim, 'Noto Sans Tibetan', -apple-system, sans-serif;">
                <!-- Project Summary -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 32px; border-radius: 12px; margin-bottom: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                    <h1 style="margin: 0 0 24px 0; font-size: 32px; font-weight: bold;">📊 Completion Matrix</h1>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                        <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                            <div style="font-size: 36px; font-weight: bold;">${data.summary.total_examples}</div>
                            <div style="font-size: 14px; opacity: 0.9;">Total Examples</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                            <div style="font-size: 36px; font-weight: bold;">${data.summary.completed_examples}</div>
                            <div style="font-size: 14px; opacity: 0.9;">Completed</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                            <div style="font-size: 36px; font-weight: bold;">${data.summary.assigned_examples}</div>
                            <div style="font-size: 14px; opacity: 0.9;">Assigned</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                            <div style="font-size: 36px; font-weight: bold;">${data.summary.completion_rate.toFixed(1)}%</div>
                            <div style="font-size: 14px; opacity: 0.9;">Overall Completion</div>
                        </div>
                    </div>
                </div>
                
                <!-- Annotators Table -->
                <div style="background: white; padding: 24px; border-radius: 12px; margin-bottom: 32px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
                    <h2 style="margin: 0 0 20px 0; font-size: 24px; color: #333; display: flex; align-items: center;">
                        <span style="font-size: 28px; margin-right: 12px;">👥</span>
                        Annotators Progress
                    </h2>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                                    <th style="padding: 16px; text-align: left; font-weight: 600; color: #495057;">Username</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">Assigned</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">In Progress</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">Completed</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">Progress</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.annotators.map((a, idx) => {
                                    const bgColor = idx % 2 === 0 ? '#ffffff' : '#f8f9fa';
                                    const progressColor = a.completion_rate >= 100 ? '#28a745' : 
                                                         a.completion_rate >= 50 ? '#007bff' : 
                                                         a.completion_rate >= 25 ? '#ffc107' : '#dc3545';
                                    return `
                                        <tr style="background: ${bgColor}; border-bottom: 1px solid #dee2e6; transition: background 0.2s;" onmouseover="this.style.background='#e9ecef'" onmouseout="this.style.background='${bgColor}'">
                                            <td style="padding: 16px; font-weight: 500; color: #212529;">${a.username}</td>
                                            <td style="padding: 16px; text-align: center; color: #6c757d;">${a.total_assigned}</td>
                                            <td style="padding: 16px; text-align: center; color: #6c757d;">${a.in_progress}</td>
                                            <td style="padding: 16px; text-align: center; color: #6c757d;">${a.completed}</td>
                                            <td style="padding: 16px; text-align: center;">
                                                <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                                                    <div style="flex: 1; max-width: 150px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                                                        <div style="width: ${Math.min(a.completion_rate, 100)}%; height: 100%; background: ${progressColor}; transition: width 0.3s;"></div>
                                                    </div>
                                                    <span style="font-weight: 600; color: ${progressColor}; min-width: 50px;">${a.completion_rate.toFixed(1)}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Approvers Table -->
                <div style="background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
                    <h2 style="margin: 0 0 20px 0; font-size: 24px; color: #333; display: flex; align-items: center;">
                        <span style="font-size: 28px; margin-right: 12px;">✅</span>
                        Approvers Activity
                    </h2>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                                    <th style="padding: 16px; text-align: left; font-weight: 600; color: #495057;">Username</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">Pending Review</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">Approved</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">Rejected</th>
                                    <th style="padding: 16px; text-align: center; font-weight: 600; color: #495057;">Approval Rate</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.approvers.map((a, idx) => {
                                    const bgColor = idx % 2 === 0 ? '#ffffff' : '#f8f9fa';
                                    const approvalColor = a.approval_rate >= 90 ? '#28a745' : 
                                                         a.approval_rate >= 70 ? '#007bff' : '#ffc107';
                                    return `
                                        <tr style="background: ${bgColor}; border-bottom: 1px solid #dee2e6; transition: background 0.2s;" onmouseover="this.style.background='#e9ecef'" onmouseout="this.style.background='${bgColor}'">
                                            <td style="padding: 16px; font-weight: 500; color: #212529;">${a.username}</td>
                                            <td style="padding: 16px; text-align: center; color: #6c757d;">${a.pending_review}</td>
                                            <td style="padding: 16px; text-align: center; color: #28a745; font-weight: 500;">${a.approved}</td>
                                            <td style="padding: 16px; text-align: center; color: #dc3545; font-weight: 500;">${a.rejected}</td>
                                            <td style="padding: 16px; text-align: center;">
                                                <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
                                                    <div style="flex: 1; max-width: 150px; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                                                        <div style="width: ${Math.min(a.approval_rate, 100)}%; height: 100%; background: ${approvalColor}; transition: width 0.3s;"></div>
                                                    </div>
                                                    <span style="font-weight: 600; color: ${approvalColor}; min-width: 50px;">${a.approval_rate.toFixed(1)}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Inject completion matrix into metrics page
     */
    async function injectCompletionMatrix() {
        if (!isMetricsPage()) {
            console.log('[Monlam] Not on metrics page, skipping');
            return;
        }
        
        const projectId = getProjectId();
        if (!projectId) {
            console.error('[Monlam] Could not extract project ID');
            return;
        }
        
        console.log('[Monlam] Injecting completion matrix for project', projectId);
        
        // Wait for main content area
        let attempts = 0;
        const maxAttempts = 20;
        
        const checkForContent = setInterval(async () => {
            attempts++;
            
            const mainContent = document.querySelector('.v-main__wrap, main, .container');
            
            if (mainContent || attempts >= maxAttempts) {
                clearInterval(checkForContent);
                
                if (!mainContent) {
                    console.error('[Monlam] Could not find main content area');
                    return;
                }
                
                // Check if already injected
                if (document.querySelector('.monlam-completion-matrix')) {
                    console.log('[Monlam] Matrix already injected');
                    return;
                }
                
                // Show loading state
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'monlam-loading';
                loadingDiv.style.cssText = 'padding: 48px; text-align: center; font-size: 18px; color: #667eea;';
                loadingDiv.innerHTML = '<div style="font-size: 48px; margin-bottom: 16px;">⏳</div>Loading completion data...';
                mainContent.innerHTML = '';
                mainContent.appendChild(loadingDiv);
                
                // Fetch and display data
                const data = await fetchCompletionData(projectId);
                
                if (data) {
                    mainContent.innerHTML = createCompletionMatrixHTML(data);
                    console.log('[Monlam] Completion matrix successfully injected');
                } else {
                    mainContent.innerHTML = `
                        <div style="padding: 48px; text-align: center;">
                            <div style="font-size: 64px; margin-bottom: 16px;">⚠️</div>
                            <h2 style="color: #666; margin-bottom: 16px;">Could Not Load Completion Data</h2>
                            <p style="color: #999; margin-bottom: 24px;">
                                Please ensure:
                                <br>• The completion tracking API is enabled
                                <br>• You have permission to view this data
                                <br>• The backend server is running
                            </p>
                            <button onclick="location.reload()" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 16px; cursor: pointer;">
                                Retry
                            </button>
                        </div>
                    `;
                }
            }
        }, 200);
    }
    
    /**
     * Initialize
     */
    function init() {
        if (isMetricsPage()) {
            console.log('[Monlam] On metrics page, initializing completion matrix');
            injectCompletionMatrix();
            
            // Re-inject on navigation
            let lastUrl = window.location.href;
            const observer = new MutationObserver(() => {
                if (window.location.href !== lastUrl) {
                    lastUrl = window.location.href;
                    if (isMetricsPage()) {
                        setTimeout(injectCompletionMatrix, 500);
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
        setTimeout(init, 500);
    }
})();

