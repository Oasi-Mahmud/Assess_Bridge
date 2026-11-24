from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Assignment, Course


class CourseworkAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.instructor = users.create_user("instructor", password="test-password", is_staff=True)
        cls.other_instructor = users.create_user("other", password="test-password", is_staff=True)
        cls.student = users.create_user("student", password="test-password")
        cls.other_course = Course.objects.create(
            instructor=cls.other_instructor, code="CSE9999", name="Other Instructor's Course"
        )

    def setUp(self):
        self.assertTrue(self.client.login(username="instructor", password="test-password"))
        self.courses = reverse("course-list")
        self.assignments = reverse("assignment-list")
        self.course_data = {"code": "CSE3102L", "name": "Web Technology Lab"}

    def create_course(self):
        response = self.client.post(self.courses, self.course_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data["id"]

    def assignment_data(self, course_id):
        return {
            "course": course_id,
            "title": "REST API Lab",
            "instructions": "Implement and test one CRUD resource.",
            "kind": "programming",
            "due_at": "2026-12-01T23:59:00+06:00",
        }

    def create_assignment(self, course_id):
        response = self.client.post(
            self.assignments, self.assignment_data(course_id), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return response.data["id"]

    def test_course_full_crud_lifecycle(self):
        course_id = self.create_course()
        detail = reverse("course-detail", args=[course_id])
        self.assertEqual(Course.objects.get(pk=course_id).instructor, self.instructor)

        listing = self.client.get(self.courses)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual([course["id"] for course in listing.data], [course_id])

        response = self.client.get(detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.course_data["name"])

        replacement = {"code": "CSE3102", "name": "Web Technology"}
        response = self.client.put(detail, replacement, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Course.objects.get(pk=course_id).code, "CSE3102")

        response = self.client.patch(detail, {"name": "Web Technology Demo"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "CSE3102")
        self.assertEqual(Course.objects.get(pk=course_id).name, "Web Technology Demo")

        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(pk=course_id).exists())
        self.assertEqual(self.client.get(detail).status_code, status.HTTP_404_NOT_FOUND)

    def test_assignment_full_crud_lifecycle(self):
        course_id = self.create_course()
        assignment_id = self.create_assignment(course_id)
        detail = reverse("assignment-detail", args=[assignment_id])

        listing = self.client.get(self.assignments)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in listing.data], [assignment_id])
        response = self.client.get(detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["course"], course_id)
        self.assertEqual(response.data["title"], "REST API Lab")

        replacement = self.assignment_data(course_id)
        replacement["title"] = "REST API and Testing Lab"
        response = self.client.put(detail, replacement, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], replacement["title"])

        response = self.client.patch(detail, {"kind": "mixed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], replacement["title"])
        self.assertEqual(Assignment.objects.get(pk=assignment_id).kind, "mixed")

        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Assignment.objects.filter(pk=assignment_id).exists())
        self.assertEqual(self.client.get(detail).status_code, status.HTTP_404_NOT_FOUND)

    def test_course_requires_a_name(self):
        response = self.client.post(self.courses, {"code": "CSE3102L"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertFalse(Course.objects.filter(instructor=self.instructor).exists())

    def test_assignment_rejects_invalid_timestamp_and_kind(self):
        data = self.assignment_data(self.create_course())
        data.update(due_at="tomorrow", kind="essay")
        response = self.client.post(self.assignments, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("due_at", response.data)
        self.assertIn("kind", response.data)
        self.assertFalse(Assignment.objects.exists())

    def test_logged_out_user_cannot_list_or_create_courses(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.courses).status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(self.courses, self.course_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_manage_courses_or_assignments(self):
        self.assertTrue(self.client.login(username="student", password="test-password"))
        for url in (self.courses, self.assignments):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)
                self.assertEqual(
                    self.client.post(url, {}, format="json").status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_instructor_cannot_read_or_delete_another_instructors_course(self):
        detail = reverse("course-detail", args=[self.other_course.pk])
        self.assertEqual(self.client.get(detail).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Course.objects.filter(pk=self.other_course.pk).exists())

    def test_instructor_cannot_attach_an_assignment_to_another_instructors_course(self):
        data = self.assignment_data(self.other_course.pk)
        response = self.client.post(self.assignments, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("course", response.data)

        course_id = self.create_course()
        assignment_id = self.create_assignment(course_id)
        detail = reverse("assignment-detail", args=[assignment_id])
        response = self.client.patch(detail, {"course": self.other_course.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Assignment.objects.get(pk=assignment_id).course_id, course_id)

    def test_instructor_cannot_list_or_edit_another_instructors_assignment(self):
        other = Assignment.objects.create(
            course=self.other_course,
            title="Private Lab",
            instructions="Other course instructions.",
            kind=Assignment.Kind.THEORY,
            due_at="2026-12-01T23:59:00+06:00",
        )
        listing = self.client.get(self.assignments)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data, [])
        detail = reverse("assignment-detail", args=[other.pk])
        response = self.client.patch(detail, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other.refresh_from_db()
        self.assertEqual(other.title, "Private Lab")

    def test_deleting_course_also_deletes_its_assignments(self):
        course_id = self.create_course()
        assignment_id = self.create_assignment(course_id)
        detail = reverse("course-detail", args=[course_id])

        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Assignment.objects.filter(pk=assignment_id).exists())
        assignment = reverse("assignment-detail", args=[assignment_id])
        self.assertEqual(self.client.get(assignment).status_code, status.HTTP_404_NOT_FOUND)
