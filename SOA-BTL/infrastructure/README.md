# Hạ tầng

Hệ thống dùng PostgreSQL + pgvector để lưu dữ liệu quan hệ và vector embedding. Cấu hình chạy cục bộ đã có trong [compose.yaml](../compose.yaml).

- `postgres/init/001-enable-pgvector.sql`: bật extension `vector` trong cơ sở dữ liệu đích. PostgreSQL cần được cài pgvector trước; tài khoản chạy SQL phải có quyền tạo extension phù hợp. File này chưa tạo bảng hoặc chỉ mục nghiệp vụ.
- [`../backend/Dockerfile`](../backend/Dockerfile): image Python 3.13 chạy Flask bằng Waitress, có mục tiêu build riêng cho kiểm thử.
- [`../compose.yaml`](../compose.yaml): backend, PostgreSQL 17 với pgvector 0.8.7, kiểm tra trạng thái sẵn sàng và volume dữ liệu.
- [`docker/README.md`](docker/README.md): cách chạy, cấu hình, đọc log, kiểm thử và quản lý database cho cả nhóm.

Migrations nghiệp vụ đặt tại [`../backend/migrations/`](../backend/migrations/README.md), dùng Alembic qua Flask-Migrate. Chốt mô hình embedding và kích thước vector trước khi tạo cột vector/chỉ mục. Không commit mật khẩu hay dữ liệu thật của sinh viên.
