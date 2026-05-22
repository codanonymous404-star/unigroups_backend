from django.db   import models
from django.conf import settings

class Message(models.Model):
    group      = models.ForeignKey('groups.Group', on_delete=models.CASCADE, related_name='messages')
    sender     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    content    = models.TextField()
    is_edited  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self): return f'[{self.group.name}] {self.sender.name}: {self.content[:40]}'
