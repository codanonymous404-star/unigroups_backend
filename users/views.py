from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer, AdminUpdateUserSerializer, VerifyOTPSerializer
from .permissions import IsAdminUser
from .email_utils import send_verification_email, send_welcome_email


class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        user = s.save()
        otp  = user.generate_otp()
        sent = send_verification_email(user, otp)
        return Response({
            'success': True,
            'message': f'Account created. Code sent to {user.email}',
            'roll_number': user.roll_number,
            'email_sent': sent,
            'dev_otp': otp if not sent else None,
        }, status=201)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        user = s.user
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        user.clear_otp()
        send_welcome_email(user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'message': f'Verified! Welcome {user.name}.',
            'user': UserProfileSerializer(user).data,
            'access_token':  str(refresh.access_token),
            'refresh_token': str(refresh),
        })


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        rn = request.data.get('roll_number', '').upper().strip()
        try:
            user = User.objects.get(roll_number=rn)
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'Roll number not found.'}, status=404)
        if user.is_verified:
            return Response({'success': False, 'message': 'Already verified.'}, status=400)
        otp  = user.generate_otp()
        sent = send_verification_email(user, otp)
        return Response({'success': True, 'message': f'Code sent to {user.email}', 'email_sent': sent, 'dev_otp': otp if not sent else None})


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        s = LoginSerializer(data=request.data, context={'request': request})
        if not s.is_valid():
            errs = s.errors
            non  = errs.get('non_field_errors', [])
            unverified = any('not verified' in str(e).lower() or getattr(e,'code','') == 'email_not_verified' for e in non)
            # Also handle nested dict error
            for e in non:
                if isinstance(e, dict) and e.get('code') == 'email_not_verified':
                    unverified = True
            return Response({'success': False, 'errors': errs, 'unverified': unverified}, status=400)
        d = s.validated_data
        return Response({
            'success': True,
            'user': UserProfileSerializer(d['user']).data,
            'access_token':  d['access_token'],
            'refresh_token': d['refresh_token'],
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        ref = request.data.get('refresh_token')
        if not ref:
            return Response({'success': False, 'message': 'Refresh token required.'}, status=400)
        try:
            RefreshToken(ref).blacklist()
            return Response({'success': True, 'message': 'Logged out.'})
        except TokenError:
            return Response({'success': False, 'message': 'Invalid token.'}, status=400)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({'success': True, 'user': UserProfileSerializer(request.user).data})
    def patch(self, request):
        user = request.user
        name = request.data.get('name')
        if name:
            user.name = name
            user.save(update_fields=['name'])
        return Response({'success': True, 'user': UserProfileSerializer(user).data})


class ClassmatesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        if not user.department:
            return Response({'success': False, 'message': 'No department assigned.', 'classmates': []})
        mates = User.objects.filter(department=user.department, role='student', is_active=True).exclude(pk=user.pk)
        return Response({'success': True, 'department': user.department, 'department_display': user.get_department_display(), 'count': mates.count(), 'classmates': UserProfileSerializer(mates, many=True).data})


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        users = User.objects.all()
        dept = request.query_params.get('dept')
        role = request.query_params.get('role')
        if dept: users = users.filter(department=dept)
        if role: users = users.filter(role=role)
        return Response({'success': True, 'count': users.count(), 'users': UserProfileSerializer(users, many=True).data})


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get_obj(self, uid):
        try: return User.objects.get(pk=uid)
        except: return None

    def get(self, request, user_id):
        u = self.get_obj(user_id)
        if not u: return Response({'success': False, 'message': 'Not found.'}, status=404)
        return Response({'success': True, 'user': UserProfileSerializer(u).data})

    def patch(self, request, user_id):
        u = self.get_obj(user_id)
        if not u: return Response({'success': False, 'message': 'Not found.'}, status=404)
        if u == request.user and request.data.get('role') == 'student':
            return Response({'success': False, 'message': 'Cannot remove your own admin role.'}, status=400)
        s = AdminUpdateUserSerializer(u, data=request.data, partial=True)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        s.save()
        return Response({'success': True, 'user': UserProfileSerializer(u).data})

    def delete(self, request, user_id):
        u = self.get_obj(user_id)
        if not u: return Response({'success': False, 'message': 'Not found.'}, status=404)
        if u == request.user: return Response({'success': False, 'message': 'Cannot delete yourself.'}, status=400)
        u.delete()
        return Response({'success': True, 'message': f'{u.name} deleted.'})
