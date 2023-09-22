from django.db import models
from unidecode import unidecode

from csfdScraper.models.base import BaseModel


class Actor(BaseModel):
    name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255, blank=True, db_index=True)
    link = models.URLField()

    def __str__(self):
        return self.name
