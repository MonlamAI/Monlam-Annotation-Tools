"""
Patch to filter examples by assignment.

This mixin should be added to the ExampleList view to restrict
annotators to only seeing their assigned examples.

Apply to: /doccano/backend/examples/views.py
"""


class AssignmentFilterMixin:
    """
    Mixin to filter examples by assignment.
    
    - Project Admin: sees all
    - Annotation Approver: sees all
    - Annotator: sees only assigned items
    
    Usage: Add this mixin to ExampleList view class.
    """
    
    def filter_queryset_by_assignment(self, queryset):
        """
        Filter queryset based on user's role and assignments.
        Call this in get_queryset() method.
        """
        from projects.models import Member
        
        user = self.request.user
        project_id = self.kwargs.get('project_id')
        
        # Check user's role in project
        try:
            member = Member.objects.select_related('role').get(
                project_id=project_id,
                user=user
            )
        except Member.DoesNotExist:
            return queryset.none()
        
        role_name = member.role.name.lower()
        
        # Admins and Approvers see everything
        if role_name in ['project_admin', 'annotation_approver', 'admin']:
            return queryset
        
        # Annotators only see their assigned items
        if role_name == 'annotator':
            return queryset.filter(assigned_to=user)
        
        # Default: only assigned items
        return queryset.filter(assigned_to=user)


# Instructions to apply:
"""
In /doccano/backend/examples/views.py, find the ExampleList class and modify:

1. Import the mixin:
   from .views_filter_patch import AssignmentFilterMixin

2. Add mixin to class:
   class ExampleList(AssignmentFilterMixin, generics.ListCreateAPIView):

3. Modify get_queryset:
   def get_queryset(self):
       queryset = super().get_queryset()
       # Add this line:
       queryset = self.filter_queryset_by_assignment(queryset)
       return queryset
"""

