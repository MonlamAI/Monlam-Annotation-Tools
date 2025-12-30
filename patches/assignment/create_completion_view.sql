-- ============================================================================
-- Comprehensive Completion Metrics View
-- ============================================================================
-- This view combines examples with all completion metrics in one query
-- NO table modifications required - completely safe!
-- ============================================================================

CREATE OR REPLACE VIEW example_completion_comprehensive AS
SELECT 
    -- Original Example data
    e.id as example_id,
    e.uuid,
    e.text,
    e.meta,
    e.filename,
    e.project_id,
    e.created_at as example_created_at,
    e.updated_at as example_updated_at,
    
    -- Project info
    p.name as project_name,
    
    -- Assignment info
    a.id as assignment_id,
    a.assigned_to_id as assigned_annotator_id,
    au.username as assigned_annotator_username,
    a.status as assignment_status,
    a.assigned_at,
    a.started_at,
    a.submitted_at,
    
    -- Annotator completion aggregates
    COUNT(DISTINCT ac.id) as total_annotators,
    COUNT(DISTINCT ac.id) FILTER (WHERE ac.is_completed = true) as completed_by_annotators,
    ROUND(
        COUNT(DISTINCT ac.id) FILTER (WHERE ac.is_completed = true)::numeric / 
        NULLIF(COUNT(DISTINCT ac.id), 0) * 100, 
        1
    ) as annotator_completion_rate,
    
    -- Approver completion aggregates  
    COUNT(DISTINCT ap.id) as total_approvers,
    COUNT(DISTINCT ap.id) FILTER (WHERE ap.status = 'approved') as approved_by_approvers,
    COUNT(DISTINCT ap.id) FILTER (WHERE ap.status = 'rejected') as rejected_by_approvers,
    COUNT(DISTINCT ap.id) FILTER (WHERE ap.status = 'pending') as pending_approvers,
    ROUND(
        COUNT(DISTINCT ap.id) FILTER (WHERE ap.status = 'approved')::numeric / 
        NULLIF(COUNT(DISTINCT ap.id), 0) * 100, 
        1
    ) as approval_rate,
    
    -- Overall status (computed)
    CASE
        WHEN COUNT(DISTINCT ap.id) FILTER (WHERE ap.status = 'approved') > 0 THEN 'approved'
        WHEN COUNT(DISTINCT ap.id) FILTER (WHERE ap.status = 'rejected') > 0 THEN 'rejected'
        WHEN COUNT(DISTINCT ac.id) FILTER (WHERE ac.is_completed = true) > 0 THEN 'completed'
        WHEN a.status = 'in_progress' THEN 'in_progress'
        WHEN a.status IS NOT NULL THEN 'assigned'
        ELSE 'unassigned'
    END as overall_status,
    
    -- Timestamps
    MAX(ac.completed_at) as last_completed_at,
    MAX(ap.reviewed_at) as last_reviewed_at,
    
    -- Annotation counts
    (SELECT COUNT(*) FROM examples_annotation WHERE example_id = e.id) as annotation_count

FROM examples_example e
LEFT JOIN projects_project p ON e.project_id = p.id
LEFT JOIN assignment_assignment a ON e.id = a.example_id AND a.is_active = true
LEFT JOIN auth_user au ON a.assigned_to_id = au.id
LEFT JOIN assignment_annotatorcompletionstatus ac ON e.id = ac.example_id
LEFT JOIN assignment_approvercompletionstatus ap ON e.id = ap.example_id

GROUP BY 
    e.id, e.uuid, e.text, e.meta, e.filename, e.project_id, 
    e.created_at, e.updated_at, p.name,
    a.id, a.assigned_to_id, au.username, a.status, 
    a.assigned_at, a.started_at, a.submitted_at;

-- ============================================================================
-- Create indexes on the view for better performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_example_completion_project 
    ON assignment_annotatorcompletionstatus(example_id, project_id);
    
CREATE INDEX IF NOT EXISTS idx_example_approval_project 
    ON assignment_approvercompletionstatus(example_id, project_id);

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Get all examples with completion metrics for a project:
-- SELECT * FROM example_completion_comprehensive WHERE project_id = 1;

-- Get examples with low completion rate:
-- SELECT * FROM example_completion_comprehensive 
-- WHERE annotator_completion_rate < 50 AND project_id = 1;

-- Get approved examples:
-- SELECT * FROM example_completion_comprehensive 
-- WHERE overall_status = 'approved' AND project_id = 1;

-- Get examples pending review:
-- SELECT * FROM example_completion_comprehensive 
-- WHERE overall_status = 'completed' AND pending_approvers > 0;

-- ============================================================================
-- Drop view if you need to remove it:
-- DROP VIEW IF EXISTS example_completion_comprehensive;
-- ============================================================================

