from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def sample_user(email='test@test.com', password='testpass'):
    """
    Create a sample user
    :param email: email of the user
    :param password: password of the user
    :return: user object
    """
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class ModelTest(TestCase):

    def test_create_user_with_email_successful(self):
        """
        Test creating a new user with email is successful
        :return: None
        """
        email = 'test@test.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password), password)

    def test_new_user_email_normalized(self):
        """
        Test the email for a new user is normalized
        :return: None
        """
        email = 'test@TEST.COM'
        user = get_user_model().objects.create_user(
            email=email,
            password='random'
        )

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """
        Test creating user with no email raises error
        :return: None
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email=None,
                password='random'
            )

    def test_create_new_super_user(self):
        """
        Test creating super user
        :return: None
        """
        user = get_user_model().objects.create_superuser(
            email='test@test.com',
            password='password123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """
        Test the string tag representation
        :return: None
        """
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)
