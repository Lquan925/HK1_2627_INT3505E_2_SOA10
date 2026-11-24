"""Phục vụ Swagger UI và các tệp đặc tả OpenAPI theo mô-đun."""

from pathlib import Path

from flask import Blueprint, Flask, abort, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint


def register_api_docs(app: Flask) -> None:
    """Đăng ký tài liệu cùng ứng dụng, không phụ thuộc thư mục chạy lệnh."""
    default_spec_dir = (
        Path(__file__).resolve().parents[3]
        / "openapi"
        / "openapi_modular"
        / "openapi_modular"
    )
    spec_dir = Path(app.config.get("OPENAPI_SPEC_DIR") or default_spec_dir).resolve()
    openapi = Blueprint("openapi", __name__, url_prefix="/openapi")

    @openapi.get("/<path:filename>")
    def specification(filename: str):
        if not filename.endswith(".yaml"):
            abort(404)
        return send_from_directory(spec_dir, filename, mimetype="application/yaml")

    app.register_blueprint(openapi)
    app.register_blueprint(
        get_swaggerui_blueprint(
            "/docs",
            "/openapi/openapi.yaml",
            config={
                "app_name": "AI Student Assistant — Tài liệu API",
                "validatorUrl": None,
                "persistAuthorization": False,
                "displayRequestDuration": True,
            },
        )
    )
