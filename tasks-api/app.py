import os
import uuid
import yaml
import datetime
from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.json.ensure_ascii = False 

# Dữ liệu lưu trữ tạm thời trong RAM (Hạn chế đã biết: Mất toàn bộ dữ liệu khi restart server)
TASKS = {}

# Token demo (tương ứng với security: bearerAuth)
API_TOKEN = os.environ.get("TASKS_API_TOKEN", "demo-token")


# --- Xử lý lỗi theo chuẩn RFC 7807/9457 Problem Details ---
class ProblemException(Exception):
    """
    Ngoại lệ trả về thông tin lỗi chuẩn RFC 7807/9457 Problem Details.
    (RFC 7807/9457 chỉ định nghĩa cấu trúc body phản hồi, không quy định status code).
    """
    def __init__(self, status: int, title: str, detail: str):
        self.status = status
        self.title = title
        self.detail = detail
        self.type = f"https://api.example.vn/errors/{status}"
        self.instance = request.path


@app.errorhandler(ProblemException)
def handle_problem_exception(e: ProblemException):
    resp = jsonify({
        "type": e.type,
        "title": e.title,
        "status": e.status,
        "detail": e.detail,
        "instance": e.instance
    })
    resp.status_code = e.status
    resp.content_type = "application/problem+json"
    if e.status == 401:
        resp.headers["WWW-Authenticate"] = "Bearer"
    return resp


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    """
    Bắt các lỗi HTTP chuẩn của Flask/Werkzeug (404, 405, 413...) 
    để không bị handler(Exception) biến thành 500.
    """
    return handle_problem_exception(ProblemException(
        e.code or 500,
        e.name or "HTTP Error",
        e.description or ""
    ))


@app.errorhandler(Exception)
def handle_unexpected(e: Exception):
    return handle_problem_exception(
        ProblemException(500, "Server Error", "Lỗi máy chủ không xác định")
    )


# --- Middleware Xác thực (Bearer JWT) ---
@app.before_request
def require_bearer_token():
    # Chỉ bảo vệ các endpoint /v1/tasks, bỏ qua /docs và /openapi.json
    if not request.path.startswith("/v1/tasks"):
        return None
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise ProblemException(401, "Unauthorized", "Thiếu Bearer token")
    
    token = auth_header.split(" ", 1)[1]
    if token != API_TOKEN:
        raise ProblemException(401, "Unauthorized", "Token không hợp lệ")


# --- Hàm hỗ trợ Validate ---
def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def validate_task_input(body: dict, is_patch: bool = False):
    if not isinstance(body, dict):
        raise ProblemException(400, "Bad Request", "Body phải là JSON object")
    
    # PATCH: body không được rỗng (khớp minProperties: 1 trong OpenAPI spec)
    if is_patch and len(body) == 0:
        raise ProblemException(422, "Validation Error", "Body PATCH không được rỗng")
    
    # TaskInput: khi tạo mới (POST) thì title bắt buộc
    if not is_patch and "title" not in body:
        raise ProblemException(422, "Validation Error", "Trường 'title' là bắt buộc")
    
    if "title" in body:
        title = body.get("title")
        if not isinstance(title, str) or not (1 <= len(title) <= 200):
            raise ProblemException(422, "Validation Error", "title phải dài từ 1 đến 200 ký tự")
    
    if "status" in body and body["status"] not in ["open", "done"]:
        raise ProblemException(422, "Validation Error", "status phải là 'open' hoặc 'done'")
        
    if "priority" in body and body["priority"] not in ["low", "normal", "high"]:
        raise ProblemException(422, "Validation Error", "priority phải là 'low', 'normal', hoặc 'high'")
        
    if "dueDate" in body and body["dueDate"] is not None:
        try:
            datetime.date.fromisoformat(body["dueDate"])
        except (ValueError, TypeError):
            raise ProblemException(422, "Validation Error", "dueDate phải có định dạng YYYY-MM-DD")

    if "assigneeId" in body and body["assigneeId"] is not None:
        if not is_valid_uuid(body["assigneeId"]):
            raise ProblemException(422, "Validation Error", "assigneeId phải là định dạng UUID hợp lệ")


def get_task_or_404(task_id: str):
    if not is_valid_uuid(task_id):
        raise ProblemException(404, "Not Found", f"Không tìm thấy task với ID {task_id}")
    task = TASKS.get(task_id)
    if not task:
        raise ProblemException(404, "Not Found", f"Không tìm thấy task với ID {task_id}")
    return task


# --- Endpoints ---
@app.route("/v1/tasks", methods=["GET"])
def list_tasks():
    # Parse query params — bắt lỗi không phải số → 422
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
    except (ValueError, TypeError):
        raise ProblemException(422, "Validation Error", "limit và offset phải là số nguyên")

    status = request.args.get("status")

    if status and status not in ["open", "done"]:
        raise ProblemException(422, "Validation Error", "status param chỉ được là 'open' hoặc 'done'")
    
    if limit < 1 or limit > 100 or offset < 0:
        raise ProblemException(422, "Validation Error", "limit phải từ 1-100, offset phải >= 0")

    # Filter
    matched_tasks = [t for t in TASKS.values() if status is None or t["status"] == status]
    # Pagination: Sử dụng list slicing in-memory (O(1) truy cập, không có chi phí SQL OFFSET).
    # Hành vi: Nếu offset >= total, Python list slicing tự động trả về mảng rỗng `[]`.
    paginated_tasks = matched_tasks[offset : offset + limit]

    return jsonify({
        "items": paginated_tasks,
        "total": len(matched_tasks),
        "limit": limit,
        "offset": offset
    }), 200


@app.route("/v1/tasks", methods=["POST"])
def create_task():
    body = request.get_json(silent=True)
    validate_task_input(body, is_patch=False)
    
    task_id = str(uuid.uuid4())
    new_task = {
        "id": task_id,
        "title": body["title"],
        "status": body.get("status", "open"),
        "priority": body.get("priority", "normal"),
        "dueDate": body.get("dueDate"),
        "assigneeId": body.get("assigneeId")
    }
    
    TASKS[task_id] = new_task
    return jsonify(new_task), 201


@app.route("/v1/tasks/<task_id>", methods=["GET"])
def get_task(task_id: str):
    task = get_task_or_404(task_id)
    return jsonify(task), 200


@app.route("/v1/tasks/<task_id>", methods=["PATCH"])
def patch_task(task_id: str):
    task = get_task_or_404(task_id)
    body = request.get_json(silent=True)
    
    validate_task_input(body, is_patch=True) 
    
    task.update({
        k: v for k, v in body.items() 
        if k in ["title", "status", "priority", "dueDate", "assigneeId"]
    })
    
    return jsonify(task), 200


@app.route("/v1/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    get_task_or_404(task_id)
    del TASKS[task_id]
    return Response(status=204)


# --- Meta endpoints ---
@app.route("/openapi.json", methods=["GET"])
def openapi_json():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    spec_path = os.path.join(current_dir, "openapi.yaml")
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    return jsonify(spec)


@app.route("/docs", methods=["GET"])
def docs():
    swagger_html = """<!doctype html>
    <html lang="vi">
    <head>
      <meta charset="utf-8">
      <title>Tasks API - Swagger UI</title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
      <style>body { margin: 0; padding: 0; }</style>
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
      <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
              url: "/openapi.json",
              dom_id: "#swagger-ui",
              tryItOutEnabled: true,
              persistAuthorization: true,
              layout: "BaseLayout"
            });
        }
      </script>
    </body>
    </html>
    """
    return Response(swagger_html, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)