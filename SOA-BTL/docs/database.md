# Database theo ERD

Schema bám theo [`ai-student-assistant-extension-erd-updated.svg`](../ai-student-assistant-extension-erd-updated.svg) và đặc tả nguồn [DOT](../ai-student-assistant-extension-erd-updated.dot). Có 18 bảng SQLAlchemy, revision Alembic đầu tiên `0001_initial` và lệnh seed dữ liệu phát triển. API nghiệp vụ, xác thực/phân quyền ở API và AI client chưa được triển khai.

## Bảng theo module sở hữu

| Module | Bảng | Vai trò |
| --- | --- | --- |
| `auth` | `client_sessions`, `data_consents`, `consent_courses` | Phiên ẩn danh, quyền theo loại dữ liệu/mục đích và phạm vi môn |
| `documents` | `documents`, `document_access`, `document_chunks` | Metadata tài liệu, lần kiểm tra nguồn gần nhất, nội dung chunk và vector theo thế hệ chỉ mục |
| `chat` | `chat_sessions`, `chat_messages`, `chat_citations`, `message_documents` | Hội thoại, tin nhắn, trích dẫn chunk và toàn bộ phạm vi tài liệu đã dùng |
| `quiz_review` | `quiz_reviews`, `quiz_review_items` | Đánh giá tham khảo quiz và từng câu hỏi |
| `grade_planning` | `grade_goals` | Mục tiêu điểm, phạm vi và quy tắc tính |
| `recommendations` | `knowledge_topics`, `learning_analyses`, `learning_evidence`, `learning_recommendations`, `analysis_documents` | Chủ đề, phân tích, bằng chứng, đề xuất và các tài liệu nguồn |

Comment suggestion sinh kết quả tức thời, không có bảng riêng. Phép tính điểm UC09 dùng mục tiêu đã lưu và dữ liệu đầu vào, không lưu riêng danh sách thành phần hoặc kết quả tính.

## Tạo bảng và dữ liệu phát triển

Từ thư mục gốc repo với Docker Desktop/Engine đã sẵn sàng:

```sh
docker compose up --build -d
docker compose exec backend python -m flask --app wsgi:app db upgrade
docker compose exec backend python -m flask --app wsgi:app db current
docker compose exec backend python -m flask --app wsgi:app db-seed-demo
```

`db current` phải hiển thị `0001_initial`. `db upgrade` chỉ chạy các revision còn thiếu. Với Python trực tiếp, cấu hình `DATABASE_URL`, chạy các lệnh Flask tương đương từ `backend/`. PostgreSQL phải có pgvector; xem [migration](../backend/migrations/README.md) và [Docker](../infrastructure/docker/README.md).

Máy đang triển khai repo này dùng cổng host `5433` vì `5432` đang được sử dụng: file `.env` cục bộ ở thư mục gốc đặt `POSTGRES_PORT=5433` và được Git bỏ qua. Dùng `localhost:5433` khi kết nối từ công cụ trên máy này; các máy khác mặc định vẫn là `localhost:5432`. Kết nối giữa các container luôn dùng `db:5432`.

Seed chỉ phục vụ phát triển: có hai phiên/hai môn, consent tài liệu, metadata tài liệu, mục tiêu điểm và tin nhắn người dùng. ID fixture cố định; chạy lại chỉ thêm bản ghi thiếu, không ghi đè thay đổi trước đó. Các token ngẫu nhiên bị bỏ sau khi hash nên phiên mẫu không phải thông tin đăng nhập API. Tài liệu giữ trạng thái `PENDING`; không tạo vector, câu trả lời AI hoặc kết quả review giả.

## Khóa, quan hệ và ràng buộc

