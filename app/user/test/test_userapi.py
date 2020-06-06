from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """
    Helper function for creating user
    :param params: parameters(payload) for creating user
    :return: user object
    """
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """
    Test the users API public.
    """
    def setUp(self) -> None:
        """
        Setting up parameters which will be used in following tests.
        :return: None
        """
        self.apiclient = APIClient()

    def test_create_valid_user_success(self):
        """
        Test creating user with valid payload is successful.
        :return: None
        """
        # payload to create the user.
        payload = {
            'email': 'test@test.com',
            'password': 'pass123',
            'name': 'user',
        }
        # make a post call
        res = self.apiclient.post(CREATE_USER_URL, payload)
        # check if 201 user created
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # check in the database if the user is created
        user = get_user_model().objects.get(**res.data)
        # check if the password is correct
        self.assertTrue(user.check_password(payload['password']))
        # check if the password field is not included in response(for security)
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """
        Test creating a use that already exists.
        :return: None
        """
        # payload to create the user
        payload = {
            'email': 'test@test.com',
            'password': 'pass123',
            'name': 'user'
        }
        # create a user
        create_user(**payload)
        # try to create a duplicate user
        res = self.apiclient.post(CREATE_USER_URL, payload)

        # check if we get an expected response
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_restriction(self):
        """
        Test if the password is of appropriate length(more than 5 characters).
        :return: None
        """
        payload = {
            'email': 'test@test.com',
            'password': 'pw',
            'name': 'user',
        }
        res = self.apiclient.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """
        Test that a token is created for the user
        :return: None
        """
        payload = {
            'email': 'test@test.com',
            'password': 'testpass',
            'name': 'user'
        }
        create_user(**payload)
        res = self.apiclient.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """
        Test that token is not created if invalid credentials are given.
        :return: None
        """
        create_user(
            email='test@test.com',
            password='password123',
            name='user'
        )
        payload = {
            'email': 'test@test.com',
            'password': 123445,
            'name': 'user'
        }
        res = self.apiclient.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """
        Test that token is not created if user doesn't exist
        :return: None
        """
        payload = {
            'email': 'test@test.com',
            'password': 'password',
            'name': 'user'
        }
        res = self.apiclient.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """
         Test that email and password are required
        :return: None
        """
        res = self.apiclient.post(TOKEN_URL, {'email': 'one', 'password': ''})

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """
        Test that authentication is required for users
        :return: None
        """
        res = self.apiclient.post(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """
    Test user private API(requires authentication)
    """
    def setUp(self) -> None:
        """
        Setup required attributes for rest of the tests
        :return: None
        """
        self.user = create_user(
            email='test@test.com',
            password='testpass',
            name='user'
        )
        self.apiclient = APIClient()
        self.apiclient.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """
        Test retrieving profile for logged in user
        :return: None
        """
        res = self.apiclient.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        """
        Test that post is not allowed on the me url
        :return: None
        """
        res = self.apiclient.post(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """
        Test updating user profile for authenticated user
        :return: None
        """
        payload = {
            'email': 'newemail@test.com',
            'password': 'newpassword',
            'name': 'newname'
        }
        res = self.apiclient.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertEqual(self.user.email, payload['email'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
