import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import json
import threading
import time
from plyer import notification
import os
import sys
import ctypes
import winreg
import pystray
from PIL import Image, ImageDraw

TODO_FILE = "todos.json"


def load_tasks_from_file():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks_to_file(tasks):
    with open(TODO_FILE, "w") as f:
        json.dump(tasks, f, indent=4)


def reminder_loop():
    while True:
        tasks = load_tasks_from_file()
        now = datetime.now()
        updated = False
        for task in tasks:
            if not task["done"] and task.get("reminder"):
                reminder_time = datetime.fromisoformat(task["reminder"])
                if now >= reminder_time:
                    notification.notify(
                        title="📌 Reminder",
                        message=f"⏰ Task: {task['task']}",
                        timeout=10,
                        app_name="To-Do App"
                    )
                    task["reminder"] = None
                    updated = True
        if updated:
            save_tasks_to_file(tasks)
        time.sleep(60)


def enable_autostart():
    if sys.platform.startswith("win"):
        exe_path = sys.executable
        script_path = os.path.realpath(__file__)
        command = f'"{exe_path}" "{script_path}"'
        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        try:
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "TodoApp", 0, winreg.REG_SZ, command)
        except Exception as e:
            print("Failed to set startup: ", e)


def create_system_tray_icon(app):
    image = Image.new('RGB', (64, 64), (255, 255, 255))
    d = ImageDraw.Draw(image)
    d.rectangle((10, 10, 54, 54), fill=(0, 102, 204))

    def on_show(icon, item):
        app.root.after(0, app.show_main_window)

    def on_exit(icon, item):
        icon.stop()
        app.root.after(0, app.root.quit)

    icon = pystray.Icon("TodoApp", image, "To-Do App", menu=pystray.Menu(
        pystray.MenuItem("Show", on_show),
        pystray.MenuItem("Quit", on_exit)
    ))
    threading.Thread(target=icon.run, daemon=True).start()


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do App with Reminders")
        self.root.geometry("600x400")
        self.root.configure(bg="#f7f9fb")

        self.task_entry = tk.Entry(root, width=50, font=("Arial", 12))
        self.task_entry.pack(pady=10)

        self.add_button = tk.Button(root, text="➕ Add Task", command=self.add_task, bg="#28a745", fg="white", font=("Arial", 11))
        self.add_button.pack(pady=5)

        self.tasks_listbox = tk.Listbox(root, width=80, font=("Consolas", 11))
        self.tasks_listbox.pack(pady=10)

        self.done_button = tk.Button(root, text="✔ Done", command=self.mark_task_done, bg="#007bff", fg="white", font=("Arial", 11))
        self.done_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.delete_button = tk.Button(root, text="❌ Delete", command=self.delete_task, bg="#dc3545", fg="white", font=("Arial", 11))
        self.delete_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        create_system_tray_icon(self)
        self.load_tasks()
        threading.Thread(target=reminder_loop, daemon=True).start()

    def minimize_to_tray(self):
        self.root.withdraw()

    def show_main_window(self):
        self.root.deiconify()

    def add_task(self):
        task_text = self.task_entry.get()
        if not task_text:
            messagebox.showwarning("Warning", "Enter a task!")
            return

        remind_in = simpledialog.askinteger("Reminder", "Remind in how many minutes? (Optional)", initialvalue=0)
        reminder_time = (datetime.now() + timedelta(minutes=remind_in)).isoformat() if remind_in else None

        tasks = load_tasks_from_file()
        tasks.append({"task": task_text, "done": False, "reminder": reminder_time})
        save_tasks_to_file(tasks)
        self.task_entry.delete(0, tk.END)
        self.load_tasks()

    def load_tasks(self):
        self.tasks_listbox.delete(0, tk.END)
        tasks = load_tasks_from_file()
        for i, task in enumerate(tasks):
            status = "✅" if task["done"] else "❌"
            reminder = f" | ⏰ {task['reminder']}" if task.get("reminder") else ""
            self.tasks_listbox.insert(tk.END, f"{i+1}. {status} {task['task']}{reminder}")

    def mark_task_done(self):
        selection = self.tasks_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        tasks = load_tasks_from_file()
        tasks[index]["done"] = True
        save_tasks_to_file(tasks)
        self.load_tasks()

    def delete_task(self):
        selection = self.tasks_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        tasks = load_tasks_from_file()
        tasks.pop(index)
        save_tasks_to_file(tasks)
        self.load_tasks()


if __name__ == "__main__":
    enable_autostart()
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
