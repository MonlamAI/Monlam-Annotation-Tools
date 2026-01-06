/**
 * Proper Dataset Columns Enhancement
 * 
 * This version works with the backend API that includes assignment data
 * Inserts columns at positions 4 and 5 (after ID, Text, Created)
 */

(function() {
    'use strict';
    
    console.log('[Monlam Dataset] Initializing proper column enhancement...');
    
    function isDatasetPage() {
        return window.location.pathname.includes('/dataset');
    }
    
    function getProjectId() {
        const match = window.location.pathname.match(/\/projects\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }
    
    function enhanceDatasetTable() {
        if (!isDatasetPage()) return;
        
        const projectId = getProjectId();
        if (!projectId) return;
        
        console.log('[Monlam Dataset] Enhancing dataset table for project', projectId);
        
        // Wait for Vue to render the table
        setTimeout(() => {
            addHeaders();
            observeTableChanges();
        }, 2000);
    }
    
    function addHeaders() {
        const headerRow = document.querySelector('thead tr');
        if (!headerRow) {
            console.log('[Monlam Dataset] Header row not found');
            return;
        }
        
        // Check if already added
        if (headerRow.querySelector('.monlam-header')) {
            console.log('[Monlam Dataset] Headers already added');
            return;
        }
        
        // Get all header cells
        const headers = headerRow.querySelectorAll('th');
        
        // Insert after the 3rd column (ID, Text, Created)
        // Position 4: Annotated By
        // Position 5: Reviewed By
        if (headers.length >= 3) {
            const insertAfter = headers[2]; // After 3rd column
            
            // Create Annotated By header
            const annotatedHeader = document.createElement('th');
            annotatedHeader.textContent = 'Annotated By';
            annotatedHeader.className = 'monlam-header monlam-annotated-header';
            annotatedHeader.style.cssText = 'padding: 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e0e0e0;';
            
            // Create Reviewed By header
            const reviewedHeader = document.createElement('th');
            reviewedHeader.textContent = 'Reviewed By';
            reviewedHeader.className = 'monlam-header monlam-reviewed-header';
            reviewedHeader.style.cssText = 'padding: 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e0e0e0;';
            
            // Create Status header
            const statusHeader = document.createElement('th');
            statusHeader.textContent = 'Status';
            statusHeader.className = 'monlam-header monlam-status-header';
            statusHeader.style.cssText = 'padding: 8px; text-align: left; font-weight: 600; border-bottom: 1px solid #e0e0e0;';
            
            // Insert after the 3rd column
            insertAfter.insertAdjacentElement('afterend', annotatedHeader);
            annotatedHeader.insertAdjacentElement('afterend', reviewedHeader);
            reviewedHeader.insertAdjacentElement('afterend', statusHeader);
            
            console.log('[Monlam Dataset] ✅ Headers inserted at positions 4, 5, 6');
        }
    }
    
    function addDataCells() {
        const dataRows = document.querySelectorAll('tbody tr');
        
        dataRows.forEach(row => {
            // Check if already added
            if (row.querySelector('.monlam-cell')) {
                return;
            }
            
            // Try to get example data from Vue
            const exampleData = getExampleDataFromRow(row);
            if (!exampleData) {
                console.log('[Monlam Dataset] Could not get example data for row');
                return;
            }
            
            // Get the 3rd cell to insert after
            const cells = row.querySelectorAll('td');
            if (cells.length < 3) return;
            
            const insertAfter = cells[2];
            
            // Get values from API data (if available)
            const annotatedBy = exampleData.annotated_by_username || '—';
            const reviewedBy = exampleData.reviewed_by_username || '—';
            const status = exampleData.assignment_status || 'unassigned';
            
            // Create cells
            const annotatedCell = createCell(annotatedBy, 'monlam-annotated-cell');
            const reviewedCell = createCell(reviewedBy, 'monlam-reviewed-cell');
            const statusCell = createStatusCell(status);
            
            // Insert after the 3rd cell
            insertAfter.insertAdjacentElement('afterend', annotatedCell);
            annotatedCell.insertAdjacentElement('afterend', reviewedCell);
            reviewedCell.insertAdjacentElement('afterend', statusCell);
        });
        
        console.log('[Monlam Dataset] ✅ Data cells added to', dataRows.length, 'rows');
    }
    
    function createCell(text, className) {
        const cell = document.createElement('td');
        cell.textContent = text;
        cell.className = `monlam-cell ${className}`;
        cell.style.cssText = 'padding: 8px; border-bottom: 1px solid #e0e0e0;';
        return cell;
    }
    
    function createStatusCell(status) {
        const cell = document.createElement('td');
        cell.className = 'monlam-cell monlam-status-cell';
        cell.style.cssText = 'padding: 8px; border-bottom: 1px solid #e0e0e0;';
        
        const statusColors = {
            'assigned': '#9e9e9e',
            'in_progress': '#2196f3',
            'submitted': '#ff9800',
            'approved': '#4caf50',
            'rejected': '#f44336',
            'unassigned': '#e0e0e0'
        };
        
        const color = statusColors[status] || '#e0e0e0';
        const textColor = status === 'unassigned' ? '#666' : 'white';
        
        cell.innerHTML = `<span style="background: ${color}; color: ${textColor}; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;">${status.replace('_', ' ').toUpperCase()}</span>`;
        
        return cell;
    }
    
    function getExampleDataFromRow(row) {
        // Try to access Vue component data
        // This works if Vue exposes the data on the DOM element
        if (row.__vue__) {
            return row.__vue__.item || row.__vue__.$data.item;
        }
        
        // Fallback: Return empty data, will be filled by API call
        return {
            annotated_by_username: null,
            reviewed_by_username: null,
            assignment_status: 'unassigned'
        };
    }
    
    function observeTableChanges() {
        // Watch for table updates (pagination, filtering, etc.)
        const tableBody = document.querySelector('tbody');
        if (!tableBody) return;
        
        const observer = new MutationObserver(() => {
            addDataCells();
        });
        
        observer.observe(tableBody, {
            childList: true,
            subtree: true
        });
        
        // Initial population
        addDataCells();
    }
    
    // Initialize
    function init() {
        console.log('[Monlam Dataset] Initializing...');
        
        enhanceDatasetTable();
        
        // Re-run on navigation
        let lastPath = window.location.pathname;
        setInterval(() => {
            if (window.location.pathname !== lastPath) {
                lastPath = window.location.pathname;
                if (isDatasetPage()) {
                    setTimeout(enhanceDatasetTable, 1000);
                }
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

