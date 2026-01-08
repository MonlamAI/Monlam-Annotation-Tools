#!/usr/bin/env python
"""
Initialize Monlam Doccano with proper roles and permissions
Ties roles to custom tracking and visibility logic
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from roles.models import Role
from django.contrib.auth import get_user_model

User = get_user_model()

print("🚀 Initializing Monlam Doccano...")
print("=" * 50)

# First, show existing roles
print("\n📋 Existing Roles in Database:")
print("-" * 50)
existing_roles = Role.objects.all()
if existing_roles:
    for role in existing_roles:
        print(f"  - ID: {role.id}, Name: '{role.name}'")
else:
    print("  (No roles found)")

# Define roles with their permissions and mapping to our custom logic
# These are the roles needed for our custom visibility/approval features
MONLAM_ROLES = [
    {
        'name': 'project_admin',
        'description': 'Project Admin - Full project control, can manage members and see all data',
        'permissions': [
            '✅ Create/delete projects',
            '✅ Manage members',
            '✅ See all examples',
            '✅ Approve/reject annotations',
            '✅ View all tracking data',
        ]
    },
    {
        'name': 'project_manager', 
        'description': 'Project Manager - Manage workflow and approve annotations',
        'permissions': [
            '✅ Manage assignments',
            '✅ See all examples',
            '✅ Approve/reject annotations',
            '✅ View tracking reports',
        ]
    },
    {
        'name': 'annotation_approver',
        'description': 'Approver - Review and approve/reject annotations',
        'permissions': [
            '✅ See all examples',
            '✅ Approve/reject annotations',
            '✅ View tracking data',
        ]
    },
    {
        'name': 'annotator',
        'description': 'Annotator - Create annotations, filtered view',
        'permissions': [
            '✅ See only unannotated examples',
            '✅ See own rejected examples (to fix)',
            '✅ Create annotations',
            '❌ Cannot see submitted examples',
            '❌ Cannot approve/reject',
        ]
    },
]

print("\n📋 Creating Roles...")
print("-" * 50)

for role_data in MONLAM_ROLES:
    role, created = Role.objects.get_or_create(
        name=role_data['name'],
        defaults={'description': role_data['description']}
    )
    
    if created:
        print(f"\n✅ Created: {role.name}")
    else:
        print(f"\n⏭️  Exists: {role.name}")
    
    print(f"   Description: {role_data['description']}")
    print(f"   Permissions:")
    for perm in role_data['permissions']:
        print(f"      {perm}")

print("\n" + "=" * 50)
print("🎉 Roles initialized successfully!")
print("\n📌 ROLE MAPPING FOR CUSTOM FEATURES:")
print("-" * 50)

print("""
1. VISIBILITY FILTERING (monlam_tracking/filters.py):
   ├─ Annotators: See only unannotated or rejected examples
   ├─ Approvers/PMs/Admins: See all examples
   └─ Locked examples: Hidden from all except locker

2. APPROVE/REJECT BUTTONS (frontend/index.html):
   ├─ Visible for: annotation_approver, project_manager, project_admin
   └─ Hidden for: annotator

3. DATASET TABLE COLUMNS:
   ├─ Column 4: Annotated By (username)
   ├─ Column 5: Reviewed By (username)
   └─ Column 6: Status (pending, approved, rejected)

4. AUTO-TRACKING (monlam_tracking/signals.py):
   ├─ Tracks: Category, Span, TextLabel saves
   ├─ Updates: annotated_by, annotated_at
   └─ Status: pending → approved/rejected (via buttons)
""")

print("\n✅ All systems ready!")
print("\n👤 Next steps:")
print("   1. Logout and login again")
print("   2. Create a project")
print("   3. Add members with appropriate roles")
print("   4. Test annotation workflow")
print("\n🚀 Happy annotating!")

