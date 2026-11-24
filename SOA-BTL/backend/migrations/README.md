# Database migrations

Thư mục đã có cấu hình Alembic cho Flask-Migrate; không cần chạy lại `flask db init`. Chưa có revision hoặc bảng nghiệp vụ.

Sau khi khai báo model và cấu hình PostgreSQL, chạy từ `backend/` trong môi trường đã cài dependency:

```powershell
flask --app wsgi:app db migrate -m "Create initial tables"
# Đọc và chỉnh revision được sinh trong versions/ trước khi áp dụng.
flask --app wsgi:app db upgrade
```

Lệnh `db migrate` cần kết nối database. Script bật pgvector đặt tại `../../infrastructure/postgres/init/001-enable-pgvector.sql`; cần cài pgvector và bật extension trong database đích trước khi tạo cột vector.

Khi dùng Docker Compose, pgvector được bật lúc khởi tạo database lần đầu. Tạo và kiểm tra revision trên mã nguồn ở máy phát triển, build lại backend rồi chạy `docker compose exec backend python -m flask --app wsgi:app db upgrade` từ thư mục gốc repo. Xem [hướng dẫn Docker](../../infrastructure/docker/README.md).
