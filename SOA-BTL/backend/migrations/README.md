# Database migrations

Thư mục đã có cấu hình Alembic cho Flask-Migrate và revision đầu tiên `0001_initial`, tạo 18 bảng theo ERD. Không cần chạy lại `flask db init` hoặc tạo lại revision đầu tiên trên mỗi máy.

Sau khi cấu hình PostgreSQL có pgvector và cài dependency, chạy từ `backend/`:

```powershell
flask --app wsgi:app db upgrade
flask --app wsgi:app db current
# Tùy chọn, chỉ cho database phát triển:
flask --app wsgi:app db-seed-demo
```

`db current` phải hiển thị revision `0001_initial` sau khi áp dụng. `db upgrade` có thể chạy lại: Alembic chỉ áp dụng revision còn thiếu. Seed thêm fixture phát triển còn thiếu và giữ nguyên bản ghi hiện có; tài liệu mẫu ở trạng thái `PENDING`, chưa có embedding hay kết quả AI. Token của phiên mẫu không được lưu hoặc in ra nên seed không cung cấp thông tin đăng nhập API.

Khi dùng Docker Compose, chạy từ thư mục gốc repo:

```sh
docker compose up --build -d
docker compose exec backend python -m flask --app wsgi:app db upgrade
docker compose exec backend python -m flask --app wsgi:app db current
docker compose exec backend python -m flask --app wsgi:app db-seed-demo
```

Image PostgreSQL phải có pgvector; script bật extension đặt tại `../../infrastructure/postgres/init/001-enable-pgvector.sql`. Script init của PostgreSQL chỉ chạy khi tạo volume lần đầu. Tài khoản áp dụng migration cần đủ quyền tạo các đối tượng mà revision yêu cầu trong database đích.

## Khi thay đổi model

1. Cập nhật model trong module sở hữu dữ liệu và thống nhất ảnh hưởng tới các module khác.
2. Trên database phát triển đã ở revision hiện tại, chạy `flask --app wsgi:app db migrate -m "Describe schema change"`.
3. Đọc revision được sinh; bổ sung SQL cho trigger hoặc ràng buộc mà autogenerate không quản lý. Không sửa revision đã được chia sẻ và áp dụng trên các máy khác.
4. Kiểm thử revision trên database thử riêng, rồi commit model và revision cùng nhau.
5. Với Docker, build lại backend trước khi chạy `db upgrade`; sửa file trong container không tự cập nhật repo.

Cột `document_chunks.embedding` hiện là `vector` không cố định số chiều vì nhóm chưa chọn provider. Phải dùng cùng model và chiều vector khi truy vấn; chỉ thêm `vector(D)`/chỉ mục ANN qua revision tiếp theo sau khi chốt cấu hình và kế hoạch chuyển dữ liệu.

UUID được sinh bởi SQLAlchemy khi insert qua model; client SQL trực tiếp phải cung cấp ID. `updated_at` có giá trị mặc định khi tạo, nhưng cập nhật tự động là hành vi ORM (`onupdate`); câu SQL trực tiếp phải tự đặt `updated_at`.

Model và migration chưa triển khai API xác thực, consent enforcement hoặc nghiệp vụ AI. Các kiểm tra quyền hiện hành vẫn phải được bổ sung tại service/API. Xem [database](../../docs/database.md) và [hướng dẫn Docker](../../infrastructure/docker/README.md).
