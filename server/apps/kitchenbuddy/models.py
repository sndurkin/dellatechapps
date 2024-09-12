import enum
from django.db import models
from django.db.models import Model, CharField, JSONField, DateTimeField, IntegerField, TextField
from django.utils.translation import gettext_lazy as _


class Recipe(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    title = CharField(_('Title'), max_length=255)
    url = CharField(_('URL'), max_length=1024)
    content = TextField(_('Content'))
    parsed_recipe = JSONField(_('Parsed Recipe'))
