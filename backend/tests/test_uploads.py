"""Tests for /api/uploads (file type checks, size limit, download, delete)."""

import pytest

from app.config import settings
from app.models import Upload

URL = "/api/uploads"

pytestmark = pytest.mark.usefixtures("demo_user")

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PDF = b"%PDF-1.7\n" + b"x" * 64


def upload(client, name, data, content_type="application/octet-stream"):
    return client.post(URL, files={"file": (name, data, content_type)})


@pytest.mark.parametrize(
    ("name", "data", "expected_type"),
    [
        ("photo.png", PNG, "image/png"),
        ("photo.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 32, "image/jpeg"),
        ("anim.gif", b"GIF89a" + b"\x00" * 32, "image/gif"),
        ("pic.webp", b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 16, "image/webp"),
        ("notes.pdf", PDF, "application/pdf"),
        ("main.py", "print('héllo')\n".encode(), "text/plain"),
        ("README.md", b"# Title\n", "text/plain"),
    ],
)
def test_upload_allowed_types(client, upload_dir, name, data, expected_type):
    response = upload(client, name, data)

    assert response.status_code == 201
    body = response.json()
    assert body["content_type"] == expected_type
    assert body["filename"] == name
    assert body["size"] == len(data)
    assert body["url"] == f"/api/uploads/{body['id']}"
    assert (upload_dir / body["id"]).read_bytes() == data


def test_type_comes_from_content_not_name_or_header(client):
    # An executable renamed to .png and labelled image/png is still rejected
    response = upload(client, "evil.png", b"MZ\x90\x00" + b"\x00" * 64, "image/png")
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("video.mp4", b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32),
        ("doc.docx", b"PK\x03\x04" + b"\x00" * 32),
        ("binary.txt", b"\xff\xfe\x00\x00\x80\x81"),  # .txt but not UTF-8
        ("image.svg", b"<svg onload='alert(1)'></svg>"),  # SVG can run scripts
    ],
)
def test_upload_rejected_types(client, upload_dir, name, data):
    response = upload(client, name, data)

    assert response.status_code == 400
    assert not upload_dir.exists() or list(upload_dir.iterdir()) == []  # nothing kept


def test_empty_file_rejected(client):
    assert upload(client, "empty.txt", b"").status_code == 400


def test_too_large_file_rejected(client, upload_dir, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)

    response = upload(client, "big.pdf", b"%PDF-" + b"x" * (1024 * 1024))

    assert response.status_code == 413
    assert list(upload_dir.iterdir()) == []


def test_filename_folders_are_dropped(client):
    response = upload(client, "../../etc/passwd.txt", b"hello")
    assert response.json()["filename"] == "passwd.txt"


def test_download_returns_file_with_safe_headers(client):
    file = upload(client, "photo.png", PNG).json()

    response = client.get(file["url"])

    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "photo.png" in response.headers["content-disposition"]


def test_html_file_is_served_as_plain_text(client):
    file = upload(client, "page.html", b"<script>alert(1)</script>").json()

    response = client.get(file["url"])

    assert response.headers["content-type"] == "text/plain; charset=utf-8"


def test_download_unknown_file_returns_404(client):
    assert client.get(f"{URL}/{'0' * 32}").status_code == 404


def test_cannot_download_another_users_file(client, db, make_user, upload_dir):
    other = make_user()
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / ("a" * 32)).write_bytes(PNG)
    db.add(Upload(id="a" * 32, user_id=other.id, filename="x.png", content_type="image/png", size=len(PNG)))
    db.commit()

    assert client.get(f"{URL}/{'a' * 32}").status_code == 404


def test_delete_removes_record_and_file(client, upload_dir):
    file = upload(client, "photo.png", PNG).json()

    assert client.delete(file["url"]).status_code == 204
    assert client.get(file["url"]).status_code == 404
    assert not (upload_dir / file["id"]).exists()
