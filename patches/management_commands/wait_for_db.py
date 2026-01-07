"""
Custom management command: wait_for_db

This command waits for the database to be ready before proceeding.
Required by Render deployment initialization script.
"""

import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database to be available"""
    
    help = 'Wait for database to be available'

    def handle(self, *args, **options):
        """Handle the command"""
        self.stdout.write('Waiting for database...')
        db_conn = None
        retries = 0
        max_retries = 30
        
        while not db_conn and retries < max_retries:
            try:
                # Try to connect to database
                connection.ensure_connection()
                db_conn = True
                self.stdout.write(self.style.SUCCESS('✅ Database available!'))
            except OperationalError:
                retries += 1
                self.stdout.write(
                    f'Database unavailable, waiting 1 second... (attempt {retries}/{max_retries})'
                )
                time.sleep(1)
        
        if not db_conn:
            self.stdout.write(
                self.style.ERROR('❌ Database connection failed after 30 attempts')
            )
            raise OperationalError('Could not connect to database')

