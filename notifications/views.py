from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)[:50]
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({
            'success': True,
            'unread':  unread,
            'notifications': NotificationSerializer(notifs, many=True).data
        })


class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        nid = request.data.get('id')
        if nid:
            Notification.objects.filter(user=request.user, id=nid).update(is_read=True)
        else:
            # Mark all as read
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'success': True, 'unread': unread})


class DeleteNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, notif_id):
        Notification.objects.filter(user=request.user, id=notif_id).delete()
        return Response({'success': True})
