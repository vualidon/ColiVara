from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import get_random_string


class CustomUser(AbstractUser):
    TIER = (
        ("starter", "Starter"),
        ("professional", "Professional"),
    )
    subscribe_to_emails = models.BooleanField(default=True)
    tier = models.CharField(max_length=50, choices=TIER, default="free")
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    svix_application_id = models.CharField(max_length=255, blank=True)
    svix_endpoint_id = models.CharField(max_length=255, blank=True)
    token = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return self.email

    def generate_token(self) -> str:
        self.token = get_random_string(length=32)
        self.save()
        return self.token

    # create token on user creation
    def save(self, *args, **kwargs) -> None:
        if not self.token:
            self.generate_token()
        super().save(*args, **kwargs)
