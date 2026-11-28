# AI Student Assistant

Khung Chrome Extension và backend Flask theo [tài liệu SOA](https://docs.google.com/document/d/1RdrPaiqRVWgo-E0XVKrm6I3uy3kMsrF4lWUEg6vdPHw/edit).

## Cấu trúc module

```text
backend/src/student_assistant/
├── modules/
│   ├── auth/               # Danh tính ứng dụng, cấp quyền (UC02)
│   ├── chat/               # RAG, hỏi đáp và tìm kiếm (UC03–04)
│   ├── documents/          # Nhập, lập chỉ mục, tóm tắt (UC02,04,05)
│   ├── quiz_review/        # Đánh giá tham khảo quiz (UC06)
│   ├── grade_planning/     # Mục tiêu và dự tính điểm (UC08–09)
│   ├── comments/           # Gợi ý comment (UC07)
│   └── recommendations/    # Gợi ý ôn tập (UC10)
├── api/                   # Đăng ký Blueprint của các module
├── shared/                # Validation dùng chung
├── integrations/          # LLM, embedding, API Portal được cho phép
├── factory.py             # Khởi tạo Flask và nạp model các module
├── extensions.py          # SQLAlchemy, Migrate dùng chung
├── config.py
├── errors.py
└── logging.py

extension/src/
├── sidebar/features/      # consent, chat, documents, quiz-review,
│                          # comments, grade-planning, recommendations
├── sidebar/components/
├── content/               # portal-adapters, extractors
├── background/            # messaging, storage
└── shared/                # constants, types, utils

contracts/                 # Hợp đồng REST và extension message
infrastructure/            # PostgreSQL + pgvector, container
backend/migrations/        # Migration chung cho ứng dụng
docs/                      # Kiến trúc, use case và bảng nhận module
tests/e2e/                 # Kiểm thử xuyên suốt
```

Mỗi thư mục nghiệp vụ chứa `api.py`, `service.py`, `schemas.py`; module có dữ liệu riêng có thêm `repository.py`, `models.py`. Document sở hữu `vector_repository.py` để Chat tái sử dụng. Recommendation sở hữu bảng phân tích, bằng chứng, chủ đề và đề xuất; Comment sinh kết quả tức thời nên không có bảng riêng. Các model hiện mô tả đủ 18 bảng theo ERD, kèm migration đầu tiên `0001_initial`.

Mỗi thành viên nhận một thư mục trong `modules/` và phần UI tương ứng. Backend vẫn là một ứng dụng Flask, các module dùng chung cơ sở dữ liệu và hạ tầng AI.

## Chạy nhanh cho cả nhóm bằng Docker

Cài Docker Desktop, bật chế độ Linux containers và mở terminal tại thư mục gốc của repo:

```sh
docker compose up --build -d
docker compose exec backend python -m flask --app wsgi:app db upgrade
docker compose exec backend python -m flask --app wsgi:app db current
# Tùy chọn: thêm dữ liệu phát triển mẫu, giữ nguyên bản ghi đã tồn tại.
docker compose exec backend python -m flask --app wsgi:app db-seed-demo
```

- Swagger UI: [http://localhost:8000/docs/](http://localhost:8000/docs/).
- Đặc tả OpenAPI: [http://localhost:8000/openapi/openapi.yaml](http://localhost:8000/openapi/openapi.yaml).
- PostgreSQL có pgvector: `localhost:5432`; database và tài khoản mặc định là `ai_student_assistant`, mật khẩu phát triển là `student_assistant_local`.

Không cần cài Python, PostgreSQL hoặc Node.js trên máy khi chạy bằng Docker. Lần đầu Docker tải image và cài phụ thuộc. Backend chờ PostgreSQL sẵn sàng rồi khởi động; cần chạy `db upgrade` để tạo bảng. Dữ liệu database được giữ trong volume khi dừng container. Seed chỉ là fixture phát triển: tài liệu ở trạng thái `PENDING`, không có vector hay câu trả lời AI giả và không cung cấp token đăng nhập.

Nếu cổng 8000 hoặc 5432 đang được sử dụng, sao chép `.env.docker.example` thành `.env` ở thư mục gốc rồi đổi `API_PORT` hoặc `POSTGRES_PORT`. Ví dụ `API_PORT=8001` thì mở `http://localhost:8001/docs/`. File `backend/.env` dành cho chạy Python cục bộ, không được dùng làm cấu hình Docker.

Xem [hướng dẫn Docker](infrastructure/docker/README.md) để đọc log, chạy test, quản lý database và cập nhật mã nguồn. Các endpoint nghiệp vụ vẫn đang là khung, chưa được triển khai.

Xem [thiết kế database](docs/database.md) để biết bảng của từng module, khóa ngoại và cách đổi schema. Cột embedding dùng `vector` chưa cố định chiều; nhóm cần chốt model/kích thước trước khi thêm chỉ mục ANN và luôn lọc cùng model/chiều khi truy vấn.

## Phối hợp phát triển

1. Nhận module tại [bảng chia việc](docs/modules.md), xem [kiến trúc](docs/architecture.md) và [UC01–UC10](docs/use-cases.md).
2. Cài và chạy theo [backend/README.md](backend/README.md).
3. Chốt request/response tại [OpenAPI](backend/openapi/openapi_modular/openapi_modular/openapi.yaml) và message tại `contracts/extension-messages/` trước khi ghép UI/backend. Xem [hướng dẫn bundle/lint](backend/openapi/openapi_modular/openapi_modular/README.md).
4. Thêm nghiệp vụ và kiểm thử trong module mình nhận; phối hợp khi đổi cấu hình chung, đăng ký Blueprint hoặc migration.

Phần database đã có model, migration và seed; API nghiệp vụ, cơ chế xác thực/phân quyền tại API, provider AI và extension cài chạy được vẫn cần triển khai. Bảng phiên/consent không tự cung cấp cơ chế kiểm tra quyền. Chỉ xử lý dữ liệu Portal sau cấp quyền; không thu mật khẩu/token Portal, không tự sửa điểm hay gửi comment. API key AI đặt ở backend. RAG phải giới hạn theo người dùng/môn và trích dẫn nguồn có thật; tính điểm dùng công thức và trọng số thực tế.
