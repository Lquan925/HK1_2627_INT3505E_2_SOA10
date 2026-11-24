# Chrome Extension

Tầng trình bày và tích hợp trình duyệt cho AI Student Assistant. Chưa chọn framework UI, công cụ build hay viết `manifest.json`.

| Thư mục | Trách nhiệm |
| --- | --- |
| `public/` | Tài nguyên tĩnh và biểu tượng extension. |
| `src/sidebar/components/` | Thành phần giao diện dùng chung. |
| `src/sidebar/features/consent/` | Cấp, từ chối và thu hồi quyền sử dụng từng loại dữ liệu (UC02). |
| `src/sidebar/features/chat/` | Hỏi đáp kiến thức và hiển thị nguồn (UC03). |
| `src/sidebar/features/documents/` | Tìm kiếm, chọn tài liệu và tóm tắt (UC04, UC05). |
| `src/sidebar/features/quiz-review/` | Hiển thị đánh giá tham khảo, điểm khác biệt và giới hạn dữ liệu (UC06). |
| `src/sidebar/features/comments/` | Xem, sửa và sao chép comment; sinh viên tự gửi (UC07). |
| `src/sidebar/features/grade-planning/` | Thiết lập mục tiêu, bổ sung dữ liệu và xem dự tính điểm (UC08, UC09). |
| `src/sidebar/features/recommendations/` | Nội dung nên ôn tập cùng tài liệu có căn cứ (UC10). |
| `src/content/portal-adapters/` | Kiểm tra Portal được hỗ trợ, đọc cấu trúc trang qua adapter riêng cho từng Portal. |
| `src/content/extractors/` | Trích xuất môn học, tài liệu, quiz và điểm trong phạm vi quyền đã cấp. |
| `src/background/messaging/` | Service worker điều phối message giữa sidebar/content script và request đến backend. |
| `src/background/storage/` | Lưu cấu hình, trạng thái consent và xử lý thu hồi quyền. |
| `src/shared/` | `constants/`, `types/`, `utils/` chỉ dùng trong extension. |
| `tests/unit/`, `tests/integration/` | Dành cho kiểm thử khi có mã nguồn. |

Việc mở/đóng sidebar và kiểm tra trang được hỗ trợ thuộc UC01, cần phối hợp sidebar, content script và service worker.

Khi triển khai, dùng allowlist cho URL Portal và backend, khai báo quyền Chrome tối thiểu cần thiết. Chỉ trích xuất sau consent; không đọc thông tin đăng nhập hoặc làm thay đổi dữ liệu chính thức trên Portal. Thu hồi quyền phải chặn lần lấy dữ liệu tiếp theo và ngừng xử lý đang phụ thuộc quyền đó.

Hợp đồng message nằm tại [`../contracts/extension-messages/`](../contracts/extension-messages/README.md); hợp đồng REST nằm tại [`../contracts/http/`](../contracts/http/README.md). API key của nhà cung cấp AI không được đưa vào extension.
