# Bảng nhận module cho nhóm

Điền tên người phụ trách vào bảng khi chia việc. Một người có thể nhận nhiều module; mỗi module nghiệp vụ nên có một người chịu trách nhiệm xuyên suốt API → service → repository và phối hợp UI tương ứng.

| Module | Phạm vi/file chính | Đầu ra cần bàn giao | Phụ trách |
| --- | --- | --- | --- |
| Extension nền tảng (UC01–02) | `extension/src/sidebar/components/`, `content/`, `background/`, `shared/` | Mở/đóng sidebar, adapter Portal, consent, message và API client | Chưa phân công |
| Gateway & bảo mật | `modules/auth/api.py`, `shared/validation.py`, `modules/auth/repository.py`, `modules/auth/models.py` | Danh tính ứng dụng, kiểm tra quyền/đầu vào, lỗi API thống nhất | Chưa phân công |
| RAG / Chat (UC03–04) | `modules/chat/api.py`, `modules/chat/service.py`, `modules/chat/repository.py`, `modules/documents/vector_repository.py`, `modules/chat/models.py`, UI `features/chat/` | Hỏi đáp/tìm kiếm theo người dùng và môn, lịch sử, trích dẫn nguồn | Chưa phân công |
| Document (UC02,04,05) | `modules/documents/api.py`, `modules/documents/service.py`, `modules/documents/repository.py`, `modules/documents/models.py`, UI `features/documents/` | Nhập, trích xuất, chia đoạn, embedding/lập chỉ mục, tóm tắt | Chưa phân công |
| Quiz Review (UC06) | `modules/quiz_review/api.py`, `modules/quiz_review/service.py`, `modules/quiz_review/repository.py`, `modules/quiz_review/models.py`, UI `features/quiz-review/` | Đối chiếu đáp án/rubric, phân tích chênh lệch, lưu kết quả tham khảo | Chưa phân công |
| Grade Planning (UC08–09) | `modules/grade_planning/api.py`, `modules/grade_planning/service.py`, `modules/grade_planning/repository.py`, `modules/grade_planning/models.py`, UI `features/grade-planning/` | Lưu mục tiêu, tính điểm còn thiếu và tính khả thi từ trọng số thực | Chưa phân công |
| Comment Suggestion (UC07) | `modules/comments/api.py`, `modules/comments/service.py`, UI `features/comments/` | Tạo/viết lại bản nháp có căn cứ từ review; sửa/sao chép, sinh viên tự gửi | Chưa phân công |
| Learning Recommendation (UC10) | `modules/recommendations/api.py`, `modules/recommendations/service.py`, `modules/recommendations/models.py`, UI `features/recommendations/` | Chủ đề ưu tiên ôn từ lỗi chi tiết và nguồn tài liệu; lưu phân tích/bằng chứng/đề xuất, báo thiếu dữ liệu | Chưa phân công |
| AI Integration | `integrations/llm.py`, `integrations/embeddings.py` | Interface provider dùng chung, timeout/retry và lỗi; API key ở backend | Chưa phân công |
| Database & hạ tầng | `extensions.py`, `migrations/`, `infrastructure/` | PostgreSQL + pgvector, migration, hướng dẫn môi trường chạy | Chưa phân công |

Các đường dẫn backend ở trên tính từ `backend/src/student_assistant/`; đường dẫn UI tính từ `extension/src/sidebar/`.

## Thứ tự phối hợp

1. Nhóm chốt request/response trong [OpenAPI](../backend/openapi/openapi_modular/openapi_modular/openapi.yaml), message trong `contracts/extension-messages/`, và cơ chế xác thực trước khi nối UI. Xem [hướng dẫn bundle/lint](../backend/openapi/openapi_modular/openapi_modular/README.md).
2. Document và Chat chốt chunk, metadata nguồn, chiều embedding và bộ lọc người dùng/môn; dùng cùng embedding model.
3. Quiz Review bàn giao định dạng kết quả có câu hỏi, rubric, điểm chính thức, nhận xét tham khảo và căn cứ cho Comment/Recommendation.
4. Grade Planning chốt thang điểm, trọng số, cách biểu diễn bài chưa chấm và mục tiêu bất khả thi.
5. Mỗi người triển khai trong phần mình nhận; thay đổi `factory.py`, đăng ký Blueprint, dependencies và migration cần trao đổi với người phụ trách nền tảng.

## Điều kiện bàn giao

- Request/response và trường hợp lỗi được ghi rõ; đánh dấu đề xuất chưa được nhóm thống nhất.
- API có kiểm tra quyền dữ liệu và validation tương ứng; không trả kết quả giả để che phần chưa triển khai.
- Có kiểm thử luồng chính và lỗi đặc thù của module khi đã có nghiệp vụ.
- Hướng dẫn cách chạy và giới hạn còn lại; UI phân biệt kết quả AI với dữ liệu chính thức.

Phần database đã có 18 model, migration `0001_initial` và seed phát triển; xem [database](database.md). Các chủ module bổ sung nghiệp vụ/repository trên model hiện có và phối hợp revision mới với người phụ trách nền tảng. Seed chạy lại giữ nguyên bản ghi hiện có, chưa tạo embedding hoặc câu trả lời AI.

API nghiệp vụ, xác thực/phân quyền tại API, provider AI và Extension cài chạy được vẫn cần triển khai. Database không tự thực hiện kiểm tra token, consent hiện hành hoặc quyền Portal. Chiều vector và provider embedding cần được nhóm chốt trước khi thêm ANN index.
