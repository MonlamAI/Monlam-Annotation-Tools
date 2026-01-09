"""
Monlam-patched create_roles command.
Adds project_manager role in addition to the default 3 roles.
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from ...models import Role


class Command(BaseCommand):
    help = "Non-interactively create default roles"

    def handle(self, *args, **options):
        # Standard Doccano roles from settings
        try:
            role_names = [
                settings.ROLE_PROJECT_ADMIN, 
                settings.ROLE_ANNOTATOR, 
                settings.ROLE_ANNOTATION_APPROVER
            ]
        except KeyError as key_error:
            self.stderr.write(self.style.ERROR(f'Missing Key: "{key_error}"'))
            role_names = ['project_admin', 'annotator', 'annotation_approver']
        
        # MONLAM: Add project_manager role
        role_names.append('project_manager')
        
        for role_name in role_names:
            if Role.objects.filter(name=role_name).exists():
                self.stdout.write(f'Role already exists: "{role_name}"')
                continue
            role = Role()
            role.name = role_name
            try:
                role.save()
            except DatabaseError as db_error:
                self.stderr.write(self.style.ERROR(f'Database Error: "{db_error}"'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Role created successfully "{role_name}"'))

