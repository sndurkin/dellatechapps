import enum
from django.db import models
from django.db.models import Model, CharField, JSONField, DateTimeField, IntegerField, TextField
from django.utils.translation import gettext_lazy as _


class User(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    username = models.CharField(max_length=32, unique=True)

class Recipe(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes', null=True)
    title = CharField(_('Title'), max_length=255)
    url = CharField(_('URL'), max_length=1024)
    content = TextField(_('Content'))
    parsed_recipe = JSONField(_('Parsed Recipe'))

    class Meta:
        unique_together = [('user', 'url')]

class GroceryList(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grocery_lists', unique=True)
    items = JSONField(_('Items'))
