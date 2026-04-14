import tkinter as tk

class SnipUI:
    def __init__(self, master=None):
        if master:
            self.root = tk.Toplevel(master)
        else:
            self.root = tk.Tk()
            
        self.root.attributes('-alpha', 0.25)
        self.root.attributes('-topmost', True)
        self.root.config(cursor="cross")
        self.root.configure(background='black')
        
        self.root.attributes("-fullscreen", True)

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.rect = None
        self.start_x = None
        self.start_y = None
        self.cur_x = None
        self.cur_y = None
        self.coords = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = self.root.winfo_pointerx()
        self.start_y = self.root.winfo_pointery()
        self.rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, 
            outline='red', width=3, fill="red", stipple="gray25"
        )

    def on_move_press(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.canvas.canvasx(self.start_x - self.root.winfo_rootx()), 
                                    self.canvas.canvasy(self.start_y - self.root.winfo_rooty()), 
                                    cur_x, cur_y)

    def on_button_release(self, event):
        self.end_x = self.root.winfo_pointerx()
        self.end_y = self.root.winfo_pointery()

        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)

        self.coords = (x1, y1, x2 - x1, y2 - y1)
        
        if self.root.master:
            self.root.destroy()
            self.root.quit() # Stop the waiting mainloop for toplevel
        else:
            self.root.destroy()

def get_region(master=None):
    app = SnipUI(master)
    app.root.mainloop()
    return app.coords

if __name__ == "__main__":
    coords = get_region()
    print("Selected region:", coords)
