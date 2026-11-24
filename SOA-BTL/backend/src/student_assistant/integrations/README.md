# External Integration Layer

llm.py và embeddings.py đóng gói API provider, timeout, retry, rate limit và lỗi. API key chỉ ở backend. portal.py chỉ dành cho API chính thức được phép; việc đọc DOM thuộc Content Script.

Hiện là file khung, chưa triển khai nghiệp vụ. Xem [bảng chia việc](../../../../docs/modules.md) và [kiến trúc](../../../../docs/architecture.md).
