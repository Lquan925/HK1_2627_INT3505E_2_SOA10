# Ánh xạ use case sang module

| UC | Chức năng | Extension | Backend |
| --- | --- | --- | --- |
| UC01 | Bật/tắt AI Assistant | Sidebar, Content Script, Service Worker | Không cần service nghiệp vụ riêng |
| UC02 | Cấp/thu hồi quyền dữ liệu | `features/consent`, content, background/storage | `modules/auth/api.py`, `modules/auth/repository.py`, Document khi nhập dữ liệu |
| UC03 | Hỏi đáp kiến thức | `features/chat` | `modules/chat/api.py`, `modules/chat/service.py`, chats/vectors repositories |
| UC04 | Tìm kiếm kiến thức | `features/documents` | Chat truy xuất vector; Document chuẩn bị và lập chỉ mục tài liệu |
| UC05 | Tóm tắt tài liệu | `features/documents` | `modules/documents/api.py`, `modules/documents/service.py` |
| UC06 | Đánh giá lại quiz | `features/quiz-review` | `modules/quiz_review/api.py`, `modules/quiz_review/service.py`, `modules/quiz_review/repository.py` |
| UC07 | Gợi ý comment | `features/comments` | `modules/comments/api.py`, `modules/comments/service.py`; dùng kết quả Quiz Review |
| UC08 | Thiết lập mục tiêu điểm | `features/grade-planning` | `modules/grade_planning/api.py`, `modules/grade_planning/service.py`, grade_goals repository |
| UC09 | Dự tính điểm cần đạt | `features/grade-planning` | Grade Planning tính theo công thức, thang điểm, trọng số |
| UC10 | Gợi ý cải thiện học tập | `features/recommendations` | `modules/recommendations/api.py`, `modules/recommendations/service.py`; quiz và tài liệu |

Đây là vị trí triển khai dự kiến; các API/service hiện chưa có nghiệp vụ. UC04 cần hai module thống nhất định dạng đoạn tài liệu, nguồn và bộ lọc quyền/môn học.
