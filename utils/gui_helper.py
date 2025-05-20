import tkinter as tk

def center_window(win: tk.Tk | tk.Toplevel):
    """Place *win* so its centre matches the screen centre."""
    win.update_idletasks()                     # geometry up-to-date
    w, h = win.winfo_width(),  win.winfo_height()
    if not (w and h):                          # first time fallback
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")
