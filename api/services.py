import requests
from .models import Artwork

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
