from rest_framework import serializers
from users.serializers import UserProfileSerializer
from .models import Group, GroupMember, JoinRequest

class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    class Meta:
        model  = GroupMember
        fields = ['id','user','role','joined_at']

class JoinRequestSerializer(serializers.ModelSerializer):
    user        = UserProfileSerializer(read_only=True)
    reviewed_by = UserProfileSerializer(read_only=True)
    group_name  = serializers.SerializerMethodField()
    class Meta:
        model  = JoinRequest
        fields = ['id','group','group_name','user','status','message','reviewed_by','reviewed_at','created_at']
        read_only_fields = ['id','user','status','reviewed_by','reviewed_at','created_at']
    def get_group_name(self, obj): return obj.group.name

class GroupListSerializer(serializers.ModelSerializer):
    member_count       = serializers.ReadOnlyField()
    slots_remaining    = serializers.ReadOnlyField()
    leader_name        = serializers.SerializerMethodField()
    department_display = serializers.SerializerMethodField()
    class Meta:
        model  = Group
        fields = ['id','name','department','department_display','description','max_members','member_count','slots_remaining','status','is_locked','leader_name','created_at']
    def get_leader_name(self, obj):
        l = obj.get_leader(); return l.name if l else None
    def get_department_display(self, obj): return obj.get_department_display()

class GroupDetailSerializer(serializers.ModelSerializer):
    members            = GroupMemberSerializer(source='memberships', many=True, read_only=True)
    member_count       = serializers.ReadOnlyField()
    slots_remaining    = serializers.ReadOnlyField()
    created_by         = UserProfileSerializer(read_only=True)
    pending_requests   = serializers.SerializerMethodField()
    department_display = serializers.SerializerMethodField()
    class Meta:
        model  = Group
        fields = ['id','name','department','department_display','description','max_members','member_count','slots_remaining','status','is_locked','created_by','members','pending_requests','created_at','updated_at']
    def get_department_display(self, obj): return obj.get_department_display()
    def get_pending_requests(self, obj):
        req = self.context.get('request')
        if not req or not req.user.is_authenticated: return []
        u = req.user
        is_leader = obj.memberships.filter(user=u, role='leader').exists()
        if not (is_leader or u.is_admin): return []
        pending = obj.join_requests.filter(status='pending')
        return JoinRequestSerializer(pending, many=True).data

class GroupCreateSerializer(serializers.ModelSerializer):
    member_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=list, write_only=True)
    class Meta:
        model  = Group
        fields = ['id','name','department','description','max_members','member_ids']
        extra_kwargs = {'description':{'required':False},'department':{'required':True}}

    def validate_max_members(self, v):
        if v < 2:  raise serializers.ValidationError('Minimum 2.')
        if v > 20: raise serializers.ValidationError('Maximum 20.')
        return v

    def create(self, validated_data):
        from users.models import User as U
        ids   = validated_data.pop('member_ids', [])
        user  = self.context['request'].user
        group = Group.objects.create(created_by=user, **validated_data)
        GroupMember.objects.create(group=group, user=user, role='leader')
        for uid in ids:
            if uid == user.id: continue
            try:
                mu = U.objects.get(pk=uid)
                GroupMember.objects.get_or_create(group=group, user=mu, defaults={'role':'member'})
            except U.DoesNotExist: pass
        return group

class GroupUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Group
        fields = ['name','department','description','max_members']
        extra_kwargs = {'max_members':{'required':False},'department':{'required':False}}
    def validate_max_members(self, v):
        g = self.instance
        if g and v < g.member_count:
            raise serializers.ValidationError(f'Cannot set below current count ({g.member_count}).')
        return v

class RequestActionSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    def validate_request_id(self, v):
        try: jr = JoinRequest.objects.select_related('group','user').get(pk=v)
        except JoinRequest.DoesNotExist:
            raise serializers.ValidationError('Request not found.')
        if jr.status != 'pending':
            raise serializers.ValidationError(f'Already {jr.status}.')
        u = self.context['request'].user
        is_leader = GroupMember.objects.filter(group=jr.group, user=u, role='leader').exists()
        if not (is_leader or u.is_admin):
            raise serializers.ValidationError('Only leader or admin can act.')
        self.join_request = jr
        return v

class AddMemberSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    user_id  = serializers.IntegerField()
    role     = serializers.ChoiceField(choices=[('leader','Leader'),('member','Member')], default='member')
