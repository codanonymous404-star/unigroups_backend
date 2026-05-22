from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPES = [
        ('join_request',   'Join Request'),
        ('request_accepted', 'Request Accepted'),
        ('request_rejected', 'Request Rejected'),
        ('member_removed', 'Removed from Group'),
        ('group_locked',   'Group Locked'),
        ('group_unlocked', 'Group Unlocked'),
        ('member_added',   'Added to Group'),
        ('general',        'General'),
    ]

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=30, choices=TYPES, default='general')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    data       = models.JSONField(default=dict, blank=True)  # extra context e.g. group_id
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] {self.user.name}: {self.title}'
