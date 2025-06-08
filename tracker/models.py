from django.db import models
from django.utils import timezone

class BrowsingHistory(models.Model):
    url = models.URLField()
    query = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    sentiment_score = models.FloatField(default=0.0)
    time_spent = models.FloatField(help_text="Time spent in seconds", default=0.0)
    mental_state = models.CharField(max_length=50, default="Unknown")

    def __str__(self):
        return f"{self.url} - {self.timestamp}"

class AlertControl(models.Model):
    is_active = models.BooleanField(default=True)
    last_email_sent = models.DateTimeField(default=timezone.now)
    reset_timestamp = models.DateTimeField(default=timezone.now)
    

