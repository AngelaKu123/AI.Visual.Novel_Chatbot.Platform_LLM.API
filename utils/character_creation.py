import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from utils.character_loader import get_ips

# Root directory for character JSON files
CHARACTER_ROOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'characters')

# This function creates a new character JSON file under IP and optional unit/folder
def create_character(ip_name, character_data, unit_folder=None):
    ip_path = os.path.join(CHARACTER_ROOT_DIR, ip_name)
    if not os.path.exists(ip_path):
        os.makedirs(ip_path)

    if unit_folder:
        ip_path = os.path.join(ip_path, unit_folder)
        if not os.path.exists(ip_path):
            os.makedirs(ip_path)

    char_name = character_data["name"].strip().replace(" ", "_")
    file_path = os.path.join(ip_path, f"{char_name}.json")

    if os.path.exists(file_path):
        raise ValueError(f"Character '{char_name}' already exists under '{ip_path}'!")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(character_data, f, indent=4)

    return char_name

# This function creates the character creation popup window
def open_create_character_window(app):
    window = Toplevel(app.root)
    window.title("Create New Character")
    window.geometry("600x700")

    fields = [
        ("IP Name", tk.StringVar(value="")),
        ("Unit / Folder (optional)", tk.StringVar(value="")),
        ("Character Name", tk.StringVar()),
        ("Age", tk.StringVar()),
        ("Height (cm)", tk.StringVar()),
        ("Greeting", tk.StringVar()),
        ("Hair", tk.StringVar()),
        ("Eyes", tk.StringVar()),
        ("Build", tk.StringVar()),
        ("Notable Features (comma-separated)", tk.StringVar()),
        ("Style Type", tk.StringVar()),
        ("Style Description", tk.StringVar()),
        ("Background", tk.StringVar()),
        ("Catchphrases (comma-separated)", tk.StringVar()),
        ("Outfit Name", tk.StringVar()),
        ("Outfit Description", tk.StringVar())
    ]

    entries = {}
    for i, (label, var) in enumerate(fields):
        ttk.Label(window, text=label + ":").grid(row=i, column=0, padx=5, pady=5, sticky="w")
        entry = ttk.Entry(window, textvariable=var)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
        entries[label] = var

    def submit():
        try:
            ip = entries["IP Name"].get().strip()
            unit = entries["Unit / Folder (optional)"].get().strip() or None

            data = {
                "name": entries["Character Name"].get().strip(),
                "age": int(entries["Age"].get().strip()),
                "height_cm": int(entries["Height (cm)"].get().strip()),
                "greeting": entries["Greeting"].get().strip(),
                "appearance": {
                    "hair": entries["Hair"].get().strip(),
                    "eyes": entries["Eyes"].get().strip(),
                    "build": entries["Build"].get().strip(),
                    "notable_features": entries["Notable Features (comma-separated)"].get().split(", ")
                },
                "style": {
                    "type": entries["Style Type"].get().strip(),
                    "description": entries["Style Description"].get().strip()
                },
                "background": entries["Background"].get().strip(),
                "catchphrases": entries["Catchphrases (comma-separated)"].get().split(", "),
                "outfits": [{
                    "name": entries["Outfit Name"].get().strip(),
                    "description": entries["Outfit Description"].get().strip()
                }],
                "example_conversations": {}
            }

            created = create_character(ip, data, unit_folder=unit)
            location = f"{ip}/{unit}" if unit else ip
            messagebox.showinfo("Success", f"Character '{created}' created under '{location}'!")

            # Refresh dropdown in app after creation
            if hasattr(app, "ip_combo") and hasattr(app, "ip_var"):
                app.ip_combo['values'] = get_ips()
                app.ip_var.set(ip)

            window.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Button(window, text="Create", command=submit).grid(row=len(fields), column=0, columnspan=2, pady=10)
