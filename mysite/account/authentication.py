from django.contrib.auth import get_user_model
from account.models import Profile

class EmailAuthBackend:
    """Аутентифицировать посредством адреса электронной почты."""
    def authenticate(self, request, username=None, password=None):
        try:
            user = get_user_model().objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except get_user_model().DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except get_user_model().DoesNotExist:
            return None


def create_profile(backend, user, *args, **kwargs):
    # Создать профиль пользователя для социальной аутентификации
    Profile.objects.get_or_create(user=user)