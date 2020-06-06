from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


class PublicTagApiTest(TestCase):
    """
    Test publicly available tags API
    """

    def setUp(self) -> None:
        """
        Setup requirements for the following tests in the
        PublicTagApiTest class
        :return: None
        """
        self.apiclient = APIClient()

    def test_login_required(self):
        """
        Test that login is required for retrieving tags
        :return: None
        """
        res = self.apiclient.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTest(TestCase):
    """
    Test the tag API requiring authentication
    """

    def setUp(self) -> None:
        """
        Setup requirements for the following tests in the
        PrivateTagApiTest class
        :return: None
        """
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='password'
        )
        self.apiclient = APIClient()
        self.apiclient.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """
        Test retrieving tags
        :return: None
        """
        Tag.objects.create(
            user=self.user,
            name='Vegan'
        )
        Tag.objects.create(
            user=self.user,
            name='Dessert'
        )

        res = self.apiclient.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """
        Test that tags are returned only for the authenticated user
        :return: None
        """
        user_two = get_user_model().objects.create_user(
            email='test1@test1.com',
            password='password1',
        )
        Tag.objects.create(
            user=user_two,
            name='Fruity'
        )
        tag = Tag.objects.create(
            user=self.user,
            name='Comfort food'
        )

        res = self.apiclient.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """
        Test creating a new tag
        :return: None
        """
        payload = {
            'name': 'test tag'
        }
        self.apiclient.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """
        Test creating a new tag with an invalid payload
        :return: None
        """
        payload = {'name': ''}
        res = self.apiclient.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
