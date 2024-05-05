import tkinter as tk
from tkinter import filedialog, ttk  # ttk モジュールを追加
import pyautogui
import csv
import time
import cv2
import numpy as np
import pytesseract
from threading import Thread
from datetime import datetime
import unicodedata

# プログレスバーの時間が同期していないがまぁいいか。

# テキストをクリーンアップして非ASCII文字を取り除く関数
def clean_text(text):
    return ''.join(char for char in text if unicodedata.category(char)[0] != 'C')

class TransparentCanvas(tk.Canvas):
    def __init__(self, parent, recorder):
        # スクリーンサイズを取得
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
        
        # 位置情報を取得するボタン
        self.position_button = tk.Button(root, text="位置情報を取得", command=self.show_canvas)
        self.position_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        # テキストボックスとラベル
        tk.Label(root, text="範囲設定（左上の座標と幅・高さ）").grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        self.x_label = tk.Label(root, text="左上のX座標:")
        self.x_label.grid(row=5, column=0, padx=5, pady=5)
        self.x_entry = tk.Entry(root)
        self.x_entry.grid(row=5, column=1, padx=5, pady=5)
        self.y_label = tk.Label(root, text="左上のY座標:")
        self.y_label.grid(row=6, column=0, padx=5, pady=5)
        self.y_entry = tk.Entry(root)
        self.y_entry.grid(row=6, column=1, padx=5, pady=5)
        self.width_label = tk.Label(root, text="幅:")
        self.width_label.grid(row=7, column=0, padx=5, pady=5)
        self.width_entry = tk.Entry(root)
        self.width_entry.grid(row=7, column=1, padx=5, pady=5)
        self.height_label = tk.Label(root, text="高さ:")
        self.height_label.grid(row=8, column=0, padx=5, pady=5)
        self.height_entry = tk.Entry(root)
        self.height_entry.grid(row=8, column=1, padx=5, pady=5)

        # 時間間隔のテキストボックスとラベル
        #tk.Label(root, text="時間間隔設定（秒）").grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        self.interval_label = tk.Label(root, text="時間間隔(秒):")
        self.interval_label.grid(row=0, column=0, padx=5, pady=5)
        self.interval_entry = tk.Entry(root)
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5)

        # CSVファイル選択ボタン
        self.select_button = tk.Button(root, text="保存するCSVファイルを選択", command=self.select_csv_file)
        self.select_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        # CSVファイル名を表示するラベル
        self.csv_label = tk.Label(root, text="")
        self.csv_label.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        # スクリーンショット範囲確認ボタン
        self.confirm_button = tk.Button(root, text="スクリーンショット範囲を確認", command=self.confirm_screenshot)
        self.confirm_button.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

        # 開始と停止ボタン
        self.start_button = tk.Button(root, text="記録を開始", command=self.start_recording)
        self.start_button.grid(row=10, column=0, padx=5, pady=5)
        self.stop_button = tk.Button(root, text="記録を停止", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.grid(row=10, column=1, padx=5, pady=5)

        # テキスト表示用のラベル
        self.text_label = tk.Label(root, text="")
        self.text_label.grid(row=11, column=0, columnspan=2, padx=5, pady=5)

        # デフォルトの値設定
        self.x_entry.insert(0, "100")
        self.y_entry.insert(0, "100")
        self.width_entry.insert(0, "300")
        self.height_entry.insert(0, "200")
        self.interval_entry.insert(0, "5")

        # 初期化
        self.csv_filename = ""
        self.recording = False
        self.record_thread = None
        self.position_clicked = False
        
        self.progress_bar_step = 0.1  # プログレスバーの更新ステップを0.1に設定

        # プログレスバーの初期化
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.grid(row=12, column=0, columnspan=2, padx=5, pady=5)

    # CSVファイルを選択する
    def select_csv_file(self):
        self.csv_filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        self.csv_label.config(text=self.csv_filename)

    # スクリーンショット範囲を確認する
    def confirm_screenshot(self):
        x = int(self.x_entry.get())
        y = int(self.y_entry.get())
        width = int(self.width_entry.get())
        height = int(self.height_entry.get())

        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        cv2.imshow('Screenshot', cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # 位置情報を取得する
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

    # 記録を開始する
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
        
        self.progress_bar_interval = int(self.interval_entry.get()) * 100  # プログレスバー更新間隔を1目盛りごとに1秒に設定
        self.progress_bar_max = int(self.interval_entry.get())  # プログレスバーの最大値を入力した時間に設定
        self.progress_bar["maximum"] = self.progress_bar_max  # プログレスバーの最大値を更新
        self.progress_bar.update()
        self.progress_bar_value = 0  # プログレスバーの値をリセット
        self.progress_bar.start(self.progress_bar_interval)  # プログレスバーを開始（指定された時間間隔ごとに更新）

    # 記録を停止する
    def stop_recording(self):
        self.recording = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        self.progress_bar.stop()  # プログレスバーを停止

    # データを記録する
    def record_data(self, x, y, width, height, interval):
        if not self.csv_filename:
            print("CSVファイルを選択してください。")
            return

        with open(self.csv_filename, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            while self.recording:
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                #screenshot.save('temp.png')

                # 画像からテキストを抽出する
                text = pytesseract.image_to_string(screenshot)
                
                # テキストをクリーンアップ
                cleaned_text = clean_text(text)
                csv_writer.writerow([datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), cleaned_text])

                # テキストをGUIに表示する
                self.text_label.config(text=cleaned_text)
                
                # プログレスバーの値を更新
                self.progress_bar_value += self.progress_bar_step
                if self.progress_bar_value >= self.progress_bar_max:
                    self.progress_bar_value = 0  # プログレスバーの値が最大値に達したらリセット
                self.progress_bar_max = int(self.interval_entry.get())  # プログレスバーの最大値を設定

                self.root.update_idletasks()  # GUIの更新

                time.sleep(interval)

def main():
    root = tk.Tk()
    app = ScreenshotRecorder(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    
# pyinstaller -F --noconsole SS_temp_read2.py