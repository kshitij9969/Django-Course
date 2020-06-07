from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

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
            email='test6@test6.com',
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

    def test_retrieve_tags_assigned_to_recipe(self):
        """
        Test filtering tags that are assigned to recipes
        :return: None
        """
        tag_one = Tag.objects.create(
            user=self.user,
            name='breakfast'
        )
        tag_two = Tag.objects.create(
            user=self.user,
            name='lunch'
        )
        recipe_one = Recipe.objects.create(
            user=self.user,
            title='title',
            time_minutes=10,
            price=10,
        )
        recipe_one.tags.add(tag_one)

        res = self.apiclient.get(TAGS_URL, {'assigned_only': 1})

        serializer_one = TagSerializer(tag_one)
        serializer_two = TagSerializer(tag_two)

        self.assertIn(serializer_one.data, res.data)
        self.assertNotIn(serializer_two.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """
        Test filtering tags by assigned returns unique items
        :return: None
        """
        tag = Tag.objects.create(
            user=self.user,
            name='breakfast'
        )
        Tag.objects.create(
            user=self.user,
            name='Lunch'
        )
        recipe_one = Recipe.objects.create(
            title='title',
            price=3.00,
            time_minutes=10,
            user=self.user
        )
        recipe_two = Recipe.objects.create(
            title='title1',
            price=5.00,
            time_minutes=10,
            user=self.user
        )
        recipe_one.tags.add(tag)
        recipe_two.tags.add(tag)

        res = self.apiclient.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
