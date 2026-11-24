from django.urls import include, path
from rest_framework.routers import DefaultRouter

from coursework.views import AssignmentViewSet, CourseViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("assignments", AssignmentViewSet, basename="assignment")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
]
