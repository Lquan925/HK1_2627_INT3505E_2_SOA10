# Kiểm thử hệ thống

`e2e/` dành cho kiểm thử xuyên suốt Chrome Extension → backend → cơ sở dữ liệu khi ứng dụng được triển khai. Chưa có bài test hoặc công cụ e2e. Backend đã khai báo pytest trong nhóm dependency `dev`.

Unit/integration test của từng phía đặt tại `extension/tests/` và `backend/tests/`. Các luồng cần ưu tiên gồm cấp/từ chối/thu hồi quyền (UC02), giới hạn tài liệu theo người dùng/môn học (UC03–UC05), thiếu đáp án/rubric (UC06), comment do sinh viên tự gửi (UC07), công thức/trọng số và mục tiêu không khả thi (UC08–UC09), lỗi dịch vụ AI.

Sử dụng fixture giả và Portal giả lập cho kiểm thử; không đưa dữ liệu cá nhân hoặc thông tin đăng nhập thật vào repository.
