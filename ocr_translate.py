import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import easyocr
from datetime import datetime
from deep_translator import GoogleTranslator
import cv2
import numpy as np
from PIL import ImageGrab, Image, ImageDraw, ImageFont

# OCR 엔진 초기화
reader = easyocr.Reader(['ko', 'en'])

# 기본 한글 폰트 (맑은 고딕)
def get_korean_font(size=20):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", size)
    except:
        return ImageFont.load_default()

def blur_roi(img_bgr, x1, y1, x2, y2, ksize=(25, 25)):
    """ROI 영역 블러 처리"""
    h, w = img_bgr.shape[:2]
    x1, x2 = max(0, x1), min(w-1, x2)
    y1, y2 = max(0, y1), min(h-1, y2)
    if x2 <= x1 or y2 <= y1:
        return
    roi = img_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return
    blurred = cv2.GaussianBlur(roi, ksize, 0)
    img_bgr[y1:y2, x1:x2] = blurred

def process_image(img_path=None, pil_image=None):
    """이미지 처리: OCR → 번역 → 블러 → 번역문 표시"""
    if img_path:
        img_bgr = cv2.imread(img_path)
        results = reader.readtext(img_path, detail=1)
    elif pil_image:
        img_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        results = reader.readtext(img_bgr, detail=1)
    else:
        return

    original_texts, translated_texts = [], []

    # OCR + 번역 + 블러 처리
    for (bbox, text, confidence) in results:
        if not text.strip():
            continue
        original_texts.append(text)
        try:
            translated = GoogleTranslator(source="en", target="ko").translate(text)
        except:
            translated = text
        translated_texts.append(translated)

        xs = [int(pt[0]) for pt in bbox]
        ys = [int(pt[1]) for pt in bbox]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        blur_roi(img_bgr, x1, y1, x2, y2, ksize=(31, 31))

    # Pillow 변환
    img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = get_korean_font(22)  # 고정 크기 폰트

    # 번역문 표시 (박스 좌상단에 출력)
    for i, (bbox, text, confidence) in enumerate(results):
        if not text.strip():
            continue
        translated = translated_texts[i]
        xs = [int(pt[0]) for pt in bbox]
        ys = [int(pt[1]) for pt in bbox]
        x1, x2 = min(xs), max(xs)
        y1, y2 = min(ys), max(ys)
        draw.text((x1, y1), translated, font=font, fill=(0,0,0))

    # 결과 텍스트 저장
    filename = f"ocr_translate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("===== OCR 원문 (영어) =====\n")
        f.write("\n".join(original_texts) + "\n\n")
        f.write("===== 번역문 (한국어) =====\n")
        f.write("\n".join(translated_texts))

    print("결과 텍스트 저장:", filename)

    # 결과 이미지 출력
    img_result = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    cv2.imshow("Translated Overlay (영→한)", img_result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 이벤트 루프 종료
    try:
        root.quit()
    except:
        pass

def handle_drop(event):
    filepath = event.data.strip("{}")
    print("드래그된 파일 경로:", filepath)
    process_image(img_path=filepath)

def handle_paste(event):
    try:
        pil_image = ImageGrab.grabclipboard()
        if pil_image:
            process_image(pil_image=pil_image)
        else:
            print("클립보드에 이미지가 없습니다.")
    except Exception as e:
        print("붙여넣기 실패:", e)

# TkinterDnD GUI
root = TkinterDnD.Tk()
root.title("Drag & Drop / Paste OCR + 번역 (영→한)")

label = tk.Label(root, text="이미지를 드래그하거나 Ctrl+V로 붙여넣으세요", width=50, height=10, bg="lightgray")
label.pack(padx=20, pady=20)

label.drop_target_register(DND_FILES)
label.dnd_bind("<<Drop>>", handle_drop)
root.bind("<Control-v>", handle_paste)

# 메인 루프 실행
root.mainloop()

# 루프가 끝난 뒤 안전하게 종료
try:
    root.destroy()
except:
    pass