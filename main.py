import sys
import copy
from gui_selector import get_region
from vision import capture_screen, extract_sudoku_grid
from solver import solve, print_board
from automator import fill_sudoku
from pynput import keyboard

def start_process():
    print("\n--- BƯỚC 1: Chọn vùng Sudoku ---")
    print("Màn hình sẽ mờ đi. Hãy nhấn, giữ và kéo để chọn CHÍNH XÁC bảng Sudoku (bao gồm cả các viền ngoài).")
    coords = get_region()
    
    if not coords or coords[2] <= 0 or coords[3] <= 0:
        print("Lỗi: Bạn chưa chọn vùng hợp lệ. Hãy thử lại.")
        return

    left, top, width, height = coords
    print(f"Đã chọn tọa độ: Tọa độ: ({left}, {top}), Kích thước: {width}x{height}")

    print("\n--- BƯỚC 2: Phân tích hình ảnh (OCR) ---")
    img = capture_screen(left, top, width, height)
    grid = extract_sudoku_grid(img)
    
    # Giữ lại bản gốc để xem ô nào trống cần điền
    original_grid = copy.deepcopy(grid)
    
    print("Lưới cắt được từ viền màn hình:")
    print_board(grid)

    print("\n--- BƯỚC 3: Giải Sudoku ---")
    if solve(grid):
        print("Giải thành công!")
        print_board(grid)
        
        print("\n--- BƯỚC 4: Điền kết quả ---")
        fill_sudoku(original_grid, grid, left, top, width, height)
    else:
        print("Mô hình không thể giải cấu hình này. (Có thể nhận diện số sai dẫn đến vô nghiệm, hãy điều chỉnh vùng chọn kỹ hơn).")


def on_press(key):
    try:
        if key == keyboard.Key.f4:
            start_process()
            print("\nNhấn F4 để chọn một khung hình mới, hoặc Ctrl+C ở terminal để thoát.")
    except Exception as e:
        pass

if __name__ == "__main__":
    print("="*40)
    print("SUDOKU AUTO-SOLVER ĐÃ KHỞI ĐỘNG")
    print("Nhấn phím F4 để bắt đầu chọn vùng Sudoku")
    print("="*40)
    
    # Start checking keyboard hooks
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
