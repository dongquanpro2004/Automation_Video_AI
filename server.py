from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import asyncio
import requests
import random
import edge_tts
import traceback  # Vũ khí bí mật để in sạch lỗi ra Terminal
from huggingface_hub import InferenceClient
from gradio_client import Client, handle_file
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip
from moviepy.video.fx import Crop, Resize
from gtts import gTTS
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env bảo mật
load_dotenv()

app = FastAPI()

class VideoRequest(BaseModel):
    voice_text: str
    image_prompt: str

@app.post("/render")
async def render_video(req: VideoRequest):
    AUDIO_OUT = r"C:\Users\dongq\Desktop\AutomationContentVideo\voice.mp3"
    IMAGE_OUT = r"C:\Users\dongq\Desktop\AutomationContentVideo\background.jpg"
    IMAGE_PADDED = r"C:\Users\dongq\Desktop\AutomationContentVideo\background_padded.jpg"
    VIDEO_AI_OUT = r"C:\Users\dongq\Desktop\AutomationContentVideo\ai_silent.mp4"
    VIDEO_OUT = r"C:\Users\dongq\Desktop\AutomationContentVideo\final_shorts.mp4"
    
    print("\n==========================================================")
    print("-> [HỆ THỐNG] Nhận lệnh từ n8n! Khởi động quy trình render...")
    print("==========================================================")

    # Dọn dẹp hệ thống file cũ kèm cảnh báo kẹt file
    print("-> Đang kiểm tra và dọn dẹp file cũ...")
    for f in [AUDIO_OUT, IMAGE_OUT, IMAGE_PADDED, VIDEO_AI_OUT, VIDEO_OUT]:
        if os.path.exists(f):
            try: 
                os.remove(f)
            except Exception as e:
                print(f"⚠️ [CẢNH BÁO] Không thể xóa file {os.path.basename(f)}. Chi tiết: {e}")

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token or hf_token.startswith("hf_XXXX") or hf_token == "":
        raise ValueError("Ný ơi, chưa khai báo mã token HF_TOKEN trong file .env kìa!")
    
    # Kiểm tra văn bản thoại đầu vào tránh lỗi rỗng từ n8n
    voice_text_clean = req.voice_text.strip() if req.voice_text else ""
    print(f"-> Nội dung thoại nhận được từ n8n (Độ dài {len(voice_text_clean)} ký tự): '{voice_text_clean}'")
    if not voice_text_clean:
        raise HTTPException(
            status_code=400, 
            detail="Lỗi: Văn bản thoại 'voice_text' gửi từ n8n bị rỗng hoặc chỉ toàn khoảng trắng!"
        )
    
    # TÁC VỤ 1: Tạo giọng đọc AI (Microsoft TTS)
    voices = ["vi-VN-NamMinhNeural", "vi-VN-HoaiAnNeural"]
    tts_success = False
    last_tts_err = None
    
    for voice in voices:
        try:
            print(f"-> Đang gọi Microsoft TTS với giọng {voice}...")
            communicate = edge_tts.Communicate(voice_text_clean, voice)
            await communicate.save(AUDIO_OUT)
            if os.path.exists(AUDIO_OUT) and os.path.getsize(AUDIO_OUT) > 0:
                print(f"-> [OK] Đã tạo xong file voice.mp3 bằng giọng {voice}!")
                tts_success = True
                break
        except Exception as e:
            last_tts_err = e
            print(f"   [Cảnh báo] Giọng {voice} vấp lỗi: {str(e)}. Đang thử giọng tiếp theo...")
            await asyncio.sleep(1)
            
    if not tts_success:
        print("\n⚠️ [CẢNH BÁO] Microsoft TTS bị chặn hoặc gặp sự cố. Kích hoạt Google TTS dự phòng...")
        try:
            # Tạo giọng đọc tiếng Việt bằng Google TTS
            tts = gTTS(text=voice_text_clean, lang="vi")
            tts.save(AUDIO_OUT)
            if os.path.exists(AUDIO_OUT) and os.path.getsize(AUDIO_OUT) > 0:
                print("-> [OK] Đã tạo xong file voice.mp3 bằng Google TTS dự phòng cực kỳ ổn định!")
                tts_success = True
        except Exception as gtts_err:
            print("\n❌ [CRITICAL ERROR] LỖI CẢ TÁC VỤ GIỌNG ĐỌC CHÍNH VÀ DỰ PHÒNG:")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Lỗi tạo giọng đọc: {str(gtts_err)}")

    # TÁC VỤ 2: Tạo ảnh gốc từ chiến thần FLUX
    try:
        print("-> Đang gọi API Hugging Face tạo ảnh Flux siêu thực...")
        client_hf = InferenceClient(token=os.environ["HF_TOKEN"])
        final_prompt = f"{req.image_prompt}, vertical portrait photography, 9:16 aspect ratio, cinematic lighting, highly detailed"
        
        try:
            image = client_hf.text_to_image(prompt=final_prompt, model="black-forest-labs/FLUX.1-schnell", width=720, height=1280)
            image.save(IMAGE_OUT)
            print("-> [OK] Đã đẻ xong ảnh background.jpg từ chiến thần FLUX!")
        except Exception as flux_err:
            print(f"-> [Cảnh báo] Bản FLUX bận. Chuyển sang dùng Stable Diffusion XL dự phòng...")
            image = client_hf.text_to_image(prompt=final_prompt, model="stabilityai/stable-diffusion-xl-base-1.0", width=720, height=1280)
            image.save(IMAGE_OUT)
            print("-> [OK] Đã đẻ xong ảnh background.jpg bằng Stable Diffusion XL!")

        # Tác vụ bổ sung: Pad ảnh dọc 9:16 thành ngang 16:9 để SVD không crop mất đầu/chân của ný
        try:
            from PIL import Image, ImageEnhance
            img = Image.open(IMAGE_OUT)
            
            # Tăng cường độ nét (Sharpness) và độ tương phản (Contrast) của ảnh gốc trước
            sharp_enhancer = ImageEnhance.Sharpness(img)
            img_sharp = sharp_enhancer.enhance(1.8)  # Tăng 80% độ sắc nét cho các tiểu tiết hoạt hình
            contrast_enhancer = ImageEnhance.Contrast(img_sharp)
            img_final = contrast_enhancer.enhance(1.1)  # Tăng 10% độ tương phản để màu sắc sâu và nổi bật
            img_final.save(IMAGE_OUT)  # Lưu đè lại ảnh gốc đã làm nét căng
            
            # Tạo canvas đen 1024x576 chuẩn của SVD
            canvas = Image.new("RGB", (1024, 576), (0, 0, 0))
            
            # Resize ảnh dọc 9:16 về khung 324x576 ở chính giữa
            resized_img = img_final.resize((324, 576), Image.Resampling.LANCZOS)
            
            # Làm nét thêm một lần nữa cho phần ảnh thu nhỏ (vì thu nhỏ rất dễ bị mờ)
            mini_sharp = ImageEnhance.Sharpness(resized_img)
            resized_sharp = mini_sharp.enhance(2.0)  # Tăng gấp đôi độ sắc nét cho ảnh thu nhỏ
            
            canvas.paste(resized_sharp, (350, 0)) # 350 = (1024 - 324) / 2
            canvas.save(IMAGE_PADDED)
            print("-> [OK] Đã pad và tối ưu hóa NÉT CĂNG ảnh dọc thành ngang 1024x576 thành công!")
        except Exception as pad_err:
            print(f"⚠️ [CẢNH BÁO] Không thể thực hiện pad ảnh: {pad_err}")
            IMAGE_PADDED = IMAGE_OUT

    except Exception as e:
        print("\n❌ [CRITICAL ERROR] LỖI TẠI TÁC VỤ TẠO ẢNH HUGGING FACE:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lỗi tạo ảnh: {str(e)}")
            
    # TÁC VỤ 3: Tạo chuyển động video (Sử dụng API chuẩn của Space và handle_file)
    try:
        print("-> Đang đẩy ảnh lên Hugging Face Space để thổi hồn chuyển động...")
        # Sử dụng HF_TOKEN để xác thực và tránh bị giới hạn rate limit
        hf_token = os.environ.get("HF_TOKEN")
        client_video = Client("multimodalart/stable-video-diffusion", token=hf_token)
        
        try:
            print("   [Thử nghiệm] Gửi dữ liệu qua API /video...")
            # Tạo seed ngẫu nhiên để kích hoạt chuyển động đồ vật phong phú
            random_seed = random.randint(1, 10000000)
            # Gọi API /video với handle_file và ảnh đã pad
            result = client_video.predict(
                image=handle_file(IMAGE_PADDED), # Bọc trong handle_file
                seed=random_seed,
                randomize_seed=True,
                motion_bucket_id=60,        # Đặt 60 để chuyển động hoạt hình rõ rệt và sinh động
                fps_id=6,
                api_name="/video"
            )
        except Exception as api_err:
            print(f"   [Thông báo] API /video gặp lỗi ({str(api_err)}). Kích hoạt Fallback tự động...")
            random_seed = random.randint(1, 10000000)
            # Fallback: gọi theo vị trí nhưng dùng handle_file và fn_index=1 (/video)
            result = client_video.predict(
                handle_file(IMAGE_PADDED),
                random_seed,
                True,
                60,                         # Đặt 60 để chuyển động hoạt hình rõ rệt và sinh động
                6,
                fn_index=1
            )
        
        # Kết quả trả về là một tuple (video_data, seed)
        temp_video_data = result[0] if isinstance(result, tuple) else result
        # Giải nén đường dẫn file video từ dict nếu cần
        if isinstance(temp_video_data, dict) and "video" in temp_video_data:
            temp_video_path = temp_video_data["video"]
        else:
            temp_video_path = temp_video_data
            
        with open(VIDEO_AI_OUT, "wb") as f_out, open(temp_video_path, "rb") as f_in:
            f_out.write(f_in.read())
            
        print("-> [OK] AI đã dựng xong clip chuyển động hoàn toàn free!")
    except Exception as e:
        print(f"\n⚠️ [CẢNH BÁO] Không thể tạo chuyển động video từ Hugging Face: {str(e)}")
        print("-> Đang kích hoạt Fallback: Tạo video tĩnh từ background.jpg...")
        try:
            # Tạo clip tĩnh thời lượng 4 giây (tương đương video động chuẩn) làm dự phòng
            static_clip = ImageClip(IMAGE_OUT).with_duration(4)
            static_clip.write_videofile(VIDEO_AI_OUT, fps=24, codec="libx264", logger=None)
            static_clip.close()
            print("-> [OK] Đã tạo xong clip tĩnh dự phòng thành công!")
        except Exception as fallback_err:
            print("\n❌ [CRITICAL ERROR] LỖI CẢ TÁC VỤ DỰ PHÒNG VIDEO TĨNH:")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Lỗi làm video động & dự phòng: {str(fallback_err)}")

    # TÁC VỤ 4: Dùng MoviePy gộp nhạc thoại, loop video và ÉP BUỘC ĐỊNH DẠNG DỌC 9:16 NÉT CĂNG
    try:
        print("-> Đang dùng MoviePy xử lý đồng bộ cú chốt và ép khung hình dọc 9:16...")
        audio_clip = AudioFileClip(AUDIO_OUT)
        video_clip = VideoFileClip(VIDEO_AI_OUT)
        
        # BƯỚC KHẮC PHỤC KÍCH THƯỚC BẰNG CƠ CHẾ CROP CẮT BỎ KHUNG ĐEN 16:9:
        if video_clip.w > video_clip.h:
            print(f"   [Xử lý] Khôi phục chính xác khung hình dọc 9:16 nguyên bản...")
            # Cắt bỏ phần viền đen hai bên, giữ lại đúng phần trung tâm 324x576 (từ x1=350 đến x2=674)
            cropped_clip = video_clip.with_effects([
                Crop(
                    x1=350,
                    y1=0,
                    x2=674,
                    y2=576
                )
            ])
            # Resize chất lượng cao về chuẩn 720x1280 (Sử dụng hiệu ứng Resize của MoviePy 2.x)
            processed_video = cropped_clip.with_effects([
                Resize(width=720, height=1280)
            ])
        else:
            # Nếu video đã là dọc sẵn, chỉ cần resize về 720x1280 cho đồng bộ độ nét
            processed_video = video_clip.with_effects([
                Resize(width=720, height=1280)
            ])
            
        clips = []
        current_dur = 0
        while current_dur < audio_clip.duration:
            clips.append(processed_video)
            current_dur += processed_video.duration
            
        final_video = concatenate_videoclips(clips).with_duration(audio_clip.duration)
        final_video = final_video.with_audio(audio_clip)
        
        # Xuất video HD nét căng
        final_video.write_videofile(
            VIDEO_OUT, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac", 
            write_logfile=False,
            logger=None
        )
        
        audio_clip.close()
        video_clip.close()
        processed_video.close()
        print("\n=== ✨ [THÀNH CÔNG THẦN SẦU] VIDEO ĐỘNG ĐỌC 9:16 ĐÃ LÊN ĐĨA TẠI DESKTOP! ===")
        return {"status": "Render Success", "video_path": VIDEO_OUT}
    except Exception as e:
        print("\n❌ [CRITICAL ERROR] LỖI TẠI TÁC VỤ XUẤT MOVIEPY:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lỗi MoviePy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)