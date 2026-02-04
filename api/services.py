import requests
from .models import Artwork, Project, ProjectArtwork

ARTIC_BASE = "https://api.artic.edu/api/v1/artworks"


class ArtworkService:
    @staticmethod
    def fetch_missing_artworks(missing_ids):
        """
        Fetch missing artworks from Art Institute API.
        
        Args:
            missing_ids: List of artwork external IDs to fetch
            
        Returns:
            tuple: (created_artworks, fetch_errors)
        """
        created_artworks = []
        fetch_errors = []

        for aid in missing_ids:
            try:
                r = requests.get(f"{ARTIC_BASE}/{aid}", timeout=10)
                if r.status_code != 200:
                    fetch_errors.append({"id": aid, "status_code": r.status_code})
                    continue

                payload = r.json() or {}
                api_data = payload.get("data") or {}
                info = payload.get("info") or {}

                title = api_data.get("title") or ""
                license_text = info.get("license_text") or ""

                if not title:
                    # Up to you: allow blank title, or treat as error
                    title = f"Artwork {aid}"

                created_artworks.append(
                    Artwork(
                        external_id=aid,
                        title=title,
                        license_text=license_text,
                    )
                )
            except requests.RequestException as e:
                fetch_errors.append({"id": aid, "error": str(e)})

        return created_artworks, fetch_errors


class ProjectService:
    @staticmethod
    def sync_completion(project_id: int) -> Project:
        """
        Recalculate and persist Project completion state based on its ProjectArtwork rows.

        Must be called inside transaction.atomic() if you want race-safety.
        """
        project = Project.objects.select_for_update().get(pk=project_id)

        any_unvisited = ProjectArtwork.objects.filter(project_id=project_id, visited=False).exists()

        if not any_unvisited:
            if not project.is_completed:
                project.is_completed = True
                project.save(update_fields=["is_completed"])
        else:
            if project.is_completed:
                project.is_completed = False
                project.save(update_fields=["is_completed"])

        return project


class ProjectArtworkService:
    MAX_PLACES = 10

    @staticmethod
    def add_artwork_to_project(*, project: Project, artwork: Artwork) -> bool:
        """
        Transaction-safe add.
        Returns True if link created, False if it already existed.

        Enforces MAX_PLACES and prevents duplicates.
        Must be called inside transaction.atomic().
        """
        # Lock existing rows for race-safety on count and duplicates
        ProjectArtwork.objects.select_for_update().filter(project=project)

        if ProjectArtwork.objects.filter(project=project, artwork=artwork).exists():
            return False

        if ProjectArtwork.objects.filter(project=project).count() >= ProjectArtworkService.MAX_PLACES:
            raise ValueError({"detail": f"A project can contain at most {ProjectArtworkService.MAX_PLACES} places."})

        try:
            ProjectArtwork.objects.create(project=project, artwork=artwork, notes="", visited=False)
        except IntegrityError:
            return False

        return True