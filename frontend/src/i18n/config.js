/**
 * i18n Configuration for Monlam Annotation Tools
 * Supports English and Tibetan (བོད་ཡིག)
 */

import { createI18n } from 'vue-i18n'

// Import Tibetan translations
import bo from './bo/index.js'

// English translations (default)
const en = {
  // Generic
  generic: {
    continue: 'Continue',
    yes: 'Yes',
    all: 'All',
    save: 'Save',
    edit: 'Edit',
    create: 'Create',
    cancel: 'Cancel',
    close: 'Close',
    upload: 'Upload',
    add: 'Add',
    delete: 'Delete',
    deleteAll: 'Delete All',
    search: 'Search',
    name: 'Name',
    import: 'Import',
    export: 'Export',
    description: 'Description',
    type: 'Type',
    loading: 'Loading...'
  },
  
  // Header
  header: {
    projects: 'Projects'
  },
  
  // Home
  home: {
    welcome: 'Welcome to Monlam Annotation Tools',
    description: 'A powerful annotation platform for Tibetan language data'
  },
  
  // Annotation
  annotation: {
    checkedTooltip: 'Checked',
    notCheckedTooltip: 'Not Checked',
    selectFilterTooltip: 'Select Filter',
    filterOption1: 'All',
    filterOption2: 'Completed',
    filterOption3: 'Incomplete',
    guidelineTooltip: 'Show Guideline',
    guidelinePopupTitle: 'Annotation Guideline',
    commentTooltip: 'Add Comment',
    commentPopupTitle: 'Comment',
    metadataDefaultMessage: 'No metadata',
    key: 'Key',
    value: 'Value',
    newText: 'New Text'
  },
  
  // Dataset
  dataset: {
    dataset: 'Dataset',
    actions: 'Actions',
    importDataset: 'Import Dataset',
    exportDataset: 'Export Dataset',
    text: 'Text',
    metadata: 'Metadata',
    action: 'Action',
    annotate: 'Annotate',
    importDataTitle: 'Import Dataset',
    importDataMessage1: 'Select file format',
    importDataMessage2: 'Select file',
    importDataPlaceholder: 'Drop file here',
    exportDataTitle: 'Export Dataset',
    exportDataMessage: 'Select file format',
    exportDataMessage2: 'Select file name',
    deleteDocumentsTitle: 'Delete Document',
    deleteDocumentsMessage: 'Are you sure you want to delete {number} item(s)?',
    deleteBulkDocumentsTitle: 'Delete All Documents',
    deleteBulkDocumentsMessage: 'Are you sure you want to delete all documents?',
    pageText: '{0}-{1} / {2}'
  },
  
  // Completion/Tracking
  completion: {
    completionMatrix: 'Completion Matrix',
    completionTracking: 'Completion Tracking',
    dashboard: 'Dashboard',
    summary: 'Summary',
    totalExamples: 'Total Examples',
    assignedExamples: 'Assigned Examples',
    unassignedExamples: 'Unassigned Examples',
    completedExamples: 'Completed Examples',
    approvedExamples: 'Approved Examples',
    completionRate: 'Completion Rate',
    approvalRate: 'Approval Rate',
    status: 'Status',
    notStarted: 'Not Started',
    assigned: 'Assigned',
    inProgress: 'In Progress',
    submitted: 'Submitted',
    completed: 'Completed',
    approved: 'Approved',
    rejected: 'Rejected',
    reassigned: 'Reassigned',
    pending: 'Pending',
    annotatorMatrix: 'Annotator Matrix',
    approverMatrix: 'Approver Matrix',
    annotator: 'Annotator',
    totalAssigned: 'Total Assigned',
    completedCount: 'Completed',
    inProgressCount: 'In Progress',
    submittedCount: 'Submitted',
    approvedCount: 'Approved',
    progress: 'Progress',
    approver: 'Approver',
    totalToReview: 'Total to Review',
    approvedByApprover: 'Approved',
    rejectedCount: 'Rejected',
    pendingCount: 'Pending',
    markComplete: 'Mark Complete',
    markIncomplete: 'Mark Incomplete',
    approve: 'Approve',
    reject: 'Reject',
    reviewNotes: 'Review Notes',
    export: 'Export',
    exportCSV: 'Export CSV',
    sync: 'Sync',
    syncFromAssignments: 'Sync from Assignments',
    completionMarked: 'Marked as complete',
    approvalRecorded: 'Approval recorded',
    rejectionRecorded: 'Rejection recorded',
    noExamples: 'No examples',
    loadingMatrix: 'Loading matrix...',
    projectManagerOnly: 'Project managers only',
    insufficientPermissions: 'Insufficient permissions',
    yourStats: 'Your Stats',
    annotatorStats: 'Annotator Stats',
    approverStats: 'Approver Stats',
    legend: 'Legend',
    statusIndicators: 'Status Indicators'
  },
  
  // Projects
  projects: {
    home: {
      title: 'Projects',
      createProject: 'Create Project'
    },
    overview: {
      title: 'Overview',
      description: 'Project Description'
    },
    settings: {
      title: 'Settings'
    }
  }
}

// Create i18n instance
const i18n = createI18n({
  legacy: false,
  locale: 'bo', // Default to Tibetan
  fallbackLocale: 'en',
  messages: {
    en,
    bo
  }
})

export default i18n

// Export available locales
export const locales = [
  { code: 'en', name: 'English', iso: 'en-US' },
  { code: 'bo', name: 'བོད་ཡིག', iso: 'bo-CN' }
]

