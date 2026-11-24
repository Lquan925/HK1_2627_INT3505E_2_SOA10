"""Kiểm tra tài liệu, tài nguyên giao diện và toàn bộ tham chiếu OpenAPI."""

from html.parser import HTMLParser
from urllib.parse import unquote, urldefrag, urljoin, urlsplit

import pytest
import yaml

from student_assistant import create_app


@pytest.fixture
def client(monkeypatch, tmp_path):
    # Tài liệu phải hoạt động khi chạy ngoài backend/ và không cần PostgreSQL.
    monkeypatch.chdir(tmp_path)
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "OPENAPI_SPEC_DIR": None}
    )
    return app.test_client()


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("src"):
            self.urls.append(attributes["src"])
        if tag == "link" and attributes.get("href"):
            self.urls.append(attributes["href"])


def test_swagger_ui_and_local_assets(client):
    response = client.get("/docs", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '"url": "/openapi/openapi.yaml"' in html
    assert '"validatorUrl": null' in html
    assert '"persistAuthorization": false' in html

    parser = AssetParser()
    parser.feed(html)
    assert any("swagger-ui-bundle.js" in url for url in parser.urls)
    assert any("swagger-ui.css" in url for url in parser.urls)
    for url in parser.urls:
        assert url.startswith("/docs/")
        asset = client.get(url)
        assert asset.status_code == 200, url
        assert asset.data, url


def test_openapi_resolves_all_modular_references(client):
    documents = {}
    pending = []
    reference_count = 0

    def load_document(url):
        if url not in documents:
            response = client.get(url)
            assert response.status_code == 200, url
            assert response.mimetype == "application/yaml"
            documents[url] = yaml.safe_load(response.data)
            pending.append(url)
        return documents[url]

    def walk(node, document_url):
        nonlocal reference_count
        if isinstance(node, dict):
            if "$ref" in node:
                target_url, fragment = urldefrag(urljoin(document_url, node["$ref"]))
                assert not urlsplit(target_url).netloc
                assert target_url.startswith("/openapi/")
                target = load_document(target_url)
                if fragment:
                    assert fragment.startswith("/")
                    for token in unquote(fragment)[1:].split("/"):
                        key = token.replace("~1", "/").replace("~0", "~")
                        target = target[int(key)] if isinstance(target, list) else target[key]
                reference_count += 1
            for value in node.values():
                walk(value, document_url)
        elif isinstance(node, list):
            for item in node:
                walk(item, document_url)

    root = load_document("/openapi/openapi.yaml")
    visited = set()
    while pending:
        url = pending.pop()
        if url not in visited:
            visited.add(url)
            walk(documents[url], url)

    assert root["openapi"] == "3.0.3"
    assert root["servers"][0]["url"] == "/api/v1"
    assert root["components"]["securitySchemes"]["sessionAuth"]
    assert root["paths"]
    assert reference_count > 0
    assert any("/paths/" in url for url in documents)
    assert any("/schemas/" in url for url in documents)
    assert any("/common/" in url for url in documents)


@pytest.mark.parametrize(
    "filename",
    [
        "README.md",
        "missing.yaml",
        "../private.yaml",
        "%2e%2e/private.yaml",
        "..%5cprivate.yaml",
    ],
)
def test_spec_directory_does_not_expose_other_files(tmp_path, filename):
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    (tmp_path / "private.yaml").write_text("private: true", encoding="utf-8")
    (spec_dir / "README.md").write_text("Private notes", encoding="utf-8")
    (spec_dir / "openapi.yaml").write_text("openapi: 3.0.3", encoding="utf-8")
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "OPENAPI_SPEC_DIR": spec_dir,
        }
    )
    client = app.test_client()
    assert client.get("/openapi/openapi.yaml").status_code == 200
    assert client.get(f"/openapi/{filename}").status_code == 404
