from rest_framework import serializers

from .models import Assignment, Course


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "name"]


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ["id", "course", "title", "instructions", "kind", "due_at"]

    def get_fields(self):
        fields = super().get_fields()
        instructor = self.context["request"].user
        fields["course"].queryset = Course.objects.filter(instructor=instructor)
        return fields
