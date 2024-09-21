from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField
from django_stubs_ext.db.models import TypedModelMeta
from pgvector.django import VectorField

from accounts.models import CustomUser


class Collection(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="collections"
    )
    metadata = JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    
    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(fields=["name", "owner"], name="unique_collection_per_user")
        ]

class Document(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="documents"
    )
    name = models.CharField(max_length=255)
    metadata = JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(fields=["name", "collection"], name="unique_document_per_collection")
        ]

class Page(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="pages"
    )
    page_number = models.IntegerField()
    content = models.TextField(blank=True)
    base64 = models.TextField(blank=True)
    embeddings = ArrayField(
        VectorField(dimensions=128)
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(TypedModelMeta):
        constraints = [
            models.UniqueConstraint(fields=["content", "document"], name="unique_page_per_document")
        ]