import tkinter as tk
from utils.gui_setup import ApplicationGUI
from utils.user_data import load_user



username = "User"  
user_data = load_user(username)

if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicationGUI(root, user_data)
    root.mainloop()
       