from django.db import models

class Todo(models.Model):
    title = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='uploads/', blank=True, null=True)  # Optional file attachment

    def __str__(self):
        return self.title