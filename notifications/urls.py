from django.urls import path
from .views import NotificationListView, MarkReadView, DeleteNotificationView

urlpatterns = [
    path('',                      NotificationListView.as_view()),
    path('mark-read/',            MarkReadView.as_view()),
    path('<int:notif_id>/delete/', DeleteNotificationView.as_view()),
]
