#!/usr/bin/env python
"""
Diagnostic script to check Monlam Doccano database state.
Run in Render Shell: DJANGO_SETTINGS_MODULE=config.settings.production python check_database.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

print("=" * 60)
print("🔍 MONLAM DOCCANO DATABASE DIAGNOSTIC")
print("=" * 60)

# 1. Check Roles
print("\n📋 ROLES:")
print("-" * 40)
try:
    from roles.models import Role
    roles = Role.objects.all()
    if roles:
        for role in roles:
            print(f"  ID: {role.id:3d} | Name: '{role.name}'")
    else:
        print("  ⚠️ No roles found! Run init_monlam.py")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 2. Check Users
print("\n👤 USERS:")
print("-" * 40)
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all()[:10]  # First 10
    print(f"  Total users: {User.objects.count()}")
    for user in users:
        print(f"  - {user.username} (superuser: {user.is_superuser})")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 3. Check Projects
print("\n📁 PROJECTS:")
print("-" * 40)
try:
    from projects.models import Project
    projects = Project.objects.all()
    for p in projects:
        print(f"  ID: {p.id:3d} | Name: {p.name} | Type: {p.project_type}")
        print(f"        Examples: {p.examples.count()}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 4. Check Members in Projects
print("\n👥 PROJECT MEMBERS (with roles):")
print("-" * 40)
try:
    from roles.models import Member
    members = Member.objects.select_related('user', 'role', 'project').all()[:20]
    for m in members:
        print(f"  Project '{m.project.name}': {m.user.username} → Role: {m.role.name}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 5. Check AnnotationTracking table exists
print("\n📊 ANNOTATION TRACKING TABLE:")
print("-" * 40)
try:
    from assignment.simple_tracking import AnnotationTracking
    count = AnnotationTracking.objects.count()
    print(f"  ✅ Table exists! Total records: {count}")
    
    if count > 0:
        print("\n  Sample tracking records:")
        for t in AnnotationTracking.objects.select_related('annotated_by', 'reviewed_by')[:10]:
            annotator = t.annotated_by.username if t.annotated_by else 'None'
            reviewer = t.reviewed_by.username if t.reviewed_by else 'None'
            print(f"    Example {t.example_id}: status={t.status}, annotated_by={annotator}, reviewed_by={reviewer}")
    else:
        print("  ⚠️ No tracking records yet. Create an annotation to test.")
except Exception as e:
    print(f"  ❌ Error: {e}")
    print("  🔧 Table might not exist. Run migrations:")
    print("     python manage.py migrate assignment")

# 6. Check Labels/Annotations
print("\n🏷️ ANNOTATIONS (TextLabel for STT):")
print("-" * 40)
try:
    from labels.models import TextLabel
    count = TextLabel.objects.count()
    print(f"  TextLabel records: {count}")
    
    if count > 0:
        print("\n  Sample labels:")
        for label in TextLabel.objects.select_related('example', 'user')[:5]:
            print(f"    Example {label.example_id}: '{label.text[:50]}...' by {label.user.username if label.user else 'Unknown'}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 7. Check Signals Setup
print("\n🔌 SIGNALS STATUS:")
print("-" * 40)
try:
    from django.db.models.signals import post_save
    from labels.models import TextLabel
    
    receivers = post_save._live_receivers(TextLabel)
    if receivers:
        print(f"  ✅ {len(list(receivers))} signal receivers connected for TextLabel")
    else:
        print("  ⚠️ No signal receivers for TextLabel")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 8. Summary
print("\n" + "=" * 60)
print("📋 SUMMARY:")
print("=" * 60)
print("""
For visibility & approve/reject to work:

1. ROLES must include: project_admin, project_manager, annotation_approver, annotator
   → Run: python init_monlam.py

2. MEMBERS must have correct roles assigned
   → Check project settings in Doccano UI

3. ANNOTATION_TRACKING table must exist
   → Run: python manage.py migrate assignment

4. SIGNALS must be connected (auto-tracking)
   → Check logs for '[Monlam Signals] ✅ Connected'

5. For approve/reject buttons:
   → User must have role containing 'approver', 'manager', or 'admin'
""")

print("\n✅ Diagnostic complete!")

