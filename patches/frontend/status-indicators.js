/**
 * Status Indicators for Completion Tracking
 * 
 * Visual indicators that can be integrated into Doccano's annotation UI
 * to show completion status for each example.
 */

// Status indicator component
class StatusIndicator {
    constructor(status, size = 'medium') {
        this.status = status;
        this.size = size;
    }
    
    /**
     * Get the HTML for the status indicator
     */
    render() {
        const config = this.getStatusConfig(this.status);
        const sizeClass = `status-indicator-${this.size}`;
        
        return `
            <div class="status-indicator ${sizeClass}" 
                 data-status="${this.status}"
                 title="${config.label}">
                <span class="status-dot" style="background-color: ${config.color}"></span>
                <span class="status-label">${config.icon} ${config.label}</span>
            </div>
        `;
    }
    
    /**
     * Get status configuration
     */
    getStatusConfig(status) {
        const configs = {
            'not_started': {
                color: '#9e9e9e',
                icon: '○',
                label: 'Not Started',
                cssClass: 'pending'
            },
            'assigned': {
                color: '#9e9e9e',
                icon: '○',
                label: 'Assigned',
                cssClass: 'assigned'
            },
            'in_progress': {
                color: '#ff9800',
                icon: '◐',
                label: 'In Progress',
                cssClass: 'in-progress'
            },
            'submitted': {
                color: '#00bcd4',
                icon: '✓',
                label: 'Submitted',
                cssClass: 'submitted'
            },
            'completed': {
                color: '#4caf50',
                icon: '✓',
                label: 'Completed',
                cssClass: 'completed'
            },
            'approved': {
                color: '#2196f3',
                icon: '✓✓',
                label: 'Approved',
                cssClass: 'approved'
            },
            'rejected': {
                color: '#f44336',
                icon: '✗',
                label: 'Rejected',
                cssClass: 'rejected'
            },
            'reassigned': {
                color: '#9c27b0',
                icon: '↻',
                label: 'Reassigned',
                cssClass: 'reassigned'
            }
        };
        
        return configs[status] || configs['not_started'];
    }
}

/**
 * Completion Badge Component
 * Shows completion percentage with color coding
 */
class CompletionBadge {
    constructor(completionRate, total, completed) {
        this.completionRate = completionRate;
        this.total = total;
        this.completed = completed;
    }
    
    render() {
        const colorClass = this.getColorClass(this.completionRate);
        
        return `
            <div class="completion-badge ${colorClass}">
                <div class="completion-badge-progress" style="width: ${this.completionRate}%"></div>
                <div class="completion-badge-text">
                    ${this.completed}/${this.total} (${this.completionRate.toFixed(1)}%)
                </div>
            </div>
        `;
    }
    
    getColorClass(rate) {
        if (rate >= 80) return 'completion-high';
        if (rate >= 50) return 'completion-medium';
        return 'completion-low';
    }
}

/**
 * Multi-User Status Indicator
 * Shows completion status for multiple annotators/approvers on the same example
 */
class MultiUserStatusIndicator {
    constructor(users) {
        // users: Array of {username, status, role}
        this.users = users;
    }
    
    render() {
        const annotators = this.users.filter(u => u.role === 'annotator');
        const approvers = this.users.filter(u => u.role === 'approver');
        
        return `
            <div class="multi-user-status">
                ${annotators.length > 0 ? this.renderUserGroup('Annotators', annotators) : ''}
                ${approvers.length > 0 ? this.renderUserGroup('Approvers', approvers) : ''}
            </div>
        `;
    }
    
    renderUserGroup(title, users) {
        const indicators = users.map(user => {
            const indicator = new StatusIndicator(user.status, 'small');
            const config = indicator.getStatusConfig(user.status);
            
            return `
                <div class="user-status-item" title="${user.username}: ${config.label}">
                    <span class="user-status-dot" style="background-color: ${config.color}"></span>
                    <span class="user-status-name">${user.username}</span>
                </div>
            `;
        }).join('');
        
        return `
            <div class="user-status-group">
                <div class="user-status-group-title">${title}</div>
                ${indicators}
            </div>
        `;
    }
}

/**
 * Per-Example Status Card
 * Compact card showing completion status for an example
 */
class ExampleStatusCard {
    constructor(exampleId, annotatorStatus, approverStatus) {
        this.exampleId = exampleId;
        this.annotatorStatus = annotatorStatus;
        this.approverStatus = approverStatus;
    }
    
