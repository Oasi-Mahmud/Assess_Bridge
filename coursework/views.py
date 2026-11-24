from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from .models import Assignment, Course
from .serializers import AssignmentSerializer, CourseSerializer


class CourseViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CourseSerializer

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)


class AssignmentViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        return Assignment.objects.filter(course__instructor=self.request.user)
