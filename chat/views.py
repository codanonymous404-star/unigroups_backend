from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from groups.models import Group, GroupMember
from .models import Message
from .serializers import MessageSerializer, MessageCreateSerializer

class GroupMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def _check(self, group_id, user):
        try:    group = Group.objects.get(pk=group_id)
        except: return None, Response({'success': False, 'message': 'Not found.'}, status=404)
        is_member = GroupMember.objects.filter(group=group, user=user).exists()
        if not (is_member or user.is_admin):
            return None, Response({'success': False, 'message': 'Members only.'}, status=403)
        return group, None

    def get(self, request, group_id):
        group, err = self._check(group_id, request.user)
        if err: return err
        limit = int(request.query_params.get('limit', 50))
        msgs  = list(reversed(list(Message.objects.filter(group=group).select_related('sender').order_by('-created_at')[:limit])))
        return Response({'success': True, 'group': group.name, 'count': len(msgs), 'messages': MessageSerializer(msgs, many=True).data})

    def post(self, request, group_id):
        group, err = self._check(group_id, request.user)
        if err: return err
        s = MessageCreateSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        msg = Message.objects.create(group=group, sender=request.user, content=s.validated_data['content'])
        return Response({'success': True, 'message': MessageSerializer(msg).data}, status=201)

class MessageDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, message_id):
        try:    msg = Message.objects.get(pk=message_id)
        except: return Response({'success': False, 'message': 'Not found.'}, status=404)
        if msg.sender != request.user and not request.user.is_admin:
            return Response({'success': False, 'message': 'Cannot delete others messages.'}, status=403)
        msg.delete()
        return Response({'success': True, 'message': 'Deleted.'})
