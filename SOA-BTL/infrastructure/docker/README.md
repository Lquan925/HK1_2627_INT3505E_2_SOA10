# Chạy dự án bằng Docker cho cả nhóm

Chạy tất cả lệnh bên dưới từ thư mục gốc repo, nơi chứa `compose.yaml`. Cần Docker Desktop ở chế độ Linux containers trên Windows/macOS, hoặc Docker Engine cùng Compose v2 trên Linux. Không cần cài Python, PostgreSQL hay Node.js riêng trên máy.

## Khởi động

```sh
docker compose up --build -d
docker compose ps
docker compose exec backend python -m flask --app wsgi:app db upgrade
docker compose exec backend python -m flask --app wsgi:app db current
```

Compose khởi động hai dịch vụ:

| Dịch vụ | Vai trò | Địa chỉ mặc định trên máy |
| --- | --- | --- |
| `backend` | Flask chạy bằng Waitress, kèm Swagger UI và đặc tả OpenAPI | `http://localhost:8000/docs/` |
| `db` | PostgreSQL 17, có pgvector 0.8.7 | `localhost:5432` |

Lần đầu có thể mất vài phút để tải image và cài thư viện. Backend chờ kiểm tra PostgreSQL thành công trước khi khởi động. Kiểm tra trạng thái backend xác nhận trang Swagger UI trả HTTP thành công, không thay thế kiểm tra nghiệp vụ hoặc truy vấn database.

Các cổng chỉ mở trên máy cục bộ. Migration `0001_initial` tạo 18 bảng theo ERD; việc khởi động backend không tự áp dụng migration. Các endpoint nghiệp vụ, kể cả tạo phiên/cấp quyền, chưa triển khai vẫn trả `404`; Swagger UI và bộ đặc tả đã hoạt động. Chưa cần API key AI để mở tài liệu hoặc tạo schema.

## Cấu hình

Các giá trị mặc định trong `compose.yaml` cho phép khởi động ngay. Nếu cần thay đổi, sao chép `.env.docker.example` thành `.env` tại thư mục gốc:

```powershell
Copy-Item .env.docker.example .env
```

Trên Linux/macOS, dùng `cp .env.docker.example .env`. Nếu đã có `.env`, cập nhật file hiện có thay vì sao chép đè.

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `API_PORT` | `8000` | Cổng backend trên máy |
| `POSTGRES_PORT` | `5432` | Cổng database trên máy |
| `POSTGRES_DB` | `ai_student_assistant` | Tên database được tạo lần đầu |
| `POSTGRES_USER` | `ai_student_assistant` | Tài khoản database |
| `POSTGRES_PASSWORD` | `student_assistant_local` | Mật khẩu phát triển cục bộ |
| `SECRET_KEY` | Trống | Cấu hình khóa khi triển khai phiên/xác thực |
| `LLM_*`, `EMBEDDING_*` | Trống | Provider, model và API key khi triển khai tích hợp AI |

Ví dụ, nếu đã chạy Flask trên cổng 8000, đặt `API_PORT=8001`, sau đó chạy lại Compose và mở `http://localhost:8001/docs/`. Thay đổi cổng công bố trên máy không thay đổi cổng nội bộ: backend gọi `db:5432`, Swagger UI gọi `/api/v1` trên cùng máy chủ.

Trên máy đang triển khai repo này, cổng 5432 đã có dịch vụ khác sử dụng nên file `.env` cục bộ ở thư mục gốc đặt `POSTGRES_PORT=5433`. Kết nối từ pgAdmin/psql trên máy dùng `localhost:5433`; các máy thành viên khác vẫn dùng mặc định `localhost:5432` nếu không đổi cấu hình. `.env` được Git bỏ qua và không làm thay đổi cấu hình mặc định của nhóm. Container backend/tests vẫn kết nối `db:5432`.

File `.env` ở thư mục gốc được Compose đọc để điền biến; `backend/.env` dành cho chạy Python trực tiếp. Các file môi trường và khóa riêng không được đưa vào image. Backend nhận thông tin database qua các biến `DB_*`, giữ nguyên ký tự đặc biệt trong mật khẩu mà không phải ghép chuỗi URL. Biến `DATABASE_URL` được đặt trống trong container để không sử dụng nhầm địa chỉ `localhost` từ cấu hình cục bộ.

Thông tin tài khoản PostgreSQL chỉ được áp dụng tự động khi tạo volume dữ liệu lần đầu. Nếu đổi tên database, tài khoản hoặc mật khẩu sau đó, cần cập nhật database hiện có tương ứng; chỉ sửa `.env` không thay đổi tài khoản đã lưu.

## Cập nhật mã nguồn và xem log

```sh
docker compose up --build -d backend
docker compose logs -f backend db
```

Image chứa bản sao mã nguồn và OpenAPI tại thời điểm build; sửa mã hoặc YAML thì build lại backend. Khi đổi phụ thuộc, cập nhật `backend/pyproject.toml` rồi chạy lại lệnh build. `requirements.txt` và `requirements-dev.txt` đọc từ file này để tránh lệch danh sách phụ thuộc.

