import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import time
import multiprocessing
import signal
import psutil
from PIL import Image, ImageTk
import pkg_resources
import requests

class GameSelectorApp:
    def __init__(self, master):
        self.master = master
        master.title("Game Selector 2")
        master.configure(bg='black')
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        chessboard_image_path = pkg_resources.resource_filename(__name__, 'chessboard.bmp')
        self.background_image = ImageTk.PhotoImage(Image.open(chessboard_image_path))
        self.background_label = tk.Label(master, image=self.background_image)
        self.background_label.place(relwidth=1, relheight=1)

        self.label = tk.Label(master, text="Select PGN File:", bg='black', fg='white')
        self.label.pack()

        self.input_button = tk.Button(master, text="Browse", command=self.load_input_file, bg='lightgreen')
        self.input_button.pack()

        self.engine_label = tk.Label(master, text="Load Engine:", bg='black', fg='white')
        self.engine_label.pack()

        self.engine_button = tk.Button(master, text="Browse", command=self.load_engine_file, bg='lightgreen')
        self.engine_button.pack()

        self.download_button = tk.Button(master, text="Download Latest Stockfish", command=self.download_stockfish, bg='lightblue')
        self.download_button.pack()

        self.hash_label = tk.Label(master, text="Enter Hash Value: (mbytes)", bg='black', fg='white')
        self.hash_label.pack()

        self.hash_entry = tk.Entry(master, bg='black', fg='white')
        self.hash_entry.insert(0, "128")
        self.hash_entry.pack()

        self.threads_label = tk.Label(master, text="Enter Number of Threads:", bg='black', fg='white')
        self.threads_label.pack()

        self.threads_entry = tk.Entry(master, bg='black', fg='white')
        self.threads_entry.insert(0, "4")
        self.threads_entry.pack()

        self.margin_label = tk.Label(master, text="Enter Score Margin: (pawn unit)", bg='black', fg='white')
        self.margin_label.pack()

        self.margin_entry = tk.Entry(master, bg='black', fg='white')
        self.margin_entry.insert(0, "5.0")
        self.margin_entry.pack()

        self.move_time_label = tk.Label(master, text="Enter Move Time (seconds):", bg='black', fg='white')
        self.move_time_label.pack()

        self.move_time_entry = tk.Entry(master, bg='black', fg='white')
        self.move_time_entry.insert(0, "2")
        self.move_time_entry.pack()

        self.run_button = tk.Button(master, text="Run", command=self.run_game_selector, bg='lightgreen')
        self.run_button.pack()

        self.quit_button = tk.Button(master, text="Quit", command=self.quit_application, bg='red', fg='white')
        self.quit_button.pack()

        self.progress = ttk.Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.input_file = None
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_good_file = os.path.join(self.output_dir, "good.pgn")
        self.output_bad_file = os.path.join(self.output_dir, "bad.pgn")
        self.engine_file = None

        self.create_default_files()
        self.load_default_engine()

    def create_default_files(self):
        with open(self.output_good_file, "w") as good_file:
            good_file.write("")
        with open(self.output_bad_file, "w") as bad_file:
            bad_file.write("")

    def load_default_engine(self):
        default_engine_path = "stockfish_x64.exe"
        if os.path.exists(default_engine_path):
            self.engine_file = os.path.abspath(default_engine_path)
            self.engine_label.config(text=os.path.basename(self.engine_file))

    def load_input_file(self):
        self.input_file = filedialog.askopenfilename(filetypes=[("PGN files", "*.pgn")])
        self.label.config(text=os.path.basename(self.input_file))

    def load_engine_file(self):
        self.engine_file = filedialog.askopenfilename(filetypes=[("Engine files", "*.exe;*.bin")])
        self.engine_label.config(text=os.path.basename(self.engine_file))

    def download_stockfish(self):
        url = "https://chess.ultimaiq.net/stockfish_x64.exe"
        local_filename = "stockfish_x64.exe"
        
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            self.progress['maximum'] = total_size
            
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    self.progress['value'] += len(chunk)
                    self.master.update()
        
        self.engine_file = os.path.abspath(local_filename)
        self.engine_label.config(text=os.path.basename(self.engine_file))
        messagebox.showinfo("Info", "Stockfish downloaded and installed successfully.")

    def run_game_selector(self):
        if not all([self.input_file, self.engine_file]):
            messagebox.showerror("Error", "Please select all files.")
            return

        hash_value = self.hash_entry.get()
        threads_value = self.threads_entry.get()
        score_margin_value = self.margin_entry.get()
        move_time_value = self.move_time_entry.get()

        command = [
            'python', 'selector.py',             
            '--input', self.input_file,
            '--output-good', self.output_good_file,
            '--output-bad', self.output_bad_file,
            '--engine', self.engine_file,
            '--hash', hash_value,
            '--threads', threads_value,
            '--score-margin', score_margin_value,
            '--move-time-sec', move_time_value
        ]

        if not os.path.exists('selector.py'):
            messagebox.showerror("Error", "selector.py not found in directory.")
            return

        self.progress.start()
        self.master.update()

        total_steps = 100
        for step in range(total_steps):
            time.sleep(0.1)
            self.progress['value'] = step + 1
            self.master.update()

        process = multiprocessing.Process(target=subprocess.run, args=(command,))
        process.start()
        process.join()

        self.progress.stop()
        messagebox.showinfo("Info", "Processing finished.")

    def quit_application(self):
        for proc in psutil.process_iter():
            if proc.name() == "python.exe" or proc.name() == "python":
                proc.send_signal(signal.SIGTERM)
        self.master.quit()

    def on_closing(self):
        self.master.attributes('-topmost', 1)
        self.master.after_idle(self.master.attributes, '-topmost', 0)

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-topmost', True)
    app = GameSelectorApp(root)
    root.update_idletasks()
    root.geometry(f"+{root.winfo_x()+root.winfo_width()}+{root.winfo_y()}")
    root.mainloop()

