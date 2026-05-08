from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError("Поле Email обязательно для идентификации пользователя")
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return self.create_user(email, password, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь системы"""

    email = models.EmailField(max_length=255, unique=True)
    surname = models.CharField(max_length=32)
    name = models.CharField(max_length=32)
    patronymic = models.CharField(max_length=32)
    position = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    # Бизнес-роли пользователя
    roles = models.ManyToManyField(
        "Role",
        through="UserRole",
        related_name="users",
        blank=True,
    )

    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        db_table = "users_user"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        """Формирует полное имя сотрудника"""
        return " ".join([self.surname, self.name, self.patronymic])

    def has_role(self, role_name: str) -> bool:
        """Проверяет наличие бизнес-роли у пользователя"""
        return self.roles.filter(name=role_name).exists()


class Role(models.Model):
    """Бизнес-роль в системе"""

    ADMINISTRATOR = "Администратор"
    SIGNER = "Подписант"
    EMPLOYEE = "Сотрудник"

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "users_role"
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """Связочная таблица User - Role"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = "users_user_role"
        verbose_name = "Соответствие Пользователь-Роль"
        verbose_name_plural = "Соответствия Пользователь-Роль"
        unique_together = [("user", "role")]


class PublicKey(models.Model):
    """Публичный ключ пользователя для верификации ЭЦП"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="public_keys")
    public_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_public_key"
        verbose_name = "Публичный ключ"
        verbose_name_plural = "Публичные ключи"

    def __str__(self):
        return f"Key #{self.pk} — {self.user.email}"
