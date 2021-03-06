import uuid
import os

from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.conf import settings


def recipe_image_file_path(instance, original_file_name):
    """
    Generate new file path of recipe image
    :param instance: recipe instance
    :param original_file_name: original file
           name of the file uploaded
    :return: new file path
    """
    ext = original_file_name.split('.')[-1]
    new_file_name = f'{uuid.uuid4()}.{ext}'

    return os.path.join('/uploads/recipe/', new_file_name)


class UserManager(BaseUserManager):
    """
    User manager for the user model
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a new user
        :param email: email address of the user
        :param password: password of the user
        :param extra_fields: extra fields
        :return: user object
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a new super user
        :param email: email address of the super user
        :param password: password of the super user
        :return: user object
        """
        user = self.create_user(
            email=email,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that supports using email instead of username
    """
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'email'


class Tag(models.Model):
    """
    Tag to be used for recipe
    """
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.name}"


class Ingredient(models.Model):
    """
    Ingredient to be used for recipe
    """
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.name}'


class Recipe(models.Model):
    """
    Recipe class for creating recipe objects
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    ingredients = models.ManyToManyField('Ingredient')
    tags = models.ManyToManyField('Tag')
    image = models.ImageField(null=True, upload_to=recipe_image_file_path)

    def __str__(self):
        return f'{self.title}'
