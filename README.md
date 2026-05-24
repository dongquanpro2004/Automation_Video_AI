# Hệ thống Tự động hóa Quy trình Sản xuất Video AI 🚀 (AI Video Automation Pipeline)

Một hệ thống tự động hóa hoàn chỉnh (End-to-End Pipeline) được thiết kế để chuyển đổi kịch bản văn bản thô thành các video ngắn chuyển động điện ảnh khổ dọc 9:16 cho TikTok/Reels/Shorts. Dự án này chứng minh các kỹ năng chuyên sâu về **Điều phối AI (AI Orchestration), Tự động hóa quy trình (Workflow Automation), Tích hợp API và Thiết kế hệ thống chịu lỗi (Fault-Tolerant System Design)** — kết hợp sức mạnh giữa nền tảng Thấp mã (Low-Code n8n) và mã nguồn Backend tùy chỉnh (FastAPI/Python).

---

## 🛠️ Kiến trúc Hệ thống & Luồng Dữ liệu (Data Flow)

Toàn bộ quy trình sản xuất được tự động hóa hoàn toàn và kích hoạt chỉ với một cú click chuột từ n8n:

1. **Điều phối & Quản lý luồng (n8n):** Tiếp nhận chủ đề video, điều phối các tác vụ, quản lý webhook và truyền dữ liệu.
2. **Tổng hợp Giọng nói AI (FastAPI + Edge-TTS):** Tự động chuyển đổi kịch bản tiếng Việt thành giọng đọc AI tự nhiên (Nam Minh/Hoài An) bằng công nghệ Neural của Microsoft, tích hợp cơ chế tự động chuyển hướng sang Google TTS nếu hệ thống chính gặp sự cố timeout.
3. **Tạo ảnh Cinematic (Hugging Face API + FLUX):** Đẻ ra hình ảnh gốc siêu thực, độ nét cao thông qua kỹ thuật Prompt Engineering tự động và cơ chế mở rộng khung hình (PIL Padding) để chống méo dạng.
4. **Thổi hồn Chuyển động (Gradio Client + SVD):** Truyền tham số hình ảnh vào mô hình Stable Video Diffusion chạy trên các không gian mã nguồn mở của Hugging Face để tạo chuyển động vật lý cho nhân vật/bối cảnh với chi phí API bằng $0.
5. **Biên tập & Xuất Video (MoviePy 2.x):** Tự động dọn dẹp bộ nhớ đệm, tính toán vòng lặp (loop) hình ảnh khớp với thời lượng giọng nói, tự động crop và resize video về chuẩn khung hình dọc HD 720x1280 (9:16).

---

## ✨ Các Tính năng Cao cấp (Tập trung vào Vận hành AI - AI Operations)

* **Khả năng chịu lỗi & Cơ chế dự phòng (Fault-Tolerance & Fallbacks):** Tích hợp logic tự động thử lại (Auto-retry) và chiến lược chuyển đổi mô hình dự phòng ở mọi giai đoạn xử lý (Microsoft TTS 🔄 Google TTS; FLUX.1-schnell 🔄 Stable Diffusion XL), đảm bảo hệ thống không bao giờ bị sập kể cả khi API thượng nguồn bị nghẽn.
* **Mô hình Lai tối ưu chi phí (Cost-Efficient Low-Code/Code Hybrid):** Loại bỏ hoàn toàn chi phí thuê server video thương mại đắt đỏ bằng cách lách luật kết nối trực tiếp vào các cổng Hugging Face Spaces miễn phí thông qua thư viện `gradio_client` và kỹ thuật truyền tham số theo vị trí (Positional Arguments).
* **Tự động Quản lý Tài nguyên (Asset Hot-Swapping):** Tự động quét thư mục và giải phóng bộ nhớ ngầm độc quyền (`os.remove`) để giải quyết triệt để lỗi kẹt file trên hệ điều hành Windows, quản lý dung lượng đĩa cứng một cách thông minh trước mỗi phiên render.
* **Thích ứng Khung hình Thông minh (Smart Frame Adaptation):** Triển khai cơ chế đệm canvas đen tự động qua `Pillow`, kết hợp cắt khung tâm trung tâm (Central localized cropping) qua `MoviePy` để biến các sản phẩm ảnh ngang 16:9 của AI Video thành clip dọc 9:16 chuẩn thiết bị di động mà không làm mất thực thể chính.

---

## 💻 Công nghệ Sử dụng (Tech Stack)

* **Điều phối luồng:** n8n (Webhook & API Gateway)
* **Backend Framework:** FastAPI, Uvicorn (Asynchronous Python)
* **Mô hình AI sử dụng:** FLUX.1-schnell, Stable Diffusion XL, Stable Video Diffusion (SVD)
* **Xử lý Đa phương tiện:** MoviePy 2.x, Pillow (PIL), Edge-TTS, gTTS
* **Quản trị hệ thống:** Python-dotenv (Bảo mật biến môi trường)

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy Nhanh

### 1. Yêu cầu Hệ thống
Máy tính đã cài đặt sẵn Python bản 3.10 trở lên.

### 2. Cài đặt Môi trường
Tải mã nguồn về máy và tiến hành cài đặt các thư viện trong môi trường ảo (`venv`):
```bash
git clone <link-kho-github-cua-ny>
cd AutomationContentVideo
python -m venv venv
# Kích hoạt venv trên Windows
.\venv\Scripts\activate
# Cài đặt toàn bộ dependencies
pip install fastapi uvicorn pydantic requests edge_tts huggingface_hub gradio_client moviepy Pillow gtts python-dotenv