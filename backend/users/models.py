"""
Users app — Tenant and custom User models for multi-tenant ESG platform.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class Tenant(models.Model):
    """
    Multi-tenant isolation. Every data object belongs to a tenant.
    """
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Custom user extending Django's AbstractUser with a tenant FK.
    Multi-tenancy is resolved from the logged-in user's tenant.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.tenant.name if self.tenant else 'No Tenant'})"
