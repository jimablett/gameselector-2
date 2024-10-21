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
import base64
import sys
import json

class GameSelectorApp:
    def __init__(self, master):
        self.master = master
        master.title("Game Selector 2")
        master.configure(bg='darkgrey')
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.label = tk.Label(master, text="Select PGN File:", bg='darkgrey', fg='black')
        self.label.pack()

        self.input_button = tk.Button(master, text="Browse", command=self.load_input_file, bg='lightgreen')
        self.input_button.pack()

        self.engine_label = tk.Label(master, text="Load Engine:", bg='darkgrey', fg='black')
        self.engine_label.pack()

        self.engine_button = tk.Button(master, text="Browse", command=self.load_engine_file, bg='lightgreen')
        self.engine_button.pack()

        self.download_button = tk.Button(master, text="Download Latest Stockfish", command=self.download_stockfish, bg='lightblue')
        self.download_button.pack()

        self.hash_label = tk.Label(master, text="Enter Hash Value: (mbytes)", bg='darkgrey', fg='black')
        self.hash_label.pack()

        self.hash_entry = tk.Entry(master, bg='darkgrey', fg='black')
        self.hash_entry.insert(0, "128")
        self.hash_entry.pack()
        self.hash_entry.bind("<FocusIn>", self.show_cursor)

        self.threads_label = tk.Label(master, text="Enter Number of Threads:", bg='darkgrey', fg='black')
        self.threads_label.pack()

        self.threads_entry = tk.Entry(master, bg='darkgrey', fg='black')
        self.threads_entry.insert(0, "4")
        self.threads_entry.pack()
        self.threads_entry.bind("<FocusIn>", self.show_cursor)

        self.margin_label = tk.Label(master, text="Enter Score Margin: (pawn unit)", bg='darkgrey', fg='black')
        self.margin_label.pack()

        self.margin_entry = tk.Entry(master, bg='darkgrey', fg='black')
        self.margin_entry.insert(0, "5.0")
        self.margin_entry.pack()
        self.margin_entry.bind("<FocusIn>", self.show_cursor)

        self.move_time_label = tk.Label(master, text="Enter Move Time (seconds):", bg='darkgrey', fg='black')
        self.move_time_label.pack()

        self.move_time_entry = tk.Entry(master, bg='darkgrey', fg='black')
        self.move_time_entry.insert(0, "2")
        self.move_time_entry.pack()
        self.move_time_entry.bind("<FocusIn>", self.show_cursor)

        self.keep_settings_var = tk.BooleanVar()
        self.keep_settings_checkbox = tk.Checkbutton(master, text="Save Settings", variable=self.keep_settings_var, command=self.save_settings, bg='darkgrey')
        self.keep_settings_checkbox.pack()

        self.restore_defaults_button = tk.Button(master, text="Restore Default Settings", command=self.restore_defaults, bg='darkgrey')
        self.restore_defaults_button.pack()

        self.run_button = tk.Button(master, text="Run", command=self.run_game_selector, bg='lightgreen')
        self.run_button.pack()

        self.quit_button = tk.Button(master, text="Quit", command=self.quit_application, bg='red', fg='white')
        self.quit_button.pack()

        self.info_button = tk.Button(master, text="Info", command=self.show_info, bg='lightblue')
        self.info_button.pack()

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
        self.load_settings()

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
        self.clear_output_folder()
        self.input_file = filedialog.askopenfilename(filetypes=[("PGN files", "*.pgn")])
        self.label.config(text=os.path.basename(self.input_file))

    def clear_output_folder(self):
        for filename in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

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
            'selector.exe',        
            '--input', self.input_file,
            '--output-good', self.output_good_file,
            '--output-bad', self.output_bad_file,
            '--engine', self.engine_file,
            '--hash', hash_value,
            '--threads', threads_value,
            '--score-margin', score_margin_value,
            '--move-time-sec', move_time_value
        ]

        if not os.path.exists('selector.exe'):
            messagebox.showerror("Error", "selector.exe not found in directory.")
            return

        self.progress.start()
        self.master.update()

        total_steps = 100
        for step in range(total_steps):
            time.sleep(0.1)
            self.progress['value'] = step + 1
            self.master.update()

        subprocess.Popen(['start', 'cmd', '/k'] + command, shell=True)

        self.progress.stop()
        messagebox.showinfo("Info", "Processing started in terminal.")

    def show_info(self):
        info_window = tk.Toplevel(self.master)
        info_window.title("Information")
        info_window.geometry("400x350")
        info_window.configure(bg='lightyellow')
        info_window.attributes('-topmost', True)
        info_text = (
            "\n"
            "This program analyzes a pgn and reviews the comment\n"
            "that the chess GUI makes at the end of each game, in \n"
            "order to remove the games that do not meet the following\n"
            "criteria:\n\n"
            "For a game to be removed, the side that\n"
            "lost on time/illegal move/crash should have an evaluation\n"
            "superior to the negative score_margin.\n\n"
            "For example:\n"
            "if the score margin is 5 and the eval of the losing\n"
            "(by time, illegal, etc.) side is -4.9, -3, 0, 5.5, etc.\n"
            "the game should be removed. The other condition to be\n"
            "removed is when an engine lost on time/illegal move/etc\n"
            "having > score margin advantage, but the chess GUI adjudicates\n"
            "a draw.\n\n"
            "The idea is to remove the games that could distort\n"
            "the rating list, i.e.: engine A had a big advantage to\n"
            "engine B, but lost on time and this changes the rating of all\n"
            "engines who played against them.\n\n"
        )
        text_label = tk.Label(info_window, text=info_text, justify="left", padx=10, pady=10, bg='lightyellow', fg='black')
        text_label.pack(expand=True, fill='both')

    def quit_application(self):
        for proc in psutil.process_iter():
            if proc.name() == "python.exe" or proc.name() == "python":
                proc.send_signal(signal.SIGTERM)
        self.master.quit()

    def on_closing(self):
        self.master.attributes('-topmost', 1)
        self.master.after_idle(self.master.attributes, '-topmost', 0)

    def show_cursor(self, event):
        event.widget.config(insertbackground='white')

    def save_settings(self):
        if self.keep_settings_var.get():
            settings = {
                "hash": self.hash_entry.get(),
                "threads": self.threads_entry.get(),
                "score_margin": self.margin_entry.get(),
                "move_time": self.move_time_entry.get()
            }
            with open("settings.json", "w") as f:
                json.dump(settings, f)

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.hash_entry.delete(0, tk.END)
                self.hash_entry.insert(0, settings.get("hash", "128"))
                self.threads_entry.delete(0, tk.END)
                self.threads_entry.insert(0, settings.get("threads", "4"))
                self.margin_entry.delete(0, tk.END)
                self.margin_entry.insert(0, settings.get("score_margin", "5.0"))
                self.move_time_entry.delete(0, tk.END)
                self.move_time_entry.insert(0, settings.get("move_time", "2"))

    def restore_defaults(self):
        self.hash_entry.delete(0, tk.END)
        self.hash_entry.insert(0, "128")
        self.threads_entry.delete(0, tk.END)
        self.threads_entry.insert(0, "4")
        self.margin_entry.delete(0, tk.END)
        self.margin_entry.insert(0, "5.0")
        self.move_time_entry.delete(0, tk.END)
        self.move_time_entry.insert(0, "2")
        self.keep_settings_var.set(False)

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes('-topmost', True)
    app = GameSelectorApp(root)
    root.update_idletasks()
    root.geometry(f"+{root.winfo_x()+root.winfo_width()}+{root.winfo_y()}")
    root.mainloop()

