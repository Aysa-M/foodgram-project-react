from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Custom Sign up form for the newcomers.
    """

    class Meta:
        """Set the fields for the sign up form."""
        model = User
        fields = ('first_name', 'username', 'last_name', 'email', 'password')


class CustomUserChangeForm(UserChangeForm):
    """
    Custom change password form for authorized users.
    """

    class Meta:
        """Set the fields for the change password form."""
        model = User
        fields = ('username', 'email', 'password')
