from django.urls import path
from .views import GroupMessagesView, MessageDeleteView

urlpatterns = [
    path('groups/<int:group_id>/messages/', GroupMessagesView.as_view()),
    path('messages/<int:message_id>/',      MessageDeleteView.as_view()),
]
