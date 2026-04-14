import pyautogui
import keyboard

def fill_sudoku(original_board, solved_board, left, top, width, height, delay_sec=0.001, log_callback=None):
    # Set độ trễ dựa trên input từ tham số
    pyautogui.PAUSE = delay_sec
    cell_width = width / 9
    cell_height = height / 9

    if log_callback:
        log_callback("Bắt đầu điền đáp án! (Bấm và giữ 'X' để dừng khẩn cấp)")

    x_first = left + (cell_width / 2)
    y_first = top + (cell_height / 2)
    pyautogui.moveTo(x_first, y_first)
    
    interrupted = False

    for i in range(9):
        for j in range(9):
            if keyboard.is_pressed('x') or keyboard.is_pressed('X'):
                if log_callback:
                    log_callback("🛑 Đã dừng khẩn cấp!")
                interrupted = True
                break

            if original_board[i][j] == 0:
                target_val = solved_board[i][j]
                
                x_center = left + (j * cell_width) + (cell_width / 2)
                y_center = top + (i * cell_height) + (cell_height / 2)

                pyautogui.click(x_center, y_center)
                pyautogui.write(str(target_val))
                
        if interrupted:
            break

    if not interrupted:
        if log_callback:
            log_callback("✅ Đã hoàn thành siêu tốc!")
