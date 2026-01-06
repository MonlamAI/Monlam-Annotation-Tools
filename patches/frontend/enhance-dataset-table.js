/**
 * Enhance Doccano's Dataset Table with Assignment Status Columns
 * 
 * Adds columns to the existing dataset table:
 * - Annotated By
 * - Reviewed By  
 * - Status
 * 
 * This modifies the EXISTING Doccano dataset page instead of creating a new one.
 */

(function() {
    'use strict';
    
    console.log('[Monlam Dataset] Initializing dataset table enhancements...');
    
    // Check if we're on a dataset page
    function isDatasetPage() {
        return window.location.pathname.includes('/dataset');
    }
    
    // Extract project ID from URL
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }
    
    // Fetch assignment data for all examples in the project
    async function fetchAssignments(projectId) {
        try {
            console.log('[Monlam Dataset] Fetching assignments for project', projectId);
            
            const response = await fetch(`/v1/projects/${projectId}/assignments/?limit=1000`);
            if (!response.ok) {
                console.error('[Monlam Dataset] Failed to fetch assignments:', response.status);
                return {};
            }
            
            const data = await response.json();
            console.log('[Monlam Dataset] Loaded', data.results?.length || 0, 'assignments');
            
            // Create a map: example_id -> assignment
            const assignmentMap = {};
            if (data.results) {
                data.results.forEach(assignment => {
                    assignmentMap[assignment.example] = assignment;
                });
            }
            
            return assignmentMap;
        } catch (error) {
            console.error('[Monlam Dataset] Error fetching assignments:', error);
            return {};
        }
    }
    
    // Fetch user data to get usernames
    async function fetchUsers(projectId) {
        try {
            const response = await fetch(`/v1/projects/${projectId}/members`);
            if (!response.ok) return {};
            
            const data = await response.json();
            const userMap = {};
            if (data.results) {
                data.results.forEach(member => {
                    userMap[member.user] = member.username;
                });
            }
            return userMap;
        } catch (error) {
            console.error('[Monlam Dataset] Error fetching users:', error);
            return {};
        }
    }
    
    // Add custom columns to the table header
    function addTableHeaders() {
        // Find the table header row
        const headerRow = document.querySelector('thead tr');
        if (!headerRow) {
            console.log('[Monlam Dataset] Table header not found');
            return false;
        }
        
        // Check if we already added headers
        if (headerRow.querySelector('.monlam-annotated-by-header')) {
            console.log('[Monlam Dataset] Headers already added');
            return true;
        }
        
        // Add three new header cells
        const headers = [
            { text: 'Annotated By', class: 'monlam-annotated-by-header' },
            { text: 'Reviewed By', class: 'monlam-reviewed-by-header' },
            { text: 'Status', class: 'monlam-status-header' }
        ];
        
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header.text;
            th.className = header.class;
            th.style.cssText = 'padding: 8px; text-align: left; font-weight: 600;';
            headerRow.appendChild(th);
        });
        
        console.log('[Monlam Dataset] ✅ Headers added');
        return true;
    }
    
    // Add data cells to each table row
    function addDataCells(assignmentMap, userMap) {
        const dataRows = document.querySelectorAll('tbody tr');
        console.log('[Monlam Dataset] Processing', dataRows.length, 'data rows');
        
        let addedCount = 0;
        
        dataRows.forEach(row => {
            // Check if we already added cells to this row
            if (row.querySelector('.monlam-annotated-by-cell')) {
                return;
            }
            
            // Extract example ID from the row
            const exampleId = extractExampleIdFromRow(row);
            if (!exampleId) {
                console.log('[Monlam Dataset] Could not extract example ID from row');
                return;
            }
            
            // Get assignment data for this example
            const assignment = assignmentMap[exampleId];
            
            // Create cells
            const annotatedBy = assignment?.assigned_to ? (userMap[assignment.assigned_to] || 'User ' + assignment.assigned_to) : '—';
            const reviewedBy = assignment?.reviewed_by ? (userMap[assignment.reviewed_by] || 'User ' + assignment.reviewed_by) : '—';
            const status = assignment?.status || 'unassigned';
            
            // Add cells
            [
                { value: annotatedBy, class: 'monlam-annotated-by-cell' },
                { value: reviewedBy, class: 'monlam-reviewed-by-cell' },
                { value: getStatusBadge(status), class: 'monlam-status-cell', html: true }
            ].forEach(cell => {
                const td = document.createElement('td');
                td.className = cell.class;
                td.style.cssText = 'padding: 8px;';
                
                if (cell.html) {
                    td.innerHTML = cell.value;
                } else {
                    td.textContent = cell.value;
                }
                
                row.appendChild(td);
            });
            
            addedCount++;
        });
        
        console.log('[Monlam Dataset] ✅ Added cells to', addedCount, 'rows');
    }
    
    // Extract example ID from a table row
    function extractExampleIdFromRow(row) {
        // Try multiple methods to find the example ID
        
        // Method 1: Look for ID in the first cell
        const firstCell = row.querySelector('td:first-child');
        if (firstCell) {
            const idMatch = firstCell.textContent.match(/\d+/);
            if (idMatch) return parseInt(idMatch[0]);
        }
        
        // Method 2: Look for data attributes
        if (row.dataset.exampleId) {
            return parseInt(row.dataset.exampleId);
        }
        
        // Method 3: Look in any cell
        const allText = row.textContent;
        const idMatch = allText.match(/^\s*(\d+)\s/);
        if (idMatch) return parseInt(idMatch[1]);
        
        return null;
    }
    
    // Get colored badge HTML for status
    function getStatusBadge(status) {
        const badges = {
            'assigned': '<span style="background: #9e9e9e; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Assigned</span>',
            'in_progress': '<span style="background: #2196f3; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">In Progress</span>',
            'submitted': '<span style="background: #ff9800; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Submitted</span>',
            'approved': '<span style="background: #4caf50; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Approved</span>',
            'rejected': '<span style="background: #f44336; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Rejected</span>',
            'unassigned': '<span style="background: #e0e0e0; color: #666; padding: 4px 8px; border-radius: 4px; font-size: 12px;">Unassigned</span>'
        };
        
        return badges[status] || badges['unassigned'];
    }
    
    // Main enhancement function
    async function enhanceDatasetTable() {
        if (!isDatasetPage()) {
            console.log('[Monlam Dataset] Not on dataset page');
            return;
        }
        
        const projectId = getProjectId();
        if (!projectId) {
            console.log('[Monlam Dataset] Could not extract project ID');
            return;
        }
        
        console.log('[Monlam Dataset] Enhancing dataset table for project', projectId);
        
        // Wait for table to render
        await waitForElement('tbody tr', 10000);
        
        // Fetch data
        const [assignmentMap, userMap] = await Promise.all([
            fetchAssignments(projectId),
            fetchUsers(projectId)
        ]);
        
        // Add headers
        const headersAdded = addTableHeaders();
        if (!headersAdded) {
            console.log('[Monlam Dataset] Could not add headers, retrying...');
            setTimeout(() => enhanceDatasetTable(), 1000);
            return;
        }
        
        // Add data cells
        addDataCells(assignmentMap, userMap);
        
        console.log('[Monlam Dataset] ✅ Dataset table enhancement complete!');
    }
    
    // Utility: Wait for element to appear
    function waitForElement(selector, timeout = 5000) {
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
    
    // Initialize on page load
    function init() {
        console.log('[Monlam Dataset] Initializing...');
        
        // Run enhancement after a delay to ensure Vue has rendered
        setTimeout(() => {
            enhanceDatasetTable();
        }, 2000);
        
        // Re-run on URL changes (SPA navigation)
        let lastPath = window.location.pathname;
        setInterval(() => {
            if (window.location.pathname !== lastPath) {
                console.log('[Monlam Dataset] URL changed, re-enhancing...');
                lastPath = window.location.pathname;
                setTimeout(() => {
                    enhanceDatasetTable();
                }, 1000);
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

