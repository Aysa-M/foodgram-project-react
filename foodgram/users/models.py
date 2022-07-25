from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, EmailField


class User(AbstractUser):
    """
    User custom model.
    """
    USER = 'user'
    ADMIN = 'admin'
    ROLE_CHOICES = (
        (USER, USER),
        (ADMIN, ADMIN),
    )
    username = CharField(
        verbose_name='Логин',
        unique=True,
        max_length=150,
        help_text='Не более 150 символов: буквы, цифры и @/./+/-/_.',
        error_messages={
            'unique': 'Пользователь с таким логин уже существует.',
        }
    )
    password = CharField(
        verbose_name='Пароль',
        max_length=150,
    )
    email = EmailField(
        verbose_name='Адрес электронной почты email',
        unique=True,
        max_length=254,
        error_messages={
            'unique': 'Указанный email уже зарегистрирован.',
        }
    )
    first_name = CharField(
        verbose_name='Имя',
        max_length=150
    )
    last_name = CharField(
        verbose_name='Фамилия',
        max_length=150
    )
    role = CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=USER,
        verbose_name='Уровень доступа'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    @property
    def is_user(self):
        """Authenticated users."""
        return self.role == self.USER

    @property
    def is_admin(self):
        """Administrator user."""
        return self.role == self.ADMIN or self.is_superuser

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        db_table = 'pair'
        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_pair',
            ),
        ]

    def __str__(self) -> str:
        return self.username


class Subscription(models.Model):
    """
    Creates a subscription.
    """
    user = models.ForeignKey(
        User,
        verbose_name='подписчик',
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='подписка',
        on_delete=models.CASCADE,
        related_name='following',
        error_messages={
            'unique': 'Вы уже подписаны на данного автора.',
        }
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        db_table = 'subscription'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_subscription'),
            models.CheckConstraint(
                name='do_not_subscribe_again',
                check=~models.Q(author=models.F('author')),
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} оформил подписку на {self.author}'
