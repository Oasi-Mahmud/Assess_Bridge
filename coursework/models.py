from django.conf import settings
from django.db import models


class Course(models.Model):
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses"
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Assignment(models.Model):
    class Kind(models.TextChoices):
        THEORY = "theory", "Theory"
        PROGRAMMING = "programming", "Programming"
        MIXED = "mixed", "Mixed"

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="assignments"
    )
    title = models.CharField(max_length=150)
    instructions = models.TextField()
    kind = models.CharField(max_length=11, choices=Kind)
    due_at = models.DateTimeField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title