Đặc tả OpenAPI, các tệp YAML mô-đun và thư mục migration được sao chép vào image. Dockerfile đặt `OPENAPI_SPEC_DIR` trỏ tới bộ đặc tả trong container nên Swagger UI hoạt động ngay sau khi build.

## Chạy kiểm thử

Dịch vụ `tests` chỉ chạy khi được gọi, không khởi động cùng bộ ứng dụng mặc định. Image kiểm thử cài thêm phụ thuộc phát triển. Các test cấu hình/Swagger có thể chạy không cần PostgreSQL hay khóa AI:

```sh
docker compose --profile test build tests
docker compose --profile test run --rm tests
```

Để chạy cả kiểm thử migration và ràng buộc trên PostgreSQL/pgvector thật:

```sh
docker compose build tests
docker compose -f compose.yaml -f compose.database-tests.yaml run --rm tests
```

File override `compose.database-tests.yaml` truyền cấu hình bằng `TEST_DB_HOST`, `TEST_DB_PORT`, `TEST_DB_NAME`, `TEST_DB_USER`, `TEST_DB_PASSWORD`; mật khẩu được truyền riêng thay vì nội suy vào URL. Khi chạy Python trực tiếp, có thể dùng các trường `TEST_DB_*` này hoặc `TEST_DATABASE_URL`. Tài khoản cần quyền tạo schema và bật pgvector nếu extension chưa có.

Mỗi lượt kiểm thử tạo schema tên ngẫu nhiên và chỉ dọn schema do lượt đó tạo; giữ nguyên bảng ứng dụng và volume dữ liệu. Bộ kiểm thử kiểm tra upgrade/downgrade migration, độ khớp model với schema, seed chạy lặp, lưu/đọc vector và các ràng buộc nghiệp vụ/owner/môn. Lệnh trả mã thoát khác 0 nếu kiểm thử thất bại. Test PostgreSQL bị bỏ qua khi thiếu cấu hình kết nối không phải bằng chứng migration đã chạy trên PostgreSQL.

## Database và migration

Mở phiên SQL rồi kiểm tra pgvector đã được bật:

```sh
docker compose exec db psql -U ai_student_assistant -d ai_student_assistant
```

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```

Lệnh mở phiên SQL dùng tên mặc định; đổi tham số nếu đã thay `POSTGRES_USER` hoặc `POSTGRES_DB`.

Script `infrastructure/postgres/init/001-enable-pgvector.sql` được PostgreSQL chạy khi khởi tạo volume trống. Script chỉ bật extension; revision `0001_initial` tạo bảng nghiệp vụ. Áp dụng revision, kiểm tra trạng thái và tùy chọn thêm dữ liệu mẫu:

```sh
docker compose exec backend python -m flask --app wsgi:app db upgrade
docker compose exec backend python -m flask --app wsgi:app db current
docker compose exec backend python -m flask --app wsgi:app db-seed-demo
```

`db current` phải hiển thị `0001_initial`. Seed chỉ dành cho phát triển, thêm bản ghi thiếu và không thay đổi bản ghi đã tồn tại. Nó tạo fixture hai phiên/hai môn với consent, metadata tài liệu `PENDING`, mục tiêu điểm và tin nhắn người dùng; không tạo embedding/câu trả lời AI và không lưu hoặc in token đăng nhập.

Việc tạo/chỉnh sửa revision thực hiện trên mã nguồn tại máy phát triển theo [hướng dẫn migration](../../backend/migrations/README.md), sau đó build lại image. Thay đổi file bên trong container không được tự ghi về repo. Không tự chạy `db migrate` khi khởi động ứng dụng.

Cột embedding hiện là `vector` chưa cố định D; cần thống nhất model/chiều trước khi thêm ANN index. Truy vấn vector phải dùng cùng model và số chiều với dữ liệu. Xem [thiết kế database](../../docs/database.md) để biết bảng, khóa ngoại và giới hạn của seed.

## Dừng ứng dụng và giữ dữ liệu

```sh
docker compose down
```

Volume `postgres_data` giữ dữ liệu để dùng lại ở lần khởi động sau. Khi cập nhật schema, build lại backend và áp dụng migration vào volume hiện có; không cần xóa hoặc tạo lại volume.

## Các file liên quan

- [`../../compose.yaml`](../../compose.yaml): các dịch vụ và mạng nội bộ.
- [`../../compose.database-tests.yaml`](../../compose.database-tests.yaml): cấu hình chạy kiểm thử PostgreSQL trong schema riêng.
- [`../../backend/Dockerfile`](../../backend/Dockerfile): mục tiêu `runtime` và `test`.
- [`../../.dockerignore`](../../.dockerignore): giới hạn dữ liệu đưa vào quá trình build.
- [`../../.env.docker.example`](../../.env.docker.example): cấu hình mẫu của Compose.
- [`../../backend/requirements.txt`](../../backend/requirements.txt) và [`../../backend/requirements-dev.txt`](../../backend/requirements-dev.txt): cài phụ thuộc trực tiếp bằng pip, chạy từ thư mục `backend/`.
