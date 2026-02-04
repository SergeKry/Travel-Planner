from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Artwork, Project, ProjectArtwork
from .serializers import (
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
)
from .utils import deduplicate_list_preserve_order
from .services import ArtworkService


class ProjectListCreateAPIView(APIView):
    """
    GET  /api/projects/       -> list
    POST /api/projects/       -> create (your existing logic)
    """

    def get(self, request, pk: int):
        project = get_object_or_404(Project, pk=pk)
        return Response(ProjectSerializer(project).data, status=status.HTTP_200_OK)

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
            links = [
                ProjectArtwork(
                    project=project,
                    artwork=artwork,
                )
                for artwork in ordered_artworks
            ]
            ProjectArtwork.objects.bulk_create(links, ignore_conflicts=True)

        response_payload = ProjectSerializer(project).data
        if fetch_errors:
            response_payload["fetch_errors"] = fetch_errors

        return Response(response_payload, status=status.HTTP_201_CREATED)


class ProjectDetailAPIView(APIView):
    """
    GET    /api/projects/<id>/  -> single
    PATCH  /api/projects/<id>/  -> update fields
    DELETE /api/projects/<id>/  -> delete if no visited places
    """

    def get(self, request, pk: int):
        project = get_object_or_404(Project, pk=pk)
        return Response(ProjectSerializer(project).data, status=status.HTTP_200_OK)

    def patch(self, request, pk: int):
        project = get_object_or_404(Project, pk=pk)
        serializer = ProjectUpdateSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProjectSerializer(project).data, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        project = get_object_or_404(Project, pk=pk)

        if ProjectArtwork.objects.filter(project=project, visited=True).exists():
            return Response(
                {"detail": "Project cannot be deleted because it has visited places."},
                status=status.HTTP_409_CONFLICT,
            )

        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)