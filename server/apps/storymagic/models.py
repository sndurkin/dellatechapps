import enum
from django.db import models
from django.db.models import Model, CharField, JSONField, DateTimeField, IntegerField
from django.utils.translation import gettext_lazy as _


class Grade(enum.Enum):
    PRESCHOOL = 'Preschool'
    KINDERGARTEN = 'Kindergarten'
    FIRST_GRADE = '1st Grade'
    SECOND_GRADE = '2nd Grade'
    THIRD_GRADE = '3rd Grade'
    FOURTH_GRADE = '4th Grade'
    FIFTH_GRADE = '5th Grade'
    SIXTH_GRADE = '6th Grade'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

class Story(Model):
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    title = CharField(_('Title'), max_length=255)
    sentences = JSONField(_('Sentences'))
    sentence_count = IntegerField(_('Sentence count'))
    topic = CharField(_('Topic'), max_length=1024)
    grade = CharField(_('Grade'), max_length=24, choices=Grade.choices)
