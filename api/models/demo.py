from django.db import models


class Demo(models.Model):
    text = models.TextField()