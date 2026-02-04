from rest_framework import serializers
from .models import Artwork, Project, ProjectArtwork


class ArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artwork
        fields = ["id", "external_id", "title", "license_text"]


class ProjectCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    start_date = serializers.DateField(required=False, allow_null=True)

    artwork_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


class ProjectArtworkSerializer(serializers.ModelSerializer):
    """Serializer for the through model"""
    artwork = ArtworkSerializer()

    class Meta:
        model = ProjectArtwork
        fields = [
            "artwork",
            "notes",
            "visited",
        ]


class ProjectSerializer(serializers.ModelSerializer):
    artworks = ProjectArtworkSerializer(
        source="project_artworks",
        many=True,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "start_date",
            "artworks",
        ]