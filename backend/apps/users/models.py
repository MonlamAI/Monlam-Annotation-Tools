"""
Custom User model for Monlam Doccano.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with additional fields for Monlam Doccano.
    """
    email = models.EmailField(unique=True)
    
    # Additional profile fields
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, default='')
    
    # Tibetan name support
    tibetan_name = models.CharField(max_length=255, blank=True, default='')
    
    class Meta:
        db_table = 'users_user'
        ordering = ['username']
    
    def __str__(self):
        return self.username

