from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTest(TestCase):

    def setUp(self) -> None:
        """
        Setup super user and user and login as super user
        for rest of the test cases.
        :return: None
        """
        self.client = Client()
        self.admin_user = get_user_model().objects.create_super_user(
            email='admin@test.com',
            password='password123',
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@test.com',
            password='password1234',
            name='test user full name',
        )

    def test_user_listed(self):
        """
        Test if the custom users are listed in the admin page.
        :return: None
        """
        url = reverse('admin:core_user_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """
        Test that the user edit page works.
        :return: None
        """
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """
        Test the create user page works.
        :return: None
        """
        url = reverse('admin:core_user_add')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
