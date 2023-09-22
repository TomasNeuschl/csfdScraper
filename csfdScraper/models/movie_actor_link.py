from django.db import models

from csfdScraper.models import Movie, Actor


class MovieActorLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='actors_link')
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE, related_name='movies_link')
