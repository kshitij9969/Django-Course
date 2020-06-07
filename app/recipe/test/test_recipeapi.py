# import tempfile
# import os
#
# from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
# from django.db import transaction

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """
    Return a image url
    :param recipe_id: recipe object id
    :return: url for image upload
    """
    print(reverse('recipe:recipe-upload-image', args=[recipe_id]))
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_basic_recipe(self):
        """
        Test creating a recipe
        :return: None
        """
        payload = {
            'title': 'Recipe title',
            'time_minutes': 10,
            'price': 5.00
        }

        res = self.apiclient.post(RECIPE_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tag(self):
        """
        Test creating a recipe with tags assigned
        :return: None
        """
        tag_one = sample_tag(self.user, name='Vegan')
        tag_two = sample_tag(self.user, name='Dessert')
        payload = {
            'title': 'New titile',
            'time_minutes': 20,
            'price': 10.00,
            'tags': [tag_one.id, tag_two.id]
        }

        res = self.apiclient.post(RECIPE_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag_one, tags)
        self.assertIn(tag_two, tags)

    def test_create_recipe_with_ingredients(self):
        """
        Test creating a recipe with ingredient assigned
        :return: None
        """
        ingredient_one = sample_ingredient(self.user, 'Ginger')
        ingredient_two = sample_ingredient(self.user, 'Chocolate')
        payload = {
            'title': 'New title',
            'time_minutes': 20,
            'price': 10.00,
            'ingredients': [ingredient_one.id, ingredient_two.id]
        }

        res = self.apiclient.post(RECIPE_URL, payload)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient_one, ingredients)
        self.assertIn(ingredient_two, ingredients)

    def test_partial_update_recipe(self):
        """
        Test updating a recipe partially with patch
        :return: None
        """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        new_tag = sample_tag(user=self.user, name='Curry')
        payload = {
            'title': 'Chicken tikka',
            'tags': [new_tag.id]
        }

        url = detail_url(recipe.id)
        self.apiclient.patch(url, payload)

        recipe = Recipe.objects.get(id=recipe.id)
        recipe.refresh_from_db()
        tags = recipe.tags.all()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """
        Test full update of a recipe with put
        :return: None
        """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Spaghetti carbonara',
            'time_minutes': 25,
            'price': 10.00
        }
        url = detail_url(recipe.id)

        self.apiclient.put(url, payload)

        recipe.refresh_from_db()
        tags = recipe.tags.all()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(len(tags), 0)


class RecipeImageUploadImageTest(TestCase):
    """
    Test the image upload to recipe model
    """

    def setUp(self) -> None:
        """
        Setup requirements for following tests
        in the RecipeImageUploadImageTest class
        :return: None
        """
        self.apiclient = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@test.com',
            password='testpass'
        )
        self.apiclient.force_authenticate(user=self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self) -> None:
        """
        Runs after the tests are completed
        (Removes redundant image files created during tests)
        :return: None
        """
        self.recipe.image.delete()

    # def test_upload_image_to_recipe(self):
    #     """Test uploading an image to recipe"""
    #     url = image_upload_url(self.recipe.id)
    #     with tempfile.NamedTemporaryFile(suffix='.png') as ntf:
    #         img = Image.new('RGB', (10, 10))
    #         img.save(ntf, format='PNG')
    #         ntf.seek(0)
    #         res = self.apiclient.post(url, {'image': ntf},
    #         format='multipart')
    #     #
    #     # self.recipe.refresh_from_db()
    #     self.assertEqual(res.status_code, status.HTTP_200_OK)
    #     self.assertIn('image', res.data)
    #     self.assertTrue(os.path.exists(self.recipe.image.path))

    # def test_upload_invalid_image_to_recipe(self):
    #     """
    #     Test uploading an invalid image to recipe
    #     :return: None
    #     """
    #     url = image_upload_url(self.recipe.id)
    #     res = self.apiclient.post(url, {'image': 'invalid image'},
    #     format='multipart')
    #
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        """
        Test returning recipes with specific tags
        :return: None
        """
        recipe_one = sample_recipe(user=self.user,
                                   title='Thai vegetable curry')
        recipe_two = sample_recipe(user=self.user,
                                   title='Aubergine with tahini')
        tag_one = sample_tag(user=self.user, name='Vegan')
        tag_two = sample_tag(user=self.user, name='Vegetarian')
        recipe_one.tags.add(tag_one)
        recipe_two.tags.add(tag_two)
        recipe_three = sample_recipe(user=self.user, title='Fish and chips')

        res = self.apiclient.get(
            RECIPE_URL,
            {'tags': f'{tag_one.id},{tag_two.id}'}
        )

        serialzer_one = RecipeSerializer(recipe_one)
        serialzer_two = RecipeSerializer(recipe_two)
        serialzer_three = RecipeSerializer(recipe_three)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serialzer_one.data, res.data)
        self.assertIn(serialzer_two.data, res.data)
        self.assertNotIn(serialzer_three.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """
        Test returning recipes with specific ingredients
        :return: None
        """
        recipe_one = sample_recipe(user=self.user,
                                   title='Posh bean on toast')
        recipe_two = sample_recipe(user=self.user,
                                   title='Chicken cacciatore')
        ingredient_one = sample_ingredient(user=self.user,
                                           name='Feta cheese')
        ingredient_two = sample_ingredient(user=self.user,
                                           name='chicken')
        recipe_one.ingredients.add(ingredient_one)
        recipe_two.ingredients.add(ingredient_two)
        recipe_three = sample_recipe(user=self.user,
                                     title='Steak and mushroom')

        res = self.apiclient.get(
            RECIPE_URL,
            {'ingredients': f'{ingredient_one.id},{ingredient_two.id}'}
        )

        serializer_one = RecipeSerializer(recipe_one)
        serializer_two = RecipeSerializer(recipe_two)
        serializer_three = RecipeSerializer(recipe_three)
        self.assertIn(serializer_one.data, res.data)
        self.assertIn(serializer_two.data, res.data)
        self.assertNotIn(serializer_three.data, res.data)
