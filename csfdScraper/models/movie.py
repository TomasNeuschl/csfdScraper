from django.db import models
from unidecode import unidecode

from csfdScraper.models.actor import Actor
from csfdScraper.models.base import BaseModel


class Movie(BaseModel):
    title = models.CharField(max_length=255)
    normalized_title = models.CharField(max_length=255, blank=True)
    year = models.IntegerField()
    link = models.URLField()
    actors = models.ManyToManyField(Actor)

    def save(self, *args, **kwargs):
        self.normalized_title = unidecode(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} ({self.year})'
