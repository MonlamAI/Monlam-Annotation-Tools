"""
Project admin configuration.
"""

from django.contrib import admin
from .models import Project, Member


class MemberInline(admin.TabularInline):
    model = Member
    extra = 1
    raw_id_fields = ['user']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'project_type', 'created_by', 'created_at', 'member_count']
    list_filter = ['project_type', 'created_at']
    search_fields = ['name', 'tibetan_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MemberInline]
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'role', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'project__name']
    raw_id_fields = ['user', 'project']

