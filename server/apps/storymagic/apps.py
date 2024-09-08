from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StorymagicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "server.apps.storymagic"
    verbose_name = _("storymagic")
