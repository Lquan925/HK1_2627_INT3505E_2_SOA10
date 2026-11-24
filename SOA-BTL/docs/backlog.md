# Backlog AI Student Assistant

**Phụ trách cập nhật** · Hưng. **Điều phối và duyệt bàn giao** · Quân.

P0 là hạng mục cần cho bài nộp. P1 là công việc triển khai tiếp theo. Trạng thái «Có bản nháp» ghi nhận tài liệu hoặc mã khung đã có trong repo. Tiêu chí nghiệm thu mô tả phần cần kiểm tra trước khi đóng việc.

| Mã | Ưu tiên | Công việc | Phụ trách | Trạng thái | Phụ thuộc | Tiêu chí nghiệm thu |
| --- | --- | --- | --- | --- | --- | --- |
| B01 | P0 | Chốt project brief | Quân | Cần hoàn thiện | — | Tài liệu 1–2 trang mô tả bài toán, người dùng và ứng dụng tiêu thụ API, use case và phạm vi MVP. |
| B02 | P0 | Chốt resource model và sơ đồ kiến trúc | Quân | Có bản nháp | B01 | Sơ đồ thể hiện Portal, Extension, Flask, PostgreSQL/pgvector và dịch vụ AI. Tài nguyên chính được đối chiếu với API và ERD. |
| B03 | P0 | Hoàn thiện thiết kế cơ sở dữ liệu và ERD | Kiên | Có bản nháp | B01, B04–B06 | ERD ghi cardinality, PK/FK, chủ sở hữu dữ liệu và phạm vi consent. Nêu rõ dữ liệu lưu lâu dài và hai thao tác stateless. |
| B04 | P0 | Rà soát đặc tả Consents và Documents | Nam | Có bản nháp | B01 | Sáu thao tác theo phân công có schema và ví dụ. Mô tả opt-in/out, trạng thái chỉ mục, `SHORT`/`DETAILED` và `is_partial_content`. |
| B05 | P0 | Rà soát đặc tả Chat và Recommendations | Hưng | Có bản nháp | B01 | Sáu thao tác theo phân công có schema và ví dụ. Mô tả ngữ cảnh môn học, citation, kiến thức ngoài nguồn và trường hợp thiếu dữ liệu. |
| B06 | P0 | Rà soát đặc tả QuizReviews và GradePlanning | Tấn | Có bản nháp | B01 | Bảy thao tác theo phân công có schema và ví dụ. Mô tả rubric, thang điểm, trọng số và tính chất stateless của gợi ý bình luận và phép tính điểm. |
| B07 | P0 | Tích hợp đặc tả và chuẩn bị Swagger UI | Quân | Có bản nháp | B04–B06 | `$ref` phân giải được; thống nhất phiên client, xác thực và lỗi chung. Swagger UI mở được bằng hướng dẫn trong README. |
| B08 | P0 | Rà soát repo, README và phân công | Quân | Có bản nháp | B02, B03, B07 | README có lệnh khởi động, địa chỉ Swagger UI và liên kết đến tài liệu thiết kế, phân công và backlog. |
| B09 | P0 | Chuẩn bị slide thuyết trình | Hưng | Có bản nháp | B02, B03, B07 | Bộ slide có 6–8 trang, trình bày bài toán, kiến trúc, tài nguyên, ERD, API và các đánh đổi. |
| B10 | P0 | Duy trì backlog và đối chiếu bài nộp | Hưng | Có bản nháp | — | Mỗi mục có người phụ trách, ưu tiên, trạng thái và tiêu chí nghiệm thu. Cập nhật trạng thái sau khi nhóm duyệt. |
| B11 | P1 | Chuẩn bị migration PostgreSQL | Kiên | Cần triển khai | B03 | Áp dụng migration được trên database mới, có PK/FK và ràng buộc chính. Chốt kích thước embedding trước khi tạo cột vector. |

Tham chiếu [bảng phân công](modules.md), [kiến trúc](architecture.md), [use case](use-cases.md), [đặc tả OpenAPI](../backend/openapi/openapi_modular/openapi_modular/openapi.yaml) và [slide thuyết trình](AI_Student_Assistant_redesign.pptx).
