from django.db import models
from unidecode import unidecode

from csfdScraper.models.base import BaseModel


class Actor(BaseModel):
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, blank=True)
    link = models.URLField()

    def save(self, *args, **kwargs):
        self.normalized_name = unidecode(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
