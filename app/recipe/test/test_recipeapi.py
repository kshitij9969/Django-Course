from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """
    Return recipe detail url
    :param recipe_id: recipe object id
    :return: url for recipe detail
    """
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """
    Create and return a sample tag
    :param user: User(custom) object
    :param name: name of the tag
    :return: Tag object
    """
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """
    Create and return a sample ingredient
    :param user: User(custom) object
    :param name: name of the ingredient
    :return: Ingredient object
    """
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """
    Create and return a sample recipe
    :param user: user object
    :param params: other parameter for recipe
    :return: Recipe object
    """
    defaults = {
        'title': 'default title',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTest(TestCase):
    """
    Test unauthenticated recipe API access
    """

    def setUp(self) -> None:
        self.apiclient = APIClient()

    def test_auth_required(self):
        """
        Test that the authentication is required for fetching recipes
        :return: None
        """
        res = self.apiclient.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTest(TestCase):
    """
    Test unauthenticated recipe API access
    """

    def setUp(self) -> None:
        self.apiclient = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='testpass'
        )
        self.apiclient.force_authenticate(user=self.user)

    def test_retrieve_recipe(self):
        """
        Test retrieving a list of recipes
        :return: None
        """
        sample_recipe(self.user)
        sample_recipe(self.user)

        res = self.apiclient.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        """
        Test retrieving recipes for user
        :return: None
        """
        user_two = get_user_model().objects.create_user(
            'test1@test1.com',
            'password1'
        )
        sample_recipe(user_two)
        sample_recipe(self.user)

        res = self.apiclient.get(RECIPE_URL)

        recipe = Recipe.objects.all().filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """
        Test viewing a recipe detail
        :return: None
        """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe_id=recipe.id)

        res = self.apiclient.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)
