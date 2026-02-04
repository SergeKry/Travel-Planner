from django.urls import path
from .views import (
    ProjectListCreateAPIView,
    ProjectDetailAPIView,
    ProjectAddArtworkAPIView,
    ProjectArtworkUpdateAPIView,
    ProjectArtworkListAPIView,
    ProjectArtworkDetailAPIView,
)

urlpatterns = [
    path("projects/", ProjectListCreateAPIView.as_view(), name="project-list-create"),
    path("projects/<int:pk>/", ProjectDetailAPIView.as_view(), name="project-detail"),
    path("projects/<int:project_id>/artworks/", ProjectAddArtworkAPIView.as_view(), name="project-add-artwork"),
    path(
        "projects/<int:project_id>/artworks/<int:artwork_id>/",
        ProjectArtworkUpdateAPIView.as_view(),
        name="project-artwork-update",
    ),
    path(
        "projects/<int:project_id>/artworks/",
        ProjectArtworkListAPIView.as_view(),
        name="project-artwork-list",
    ),
    path(
        "projects/<int:project_id>/artworks/<int:artwork_id>/",
        ProjectArtworkDetailAPIView.as_view(),
        name="project-artwork-detail",
    ),
]