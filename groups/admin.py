from django.contrib import admin
from .models import Group, GroupMember, JoinRequest

class GroupMemberInline(admin.TabularInline):
    model = GroupMember; extra = 0
    fields = ['user','role','joined_at']; readonly_fields = ['joined_at']

class JoinRequestInline(admin.TabularInline):
    model = JoinRequest; extra = 0
    fields = ['user','status','message','reviewed_by']; readonly_fields = ['reviewed_at']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display  = ['name','department','member_count','max_members','status','is_locked','created_by','created_at']
    list_filter   = ['department','status','is_locked']
    search_fields = ['name','created_by__roll_number']
    readonly_fields = ['created_at','updated_at']
    inlines = [GroupMemberInline, JoinRequestInline]
    def member_count(self, obj): return obj.member_count

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display  = ['user','group','role','joined_at']
    list_filter   = ['role']; readonly_fields = ['joined_at']

@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display  = ['user','group','status','reviewed_by','created_at']
    list_filter   = ['status']; readonly_fields = ['created_at','updated_at','reviewed_at']