    render() {
        const annotatorIndicator = new StatusIndicator(this.annotatorStatus, 'small');
        const approverIndicator = new StatusIndicator(this.approverStatus, 'small');
        
        return `
            <div class="example-status-card">
                <div class="example-status-id">Example #${this.exampleId}</div>
                <div class="example-status-indicators">
                    <div class="example-status-row">
                        <span class="example-status-role">✍️ Annotation:</span>
                        ${annotatorIndicator.render()}
                    </div>
                    <div class="example-status-row">
                        <span class="example-status-role">✅ Approval:</span>
                        ${approverIndicator.render()}
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * API Integration Helper
 * Fetches and updates status indicators from backend
 */
class StatusAPI {
    constructor(projectId) {
        this.projectId = projectId;
        this.baseUrl = `/v1/projects/${projectId}/assignments`;
    }
    
    /**
     * Get annotator completion status for an example
     */
    async getAnnotatorStatus(exampleId) {
        try {
            const response = await fetch(`${this.baseUrl}/annotator-completion/${exampleId}/`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch annotator status:', error);
        }
        return { is_completed: false };
    }
    
    /**
     * Get approver completion status for an example
     */
    async getApproverStatus(exampleId) {
        try {
            const response = await fetch(`${this.baseUrl}/approver-completion/${exampleId}/`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch approver status:', error);
        }
        return { status: 'pending' };
    }
    
    /**
     * Mark example as complete
     */
    async markComplete(exampleId) {
        try {
            const response = await fetch(`${this.baseUrl}/annotator-completion/${exampleId}/complete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Failed to mark complete:', error);
            return false;
        }
    }
    
    /**
     * Approve example
     */
    async approve(exampleId, notes = '') {
        try {
            const response = await fetch(`${this.baseUrl}/approver-completion/${exampleId}/approve/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ notes })
            });
            return response.ok;
        } catch (error) {
            console.error('Failed to approve:', error);
            return false;
        }
    }
    
    /**
     * Reject example
     */
    async reject(exampleId, notes = '') {
        try {
            const response = await fetch(`${this.baseUrl}/approver-completion/${exampleId}/reject/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ notes })
            });
            return response.ok;
        } catch (error) {
            console.error('Failed to reject:', error);
            return false;
        }
    }
    
    /**
     * Get completion matrix (Project Manager only)
     */
    async getCompletionMatrix() {
        try {
            const response = await fetch(`${this.baseUrl}/completion-matrix/`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to fetch completion matrix:', error);
        }
        return null;
    }
}

/**
 * Auto-update status indicators
 * Periodically refreshes status indicators on the page
 */
class StatusAutoUpdater {
    constructor(projectId, intervalMs = 30000) {
        this.api = new StatusAPI(projectId);
        this.intervalMs = intervalMs;
        this.intervalId = null;
    }
    
    start() {
        if (this.intervalId) return;
        
        this.update();
        this.intervalId = setInterval(() => this.update(), this.intervalMs);
    }
    
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    async update() {
        // Find all status indicators on the page
        const indicators = document.querySelectorAll('[data-example-id][data-status-type]');
        
        for (const indicator of indicators) {
            const exampleId = indicator.dataset.exampleId;
            const statusType = indicator.dataset.statusType;
            
            if (statusType === 'annotator') {
                const status = await this.api.getAnnotatorStatus(exampleId);
                this.updateIndicator(indicator, status.is_completed ? 'completed' : 'in_progress');
            } else if (statusType === 'approver') {
                const status = await this.api.getApproverStatus(exampleId);
                this.updateIndicator(indicator, status.status);
            }
        }
    }
    
    updateIndicator(element, status) {
        const statusIndicator = new StatusIndicator(status, 'small');
        element.innerHTML = statusIndicator.render();
    }
}

// CSS Styles (inject into page)
const statusIndicatorStyles = `
<style>
    /* Status Indicator Styles */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 13px;
        background-color: #f5f5f5;
    }
    
    .status-indicator-small {
        padding: 2px 6px;
        font-size: 11px;
    }
    
    .status-indicator-large {
        padding: 6px 12px;
        font-size: 14px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .status-label {
        font-weight: 500;
    }
    
    /* Completion Badge */
    .completion-badge {
        position: relative;
        height: 24px;
        border-radius: 12px;
        background-color: #e0e0e0;
        overflow: hidden;
        min-width: 100px;
    }
    
    .completion-badge-progress {
        position: absolute;
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .completion-badge.completion-high .completion-badge-progress {
        background-color: #4caf50;
    }
    
    .completion-badge.completion-medium .completion-badge-progress {
        background-color: #ff9800;
    }
    
    .completion-badge.completion-low .completion-badge-progress {
        background-color: #f44336;
    }
    
    .completion-badge-text {
        position: relative;
        z-index: 1;
        line-height: 24px;
        text-align: center;
        font-size: 12px;
        font-weight: 600;
        color: #333;
    }
    
    /* Multi-User Status */
    .multi-user-status {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .user-status-group {
        background-color: #fafafa;
        padding: 8px;
        border-radius: 4px;
    }
    
    .user-status-group-title {
        font-size: 11px;
        font-weight: 600;
        color: #666;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    
    .user-status-item {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 2px 0;
        font-size: 12px;
    }
    
    .user-status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }
    
    .user-status-name {
        color: #333;
    }
    
    /* Example Status Card */
    .example-status-card {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 12px;
        background-color: white;
    }
    
    .example-status-id {
        font-weight: 600;
        color: #333;
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    .example-status-indicators {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    
    .example-status-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
    }
    
    .example-status-role {
        color: #666;
        font-weight: 500;
    }
</style>
`;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        StatusIndicator,
        CompletionBadge,
        MultiUserStatusIndicator,
        ExampleStatusCard,
        StatusAPI,
        StatusAutoUpdater,
        statusIndicatorStyles
    };
}

