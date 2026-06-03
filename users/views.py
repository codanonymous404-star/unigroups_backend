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


# ── Admin: single + bulk user creation ───────────────────────────────────────
import csv, io
from .serializers import AdminCreateUserSerializer

class AdminCreateUserView(APIView):
    """POST /api/auth/admin/users/create/  — create one user"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        s = AdminCreateUserSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        user = s.save()
        pwd_provided = bool(request.data.get('password', '').strip())
        return Response({
            'success': True,
            'message': f'User {user.roll_number} created.',
            'user': UserProfileSerializer(user).data,
            'auto_password': f"{user.roll_number}@123" if not pwd_provided else None,
        }, status=201)


class AdminBulkCreateView(APIView):
    """
    POST /api/auth/admin/users/bulk-create/
    Accepts either:
      - JSON body: { "users": [ {roll_number, name, email, department?, role?}, ... ] }
      - CSV file:  multipart form-data field 'file' with columns:
                   roll_number, name, email, department (optional), role (optional)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        # ── CSV upload ───────────────────────────────────────────────────────
        if 'file' in request.FILES:
            f       = request.FILES['file']
            text    = f.read().decode('utf-8-sig')        # strips BOM if present
            reader  = csv.DictReader(io.StringIO(text))
            rows    = [dict(r) for r in reader]
        else:
            rows = request.data.get('users', [])

        if not rows:
            return Response({'success': False, 'message': 'No user data provided.'}, status=400)

        created, failed = [], []

        for idx, row in enumerate(rows):
            # strip whitespace from every field
            clean = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            s = AdminCreateUserSerializer(data=clean)
            if s.is_valid():
                user = s.save()
                created.append({
                    'roll_number':   user.roll_number,
                    'name':          user.name,
                    'auto_password': f"{user.roll_number}@123" if not clean.get('password') else None,
                })
            else:
                failed.append({'row': idx + 1, 'data': clean, 'errors': s.errors})

        return Response({
            'success':       True,
            'total':         len(rows),
            'created_count': len(created),
            'failed_count':  len(failed),
            'created':       created,
            'failed':        failed,
        }, status=207 if failed else 201)


class AdminResetPasswordView(APIView):
    """
    POST /api/auth/admin/users/reset-password/
    Body: { "roll_number": "SU72-BSSEM-F25-001" }  → resets to ROLL@123
    Or:   { "reset_all_csv": true }                 → resets ALL unverified/csv users
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        reset_all = request.data.get('reset_all_csv', False)

        if reset_all:
            # Reset password for all users where password might be broken
            users = User.objects.all()
            fixed = []
            for u in users:
                new_pwd = f"{u.roll_number}@123"
                u.set_password(new_pwd)
                u.is_verified = True
                u.is_active   = True
                u.save(update_fields=['password', 'is_verified', 'is_active'])
                fixed.append(u.roll_number)
            return Response({
                'success': True,
                'message': f'Reset {len(fixed)} users to ROLL@123',
                'users': fixed
            })

        rn = request.data.get('roll_number', '').upper().strip()
        if not rn:
            return Response({'success': False, 'message': 'roll_number required'}, status=400)
        try:
            u = User.objects.get(roll_number=rn)
            new_pwd = f"{rn}@123"
            u.set_password(new_pwd)
            u.is_verified = True
            u.is_active   = True
            u.save(update_fields=['password', 'is_verified', 'is_active'])
            return Response({
                'success': True,
                'message': f'{rn} password reset.',
                'new_password': new_pwd
            })
        except User.DoesNotExist:
            return Response({'success': False, 'message': 'User not found'}, status=404)


class AdminDeleteAllUsersView(APIView):
    """
    DELETE /api/auth/admin/users/delete-all/
    Deletes all non-admin users. Admin accounts safe rehte hain.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        deleted_qs = User.objects.filter(role='student')
        count = deleted_qs.count()
        deleted_qs.delete()
        return Response({
            'success': True,
            'message': f'Deleted {count} student users. Admin accounts untouched.',
            'deleted_count': count
        })


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')
        confirm      = request.data.get('confirm_password', '')

        if not old_password or not new_password or not confirm:
            return Response({'success': False, 'message': 'All fields required.'}, status=400)

        if not request.user.check_password(old_password):
            return Response({'success': False, 'message': 'Current password is incorrect.'}, status=400)

        if new_password != confirm:
            return Response({'success': False, 'message': 'New passwords do not match.'}, status=400)

        if len(new_password) < 8:
            return Response({'success': False, 'message': 'Password must be at least 8 characters.'}, status=400)

        request.user.set_password(new_password)
        request.user.save(update_fields=['password'])
        return Response({'success': True, 'message': 'Password changed successfully.'})
