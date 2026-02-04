from django.urls import path
from .views import ProjectCreateAPIView

urlpatterns = [
    path("projects/", ProjectCreateAPIView.as_view(), name="project-create"),
]