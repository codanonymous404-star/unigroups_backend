from .models import Notification

def notify(user, type, title, message, data=None):
    """Create a notification for a user."""
    Notification.objects.create(
        user=user, type=type, title=title,
        message=message, data=data or {}
    )

def notify_join_request(group, requester):
    """Notify group leader when someone requests to join."""
    leader = group.get_leader()
    if leader:
        notify(
            user=leader, type='join_request',
            title=f'New join request — {group.name}',
            message=f'{requester.name} ({requester.roll_number}) wants to join your group.',
            data={'group_id': group.id, 'group_name': group.name, 'requester_id': requester.id}
        )

def notify_request_accepted(join_request):
    notify(
        user=join_request.user, type='request_accepted',
        title=f'Request accepted — {join_request.group.name}',
        message=f'You have been accepted into "{join_request.group.name}".',
        data={'group_id': join_request.group.id, 'group_name': join_request.group.name}
    )

def notify_request_rejected(join_request):
    notify(
        user=join_request.user, type='request_rejected',
        title=f'Request rejected — {join_request.group.name}',
        message=f'Your request to join "{join_request.group.name}" was not accepted.',
        data={'group_id': join_request.group.id, 'group_name': join_request.group.name}
    )

def notify_member_removed(group, removed_user):
    notify(
        user=removed_user, type='member_removed',
        title=f'Removed from group — {group.name}',
        message=f'You have been removed from "{group.name}".',
        data={'group_id': group.id, 'group_name': group.name}
    )

def notify_member_added(group, added_user):
    notify(
        user=added_user, type='member_added',
        title=f'Added to group — {group.name}',
        message=f'You have been added to "{group.name}" by an admin.',
        data={'group_id': group.id, 'group_name': group.name}
    )

def notify_group_locked(group):
    """Notify all members when group is locked."""
    for membership in group.memberships.select_related('user').all():
        notify(
            user=membership.user, type='group_locked',
            title=f'Group locked — {group.name}',
            message=f'"{group.name}" has been locked. No new members can join.',
            data={'group_id': group.id, 'group_name': group.name}
        )

def notify_group_unlocked(group):
    """Notify all members when group is unlocked."""
    for membership in group.memberships.select_related('user').all():
        notify(
            user=membership.user, type='group_unlocked',
            title=f'Group unlocked — {group.name}',
            message=f'"{group.name}" is now open for new members.',
            data={'group_id': group.id, 'group_name': group.name}
        )
