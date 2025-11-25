from django.db import models
from django.utils import timezone

class Feed(models.Model):
    feed = models.JSONField()
    date = models.DateField(default=timezone.now)

class Chat(models.Model):
    messages = models.JSONField()
    attached_articles = models.JSONField()
    date = models.DateField(default=timezone.now)
