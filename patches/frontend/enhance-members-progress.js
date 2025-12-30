/**
 * Enhanced Members Progress Display
 * Integrates completion matrix data into the Members page
 * 
 * Features:
 * - Shows detailed completion stats per member
 * - Color-coded progress bars
 * - Hover tooltips with detailed stats
 * - Real-time updates
 * 
 * Author: Monlam AI
 * Date: December 30, 2025
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Enhanced Members Progress Patch loaded');
    
    let projectId = null;
    let completionData = null;
    
    /**
     * Extract project ID from URL
     */
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Fetch completion matrix data from API
     */
    async function fetchCompletionData() {
        if (!projectId) {
            projectId = getProjectId();
            if (!projectId) return null;
        }
        
        try {
            const response = await fetch(`/v1/projects/${projectId}/assignments/completion-matrix/summary/`);
            if (response.ok) {
                const data = await response.json();
                console.log('[Monlam] Completion data fetched:', data);
                return data;
            }
        } catch (error) {
            console.log('[Monlam] Could not fetch completion data:', error);
        }
        return null;
    }
    
    /**
     * Enhance progress bars with completion data
     */
    function enhanceProgressBars() {
        const progressContainers = document.querySelectorAll('.v-progress-linear');
        
        progressContainers.forEach(container => {
            // Find the user label
            const parentRow = container.closest('.v-list-item') || container.closest('div[class*="row"]');
            if (!parentRow) return;
            
            const userLabel = parentRow.querySelector('span, div');
            if (!userLabel || !userLabel.textContent) return;
            
            const username = userLabel.textContent.trim().split(' ')[0]; // Get first word (username)
            
            // Add enhanced styling
            if (!container.classList.contains('monlam-enhanced')) {
                container.classList.add('monlam-enhanced');
                container.style.height = '24px';
                container.style.borderRadius = '4px';
                
                // Add tooltip
                const progressText = parentRow.textContent;
                const match = progressText.match(/(\d+)\s*\/\s*(\d+)/);
                if (match) {
                    const completed = parseInt(match[1]);
                    const total = parseInt(match[2]);
                    const percentage = ((completed / total) * 100).toFixed(1);
                    
                    container.setAttribute('title', `${username}: ${completed}/${total} (${percentage}%)`);
                    
                    // Color code based on progress
                    const progressBar = container.querySelector('.v-progress-linear__determinate');
                    if (progressBar) {
                        if (percentage >= 100) {
                            progressBar.style.backgroundColor = '#4CAF50'; // Green
                        } else if (percentage >= 50) {
                            progressBar.style.backgroundColor = '#2196F3'; // Blue
                        } else if (percentage >= 25) {
                            progressBar.style.backgroundColor = '#FF9800'; // Orange
                        } else {
                            progressBar.style.backgroundColor = '#F44336'; // Red
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Add detailed stats button
     */
    function addDetailedStatsButton() {
        const memberSection = document.querySelector('h2, h3, .headline');
        if (!memberSection || memberSection.textContent.indexOf('Progress') === -1) return;
        
        // Check if button already exists
        if (document.querySelector('.monlam-stats-button')) return;
        
        const button = document.createElement('button');
        button.className = 'monlam-stats-button v-btn v-btn--flat v-btn--text theme--light v-size--default';
        button.innerHTML = `
            <span class="v-btn__content">
                <i aria-hidden="true" class="v-icon notranslate mdi mdi-chart-box theme--light"></i>
                <span>View Detailed Stats</span>
            </span>
        `;
        button.style.cssText = 'margin-left: 16px;';
        
        button.onclick = async function() {
            await showDetailedStatsModal();
        };
        
        memberSection.parentElement.appendChild(button);
    }
    
    /**
     * Show detailed stats modal
     */
    async function showDetailedStatsModal() {
        const data = await fetchCompletionData();
        if (!data) {
            alert('Could not load completion data. Please ensure the completion tracking API is enabled.');
            return;
        }
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'monlam-stats-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            border-radius: 8px;
            padding: 24px;
            max-width: 90%;
            max-height: 90%;
            overflow: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        `;
        
        modalContent.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0;">Completion Matrix - Detailed Stats</h2>
                <button class="close-modal" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
            </div>
            
            <div style="margin-bottom: 24px;">
                <h3>📊 Annotators</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Username</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Assigned</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">In Progress</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Completed</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Progress %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.annotators.map(a => `
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd;">${a.username}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${a.total_assigned}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${a.in_progress}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${a.completed}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                                    <span style="color: ${a.completion_rate >= 100 ? '#4CAF50' : a.completion_rate >= 50 ? '#2196F3' : '#FF9800'}; font-weight: bold;">
                                        ${a.completion_rate.toFixed(1)}%
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-bottom: 24px;">
                <h3>✅ Approvers</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f5f5f5;">
                            <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Username</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Pending Review</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Approved</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Rejected</th>
                            <th style="padding: 8px; text-align: center; border: 1px solid #ddd;">Approval Rate %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.approvers.map(a => `
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd;">${a.username}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${a.pending_review}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${a.approved}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">${a.rejected}</td>
                                <td style="padding: 8px; text-align: center; border: 1px solid #ddd;">
                                    <span style="color: ${a.approval_rate >= 90 ? '#4CAF50' : a.approval_rate >= 70 ? '#2196F3' : '#FF9800'}; font-weight: bold;">
                                        ${a.approval_rate.toFixed(1)}%
                                    </span>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            <div style="background: #f5f5f5; padding: 16px; border-radius: 4px;">
                <h3>📈 Project Summary</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div>
                        <div style="font-size: 24px; font-weight: bold; color: #2196F3;">${data.project_summary.total_examples}</div>
                        <div style="color: #666;">Total Examples</div>
                    </div>
                    <div>
                        <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">${data.project_summary.completed_examples}</div>
                        <div style="color: #666;">Completed</div>
                    </div>
                    <div>
                        <div style="font-size: 24px; font-weight: bold; color: #FF9800;">${data.project_summary.in_progress_examples}</div>
                        <div style="color: #666;">In Progress</div>
                    </div>
                    <div>
                        <div style="font-size: 24px; font-weight: bold; color: ${data.project_summary.overall_completion_rate >= 80 ? '#4CAF50' : '#2196F3'};">
                            ${data.project_summary.overall_completion_rate.toFixed(1)}%
                        </div>
                        <div style="color: #666;">Overall Completion</div>
                    </div>
                </div>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // Close modal handlers
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
        
        modalContent.querySelector('.close-modal').addEventListener('click', function() {
            document.body.removeChild(modal);
        });
    }
    
    /**
     * Initialize enhancements
     */
    function init() {
        projectId = getProjectId();
        if (!projectId) return;
        
        // Enhance progress bars
        enhanceProgressBars();
        
        // Add detailed stats button
        addDetailedStatsButton();
        
        // Re-run on navigation/updates
        const observer = new MutationObserver(function() {
            enhanceProgressBars();
            addDetailedStatsButton();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('[Monlam] Members progress enhancements initialized');
    }
    
    // Wait for page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

