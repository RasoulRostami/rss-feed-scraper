import json

from cerberus import Validator
from django.contrib.auth import get_user_model
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import UserFactory
from .schemas import sign_up_response_schema, user_info_schema

User = get_user_model()
fake = Faker()


# TODO check retrive and update schema
class SignUpTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/account/users/sign-up/'
        cls.password = fake.password()

    def test_sing_up(self):
        data = {'username': fake.user_name(), 'password': self.password, 'confirm_password': self.password}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        schema_validator = Validator(sign_up_response_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)
        user = User.objects.get(username=data['username'])
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        self.assertEqual(user.email, '')

    def test_user_info_after_sign_up(self):
        data = {
            'username': fake.user_name(),
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'password': self.password,
            'confirm_password': self.password,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username=data['username'])
        del data['password']
        del data['confirm_password']
        for key, value in data.items():
            self.assertTrue(getattr(user, key), value)

    def test_username_is_required(self):
        password = fake.password()
        response = self.client.post(
            path=self.url, data={'email': fake.email(), 'password': password, 'confirm_password': password}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unique_email(self):
        old_user = UserFactory()
        data = {
            'username': fake.user_name(), 'email': old_user.email, 'password': self.password, 'confirm_password': self.password
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unique_username(self):
        old_user = UserFactory()
        data = {'username': old_user.username, 'password': self.password, 'confirm_password': self.password}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_password(self):
        data = {'username': fake.user_name(), 'password': self.password, 'confirm_password': 'self_password_132'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_is_required(self):
        data = {'username': fake.user_name(), 'confirm_password': self.password}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_password_is_required(self):
        data = {'username': fake.user_name(), 'password': self.password}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_simple_password(self):
        data = {'username': fake.user_name(), 'password': 123, 'confirm_password': 132}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateUserInfoTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/account/users/update-user-info/'
        cls.user = UserFactory()

    def test_is_authenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_first_name_last_name(self):
        data = {'first_name': fake.first_name(), 'last_name': fake.last_name()}
        self.client.force_login(self.user)
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, data['first_name'])
        self.assertEqual(self.user.last_name, data['last_name'])
        schema_validator = Validator(user_info_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)

    def test_update_email(self):
        data = {'email': fake.email()}
        self.client.force_login(self.user)
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, data['email'])

    def test_update_password(self):
        password = fake.password()
        data = {'password': password, 'confirm_password': password}
        self.client.force_login(self.user)
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirm_password(self):
        password = fake.password()
        data = {'password': password}
        self.client.force_login(self.user)
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserInfoTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = '/api/v1/account/users/user-info/'
        cls.user = UserFactory()

    def test_is_authenticated(self):
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_first_name_last_name(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema_validator = Validator(user_info_schema)
        self.assertTrue(schema_validator.validate(json.loads(response.content)), msg=schema_validator.errors)
