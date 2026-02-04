from django.urls import path
from .views import ProjectListCreateAPIView, ProjectDetailAPIView, ProjectAddArtworkAPIView

urlpatterns = [
    path("projects/", ProjectListCreateAPIView.as_view(), name="project-list-create"),
    path("projects/<int:pk>/", ProjectDetailAPIView.as_view(), name="project-detail"),
    path("projects/<int:project_id>/artworks/", ProjectAddArtworkAPIView.as_view(), name="project-add-artwork"),
]