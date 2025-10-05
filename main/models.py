from django.db import models
from django.utils import timezone

class Feed(models.Model):
    feed = models.JSONField()
    date = models.DateField(default=timezone.now)