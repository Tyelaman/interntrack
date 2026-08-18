import app as app_module


def registration_data(**overrides):
    data = {
        "username": "newuser",
        "password": "password123",
        "confirmation": "password123",
    }
    data.update(overrides)
    return data


def job_data(**overrides):
    data = {
        "external_id": "adzuna-123",
        "title": "Software Engineering Intern",
        "company": "Example Corp",
        "location": "Indianapolis, IN",
        "description": "Build useful software.",
        "apply_url": "https://example.com/jobs/123",
        "posted_at": "2026-08-18T12:00:00Z",
    }
    data.update(overrides)
    return data


def test_protected_route_redirects_to_login(client):
    response = client.get("/applications")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_successful_registration(client, database):
    response = client.post("/register", data=registration_data())

    user = database.execute(
        "SELECT username FROM users WHERE username = ?",
        ("newuser",),
    ).fetchone()
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert user["username"] == "newuser"


def test_short_username_is_rejected(client):
    response = client.post(
        "/register",
        data=registration_data(username="ab"),
    )

    assert response.status_code == 400


def test_short_password_is_rejected(client):
    response = client.post(
        "/register",
        data=registration_data(password="short", confirmation="short"),
    )

    assert response.status_code == 400


def test_password_confirmation_mismatch_is_rejected(client):
    response = client.post(
        "/register",
        data=registration_data(confirmation="different123"),
    )

    assert response.status_code == 400


def test_successful_login(client, create_user):
    user_id = create_user()

    response = client.post(
        "/login",
        data={"username": "alice", "password": "password123"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as flask_session:
        assert flask_session["user_id"] == user_id


def test_invalid_login_is_rejected(client, create_user):
    create_user()

    response = client.post(
        "/login",
        data={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 403


def test_authenticated_user_can_save_internship(logged_in_client, database):
    client, user_id = logged_in_client

    response = client.post("/save", data=job_data())

    saved = database.execute(
        "SELECT title, user_id FROM applications WHERE external_id = ?",
        ("adzuna-123",),
    ).fetchone()
    assert response.status_code == 302
    assert saved["title"] == "Software Engineering Intern"
    assert saved["user_id"] == user_id


def test_duplicate_save_is_prevented(logged_in_client, database):
    client, _ = logged_in_client

    first_response = client.post("/save", data=job_data())
    second_response = client.post("/save", data=job_data())

    count = database.execute("SELECT COUNT(*) AS count FROM applications").fetchone()[
        "count"
    ]
    assert first_response.status_code == 302
    assert second_response.status_code == 302
    assert count == 1


def test_status_update_works(
    logged_in_client,
    database,
    create_application,
):
    client, user_id = logged_in_client
    application_id = create_application(user_id)

    response = client.post(
        "/update-status",
        data={"application_id": application_id, "status": "Interview"},
    )

    status = database.execute(
        "SELECT status FROM applications WHERE id = ?",
        (application_id,),
    ).fetchone()["status"]
    assert response.status_code == 302
    assert status == "Interview"


def test_deadline_and_notes_update_works(
    logged_in_client,
    database,
    create_application,
):
    client, user_id = logged_in_client
    application_id = create_application(user_id)

    response = client.post(
        "/update-details",
        data={
            "application_id": application_id,
            "application_deadline": "2026-09-30",
            "notes": "Prepare portfolio examples.",
        },
    )

    saved = database.execute(
        "SELECT application_deadline, notes FROM applications WHERE id = ?",
        (application_id,),
    ).fetchone()
    assert response.status_code == 302
    assert saved["application_deadline"] == "2026-09-30"
    assert saved["notes"] == "Prepare portfolio examples."


def test_delete_application_works(
    logged_in_client,
    database,
    create_application,
):
    client, user_id = logged_in_client
    application_id = create_application(user_id)

    response = client.post(
        "/delete-application",
        data={"application_id": application_id},
    )

    saved = database.execute(
        "SELECT id FROM applications WHERE id = ?",
        (application_id,),
    ).fetchone()
    assert response.status_code == 302
    assert saved is None


def test_invalid_status_and_filter_are_rejected(
    logged_in_client,
    create_application,
):
    client, user_id = logged_in_client
    application_id = create_application(user_id)

    status_response = client.post(
        "/update-status",
        data={"application_id": application_id, "status": "Unknown"},
    )
    filter_response = client.get("/applications?status=Unknown")

    assert status_response.status_code == 400
    assert filter_response.status_code == 400


def test_user_cannot_update_or_delete_another_users_application(
    logged_in_client,
    database,
    create_user,
    create_application,
):
    client, _ = logged_in_client
    other_user_id = create_user("bob")
    application_id = create_application(other_user_id)

    update_response = client.post(
        "/update-status",
        data={"application_id": application_id, "status": "Offer"},
    )
    delete_response = client.post(
        "/delete-application",
        data={"application_id": application_id},
    )

    saved = database.execute(
        "SELECT status FROM applications WHERE id = ?",
        (application_id,),
    ).fetchone()
    assert update_response.status_code == 302
    assert delete_response.status_code == 302
    assert saved["status"] == "Saved"


def test_discover_renders_mocked_search_results(logged_in_client, monkeypatch):
    client, _ = logged_in_client
    mocked_jobs = [
        {
            "external_id": "mock-1",
            "title": "Data Intern",
            "company": "Mock Company",
            "location": "Remote",
            "description": "Analyze data.",
            "apply_url": None,
            "posted_at": "2026-08-18",
        }
    ]

    def fake_search(keyword, location, page):
        assert (keyword, location, page) == ("data", "Remote", 1)
        return mocked_jobs, 1

    monkeypatch.setattr(app_module, "search_jobs", fake_search)

    response = client.get("/discover?keyword=data&location=Remote")

    assert response.status_code == 200
    assert b"Data Intern" in response.data
    assert b"Mock Company" in response.data


def test_csrf_rejects_post_without_token(app, client):
    app.config["WTF_CSRF_ENABLED"] = True

    response = client.post(
        "/login",
        data={"username": "alice", "password": "password123"},
    )

    assert response.status_code == 400
    assert b"your-form-expired-or-could-not-be-verified" in response.data
