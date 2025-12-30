/**
 * Completion Matrix for Metrics Page - FIXED VERSION
 * 
 * Best Practices Applied:
 * 1. Non-invasive: Adds content, doesn't replace
 * 2. Proper page detection
 * 3. Single execution (no infinite loops)
 * 4. Graceful empty state handling
 * 5. Comprehensive logging
 * 
 * Author: Monlam AI
 * Date: December 30, 2025 - Fixed Version
 */

(function() {
    'use strict';
    
    console.log('[Monlam Metrics] Script loaded');
    
    // Flag to prevent multiple injections
    let injected = false;
    
    /**
     * Strict metrics page detection
     */
    function isMetricsPage() {
        const path = window.location.pathname;
        const isMetrics = path.endsWith('/metrics') || path.match(/\/projects\/\d+\/metrics$/);
        console.log('[Monlam Metrics] Page check:', path, '→', isMetrics);
        return isMetrics;
    }
    
    /**
     * Extract project ID
     */
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Fetch completion data from public APIs
     */
    async function fetchCompletionData(projectId) {
        try {
            console.log('[Monlam Metrics] Fetching data for project', projectId);
            
            const [summaryRes, annotatorsRes, approversRes] = await Promise.all([
                fetch(`/v1/projects/${projectId}/assignments/completion-matrix/summary/`),
                fetch(`/v1/projects/${projectId}/assignments/completion-matrix/annotators/`),
                fetch(`/v1/projects/${projectId}/assignments/completion-matrix/approvers/`)
            ]);
            
            console.log('[Monlam Metrics] API Status:', {
                summary: summaryRes.status,
                annotators: annotatorsRes.status,
                approvers: approversRes.status
            });
            
            if (!summaryRes.ok) {
                console.error('[Monlam Metrics] Summary API failed:', summaryRes.status);
                return null;
            }
            
            const summary = await summaryRes.json();
            const annotators = annotatorsRes.ok ? await annotatorsRes.json() : [];
            const approvers = approversRes.ok ? await approversRes.json() : [];
            
            const data = {
                summary,
                annotators: Array.isArray(annotators) ? annotators : [],
                approvers: Array.isArray(approvers) ? approvers : []
            };
            
            console.log('[Monlam Metrics] Data fetched:', {
                summary: summary,
                annotatorCount: data.annotators.length,
                approverCount: data.approvers.length
            });
            
            return data;
        } catch (error) {
            console.error('[Monlam Metrics] Fetch error:', error);
            return null;
        }
    }
    
    /**
     * Create completion matrix HTML
     */
    function createCompletionHTML(data) {
        const hasAnnotators = data.annotators.length > 0;
        const hasApprovers = data.approvers.length > 0;
        
        return `
            <div class="monlam-completion-section" style="margin-top: 32px; padding: 24px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="border-bottom: 2px solid #667eea; padding-bottom: 16px; margin-bottom: 24px;">
                    <h2 style="margin: 0; color: #667eea; display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 32px;">📊</span>
                        <span>Completion Tracking</span>
                    </h2>
                    <p style="margin: 8px 0 0 0; color: #666; font-size: 14px;">Track annotator progress and approver activity</p>
                </div>
                
                <!-- Summary Cards -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px;">
                        <div style="font-size: 32px; font-weight: bold;">${data.summary.total_examples}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Total Examples</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px;">
                        <div style="font-size: 32px; font-weight: bold;">${data.summary.completed_examples}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Completed</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 8px;">
                        <div style="font-size: 32px; font-weight: bold;">${data.summary.assigned_examples}</div>
                        <div style="font-size: 14px; opacity: 0.9;">Assigned</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: white; padding: 20px; border-radius: 8px;">
                        <div style="font-size: 32px; font-weight: bold;">${data.summary.completion_rate.toFixed(1)}%</div>
                        <div style="font-size: 14px; opacity: 0.9;">Completion Rate</div>
                    </div>
                </div>
                
                <!-- Annotators Section -->
                <div style="margin-bottom: 32px;">
                    <h3 style="color: #333; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                        <span>👥</span> Annotators Progress
                    </h3>
                    ${hasAnnotators ? `
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; min-width: 600px;">
                                <thead>
                                    <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                                        <th style="padding: 12px; text-align: left; font-weight: 600;">Username</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">Assigned</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">In Progress</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">Completed</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">Progress</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.annotators.map((a, idx) => `
                                        <tr style="background: ${idx % 2 === 0 ? '#fff' : '#f8f9fa'}; border-bottom: 1px solid #dee2e6;">
                                            <td style="padding: 12px;">${a.username}</td>
                                            <td style="padding: 12px; text-align: center;">${a.total_assigned}</td>
                                            <td style="padding: 12px; text-align: center;">${a.in_progress}</td>
                                            <td style="padding: 12px; text-align: center;">${a.completed}</td>
                                            <td style="padding: 12px; text-align: center;">
                                                <div style="display: flex; align-items: center; gap: 8px;">
                                                    <div style="flex: 1; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                                                        <div style="width: ${Math.min(a.completion_rate, 100)}%; height: 100%; background: ${a.completion_rate >= 100 ? '#28a745' : a.completion_rate >= 50 ? '#007bff' : '#ffc107'};"></div>
                                                    </div>
                                                    <span style="font-weight: 600; min-width: 50px;">${a.completion_rate.toFixed(1)}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : `
                        <div style="padding: 32px; text-align: center; background: #f8f9fa; border-radius: 8px; color: #666;">
                            <div style="font-size: 48px; margin-bottom: 12px;">📝</div>
                            <p style="margin: 0; font-size: 16px;">No annotators assigned yet</p>
                            <p style="margin: 8px 0 0 0; font-size: 14px;">Assign tasks to see progress here</p>
                        </div>
                    `}
                </div>
                
                <!-- Approvers Section -->
                <div>
                    <h3 style="color: #333; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                        <span>✅</span> Approvers Activity
                    </h3>
                    ${hasApprovers ? `
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; min-width: 600px;">
                                <thead>
                                    <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                                        <th style="padding: 12px; text-align: left; font-weight: 600;">Username</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">Pending</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">Approved</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">Rejected</th>
                                        <th style="padding: 12px; text-align: center; font-weight: 600;">Approval Rate</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.approvers.map((a, idx) => `
                                        <tr style="background: ${idx % 2 === 0 ? '#fff' : '#f8f9fa'}; border-bottom: 1px solid #dee2e6;">
                                            <td style="padding: 12px;">${a.username}</td>
                                            <td style="padding: 12px; text-align: center;">${a.pending_review}</td>
                                            <td style="padding: 12px; text-align: center; color: #28a745; font-weight: 500;">${a.approved}</td>
                                            <td style="padding: 12px; text-align: center; color: #dc3545; font-weight: 500;">${a.rejected}</td>
                                            <td style="padding: 12px; text-align: center;">
                                                <div style="display: flex; align-items: center; gap: 8px;">
                                                    <div style="flex: 1; height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden;">
                                                        <div style="width: ${Math.min(a.approval_rate, 100)}%; height: 100%; background: ${a.approval_rate >= 90 ? '#28a745' : a.approval_rate >= 70 ? '#007bff' : '#ffc107'};"></div>
                                                    </div>
                                                    <span style="font-weight: 600; min-width: 50px;">${a.approval_rate.toFixed(1)}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : `
                        <div style="padding: 32px; text-align: center; background: #f8f9fa; border-radius: 8px; color: #666;">
                            <div style="font-size: 48px; margin-bottom: 12px;">⏳</div>
                            <p style="margin: 0; font-size: 16px;">No approvals yet</p>
                            <p style="margin: 8px 0 0 0; font-size: 14px;">Completed work will appear here for approval</p>
                        </div>
                    `}
                </div>
            </div>
        `;
    }
    
    /**
     * Inject completion section (non-invasive)
     */
    async function injectCompletionSection() {
        if (injected) {
            console.log('[Monlam Metrics] Already injected, skipping');
            return;
        }
        
        if (!isMetricsPage()) {
            console.log('[Monlam Metrics] Not on metrics page');
            return;
        }
        
        const projectId = getProjectId();
        if (!projectId) {
            console.error('[Monlam Metrics] No project ID');
            return;
        }
        
        // Wait for page to load
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Find container (don't replace, append)
        const container = document.querySelector('.v-main__wrap .container, main .container, .v-main__wrap');
        if (!container) {
            console.error('[Monlam Metrics] No container found');
            return;
        }
        
        // Check if already exists
        if (container.querySelector('.monlam-completion-section')) {
            console.log('[Monlam Metrics] Section already exists');
            injected = true;
            return;
        }
        
        console.log('[Monlam Metrics] Injecting completion section');
        
        // Fetch data
        const data = await fetchCompletionData(projectId);
        if (!data) {
            console.error('[Monlam Metrics] Failed to fetch data');
            return;
        }
        
        // Create and append (don't replace!)
        const section = document.createElement('div');
        section.innerHTML = createCompletionHTML(data);
        container.appendChild(section.firstElementChild);
        
        injected = true;
        console.log('[Monlam Metrics] ✅ Successfully injected');
    }
    
    /**
     * Initialize - runs once
     */
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', injectCompletionSection);
        } else {
            injectCompletionSection();
        }
        
        console.log('[Monlam Metrics] Initialized');
    }
    
    init();
})();

