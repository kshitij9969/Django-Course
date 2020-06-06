from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTest(TestCase):
    """
    Test the public API for ingredients
    """

    def setUp(self) -> None:
        """
        Setup requirements for following tests in the
        PublicIngredientApiTest class
        :return: None
        """
        self.apiclient = APIClient()

    def test_login_required(self):
        """
        Test that login is required to access ingredients
        :return: None
        """
        res = self.apiclient.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):
    """
    Test the private API for ingredients
    """

    def setUp(self) -> None:
        """
        Setup requirements for following tests in the
        PrivateIngredientApiTest class
        :return: None
        """
        self.user = get_user_model().objects.create_user(
            email='test5@test5.com',
            password='testpass'
        )
        self.apiclient = APIClient()
        self.apiclient.force_authenticate(user=self.user)

    def test_retrieve_ingredients_list(self):
        """
        Test retrieving a list of ingredients
        :return: None
        """
        Ingredient.objects.create(
            user=self.user,
            name='Kale'
        )
        Ingredient.objects.create(
            user=self.user,
            name='Salt'
        )

        res = self.apiclient.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """
        Test only ingredients for authenticated user are returned
        :return: None
        """
        user_two = get_user_model().objects.create_user(
            email='kshitij@singh.com',
            password='testpass'
        )
        Ingredient.objects.create(
            user=user_two,
            name='Vinegar'
        )
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Turmeric'
        )
        res = self.apiclient.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """
        Test that the creation of ingredient was successful
        :return: None
        """
        payload = {
            'name': 'Ginger'
        }
        self.apiclient.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name'],
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """
        Test that the creation of ingredient with
        invalid data fails
        :return: None
        """
        payload = {
            'name': ''
        }
        res = self.apiclient.post(INGREDIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
