from django.db import models


class Artwork(models.Model):
    external_id = models.PositiveIntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=500)
    license_text = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.external_id}: {self.title}"


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)

    artworks = models.ManyToManyField(Artwork, related_name="projects")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name