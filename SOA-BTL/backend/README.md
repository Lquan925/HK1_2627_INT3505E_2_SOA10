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

Hiện các file là scaffold; chưa có route nghiệp vụ hay bảng dữ liệu. OpenAPI có `paths: {}` và đường dẫn chưa khai báo trả 404. Xem [bảng chia việc](../docs/modules.md).

## Cài và khởi động khung Flask

Cần Python 3.11 trở lên. Chạy từ thư mục gốc repository trong PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Điền DATABASE_URL và các giá trị cục bộ trong .env.
.\.venv\Scripts\python.exe -m flask --app wsgi:app run
```

CLI mặc định nghe tại `127.0.0.1:8000` khi dùng `.env` mẫu. Factory nạp `.env` từ thư mục làm việc, vì vậy chạy các lệnh trong `backend/`. Khởi tạo app chưa truy vấn PostgreSQL; thao tác dữ liệu và migration cần PostgreSQL đã được cấu hình.

Hướng dẫn migration tại [`migrations/README.md`](migrations/README.md). Chỉ thêm thông tin xác thực riêng của ứng dụng/AI provider vào `.env`; không thêm thông tin đăng nhập Portal.

Mẫu factory/extension dựa trên [Flask Application Factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/) và [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/).
