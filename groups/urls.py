from django.urls import path
from .views import (
    GroupListView, GroupCreateView, GroupDetailView,
    GroupUpdateView, GroupDeleteView,
    JoinRequestView, MyJoinRequestsView,
    AcceptRequestView, RejectRequestView,
    LockGroupView, UnlockGroupView,
    GroupMembersView, RemoveMemberView, AddMemberView,
    MyGroupsView,
)

urlpatterns = [
    path('',                        GroupListView.as_view()),
    path('create/',                 GroupCreateView.as_view()),
    path('<int:group_id>/',         GroupDetailView.as_view()),
    path('<int:group_id>/update/',  GroupUpdateView.as_view()),
    path('<int:group_id>/delete/',  GroupDeleteView.as_view()),
    path('<int:group_id>/members/', GroupMembersView.as_view()),
    path('join-request/',           JoinRequestView.as_view()),
    path('my-requests/',            MyJoinRequestsView.as_view()),
    path('accept-request/',         AcceptRequestView.as_view()),
    path('reject-request/',         RejectRequestView.as_view()),
    path('lock/',                   LockGroupView.as_view()),
    path('unlock/',                 UnlockGroupView.as_view()),
    path('remove-member/',          RemoveMemberView.as_view()),
    path('add-member/',             AddMemberView.as_view()),
    path('my-groups/',              MyGroupsView.as_view()),
]
