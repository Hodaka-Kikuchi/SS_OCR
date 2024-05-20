import tkinter as tk
from tkinter import filedialog, ttk
import pyautogui
import time
from threading import Thread
from datetime import datetime
import numpy as np

class TransparentCanvas(tk.Canvas):
    def __init__(self, parent, recorder):
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        tk.Canvas.__init__(self, parent, bg="gray", highlightthickness=0, width=screen_width, height=screen_height)
        self.recorder = recorder
        self.parent = parent
        self.bind("<Button-1>", self.on_mouse_click)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.rect = None
        self.start_x = None
        self.start_y = None

    def on_mouse_click(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def on_mouse_drag(self, event):
        cur_x = event.x
        cur_y = event.y
        self.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_mouse_release(self, event):
        end_x = event.x
        end_y = event.y
        if self.start_x > end_x:
            self.start_x, end_x = end_x, self.start_x
        if self.start_y > end_y:
            self.start_y, end_y = end_y, self.start_y
        self.recorder.update_position((self.start_x, self.start_y, end_x - self.start_x, end_y - self.start_y))

class ScreenshotRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("Screenshot Recorder")
        
        self.position_button = tk.Button(root, text="Obtain location information", command=self.show_canvas)
        self.position_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        tk.Label(root, text="Set range (top-left X coordinate, Y coordinate, width, height)").grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.x_label = tk.Label(root, text="top-left X　coordinate:")
        self.x_label.grid(row=5, column=0, padx=5, pady=5)
        self.x_entry = tk.Entry(root)
        self.x_entry.grid(row=5, column=1, padx=5, pady=5)
        self.y_label = tk.Label(root, text="top-left Y coordinate:")
        self.y_label.grid(row=6, column=0, padx=5, pady=5)
        self.y_entry = tk.Entry(root)
        self.y_entry.grid(row=6, column=1, padx=5, pady=5)
        self.width_label = tk.Label(root, text="width:")
        self.width_label.grid(row=7, column=0, padx=5, pady=5)
        self.width_entry = tk.Entry(root)
        self.width_entry.grid(row=7, column=1, padx=5, pady=5)
        self.height_label = tk.Label(root, text="height:")
        self.height_label.grid(row=8, column=0, padx=5, pady=5)
        self.height_entry = tk.Entry(root)
        self.height_entry.grid(row=8, column=1, padx=5, pady=5)

        self.interval_label = tk.Label(root, text="Time interval (seconds):")
        self.interval_label.grid(row=0, column=0, padx=5, pady=5)
        self.interval_entry = tk.Entry(root)
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5)

        self.select_button = tk.Button(root, text="Select directory to save", command=self.select_save_directory)
        self.select_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        self.directory_label = tk.Label(root, text="")
        self.directory_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.confirm_button = tk.Button(root, text="Confirm screenshot area", command=self.confirm_screenshot)
        self.confirm_button.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

        self.start_button = tk.Button(root, text="Start recording", command=self.start_recording)
        self.start_button.grid(row=10, column=0, padx=5, pady=5)
        self.stop_button = tk.Button(root, text="Stop recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.grid(row=10, column=1, padx=5, pady=5)

        self.text_label = tk.Label(root, text="")
        self.text_label.grid(row=11, column=0, columnspan=2, padx=5, pady=5)

        self.x_entry.insert(0, "100")
        self.y_entry.insert(0, "100")
        self.width_entry.insert(0, "300")
        self.height_entry.insert(0, "200")
        self.interval_entry.insert(0, "60")

        self.save_directory = ""
        self.recording = False
        self.record_thread = None
        self.position_clicked = False
        
        self.progress_bar_step = 0.1
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.grid(row=12, column=0, columnspan=2, padx=5, pady=5)

    def select_save_directory(self):
        self.save_directory = filedialog.askdirectory()
        self.directory_label.config(text=self.save_directory)

    def confirm_screenshot(self):
        x = int(self.x_entry.get())
        y = int(self.y_entry.get())
        width = int(self.width_entry.get())
        height = int(self.height_entry.get())

        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot.show()


    def show_canvas(self):
        self.canvas_window = tk.Toplevel(self.root)
        self.canvas_window.attributes("-alpha", 0.5)
        self.canvas_window.overrideredirect(True)
        self.canvas_window.attributes("-topmost", True)
        self.canvas = TransparentCanvas(self.canvas_window, self)
        self.canvas.pack(fill="both", expand=True)

    def update_position(self, position):
        x, y, width, height = position
        self.x_entry.delete(0, tk.END)
        self.y_entry.delete(0, tk.END)
        self.width_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)
        self.x_entry.insert(0, str(x))
        self.y_entry.insert(0, str(y))
        self.width_entry.insert(0, str(width))
        self.height_entry.insert(0, str(height))
        self.canvas_window.destroy()

    def start_recording(self):
        self.recording = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        x = int(self.x_entry.get())
        y = int(self.y_entry.get())
        width = int(self.width_entry.get())
        height = int(self.height_entry.get())
        interval = int(self.interval_entry.get())
        self.record_thread = Thread(target=self.record_data, args=(x, y, width, height, interval))
        self.record_thread.start()
        
        self.progress_bar_interval = 1000  # ミリ秒単位で設定
        self.progress_bar_max = interval
        self.progress_bar["maximum"] = self.progress_bar_max
        self.progress_bar.update()
        self.progress_bar_value = 0
        self.progress_bar.start(self.progress_bar_interval)

    def stop_recording(self):
        self.recording = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()

    def record_data(self, x, y, width, height, interval):
        if not self.save_directory:
            print("Please select the directory to save.")
            self.recording = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress_bar.stop()
            return

        while self.recording:
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"{self.save_directory}/{timestamp}.png"
            screenshot.save(file_path)
            self.text_label.config(text=f"Saved: {file_path}")
            
            # プログレスバーを更新
            self.progress_bar_value += 1
            if self.progress_bar_value >= self.progress_bar_max:
                self.progress_bar_value = 0
            self.progress_bar["value"] = self.progress_bar_value
            self.root.update_idletasks()
            time.sleep(interval)

def main():
    root = tk.Tk()
    app = ScreenshotRecorder(root)
    root.mainloop()

if __name__ == "__main__":
    main()

# pyinstaller -F --noconsole SS_temp.py