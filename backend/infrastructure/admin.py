from apps.users.models import User


def register_admin(email: str, name: str, surname: str, password: str) -> str:
    if email and not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            email=email,
            password=password,
            name=name,
            surname=surname
        )
        return f"Superuser {email} created"
    return "Some error was occurred during superuser creation. Please create superuser on your own"
