# Hợp đồng HTTP

Quy ước cho API REST; đặc tả chính đặt tại [`../../backend/openapi/student_assistant.yaml`](../../backend/openapi/student_assistant.yaml). Chưa có endpoint được triển khai.

Các nhóm API cần thiết theo kiến trúc:

| Nhóm | Phạm vi |
| --- | --- |
| Chat và tìm kiếm | UC03, UC04: câu hỏi, phạm vi môn học/tài liệu, hội thoại và nguồn trích dẫn. |
| Tài liệu | UC02, UC04, UC05: dữ liệu được cho phép, metadata, trạng thái lập chỉ mục, tóm tắt. |
| Quiz review | UC06: bài làm đã chấm, đáp án/rubric nếu có, kết quả tham khảo. |
| Comment | UC07: thắc mắc, ngữ cảnh review, phong cách và nội dung gợi ý. |
| Grade planning | UC08, UC09: mục tiêu, thang điểm, công thức, điểm thành phần và trọng số. |
| Recommendation | UC10: dữ liệu chi tiết theo chủ đề và tài liệu liên quan. |
| Người dùng và consent | UC02: cấu hình, phạm vi cấp quyền và thu hồi quyền theo cơ chế xác thực được chọn. |

Mỗi hợp đồng cần xác định trường bắt buộc, quyền truy cập, mã lỗi, giới hạn payload và ví dụ. Phân biệt dữ liệu chính thức với kết quả AI/dự tính; trả trạng thái thiếu dữ liệu thay vì tạo kết luận không có căn cứ. Nguồn trích dẫn phải trỏ đến tài liệu trong phạm vi được phép.
