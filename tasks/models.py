from django.db import models

class Task(models.Model):
    title = models.CharField(max_length=400)
    due_date = models.DateField(null=True, blank=True)
    importance = models.IntegerField(default=5)
    estimated_hours = models.FloatField(default=2.0)
    dependencies = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
