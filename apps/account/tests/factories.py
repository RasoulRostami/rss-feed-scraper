from django.contrib.auth import get_user_model
from factory import django, Faker, PostGenerationMethodCall

User = get_user_model()


class UserFactory(django.DjangoModelFactory):
    username = Faker('user_name')
    email = Faker('email')
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    password = PostGenerationMethodCall('set_password', '1sdf54sf')

    class Meta:
        model = User
