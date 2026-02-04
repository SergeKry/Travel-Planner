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

    artworks = models.ManyToManyField(Artwork, through="ProjectArtwork", related_name="projects")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class ProjectArtwork(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)

    notes = models.TextField(blank=True, default="")
    visited = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "artwork")
        indexes = [
            models.Index(fields=["project", "visited"]),
        ]

    def __str__(self):
        return f"{self.project_id} -> {self.artwork_id}"