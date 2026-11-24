# Student Assistant API

Backend Flask tổ chức theo module nghiệp vụ tại `src/student_assistant/modules/`:

| Thư mục | Use case |
| --- | --- |
| `auth/` | Danh tính ứng dụng và quyền dữ liệu (UC02) |
| `chat/` | RAG, hỏi đáp, tìm kiếm (UC03–04) |
| `documents/` | Nhập, chia đoạn, lập chỉ mục và tóm tắt (UC02,04,05) |
| `quiz_review/` | Đánh giá quiz đã chấm (UC06) |
| `grade_planning/` | Mục tiêu và tính điểm (UC08–09) |
| `comments/` | Gợi ý phản hồi (UC07) |
| `recommendations/` | Gợi ý ôn tập (UC10) |

Trong từng module: `api.py` nhận HTTP; `schemas.py` kiểm tra request/response; `service.py` xử lý nghiệp vụ; `repository.py` và `models.py` quản lý dữ liệu nếu module sở hữu dữ liệu. Document có thêm `vector_repository.py`. Comment/Recommendation tái sử dụng dữ liệu Quiz Review và Document.

`api/__init__.py` đăng ký Blueprint; `factory.py` nạp model từ từng module để SQLAlchemy/Migrate thấy metadata. Các URL `/api/v1/...` giữ nguyên. `shared/validation.py` dành cho validation dùng chung; `integrations/` chứa client AI. Model dùng `db` từ `extensions.py`.

Hiện các file là scaffold; chưa có route nghiệp vụ hay bảng dữ liệu. [OpenAPI](openapi/openapi_modular/openapi_modular/openapi.yaml) mô tả hợp đồng dự kiến, chưa phải các endpoint đã triển khai; các đường dẫn nghiệp vụ hiện trả 404. Xem [hướng dẫn bundle/lint](openapi/openapi_modular/openapi_modular/README.md) và [bảng chia việc](../docs/modules.md).

## Chạy bằng Docker

Từ thư mục gốc repo, chạy `docker compose up --build -d`, sau đó mở `http://localhost:8000/docs/`. Compose khởi động backend bằng Waitress và PostgreSQL có pgvector. Không cần tạo môi trường Python trên máy. Xem [hướng dẫn Docker](../infrastructure/docker/README.md) để đổi cổng, chạy test và quản lý database.

## Cài và khởi động Flask trực tiếp bằng Python

Cần Python 3.11 trở lên. Chạy từ thư mục gốc repository trong PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
# Điền DATABASE_URL và các giá trị cục bộ trong .env.
.\.venv\Scripts\python.exe -m flask --app wsgi:app run
```

CLI mặc định nghe tại `127.0.0.1:8000` khi dùng `.env` mẫu. Factory nạp `.env` từ thư mục làm việc, vì vậy chạy các lệnh trong `backend/`. Khởi tạo app chưa truy vấn PostgreSQL; thao tác dữ liệu và migration cần PostgreSQL đã được cấu hình.

Trên Linux/macOS, thay `.\.venv\Scripts\python.exe` bằng `.venv/bin/python` và dùng `cp .env.example .env` để sao chép cấu hình.

`requirements.txt` cài ứng dụng cùng phụ thuộc chạy; `requirements-dev.txt` cài thêm công cụ kiểm thử. Cả hai đọc danh sách phụ thuộc từ `pyproject.toml`, tránh duy trì nhiều danh sách riêng. Chạy các lệnh `pip` từ thư mục `backend/`. Khi thêm thư viện, sửa `pyproject.toml` rồi cài lại requirements hoặc build lại image.

Để chạy bằng cùng máy chủ WSGI như Docker, từ thư mục `backend/` dùng `.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 wsgi:app` trên Windows hoặc `.venv/bin/waitress-serve --listen=127.0.0.1:8000 wsgi:app` trên Linux/macOS.

## Xem và thử API bằng Swagger UI

Sau khi khởi động Flask, mở [Swagger UI](http://127.0.0.1:8000/docs/). Trang tài liệu đọc trực tiếp [đặc tả OpenAPI](http://127.0.0.1:8000/openapi/openapi.yaml) và các tệp YAML được tham chiếu; không cần gộp đặc tả hoặc cài Node.js để xem tài liệu. Các tệp giao diện được phục vụ cùng Flask, không tải từ CDN.

Nếu đã cài backend trước khi thêm Swagger UI, chạy lại `python -m pip install -r requirements-dev.txt` trong môi trường ảo, từ thư mục `backend/`, để cài các phụ thuộc mới.

Nút **Try it out** gửi yêu cầu tới `/api/v1` trên cùng máy chủ đang phục vụ đặc tả, kể cả khi thay đổi cổng chạy Flask. Khi triển khai endpoint tạo phiên, dùng `POST /client-sessions` để lấy `session_token`, rồi bấm **Authorize** và nhập token để gửi header `X-Session-Token`. Token chỉ được giữ trong bộ nhớ của trang, không lưu qua lần tải lại. Backend hiện vẫn chưa triển khai các endpoint nghiệp vụ nên các yêu cầu thử tương ứng trả `404`.

Mặc định, Flask tìm bộ đặc tả trong `backend/openapi/openapi_modular/openapi_modular/` dựa trên vị trí mã nguồn. Khi triển khai bằng gói wheel, cần sao chép toàn bộ thư mục này vào máy chủ và đặt biến `OPENAPI_SPEC_DIR` thành đường dẫn tuyệt đối tới thư mục chứa `openapi.yaml`; giữ nguyên các thư mục `paths`, `schemas` và `common` bên trong.

Kiểm tra phần tích hợp bằng lệnh sau từ thư mục `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Hướng dẫn migration tại [`migrations/README.md`](migrations/README.md). Chỉ thêm thông tin xác thực riêng của ứng dụng/AI provider vào `.env`; không thêm thông tin đăng nhập Portal.

Mẫu factory/extension dựa trên [Flask Application Factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/) và [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/).
