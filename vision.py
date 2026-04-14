import cv2
import numpy as np
import mss
import pytesseract
import concurrent.futures
from collections import Counter

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def capture_screen(left, top, width, height):
    with mss.mss() as sct:
        monitor = {"top": int(top), "left": int(left), "width": int(width), "height": int(height)}
        img = np.array(sct.grab(monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

def _sharpen(img):
    """Làm sắc nét ảnh bằng unsharp masking để chữ rõ hơn."""
    blur = cv2.GaussianBlur(img, (0, 0), 3)
    sharp = cv2.addWeighted(img, 1.5, blur, -0.5, 0)
    return sharp

def _prepare_cell(cell_gray):
    """
    Chuẩn bị ô chữ số cho Tesseract.
    Trả về ảnh (chữ đen, nền trắng) đã scale lớn, hoặc None nếu ô trống.
    """
    # Cắt nhẹ 5px viền để bỏ đường kẻ bảng
    h, w = cell_gray.shape
    margin = max(4, int(min(h, w) * 0.12))
    cell = cell_gray[margin:h - margin, margin:w - margin]

    # Bước 1: Ngưỡng hoá Otsu (inv) → chữ=255, nền=0
    _, thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Đảm bảo nền là 0 (tức pixel trắng < 50%), nếu quá nhiều trắng thì đảo ngược
    if np.sum(thresh == 255) > np.sum(thresh == 0):
        thresh = cv2.bitwise_not(thresh)

    # Bước 2: Morphology — đóng lỗ hổng nhỏ bên trong chữ (fill gaps)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)

    # Bước 3: Tìm contour lớn nhất (chính là con số)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    c = max(contours, key=cv2.contourArea)
    x, y, cw, ch = cv2.boundingRect(c)

    # Bỏ hạt rác nhỏ
    if ch < 12 or cw < 4:
        return None

    # Tính tỷ lệ aspect: nếu quá rộng so với cao (aspect > 2.5) thì nhiều khả năng là đường kẻ bảng
    aspect_ratio = cw / ch
    if aspect_ratio > 2.5:
        return None

    # Bước 4: Crop sát chữ
    digit = thresh[y:y + ch, x:x + cw]

    # Bước 5: Padding rộng để Tesseract không bị cụt viền
    pad = 20
    digit = cv2.copyMakeBorder(digit, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)

    # Bước 6: Đảo ngược → chữ đen, nền trắng (Tesseract chuẩn)
    final_img = cv2.bitwise_not(digit)

    # Bước 7: Scale lên 4x bằng INTER_LANCZOS4 (sắc nét hơn INTER_CUBIC cho chữ số)
    final_img = cv2.resize(final_img, (0, 0), fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)

    # Bước 8: Sharpen nhẹ sau khi scale
    final_img = _sharpen(final_img)

    return final_img


def ocr_single_cell(cell_img):
    """
    Nhận dạng chữ số trong ô bằng voting từ nhiều config Tesseract.
    Giảm nhầm lẫn 9↔2, 6↔5, v.v.
    """
    # Danh sách config với các PSM mode khác nhau
    configs = [
        '--psm 10 --oem 3 -c tessedit_char_whitelist=123456789',  # single char
        '--psm 8  --oem 3 -c tessedit_char_whitelist=123456789',  # single word
        '--psm 13 --oem 3 -c tessedit_char_whitelist=123456789',  # raw line
        '--psm 6  --oem 3 -c tessedit_char_whitelist=123456789',  # block
        '--psm 7  --oem 3 -c tessedit_char_whitelist=123456789',  # single text line
    ]

    votes = []
    for config in configs:
        try:
            text = pytesseract.image_to_string(cell_img, config=config).strip()
            digits = ''.join(filter(str.isdigit, text))
            if digits:
                votes.append(int(digits[0]))
        except Exception:
            continue

    if not votes:
        return 0

    # Chọn kết quả được vote nhiều nhất
    most_common_val, most_common_count = Counter(votes).most_common(1)[0]

    # Nếu chỉ có 1 phiếu → không chắc, trả về 0 (ô trống) để không sai
    # Tuy nhiên nếu chỉ 1 config chạy được thì vẫn tin
    if most_common_count == 1 and len(votes) >= 3:
        return 0

    return most_common_val


def extract_sudoku_grid(img, log_callback=None):
    if log_callback:
        log_callback("⚙️ Đang xử lý ảnh với thuật toán OCR V26 nâng cao...")

    # Resize về kích thước chuẩn, sau đó upscale ngay để OCR tốt hơn
    img = cv2.resize(img, (630, 630), interpolation=cv2.INTER_LANCZOS4)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    cell_size = 630 // 9  # = 70px mỗi ô

    tasks = []

    for i in range(9):
        for j in range(9):
            x1 = j * cell_size
            y1 = i * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size

            cell = gray[y1:y2, x1:x2]
            prepared = _prepare_cell(cell)
            tasks.append(prepared)

    grid = [[0] * 9 for _ in range(9)]
    errors_logged = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_to_coords = {}

        for idx, task_img in enumerate(tasks):
            r = idx // 9
            c = idx % 9
            if task_img is not None:
                future = executor.submit(ocr_single_cell, task_img)
                future_to_coords[future] = (r, c)
            else:
                grid[r][c] = 0

        for future in concurrent.futures.as_completed(future_to_coords):
            r, c = future_to_coords[future]
            try:
                result = future.result()
                grid[r][c] = result
            except pytesseract.pytesseract.TesseractNotFoundError:
                if "tesseract_not_found" not in errors_logged:
                    if log_callback:
                        log_callback("❌ Lỗi: Máy tính của bạn CHƯA cài đặt Tesseract-OCR!")
                    errors_logged.add("tesseract_not_found")
                grid[r][c] = 0
            except Exception as exc:
                if str(exc) not in errors_logged:
                    if log_callback:
                        log_callback(f"⚠️ Lỗi OCR: {str(exc)}")
                    errors_logged.add(str(exc))
                grid[r][c] = 0

    return grid
