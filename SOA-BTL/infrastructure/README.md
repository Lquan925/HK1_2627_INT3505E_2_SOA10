# Hạ tầng

Theo tài liệu, hệ thống dùng PostgreSQL + pgvector để lưu dữ liệu quan hệ và vector embedding.

- `postgres/init/001-enable-pgvector.sql`: bật extension `vector` trong cơ sở dữ liệu đích. PostgreSQL cần được cài pgvector trước; tài khoản chạy SQL phải có quyền tạo extension phù hợp. File này chưa tạo bảng hoặc chỉ mục nghiệp vụ.
- `docker/`: dành cho Dockerfile và Compose khi triển khai backend Flask; chưa có cấu hình container hoặc image/version được chọn.

Migrations nghiệp vụ đặt tại [`../backend/migrations/`](../backend/migrations/README.md), dùng Alembic qua Flask-Migrate. Chốt mô hình embedding và kích thước vector trước khi tạo cột vector/chỉ mục. Không commit mật khẩu hay dữ liệu thật của sinh viên.
