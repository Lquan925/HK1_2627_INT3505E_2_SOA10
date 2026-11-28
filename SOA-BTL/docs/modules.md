# Bảng phân công công việc AI Student Assistant

| Thành viên | Vai trò | Phạm vi phụ trách | Tệp và đầu ra bàn giao |
| --- | --- | --- | --- |
| **Quân** | Trưởng nhóm | Điều phối và theo dõi tiến độ chung, rà soát kiến trúc, thống nhất hợp đồng API và thiết kế dữ liệu, tổng hợp và kiểm tra bài nộp. | Đặc tả OpenAPI tổng hợp (`openapi.yaml`, `common/`), tài liệu `docs/architecture.md` và bản bàn giao chung. |
| **Nam** | Viết đặc tả API · Người 1 | Dữ liệu nền và tài liệu · **Consents, Documents** · UC02, UC04, UC05 · **6 endpoint**. | Tệp `consents.yaml` và `documents.yaml` trong `paths/` và `schemas/`. |
| **Hưng** | Viết đặc tả API · Người 2; phụ trách slide và backlog | Hỏi đáp RAG và ôn tập · **Chat, Recommendations** · UC03, UC10 · **6 endpoint**. Soạn slide về thiết kế và các đánh đổi, cập nhật backlog theo tiến độ của nhóm. | `chat.yaml` và `recommendations.yaml` trong `paths/` và `schemas/`, [slide thuyết trình](AI_Student_Assistant_redesign.pptx) và [backlog](backlog.md). |
| **Tấn** | Viết đặc tả API · Người 3 | Đánh giá quiz và điểm số · **QuizReviews, GradePlanning** · UC06, UC07, UC08, UC09 · **7 endpoint**. | Tệp `quiz-reviews.yaml` và `grade-planning.yaml` trong `paths/` và `schemas/`. |
| **Kiên** | Cơ sở dữ liệu và ERD | Thiết kế schema PostgreSQL, xác định bảng, khóa chính, khóa ngoại và quan hệ giữa các thực thể, chuẩn bị migration và vẽ ERD. | `backend/migrations/`, `infrastructure/postgres/`, [mã nguồn ERD](../ai-student-assistant-extension-erd-updated.dot) và [sơ đồ ERD](../ai-student-assistant-extension-erd-updated.svg). |

Các tệp OpenAPI nằm cùng thư mục với [đặc tả chính](../backend/openapi/openapi_modular/openapi_modular/openapi.yaml). Danh sách dưới đây bám theo phạm vi 19 endpoint trong ảnh phân công.

## Phạm vi viết đặc tả API

### Nam · Người 1

- `GET /consents`, `PUT /consents`
- `POST /documents/sync`, `GET /documents`
- `GET /documents/search`, `POST /documents/summarize`

Trọng tâm gồm cơ chế opt-in/opt-out, trạng thái lập chỉ mục vector, mức tóm tắt `SHORT` và `DETAILED`, cùng cờ báo thiếu nội dung `is_partial_content`.

### Hưng · Người 2

- `GET /chat/sessions`, `POST /chat/sessions`
- `GET /chat/sessions/{session_id}/messages`, `POST /chat/sessions/{session_id}/messages`
- `POST /learning-analyses`, `GET /learning-analyses/{analysis_id}`

Trọng tâm gồm ngữ cảnh hội thoại theo môn học, mảng trích dẫn nguồn `ChatCitation` và hai cờ `has_external_knowledge`, `has_sufficient_data`.

### Tấn · Người 3

- `POST /quiz-reviews`, `GET /quiz-reviews/{review_id}`
- `POST /quiz-reviews/{review_id}/comment-suggestions` (stateless)
- `GET /grade-goals`, `POST /grade-goals`, `PATCH /grade-goals/{goal_id}`
- `POST /grade-goals/{goal_id}/calculate` (stateless)

Trọng tâm gồm đánh giá câu trắc nghiệm và tự luận theo rubric, sinh gợi ý bình luận theo văn phong, kiểm tra thang điểm và trọng số từng thành phần (`components`).

## Thứ tự phối hợp

1. Nhóm chốt request/response trong [OpenAPI](../backend/openapi/openapi_modular/openapi_modular/openapi.yaml), message trong `contracts/extension-messages/`, và cơ chế xác thực trước khi nối UI. Xem [hướng dẫn bundle/lint](../backend/openapi/openapi_modular/openapi_modular/README.md).
2. Document và Chat chốt chunk, metadata nguồn, chiều embedding và bộ lọc người dùng/môn; dùng cùng embedding model.
3. Quiz Review bàn giao định dạng kết quả có câu hỏi, rubric, điểm chính thức, nhận xét tham khảo và căn cứ cho Comment/Recommendation.
4. Grade Planning chốt thang điểm, trọng số, cách biểu diễn bài chưa chấm và mục tiêu bất khả thi.
5. Quân rà soát các thay đổi ảnh hưởng nhiều nhóm API. Kiên đối chiếu schema và migration với các đặc tả của Nam, Hưng và Tấn.

## Điều kiện bàn giao

- Request/response và trường hợp lỗi được ghi rõ; đánh dấu đề xuất chưa được nhóm thống nhất.
- API có kiểm tra quyền dữ liệu và validation tương ứng; không trả kết quả giả để che phần chưa triển khai.
- Có kiểm thử luồng chính và lỗi đặc thù của module khi đã có nghiệp vụ.
- Hướng dẫn cách chạy và giới hạn còn lại; UI phân biệt kết quả AI với dữ liệu chính thức.

## Trạng thái triển khai database

Phần database đã có 18 model, migration `0001_initial` và seed phát triển; xem [database](database.md). Các chủ module bổ sung nghiệp vụ/repository trên model hiện có và phối hợp revision mới với người phụ trách nền tảng. Seed chạy lại giữ nguyên bản ghi hiện có, chưa tạo embedding hoặc câu trả lời AI.

API nghiệp vụ, xác thực/phân quyền tại API, provider AI và Extension cài chạy được vẫn cần triển khai. Database không tự thực hiện kiểm tra token, consent hiện hành hoặc quyền Portal. Chiều vector và provider embedding cần được nhóm chốt trước khi thêm ANN index.
