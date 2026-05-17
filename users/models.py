from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random, string

def gen_otp():
    return ''.join(random.choices(string.digits, k=6))

class UserManager(BaseUserManager):
    def create_user(self, roll_number, name, email, password=None, **extra):
        if not roll_number: raise ValueError('Roll number required')
        if not email:       raise ValueError('Email required')
        extra.setdefault('role', 'student')
        user = self.model(roll_number=roll_number.upper().strip(), name=name, email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, roll_number, name, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'admin')
        extra.setdefault('is_verified', True)
        return self.create_user(roll_number, name, email, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    ROLES  = [('student','Student'), ('admin','Admin')]
    DEPTS  = [('SE','Software Engineering'), ('CS','Computer Science')]

    roll_number  = models.CharField(max_length=30, unique=True)
    name         = models.CharField(max_length=150)
    email        = models.EmailField(unique=True)
    role         = models.CharField(max_length=10, choices=ROLES, default='student')
    department   = models.CharField(max_length=2, choices=DEPTS, blank=True, default='')
    is_verified  = models.BooleanField(default=False)
    otp_code     = models.CharField(max_length=6, blank=True, default='')
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD  = 'roll_number'
    REQUIRED_FIELDS = ['name', 'email']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'{self.roll_number} — {self.name}'

    @property
    def is_admin(self):
        return self.role == 'admin'

    def generate_otp(self):
        self.otp_code = gen_otp()
        self.otp_created_at = timezone.now()
        self.save(update_fields=['otp_code','otp_created_at'])
        return self.otp_code

    def verify_otp(self, code):
        from django.conf import settings
        expiry = getattr(settings, 'EMAIL_VERIFICATION_EXPIRY_MINUTES', 10)
        if not self.otp_code or not self.otp_created_at: return False
        if self.otp_code != code.strip(): return False
        return (timezone.now() - self.otp_created_at).total_seconds() / 60 <= expiry

    def clear_otp(self):
        self.otp_code = ''
        self.otp_created_at = None
        self.save(update_fields=['otp_code','otp_created_at'])
