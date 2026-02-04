from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Artwork, Project
from .serializers import ProjectCreateSerializer, ProjectSerializer
from .utils import deduplicate_list_preserve_order
from .services import ArtworkService


class ProjectCreateAPIView(APIView):
    """
    POST /api/projects/
    Body:
    {
      "name": "My Project",
      "description": "optional",
      "start_date": "2026-02-04",
      "artwork_ids": [4, 129884, 999]
    }
    """

    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        artwork_ids = deduplicate_list_preserve_order(data["artwork_ids"])

        existing = Artwork.objects.filter(external_id__in=artwork_ids)
        existing_map = {a.external_id: a for a in existing}

        missing_ids = [aid for aid in artwork_ids if aid not in existing_map]

        # Fetch missing from Art Institute API
        created_artworks, fetch_errors = ArtworkService.fetch_missing_artworks(missing_ids)

        # Save all new artworks and create the project with transaction atomic
        with transaction.atomic():
            if created_artworks:
                Artwork.objects.bulk_create(created_artworks, ignore_conflicts=True)

            artworks = list(Artwork.objects.filter(external_id__in=artwork_ids))
            by_external = {a.external_id: a for a in artworks}

            ordered_artworks = [by_external[aid] for aid in artwork_ids if aid in by_external]

            project = Project.objects.create(
                name=data["name"],
                description=data.get("description"),
                start_date=data.get("start_date"),
            )
            project.artworks.set(ordered_artworks)

        response_payload = ProjectSerializer(project).data
        if fetch_errors:
            response_payload["fetch_errors"] = fetch_errors

        return Response(response_payload, status=status.HTTP_201_CREATED)