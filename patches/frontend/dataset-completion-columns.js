/**
 * Dataset Table Completion Columns
 * Adds completion status columns to the examples/dataset table view
 * 
 * Features:
 * - Annotator completion status column
 * - Approver completion status column
 * - Color-coded badges
 * - Hover tooltips with details
 * - Real-time updates
 * 
 * Author: Monlam AI
 * Date: December 30, 2025
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Dataset Completion Columns Patch loaded');
    
    let projectId = null;
    let exampleCompletionData = {};
    
    /**
     * Extract project ID from URL
     */
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Fetch comprehensive example data
     */
    async function fetchExampleCompletionData() {
        if (!projectId) {
            projectId = getProjectId();
            if (!projectId) return null;
        }
        
        try {
            const response = await fetch(`/v1/projects/${projectId}/assignments/comprehensive-examples/`);
            if (response.ok) {
                const data = await response.json();
                console.log('[Monlam] Comprehensive example data fetched:', data.length, 'examples');
                
                // Index by example_id for quick lookup
                const indexed = {};
                data.forEach(item => {
                    indexed[item.example_id] = item;
                });
                return indexed;
            }
        } catch (error) {
            console.log('[Monlam] Could not fetch comprehensive data:', error);
        }
        return null;
    }
    
    /**
     * Get status badge HTML
     */
    function getStatusBadge(status, type = 'annotator') {
        if (!status || status === 'null' || status === null) {
            return '<span class="monlam-status-badge monlam-status-unassigned" title="Not assigned">—</span>';
        }
        
        const statusConfig = {
            // Annotator statuses
            'not_started': { color: '#9E9E9E', text: 'Not Started', icon: '○' },
            'in_progress': { color: '#FF9800', text: 'In Progress', icon: '◐' },
            'completed': { color: '#4CAF50', text: 'Completed', icon: '●' },
            
            // Approver statuses
            'pending': { color: '#FFC107', text: 'Pending Review', icon: '⏳' },
            'approved': { color: '#4CAF50', text: 'Approved', icon: '✓' },
            'rejected': { color: '#F44336', text: 'Rejected', icon: '✗' },
            
            // Assignment statuses
            'assigned': { color: '#2196F3', text: 'Assigned', icon: '📋' },
            'submitted': { color: '#00BCD4', text: 'Submitted', icon: '📤' },
            'reassigned': { color: '#FF5722', text: 'Reassigned', icon: '↺' }
        };
        
        const config = statusConfig[status] || { color: '#757575', text: status, icon: '?' };
        
        return `
            <span class="monlam-status-badge" 
                  style="background: ${config.color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;"
                  title="${config.text}">
                <span>${config.icon}</span>
                <span>${config.text}</span>
            </span>
        `;
    }
    
    /**
     * Add completion columns to table header
     */
    function addCompletionHeaderColumns() {
        const tableHeaders = document.querySelectorAll('thead tr');
        
        tableHeaders.forEach(headerRow => {
            // Check if we're on the dataset/examples page
            const hasIdColumn = headerRow.querySelector('th');
            if (!hasIdColumn) return;
            
            // Check if columns already added
            if (headerRow.querySelector('.monlam-completion-header')) return;
            
            // Find where to insert (after Status column or before Audio)
            const statusHeader = Array.from(headerRow.querySelectorAll('th')).find(th => 
                th.textContent.toLowerCase().includes('status')
            );
            
            const insertAfter = statusHeader || headerRow.querySelector('th');
            if (!insertAfter) return;
            
            // Add Annotator Status column
            const annotatorHeader = document.createElement('th');
            annotatorHeader.className = 'monlam-completion-header';
            annotatorHeader.innerHTML = `
                <span style="display: flex; align-items: center; gap: 4px;" title="Annotator completion status">
                    <span>👤</span>
                    <span>Annotator</span>
                </span>
            `;
            annotatorHeader.style.cssText = 'padding: 8px; text-align: center; font-weight: 600; background: #f5f5f5;';
            
            // Add Approver Status column
            const approverHeader = document.createElement('th');
            approverHeader.className = 'monlam-completion-header';
            approverHeader.innerHTML = `
                <span style="display: flex; align-items: center; gap: 4px;" title="Approver review status">
                    <span>✓</span>
                    <span>Approver</span>
                </span>
            `;
            approverHeader.style.cssText = 'padding: 8px; text-align: center; font-weight: 600; background: #f5f5f5;';
            
            // Insert after Status column
            insertAfter.after(annotatorHeader);
            annotatorHeader.after(approverHeader);
        });
    }
    
    /**
     * Add completion columns to table rows
     */
    function addCompletionDataColumns() {
        const tableRows = document.querySelectorAll('tbody tr');
        
        tableRows.forEach(row => {
            // Check if columns already added
            if (row.querySelector('.monlam-completion-cell')) return;
            
            // Get example ID from the row
            const idCell = row.querySelector('td:first-child');
            if (!idCell) return;
            
            const exampleId = idCell.textContent.trim();
            const completionInfo = exampleCompletionData[exampleId];
            
            // Find where to insert (after Status column)
            const statusCell = Array.from(row.querySelectorAll('td')).find(td => {
                const badge = td.querySelector('.v-chip, .badge, [class*="status"]');
                return badge !== null;
            });
            
            const insertAfter = statusCell || row.querySelector('td');
            if (!insertAfter) return;
            
            // Add Annotator Status cell
            const annotatorCell = document.createElement('td');
            annotatorCell.className = 'monlam-completion-cell';
            annotatorCell.style.cssText = 'padding: 8px; text-align: center;';
            
            if (completionInfo) {
                const annotatorStatus = completionInfo.annotator_completion_status || completionInfo.assignment_status;
                const annotatorUser = completionInfo.assigned_to_username;
                
                annotatorCell.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                        ${getStatusBadge(annotatorStatus, 'annotator')}
                        ${annotatorUser ? `<span style="font-size: 10px; color: #666;">${annotatorUser}</span>` : ''}
                    </div>
                `;
            } else {
                annotatorCell.innerHTML = getStatusBadge(null);
            }
            
            // Add Approver Status cell
            const approverCell = document.createElement('td');
            approverCell.className = 'monlam-completion-cell';
            approverCell.style.cssText = 'padding: 8px; text-align: center;';
            
            if (completionInfo && completionInfo.reviewed_by_username) {
                const approverStatus = completionInfo.approver_completion_status;
                const approverUser = completionInfo.reviewed_by_username;
                
                approverCell.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                        ${getStatusBadge(approverStatus, 'approver')}
                        <span style="font-size: 10px; color: #666;">${approverUser}</span>
                    </div>
                `;
            } else {
                approverCell.innerHTML = getStatusBadge(null);
            }
            
            // Insert after Status column
            insertAfter.after(annotatorCell);
            annotatorCell.after(approverCell);
        });
    }
    
    /**
     * Apply completion columns to table
     */
    async function applyCompletionColumns() {
        // Fetch data if not already loaded
        if (!exampleCompletionData || Object.keys(exampleCompletionData).length === 0) {
            const data = await fetchExampleCompletionData();
            if (data) {
                exampleCompletionData = data;
            }
        }
        
        // Add header columns
        addCompletionHeaderColumns();
        
        // Add data columns
        addCompletionDataColumns();
    }
    
    /**
     * Initialize
     */
    function init() {
        projectId = getProjectId();
        if (!projectId) return;
        
        // Check if we're on the dataset page
        const isDatasetPage = window.location.pathname.includes('/dataset') || 
                             document.querySelector('[class*="dataset"]') ||
                             document.querySelector('table tbody tr td');
        
        if (!isDatasetPage) return;
        
        console.log('[Monlam] Initializing dataset completion columns');
        
        // Apply columns after short delay to ensure table is rendered
        setTimeout(applyCompletionColumns, 500);
        
        // Watch for table updates (pagination, filtering, etc.)
        const observer = new MutationObserver(function(mutations) {
            // Check if table content changed
            const tableChanged = mutations.some(m => 
                Array.from(m.addedNodes).some(node => 
                    node.nodeName === 'TR' || 
                    (node.querySelector && node.querySelector('table'))
                )
            );
            
            if (tableChanged) {
                setTimeout(applyCompletionColumns, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('[Monlam] Dataset completion columns initialized');
    }
    
    // Wait for page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 1000); // Delay to ensure Vue has rendered
    }
})();

