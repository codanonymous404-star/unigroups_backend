from rest_framework.permissions import BasePermission
from .models import GroupMember

class IsGroupLeader(BasePermission):
    message = 'Only group leader can perform this action.'
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin: return True
        return GroupMember.objects.filter(group=obj, user=request.user, role='leader').exists()
