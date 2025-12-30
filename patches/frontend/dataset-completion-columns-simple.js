/**
 * Dataset Table Completion Columns - SIMPLIFIED VERSION
 * Adds completion status columns using simpler API calls
 * 
 * Features:
 * - Annotator assignment status column
 * - Approver status column (when available)
 * - Works without comprehensive API
 * 
 * Author: Monlam AI
 * Date: December 30, 2025
 */

(function() {
    'use strict';
    
    console.log('[Monlam] Dataset Completion Columns Patch loaded (Simple)');
    
    let projectId = null;
    let assignmentData = {};
    let columnsAdded = false;
    
    /**
     * Extract project ID from URL
     */
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? match[1] : null;
    }
    
    /**
     * Check if we're on dataset page
     */
    function isDatasetPage() {
        return window.location.pathname.includes('/dataset');
    }
    
    /**
     * Fetch assignment data (simple approach)
     */
    async function fetchAssignments() {
        if (!projectId) return {};
        
        try {
            // Fetch assignments directly
            const response = await fetch(`/v1/projects/${projectId}/assignments/`);
            if (response.ok) {
                const data = await response.json();
                console.log('[Monlam] Assignments fetched:', data.length || data.results?.length || 0);
                
                // Index by example_id
                const indexed = {};
                const assignments = data.results || data;
                assignments.forEach(assignment => {
                    indexed[assignment.example_id] = assignment;
                });
                return indexed;
            }
        } catch (error) {
            console.log('[Monlam] Could not fetch assignments:', error);
        }
        return {};
    }
    
    /**
     * Get status badge HTML
     */
    function getStatusBadge(status, username) {
        if (!status) {
            return '<span style="color: #999; font-size: 12px;">—</span>';
        }
        
        const statusConfig = {
            'assigned': { color: '#2196F3', text: 'Assigned', icon: '📋' },
            'in_progress': { color: '#FF9800', text: 'In Progress', icon: '◐' },
            'completed': { color: '#4CAF50', text: 'Completed', icon: '●' },
            'submitted': { color: '#00BCD4', text: 'Submitted', icon: '📤' },
            'approved': { color: '#4CAF50', text: 'Approved', icon: '✓' },
            'rejected': { color: '#F44336', text: 'Rejected', icon: '✗' },
        };
        
        const config = statusConfig[status] || { color: '#757575', text: status, icon: '?' };
        
        return `
            <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                <span style="background: ${config.color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;">
                    <span>${config.icon}</span>
                    <span>${config.text}</span>
                </span>
                ${username ? `<span style="font-size: 10px; color: #666;">${username}</span>` : ''}
            </div>
        `;
    }
    
    /**
     * Add completion columns to table header
     */
    function addCompletionHeaderColumns() {
        const tableHeaders = document.querySelectorAll('thead tr');
        
        tableHeaders.forEach(headerRow => {
            // Check if columns already added
            if (headerRow.querySelector('.monlam-completion-header')) return;
            
            // Check if this is the data table (has ID column)
            const hasIdColumn = headerRow.querySelector('th');
            if (!hasIdColumn) return;
            
            // Find status column or last column
            const allHeaders = Array.from(headerRow.querySelectorAll('th'));
            const statusHeader = allHeaders.find(th => 
                th.textContent.toLowerCase().includes('status')
            );
            const insertAfter = statusHeader || allHeaders[allHeaders.length - 2]; // Before Actions
            
            if (!insertAfter) return;
            
            // Add Annotator Status column
            const annotatorHeader = document.createElement('th');
            annotatorHeader.className = 'monlam-completion-header text-start';
            annotatorHeader.innerHTML = `
                <span style="display: flex; align-items: center; gap: 6px; font-weight: 600;" title="Assignment status">
                    <span>👤</span>
                    <span>Assigned To</span>
                </span>
            `;
            annotatorHeader.style.cssText = 'padding: 12px 16px; text-align: center; background: #f5f5f5;';
            
            // Insert after status column
            insertAfter.after(annotatorHeader);
            
            console.log('[Monlam] Header columns added');
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
            
            // Get example ID from the first cell or data attribute
            let exampleId = null;
            
            // Try to get from onclick or route
            const clickableCell = row.querySelector('td[onclick], td a, td button');
            if (clickableCell) {
                const onclick = clickableCell.getAttribute('onclick') || clickableCell.querySelector('a, button')?.getAttribute('onclick') || '';
                const match = onclick.match(/\/projects\/\d+\/(\d+)/);
                if (match) exampleId = match[1];
            }
            
            // Fallback: try to get from any link in the row
            if (!exampleId) {
                const link = row.querySelector('a[href*="/projects/"]');
                if (link) {
                    const match = link.href.match(/\/projects\/\d+\/(\d+)/);
                    if (match) exampleId = match[1];
                }
            }
            
            // Fallback: get from first td if it's just a number
            if (!exampleId) {
                const firstCell = row.querySelector('td:first-child');
                if (firstCell && /^\d+$/.test(firstCell.textContent.trim())) {
                    exampleId = firstCell.textContent.trim();
                }
            }
            
            if (!exampleId) {
                console.log('[Monlam] Could not find example ID for row');
                return;
            }
            
            const assignment = assignmentData[exampleId];
            
            // Find where to insert (after Status column or before Actions)
            const allCells = Array.from(row.querySelectorAll('td'));
            const statusCell = allCells.find(td => 
                td.querySelector('.v-chip, .badge, [class*="status"]')
            );
            const insertAfter = statusCell || allCells[allCells.length - 2]; // Before Actions
            
            if (!insertAfter) return;
            
            // Add Annotator Status cell
            const annotatorCell = document.createElement('td');
            annotatorCell.className = 'monlam-completion-cell text-start';
            annotatorCell.style.cssText = 'padding: 12px 16px; text-align: center;';
            
            if (assignment) {
                annotatorCell.innerHTML = getStatusBadge(
                    assignment.status,
                    assignment.assigned_to_username
                );
            } else {
                annotatorCell.innerHTML = '<span style="color: #999; font-size: 12px;">Not assigned</span>';
            }
            
            // Insert after status column
            insertAfter.after(annotatorCell);
        });
        
        if (!columnsAdded && tableRows.length > 0) {
            columnsAdded = true;
            console.log('[Monlam] Data columns added to', tableRows.length, 'rows');
        }
    }
    
    /**
     * Apply completion columns to table
     */
    async function applyCompletionColumns() {
        if (!isDatasetPage()) return;
        
        // Fetch assignment data if not loaded
        if (Object.keys(assignmentData).length === 0) {
            assignmentData = await fetchAssignments();
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
        if (!projectId || !isDatasetPage()) {
            console.log('[Monlam] Not on dataset page, skipping');
            return;
        }
        
        console.log('[Monlam] Initializing dataset completion columns for project', projectId);
        
        // Apply columns after short delay
        setTimeout(applyCompletionColumns, 1000);
        
        // Watch for table updates (pagination, filtering, etc.)
        const observer = new MutationObserver(function(mutations) {
            const tableChanged = mutations.some(m => 
                Array.from(m.addedNodes).some(node => 
                    node.nodeName === 'TR' || 
                    (node.querySelector && node.querySelector('tbody tr'))
                )
            );
            
            if (tableChanged) {
                columnsAdded = false; // Reset flag
                setTimeout(applyCompletionColumns, 200);
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
        setTimeout(init, 1500); // Longer delay to ensure Vue has rendered
    }
})();

