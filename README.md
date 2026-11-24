# AssessBridge Web — Course and Assignment API

AssessBridge puts course assignments and assessment records in one place. This classroom demo covers the instructor's first workflow. The instructor makes a course, adds an assignment with instructions and a due date, and can later view, edit, or delete either record.

A course is a container for assignments. One course may have many assignments, and every assignment belongs to one course.

## Run in VS Code

Open this folder in VS Code. In its terminal on macOS or Linux, use Python 3.14 or a compatible interpreter.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py test -v 2
```

On Windows PowerShell use `py -m venv .venv` and `.\.venv\Scripts\Activate.ps1` for the first two commands. Select the `.venv` interpreter in VS Code.

Django supplies authentication, database migrations and the ORM. Django REST Framework is the separate package supplying viewsets, serializers, routers and the API test client. SQLite keeps demo data in a local file. The migration records how to create the two tables and their relationships.

## Demo in the browser

```bash
python manage.py createsuperuser
python manage.py runserver
```

The superuser is a convenient local demo login because it has Django's staff flag. The API uses that flag as its instructor role. Ordinary users receive 403. An instructor can access only courses they own and assignments linked to those courses. This slice uses session login and synthetic demo data.

1. Open [the login page](http://127.0.0.1:8000/api-auth/login/?next=/api/courses/) and sign in with the account you just created.
2. In [the courses endpoint](http://127.0.0.1:8000/api/courses/), use the form or the Raw data tab to POST the course JSON below. Show 201 and read the returned `id`.
3. Open [the assignments endpoint](http://127.0.0.1:8000/api/assignments/) and POST the assignment JSON below with that course ID. Show 201 and copy the assignment ID.
4. Open `http://127.0.0.1:8000/api/assignments/<assignment-id>/` with your actual ID. The page sends GET. Change the title and submit PUT using the form, then show the updated value. PATCH updates selected fields and is demonstrated by the automated tests.
5. Use the DELETE button on the assignment detail page. Refresh the detail URL to see 404. In a second terminal using the same virtual environment, run `python manage.py test -v 2`.

Course body

```json
{"code": "CSE3102L", "name": "Web Technology Lab"}
```

Assignment body

```json
{
  "course": 1,
  "title": "REST API Lab",
  "instructions": "Implement and test one CRUD resource.",
  "kind": "programming",
  "due_at": "2026-12-01T23:59:00+06:00"
}
```

The integer in `course` is a foreign key, meaning it refers to an existing course's ID. The accepted kinds are `theory`, `programming` and `mixed`. The deadline includes a date, time and UTC offset. `+06:00` is Dhaka time.

## API contract

| What you want | Method | Course URL | Assignment URL | Success |
| --- | --- | --- | --- | --- |
| Create | POST | `/api/courses/` | `/api/assignments/` | 201 Created |
| List | GET | `/api/courses/` | `/api/assignments/` | 200 OK |
| Read one | GET | `/api/courses/{id}/` | `/api/assignments/{id}/` | 200 OK |
| Replace writable fields | PUT | `/api/courses/{id}/` | `/api/assignments/{id}/` | 200 OK |
| Update selected fields | PATCH | `/api/courses/{id}/` | `/api/assignments/{id}/` | 200 OK |
| Delete | DELETE | `/api/courses/{id}/` | `/api/assignments/{id}/` | 204 No Content |

Invalid inputs return 400. A missing record or a record outside the instructor's courses returns 404. Django deletes the linked assignments when their course is deleted, through `on_delete=models.CASCADE`.

## How the code works

1. [config/urls.py](config/urls.py) registers each resource with a DRF router. The router sends a method and URL to the matching viewset action. For example, POST on the assignments collection goes to `create()`.
2. [coursework/views.py](coursework/views.py) uses `ModelViewSet` for the standard CRUD actions. The permission class checks the staff flag. `get_queryset()` restricts which rows this instructor can see, edit, or delete. `perform_create()` saves the course's instructor using the logged-in account.
3. [coursework/serializers.py](coursework/serializers.py) parses and validates posted data and converts saved records into response fields. The assignment serializer limits which courses can be supplied in POST, PUT or PATCH. This protects writes as well as reads.
4. [coursework/models.py](coursework/models.py) defines both tables. Django's object-relational mapper (ORM) turns Python operations into database queries. Django assigns primary keys when it inserts new records.
5. [coursework/tests.py](coursework/tests.py) sends requests to the actual URL configuration, then checks HTTP status, response data and database state. For example, one test creates an assignment, updates it, deletes it and expects the next GET to return 404.

## What the automated tests check

| Test case | Expected result |
| --- | --- |
| Course lifecycle | Create, list, read, PUT, PATCH, delete, then 404 |
| Assignment lifecycle | Create, list, read, PUT, PATCH, delete, then 404 |
| Course without a name | 400 and no course saved |
| Invalid assignment kind and deadline | 400 with both field errors and no assignment saved |
| Logged-out requests | 403 |
| Student attempts access | 403 on both resources |
| Another instructor's course | 404 for read and delete |
| Assignment points to another instructor's course | 400 on both create and update |
| Another instructor's assignment | Hidden from list, PATCH returns 404 |
| Course with an assignment is deleted | Course deletion returns 204 and its assignment becomes 404 |

`APITestCase` gives each test an `APIClient`. It does the repeatable part of Postman inside the test runner. It goes through the application's routing, session authentication, validation and database without starting a separate server. The database used for tests is separate from your demo database.

## Public GitHub handoff

After running the tests, if you need a fresh repo and have GitHub CLI installed, run the following in the project folder.

```bash
git init -b main
git add .
git commit -m "Implement AssessBridge coursework CRUD and integration tests"
gh auth login -h github.com
gh repo create assessbridge-backend --public --source=. --remote=origin --push
```

The repository should contain the source, migration, tests and README. `.gitignore` excludes the local SQLite database, virtual environment and `.env` files. Mention the use of AI assistance for the initial implementation and walkthrough in accordance with the course guidelines.

For the class demo, open the repository first. Show the model relationship, then `config/urls.py`, then one successful API call and the test output.
