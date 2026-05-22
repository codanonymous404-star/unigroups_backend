import re
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

ROLL_RE = re.compile(r'^SU\d{2}-[A-Z]{2,6}-[A-Z]\d{2}-\d{3,4}$', re.IGNORECASE)

def validate_roll(value):
    if not ROLL_RE.match(value.upper().strip()):
        raise serializers.ValidationError('Invalid format. Example: SU72-BSSEM-F25-017')
    return value.upper().strip()

class RegisterSerializer(serializers.ModelSerializer):
    roll_number = serializers.CharField(validators=[validate_roll])
    password    = serializers.CharField(write_only=True, validators=[validate_password])
    password2   = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['roll_number','name','email','password','password2','department']
        extra_kwargs = {'department': {'required': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def validate_email(self, v):
        if User.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError('Email already registered.')
        return v.lower().strip()

    def validate_roll_number(self, v):
        if User.objects.filter(roll_number__iexact=v).exists():
            raise serializers.ValidationError('Roll number already registered.')
        return v.upper().strip()

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data['is_verified'] = False
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    roll_number = serializers.CharField()
    password    = serializers.CharField(write_only=True)

    def validate(self, attrs):
        rn   = attrs.get('roll_number','').upper().strip()
        pwd  = attrs.get('password')
        user = authenticate(request=self.context.get('request'), roll_number=rn, password=pwd)
        if not user:
            raise serializers.ValidationError('Invalid roll number or password.')
        if not user.is_active:
            raise serializers.ValidationError('Account deactivated.')
        if not user.is_verified and not user.is_admin:
            raise serializers.ValidationError({'detail':'Email not verified.','code':'email_not_verified'})
        refresh = RefreshToken.for_user(user)
        return {'user': user, 'access_token': str(refresh.access_token), 'refresh_token': str(refresh)}

class UserProfileSerializer(serializers.ModelSerializer):
    department_display = serializers.SerializerMethodField()
    class Meta:
        model  = User
        fields = ['id','roll_number','name','email','role','department','department_display','is_verified','created_at']
        read_only_fields = fields
    def get_department_display(self, obj):
        return obj.get_department_display() if obj.department else 'Not Set'

class AdminUpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['name','department','role','is_verified']
        extra_kwargs = {f:{'required':False} for f in ['name','department','role','is_verified']}

class VerifyOTPSerializer(serializers.Serializer):
    roll_number = serializers.CharField()
    otp_code    = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        rn  = attrs.get('roll_number','').upper().strip()
        otp = attrs.get('otp_code','').strip()
        try:
            user = User.objects.get(roll_number=rn)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid roll number.')
        if user.is_verified:
            raise serializers.ValidationError('Already verified.')
        if not user.verify_otp(otp):
            raise serializers.ValidationError('Invalid or expired code. Request a new one.')
        self.user = user
        return attrs
