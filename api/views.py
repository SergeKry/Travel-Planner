from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Artwork, Project, ProjectArtwork
from .serializers import (
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
    ProjectArtworkUpdateSerializer
)

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

        artwork_ids = data["artwork_ids"]

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


class ProjectAddArtworkAPIView(APIView):
    """
    POST /api/projects/<project_id>/artworks/
    Body: { "artwork_id": 123 }
    """

    def post(self, request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)

        serializer = ProjectAddArtworkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        external_id = serializer.validated_data["artwork_id"]

        artwork = Artwork.objects.filter(external_id=external_id).first()
        if not artwork:
            created_artworks, fetch_errors = ArtworkService.fetch_missing_artworks([external_id])

            if fetch_errors or not created_artworks:
                return Response(
                    {
                        "detail": "Artwork does not exist in third-party API or could not be fetched.",
                        "errors": fetch_errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Artwork.objects.bulk_create(created_artworks, ignore_conflicts=True)
            artwork = Artwork.objects.get(external_id=external_id)

        with transaction.atomic():
            ProjectArtwork.objects.select_for_update().filter(project=project)
            existing_link = ProjectArtwork.objects.filter(project=project, artwork=artwork).first()
            if existing_link:
                payload = ProjectSerializer(project).data
                payload["added"] = {"external_id": artwork.external_id, "created_link": False}
                return Response(payload, status=status.HTTP_200_OK)
            current_count = ProjectArtwork.objects.filter(project=project).count()
            if current_count >= 10:
                return Response(
                    {"detail": "A project can contain at most 10 places."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ProjectArtwork.objects.create(
                project=project,
                artwork=artwork,
                notes="",
                visited=False,
            )

        payload = ProjectSerializer(project).data
        payload["added"] = {"external_id": artwork.external_id, "created_link": True}
        return Response(payload, status=status.HTTP_201_CREATED)


class ProjectArtworkUpdateAPIView(APIView):
    """
    PATCH /api/projects/<project_id>/artworks/<artwork_id>/
    Body: { "notes": "...", "visited": true }
    Updates the through-table fields for this artwork inside this project.

    Extra logic:
    - If all places in the project are visited => project.is_completed=True (+ completed_at)
    - Otherwise => project.is_completed=False (+ completed_at=None)
    """

    def patch(self, request, project_id: int, artwork_id: int):
        serializer = ProjectArtworkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        with transaction.atomic():
            project = get_object_or_404(Project.objects.select_for_update(), pk=project_id)
            artwork = get_object_or_404(Artwork, external_id=artwork_id)

            link = get_object_or_404(
                ProjectArtwork.objects.select_for_update(),
                project=project,
                artwork=artwork,
            )

            visited_changed = False

            if "notes" in payload:
                link.notes = payload["notes"]

            if "visited" in payload:
                new_visited = payload["visited"]
                visited_changed = (link.visited != new_visited)
                link.visited = new_visited

            link.save(update_fields=["notes", "visited"])

            if visited_changed:
                project = ProjectService.sync_completion(project_id=project.id)

        return Response(ProjectSerializer(project).data, status=status.HTTP_200_OK)


class ProjectArtworkListAPIView(APIView):
    """
    GET /api/projects/<project_id>/artworks/
    Lists all places/artworks in a project, including notes + visited.
    """

    def get(self, request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)

        qs = (
            ProjectArtwork.objects
            .filter(project=project)
            .select_related("artwork")
            .order_by("id")
        )

        return Response(ProjectArtworkSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class ProjectArtworkDetailAPIView(APIView):
    """
    GET /api/projects/<project_id>/artworks/<artwork_id>/
    Returns a single place/artwork within the project.
    artwork_id = Artwork.external_id
    """

    def get(self, request, project_id: int, artwork_id: int):
        project = get_object_or_404(Project, pk=project_id)
        artwork = get_object_or_404(Artwork, external_id=artwork_id)

        link = get_object_or_404(
            ProjectArtwork.objects.select_related("artwork"),
            project=project,
            artwork=artwork,
        )

        return Response(ProjectArtworkSerializer(link).data, status=status.HTTP_200_OK)