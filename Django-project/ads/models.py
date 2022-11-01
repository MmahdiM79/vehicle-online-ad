from django.db import models

# Create your models here.

class VehicleAD(models.Model):
    class StateAD(models.TextChoices):
        ACCEPTED = 'accepted'
        REVIEW = 'review'
        REJECTED = 'rejected'

    description = models.CharField(max_length=4096, default='')
    state = models.CharField(
        max_length=10,
        choices=StateAD.choices,
        default=StateAD.REVIEW,
        null=False
    )
    image = models.CharField(max_length=1024, null=False, blank=False)
    email = models.CharField(max_length=2048, null=False, blank=False)

    def __str__(self):
        return self.title
