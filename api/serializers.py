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

    def validate_artwork_ids(self, value):
        # validate after dedupe so 10 unique places max
        seen = set()
        deduped = []
        for x in value:
            if x not in seen:
                seen.add(x)
                deduped.append(x)

        if len(deduped) < 1:
            raise serializers.ValidationError("A project must contain at least 1 place.")
        if len(deduped) > 10:
            raise serializers.ValidationError("A project can contain at most 10 places.")

        return deduped


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "description", "start_date"]


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
            "is_completed",
        ]


class ProjectAddArtworkSerializer(serializers.Serializer):
    artwork_id = serializers.IntegerField(min_value=1)


class ProjectArtworkUpdateSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)
    visited = serializers.BooleanField(required=False)