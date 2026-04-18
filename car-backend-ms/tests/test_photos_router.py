from app.db.models.photo import OperationType


class TestListPhotos:
    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/photos")
        assert resp.status_code == 401

    def test_returns_empty_list_when_no_photos(self, client, auth_headers):
        resp = client.get("/photos", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["photos"] == []
        assert body["total"] == 0

    def test_returns_own_photos_with_correct_total(self, client, auth_headers, user_and_token, make_photo):
        user, _ = user_and_token
        make_photo(user)
        make_photo(user)
        resp = client.get("/photos", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["photos"]) == 2

    def test_does_not_return_other_users_photos(self, client, auth_headers, user_and_token, make_user, make_photo):
        user, _ = user_and_token
        other = make_user(firebase_uid="bob-uid", email="bob@example.com")
        make_photo(other)         # belongs to bob
        make_photo(user)          # belongs to alice
        resp = client.get("/photos", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["photos"][0]["user_id"] == user.id

    def test_pagination_skip_and_limit(self, client, auth_headers, user_and_token, make_photo):
        user, _ = user_and_token
        for _ in range(5):
            make_photo(user)
        resp = client.get("/photos?skip=2&limit=2", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["photos"]) == 2

    def test_photo_response_contains_expected_fields(self, client, auth_headers, user_and_token, make_photo):
        user, _ = user_and_token
        make_photo(user, filename="mycar.jpg", operation_type=OperationType.edit_photo)
        resp = client.get("/photos", headers=auth_headers)
        photo = resp.json()["photos"][0]
        assert photo["original_filename"] == "mycar.jpg"
        assert photo["operation_type"] == "edit_photo"
        assert "created_at" in photo


class TestDownloadPhoto:
    def test_returns_result_image_when_present(self, client, auth_headers, user_and_token, make_photo):
        user, _ = user_and_token
        photo = make_photo(user, original_image=b"original", result_image=b"result")
        resp = client.get(f"/photos/{photo.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.content == b"result"
        assert resp.headers["content-type"] == "image/png"

    def test_returns_original_when_result_is_absent(self, client, auth_headers, user_and_token, make_photo):
        user, _ = user_and_token
        photo = make_photo(user, original_image=b"original", result_image=None)
        resp = client.get(f"/photos/{photo.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.content == b"original"

    def test_nonexistent_photo_returns_404(self, client, auth_headers):
        resp = client.get("/photos/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_other_users_photo_returns_404(self, client, auth_headers, make_user, make_photo):
        other = make_user(firebase_uid="bob-uid", email="bob@example.com")
        photo = make_photo(other)
        resp = client.get(f"/photos/{photo.id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client, user_and_token, make_photo):
        user, _ = user_and_token
        photo = make_photo(user)
        resp = client.get(f"/photos/{photo.id}")
        assert resp.status_code == 401
