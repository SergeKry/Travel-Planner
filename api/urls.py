from django.urls import path
from .views import ProjectCreateAPIView, ProjectDeleteAPIView

urlpatterns = [
    path("projects/", ProjectCreateAPIView.as_view(), name="project-create"),
    path("projects/<int:pk>/", ProjectDeleteAPIView.as_view(), name="project-delete"),
]