- ID nội bộ là UUID; mã môn, mã tài liệu và mã quiz của Portal giữ dạng text. SQLAlchemy sinh UUID khi insert qua model; SQL trực tiếp phải tự cung cấp ID.
- Thời gian là `timestamptz`; điểm là `numeric` để không ép kiểu float. Trường `updated_at` có mặc định khi tạo; `onupdate` chỉ hoạt động với các câu cập nhật do SQLAlchemy quản lý. Client SQL trực tiếp phải tự đặt timestamp khi sửa.
- Tài nguyên cấp cao thuộc `client_sessions`; owner của bảng con suy ra từ cha. Các liên kết nguồn phải cùng owner và đúng môn; service vẫn cần kiểm tra scope trước khi dùng dữ liệu.
- Tài liệu duy nhất theo phiên/môn/mã ngoài; chunk duy nhất theo tài liệu/thế hệ/vị trí. `active_index_generation` chọn thế hệ hiện hành; không xóa chunk cũ đang được citation tham chiếu.
- Consent duy nhất theo phiên/loại dữ liệu/mục đích. Không có bản ghi nghĩa là chưa cấp quyền. Phạm vi môn và category-purpose phải nhất quán.
- Mục tiêu điểm kiểm tra thang điểm và phạm vi; hai partial unique index xử lý mục tiêu toàn môn có `quiz_group_id=NULL` và mục tiêu theo nhóm quiz.
- Khóa ngoại sở hữu dùng cascade để xóa dữ liệu phụ thuộc cùng cây. Các tham chiếu nguồn/citation dùng ràng buộc bảo toàn nguồn, nên xóa tài liệu/chunk đang được tham chiếu có thể bị chặn; phải xử lý dữ liệu dẫn xuất trước. Không dùng xóa trực tiếp để thay cơ chế thu hồi consent.

Các ràng buộc database bảo vệ cấu trúc và tính nhất quán của dữ liệu. Chúng không xác minh token người gọi, quyền truy cập Portal hoặc consent hiện hành của một request. API/service phải kiểm tra phiên còn hiệu lực, owner, môn, mục đích, quyền nguồn và consent trước khi đọc/lưu/trả dữ liệu, kể cả lịch sử và kết quả suy ra.

## Embedding chưa cố định chiều

ERD ghi `vector(D)` nhưng chưa chọn model/D. Schema hiện dùng `vector` không cố định chiều và chưa tạo ANN index để không tự giả định cấu hình AI. Trước khi truy vấn vector, service phải chọn dữ liệu có cùng `embedding_model` và cùng số chiều với embedding của câu hỏi; không so sánh vector khác model hoặc khác chiều.

Khi nhóm đã chốt provider/model/D, thêm migration cho ràng buộc chiều và chỉ mục phù hợp, kèm kế hoạch tạo lại embedding nếu đổi model. Không coi dữ liệu seed là chỉ mục RAG đã sẵn sàng.

## Thay đổi schema trong nhóm

Mỗi chủ module sửa model của mình, thống nhất khóa ngoại với module liên quan và gửi thay đổi cho người điều phối migration. Commit model và revision cùng nhau. Không chỉnh revision đã áp dụng trên máy khác; tạo revision tiếp theo. Cập nhật schema bằng migration trên volume hiện có, không cần xóa volume PostgreSQL.

## Kiểm thử PostgreSQL

Từ thư mục gốc, chạy bộ kiểm thử đầy đủ với PostgreSQL thật bằng:

```sh
docker compose build tests
docker compose -f compose.yaml -f compose.database-tests.yaml run --rm tests
```

Override truyền riêng các trường `TEST_DB_HOST`, `TEST_DB_PORT`, `TEST_DB_NAME`, `TEST_DB_USER`, `TEST_DB_PASSWORD` để không phải ghép mật khẩu vào URL. Chạy Python trực tiếp cũng có thể cấu hình `TEST_DATABASE_URL`. Tài khoản cần quyền tạo schema và bật pgvector nếu extension chưa có.

Các test tạo schema ngẫu nhiên, chạy migration/fixture trong schema đó và chỉ xóa schema của chính lượt chạy khi dọn dẹp. Bảng ứng dụng và volume PostgreSQL được giữ nguyên. Phạm vi kiểm tra gồm migration upgrade/downgrade, không lệch schema so với model, seed chạy lại không ghi đè dữ liệu, vector round-trip và các ràng buộc điểm, owner/môn, consent, thế hệ chỉ mục và nguồn trích dẫn. Nếu thiếu cấu hình, các test cần PostgreSQL bị bỏ qua; hãy kiểm tra kết quả để phân biệt test thực sự chạy với test bị bỏ qua.
