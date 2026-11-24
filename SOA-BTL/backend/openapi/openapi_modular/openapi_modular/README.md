# AI Student Assistant — Đặc tả OpenAPI chia theo mô-đun

Tệp đặc tả chính: `openapi.yaml`.

Phân công các phần đặc tả:

- Thành viên 1: `client-sessions`, `consents`, `documents`.
- Thành viên 2: `chat`, `recommendations`.
- Thành viên 3: `quiz-reviews`, `grade-planning`.
- Phần dùng chung: thư mục `common` và tệp `schemas/common.yaml`.

Gộp đặc tả thành một tệp để dùng trong Swagger Editor và kiểm tra đặc tả bằng Node.js:

```sh
npx @redocly/cli bundle openapi.yaml -o openapi.bundled.yaml
npx @redocly/cli lint openapi.yaml
```

Nhập tệp `openapi.bundled.yaml` vào Swagger Editor. Khi cập nhật đặc tả, sửa các tệp mô-đun rồi chạy lại lệnh gộp; không sửa trực tiếp tệp được sinh tự động. UC07 và UC09 vẫn xử lý từng yêu cầu độc lập, không lưu đầu vào hoặc kết quả xử lý vào cơ sở dữ liệu.

Các tệp mô-đun là nguồn đặc tả được duy trì chính thức. Backend chưa triển khai các tuyến API nghiệp vụ; hợp đồng này mô tả hành vi cần triển khai.

## Xem trực tiếp bằng Swagger UI

Khởi động backend theo [hướng dẫn Flask](../../../README.md), sau đó mở `http://127.0.0.1:8000/docs/`. Swagger UI đọc trực tiếp `http://127.0.0.1:8000/openapi/openapi.yaml` và tự tải các tệp được tham chiếu. Không cần chạy lệnh gộp để xem tài liệu trên backend; sửa YAML rồi tải lại trang để xem thay đổi.

Máy chủ API trong đặc tả dùng đường dẫn tương đối `/api/v1`, nên thao tác thử API luôn gọi cùng máy chủ phục vụ đặc tả. Các endpoint nghiệp vụ chưa triển khai vẫn trả `404`. Cách nhập token phiên và cấu hình thư mục đặc tả khi triển khai được mô tả trong README của backend.

## Hợp đồng API phiên bản 2.0.0

Phiên bản này thay đổi các trường bắt buộc và giới hạn công thức tính điểm được hỗ trợ. Cần cập nhật đồng bộ phía gọi API và phần kiểm tra dữ liệu tại backend:

- `CreateGradeGoalRequest` và `GradeGoalResponse` bắt buộc có `data_source` (`PORTAL` hoặc `MANUAL`) để ghi nhận nguồn thang điểm và công thức của mục tiêu. Mỗi `GradeComponentInput` cũng phải khai báo nguồn riêng để giữ đúng nguồn gốc khi trộn dữ liệu. Không tự suy đoán nguồn còn thiếu hoặc đổi nhãn dữ liệu Portal đã lưu thành dữ liệu nhập tay.
- Mục tiêu hoặc bất kỳ thành phần điểm nào lấy từ Portal đều cần quyền cho phép sử dụng dữ liệu `GRADE_BOOK` cho mục đích `GRADE_PLANNING` trong đúng môn học. Kiểm tra lại quyền trước khi trả kết quả; thiếu quyền trả `403`. Mục tiêu và phép tính hoàn toàn dùng dữ liệu nhập tay không cần quyền sử dụng dữ liệu Portal. Nhãn nguồn dữ liệu không phải bằng chứng về quyền truy cập Portal.
- `grading_rule` chỉ nhận giá trị `WEIGHTED_AVERAGE`, tức trung bình có trọng số. Quy đổi từng điểm về thang `max_scale` của mục tiêu trước khi nhân trọng số. Tổng trọng số phải bằng 100; nếu khác, trả `422 INVALID_GRADE_WEIGHTS`. Công thức chưa được hỗ trợ trả `422 UNSUPPORTED_GRADING_RULE`.
- Thành phần đã hoàn thành bắt buộc có `earned_score` khác `null`; thành phần chưa hoàn thành chỉ chấp nhận bỏ trường điểm hoặc gửi `null`. Backend phải kiểm tra quan hệ giữa điểm và thang điểm, tổng trọng số và quyền sử dụng dữ liệu; OpenAPI 3.0 không thể tự kiểm tra tất cả các điều kiện này. Thiếu điểm của bài đã hoàn thành trả `422 INSUFFICIENT_GRADE_DATA`; điểm không hợp lệ trả `422 INVALID_GRADE_SCORE`.
- `ChatMessageResponse` luôn có `is_partial_content` và `coverage_note`. Tin nhắn `SUMMARY` giữ nguyên hai giá trị từ `SummarizeResponse`; tin nhắn `CHAT` dùng `false` và `null`. Khi trả lịch sử hội thoại, phải giữ lại cảnh báo về nội dung tóm tắt chưa đầy đủ.

Trong ví dụ tính điểm, phần điểm đã đạt trên thang 10 là `C = 4.8`, tổng trọng số còn lại là `R = 0.4`: để đạt mục tiêu 8, điểm trung bình có trọng số của các bài còn lại phải đạt 8; điểm tổng tối đa có thể đạt là 8.8. Nếu không còn trọng số chưa hoàn thành, điểm trung bình cần đạt là `null`. Nếu phần điểm đã đạt đủ bảo đảm mục tiêu, điểm trung bình cần đạt là 0. Nếu mục tiêu không khả thi, giữ giá trị điểm trung bình cần đạt lớn hơn thang điểm và trả `is_feasible=false`. Xem công thức tại `GradeCalculationResponse`. UC09 không lưu đầu vào hoặc kết quả tính vào cơ sở dữ liệu.

Đường dẫn tệp đặc tả chính tính từ thư mục gốc của kho mã nguồn là `backend/openapi/openapi_modular/openapi_modular/openapi.yaml`. Chạy các lệnh gộp và kiểm tra ở trên từ thư mục chứa README này. Tệp đặc tả được gộp là sản phẩm sinh tự động trong quá trình chuẩn bị đặc tả.
