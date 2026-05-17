from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
User = get_user_model()

class RollNumberBackend(ModelBackend):
    def authenticate(self, request, roll_number=None, password=None, **kwargs):
        if not roll_number or not password: return None
        try:
            user = User.objects.get(roll_number=roll_number.upper().strip())
        except User.DoesNotExist:
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try: return User.objects.get(pk=user_id)
        except User.DoesNotExist: return None
