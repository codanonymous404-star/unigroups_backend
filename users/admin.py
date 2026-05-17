from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as Base
from .models import User

@admin.register(User)
class UserAdmin(Base):
    list_display    = ['roll_number','name','email','role','department','is_verified','is_active']
    list_filter     = ['role','department','is_verified']
    search_fields   = ['roll_number','email','name']
    ordering        = ['-created_at']
    fieldsets = (
        (None,           {'fields': ('roll_number','email','password')}),
        ('Personal',     {'fields': ('name',)}),
        ('Role & Dept',  {'fields': ('role','department')}),
        ('Verification', {'fields': ('is_verified','otp_code','otp_created_at')}),
        ('Permissions',  {'fields': ('is_active','is_staff','is_superuser')}),
    )
    add_fieldsets = ((None, {'classes':('wide',), 'fields':('roll_number','name','email','password1','password2','role','department')}),)
    readonly_fields = ['created_at','updated_at','otp_created_at']
