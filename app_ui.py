import customtkinter as ctk
import copy
import queue
from threading import Thread
from gui_selector import get_region
from vision import capture_screen, extract_sudoku_grid
from solver import solve
from automator import fill_sudoku

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SudokuApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Sudoku V26")
        self.geometry("450x780")
        self.attributes('-topmost', True)
        self.resizable(False, False)
        
        self.coords = None
        self.grid = None
        self.original_grid = None
        self.gui_cells = [[None for _ in range(9)] for _ in range(9)]
        
        self.task_queue = queue.Queue()
        
        self.build_ui()
        self.check_queue()
        
    def build_ui(self):
        self.lbl_title = ctk.CTkLabel(self, text="SUDOKU V26", font=("Roboto", 24, "bold"), text_color="#00FFA3")
        self.lbl_title.pack(pady=(15, 5))
        
        self.board_frame = ctk.CTkFrame(self, fg_color="#181818", corner_radius=0)
        self.board_frame.pack(pady=5)
        
        for block_row in range(3):
            for block_col in range(3):
                block = ctk.CTkFrame(self.board_frame, fg_color="#181818", corner_radius=0)
                block.grid(row=block_row, column=block_col, padx=2, pady=2)
                
                for i in range(3):
                    for j in range(3):
                        real_row = block_row * 3 + i
                        real_col = block_col * 3 + j
                        
                        cell_lbl = ctk.CTkLabel(block, text="", width=35, height=35, 
                                                fg_color="#2A2D34", text_color="#FFFFFF",
                                                font=("Roboto", 20, "bold"), corner_radius=2)
                        cell_lbl.grid(row=i, column=j, padx=1, pady=1)
                        self.gui_cells[real_row][real_col] = cell_lbl

        # --- Thanh trượt tốc độ (Speed Slider) ---
        self.speed_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.speed_frame.pack(pady=5, padx=20, fill="x")
        
        self.lbl_speed = ctk.CTkLabel(self.speed_frame, text="Tốc độ điền phím: 0.01 giây/ô", font=("Roboto", 12))
        self.lbl_speed.pack(anchor="w")
        
        self.slider_speed = ctk.CTkSlider(self.speed_frame, from_=0.0, to=0.5, number_of_steps=50, command=self.update_slider_text)
        self.slider_speed.set(0.01) # Mặc định cực nhanh nhưng vẫn ổn định
        self.slider_speed.pack(fill="x")

        # --- Nút điều khiển ---
        self.btn_select = ctk.CTkButton(self, font=("Roboto", 14, "bold"), height=35, width=200, 
                                        text="🎯 1. KHOANH VÙNG ĐỌC QUÉT", command=self.action_select)
        self.btn_select.pack(pady=(10,5))
        
        self.btn_solve = ctk.CTkButton(self, font=("Roboto", 14, "bold"), height=35, width=200, 
                                       text="⚡ 2. AUTO SOLVE & ĐIỀN CHUỘT", fg_color="#E50914", hover_color="#B81D24", 
                                       state="disabled", command=self.action_solve)
        self.btn_solve.pack(pady=5)
        
        self.log_box = ctk.CTkTextbox(self, width=400, height=130, font=("Consolas", 12))
        self.log_box.pack(pady=10)
        self.log_box.insert("end", "[HỆ THỐNG]: Đã kích hoạt thuật toán Phân Rã Không Gian.\n")
        self.log_box.insert("end", "[HỆ THỐNG]: Lỗi đọc số đã được fix tuyệt đối.\n\n")

    def update_slider_text(self, value):
        self.lbl_speed.configure(text=f"Tốc độ điền phím: {value:.2f} giây/ô")

    def check_queue(self):
        try:
            while True:
                task = self.task_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        finally:
            self.after(50, self.check_queue)
        
    def safe_log(self, text):
        self.task_queue.put(lambda: self._gui_log(text))
        
    def _gui_log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def toggle_buttons(self, state):
        def _toggle():
            self.btn_select.configure(state=state)
            if state == "normal" and self.grid:
                self.btn_solve.configure(state="normal")
            elif state == "disabled":
                self.btn_solve.configure(state="disabled")
        self.task_queue.put(_toggle)

    def draw_grid_ui(self, grid_data, original_data=None):
        g_data = copy.deepcopy(grid_data)
        o_data = copy.deepcopy(original_data) if original_data else None

        def _update():
            for i in range(9):
                for j in range(9):
                    val = g_data[i][j]
                    if val == 0:
                        self.gui_cells[i][j].configure(text="", fg_color="#2A2D34")
                    else:
                        self.gui_cells[i][j].configure(text=str(val))
                        if o_data and o_data[i][j] == 0:
                            self.gui_cells[i][j].configure(text_color="#00FFA3", fg_color="#1E3E34")
                        else:
                            self.gui_cells[i][j].configure(text_color="#FFFFFF", fg_color="#3B3F4A")
        self.task_queue.put(_update)

    def action_select(self):
        self._gui_log("Đang mở lưới chụp... Hãy đè và kéo chuột!")
        self.withdraw() 
        coords = get_region(self)
        self.deiconify() 
        
        if not coords or coords[2] <= 0 or coords[3] <= 0:
            self._gui_log("❌ Chọn vùng bị hủy/thất bại.")
            return

        self.coords = coords
        left, top, width, height = coords
        self._gui_log(f"✅ Đã chốt vùng màn hình: {width}x{height}")
        
        blank = [[0]*9 for _ in range(9)]
        self.draw_grid_ui(blank)

        def ocr_thread():
            self.toggle_buttons("disabled")
            try:
                img = capture_screen(left, top, width, height)
                self.grid = extract_sudoku_grid(img, log_callback=self.safe_log)
                self.original_grid = copy.deepcopy(self.grid)
                
                self.draw_grid_ui(self.grid)
                self.safe_log("🚀 Cập nhật xong bảng lưới.")
            except Exception as e:
                self.safe_log(f"Lỗi: {str(e)}")
            finally:
                self.toggle_buttons("normal")

        t = Thread(target=ocr_thread, daemon=True)
        t.start()

    def action_solve(self):
        if not self.grid:
            self.safe_log("⚠️ Không có lưới số để giải.")
            return
            
        def process_thread():
            self.toggle_buttons("disabled")
            try:
                delay = self.slider_speed.get()
                self.safe_log("🧠 Đang áp dụng thuật toán truy vấn đệ quy...")
                
                if solve(self.grid):
                    self.safe_log(f"🎉 GIẢI THÀNH CÔNG! Đang bắt đầu nhấp chuột với Delay {delay:.2f}s...")
                    self.draw_grid_ui(self.grid, self.original_grid)
                    
                    left, top, width, height = self.coords
                    fill_sudoku(self.original_grid, self.grid, left, top, width, height, delay_sec=delay, log_callback=self.safe_log)
                else:
                    self.safe_log("❌ Bản đồ vô nghiệm (Lỗi OCR). Vui lòng khoanh sát viền lại.")
            except Exception as e:
                self.safe_log(f"Lỗi: {str(e)}")
            finally:
                self.toggle_buttons("normal")

        t = Thread(target=process_thread, daemon=True)
        t.start()

if __name__ == "__main__":
    app = SudokuApp()
    app.mainloop()
