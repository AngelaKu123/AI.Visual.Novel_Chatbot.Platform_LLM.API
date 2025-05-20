import os
import json
import tkinter as tk
from tkinter import ttk

from utils.character_loader import (
    get_ips,
    get_characters_by_ip,
    load_character,
)
from utils.character_creation import open_create_character_window
from utils.gui_chatroom import open_chatroom
from utils.gui_helper import center_window
from utils.recommender import recommend_characters
from utils.story_card_loader import gather_story_cards
# ───────────────────────── home‑screen class ───────────────────────────────
class ApplicationGUI:
    """Main selector / homepage for the chatbot GUI."""

    # ------------------------------------------------------------------
    #   Init & window‑level tweaks
    # ------------------------------------------------------------------
    def __init__(self, root: tk.Tk, user_data: dict):
        self.root = root
        self.root.title("AI ChatBot Character Selector")

        # Give the window a sensible starting footprint & min size so
        # the widgets aren’t cramped on high‑DPI screens.
        self.root.geometry("900x600")
        self.root.minsize(800, 550)
        # Allow resizing – the layout uses *pack* + *expand* wisely.
        self.root.resizable(True, True)

        # navigation history (future: back / forward)
        self.context_stack: list[tuple[str, str]] = []
        self.forward_stack: list[tuple[str, str]] = []

        self.user_data = user_data
        self.current_frame: ttk.Frame | None = None

        self.build_homepage()
        center_window(root)  # centre AFTER a geometry is set

    # ------------------------------------------------------------------
    #   Helpers
    # ------------------------------------------------------------------
    def clear_frame(self) -> None:
        """Destroy the previous frame and create a fresh one."""
        if self.current_frame and self.current_frame.winfo_exists():
            self.current_frame.destroy()
        self.current_frame = ttk.Frame(self.root)
        self.current_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    #   Homepage (character picker)
    # ------------------------------------------------------------------
    def build_homepage(self) -> None:
        self.clear_frame()

        ttk.Label(
            self.current_frame,
            text="Choose a Character",
            font=("Arial", 18, "bold"),
        ).pack(pady=10)

        # --- layout:  ☐ IP‑tree | ☐ hint / preview | ☐ recommendations
        content = ttk.Frame(self.current_frame)
        content.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT – collapsible IP / Unit tree -----------------------------
        l_canvas = tk.Canvas(content, width=260, highlightthickness=0)
        l_scroll = ttk.Scrollbar(content, orient="vertical", command=l_canvas.yview)
        l_inner = ttk.Frame(l_canvas)

        l_inner.bind(
            "<Configure>", lambda e: l_canvas.configure(scrollregion=l_canvas.bbox("all"))
        )
        l_canvas.create_window((0, 0), window=l_inner, anchor="nw")
        l_canvas.configure(yscrollcommand=l_scroll.set)
        l_canvas.pack(side="left", fill="y")
        l_scroll.pack(side="left", fill="y")

        # CENTRE – hint text / (future) preview -------------------------
        c_frame = ttk.Frame(content)
        c_frame.pack(side="left", fill="both", expand=True)
        ttk.Label(
            c_frame,
            text="← Choose a character from the list",
            font=("Arial", 12),
        ).pack(pady=40)

        # RIGHT – recommended characters --------------------------------
        r_frame = ttk.Frame(content, width=240)
        r_frame.pack(side="right", fill="y", padx=5)
        ttk.Label(r_frame, text="Recommended", font=("Arial", 12, "bold")).pack(pady=5)

        for rec in recommend_characters(self.user_data) or []:
            ttk.Button(
                r_frame,
                text=os.path.basename(rec["path"]),
                command=lambda ip=rec["ip"], p=rec["path"]: self.enter_chat(ip, p),
            ).pack(anchor="w", fill="x", padx=5, pady=2)

        # Build the collapsible IP‑tree ----------------------------------
        self._build_ip_tree(l_inner)

        # ACTION buttons under the tree ----------------------------------
        ttk.Button(
            self.current_frame,
            text="Create New Character",
            command=lambda: open_create_character_window(self),
        ).pack(pady=10)
        ttk.Button(
            self.current_frame, text="View My Preferences", command=self.show_user_profile
        ).pack(pady=5)

    # ------------------------------------------------------------------
    #   Collapsible tree helpers
    # ------------------------------------------------------------------
    def _build_ip_tree(self, container: ttk.Frame):
        self.ip_sections: dict[str, dict] = {}

        for ip in get_ips():
            # IP header ----------------------------------------------------
            ip_frame = ttk.Frame(container)
            ip_frame.pack(fill="x", pady=2, padx=5)
            hdr = ttk.Label(ip_frame, text=f"▸ {ip}", font=("Arial", 10, "bold"))
            hdr.pack(fill="x")

            # container for its units
            unit_wrap = ttk.Frame(ip_frame)
            unit_wrap.pack(fill="x")
            unit_wrap.pack_forget()

            hdr.bind("<Button-1>", lambda e, key=ip: self.toggle_ip(key))

            # group characters by unit folder
            grouped: dict[str, list[str]] = {}
            for ch in get_characters_by_ip(ip):
                unit, name = ch.split("/", 1) if "/" in ch else ("Others", ch)
                grouped.setdefault(unit, []).append(name)

            units_dict: dict[str, dict] = {}
            for unit, names in sorted(grouped.items()):
                u_frame = ttk.Frame(unit_wrap)
                u_frame.pack(fill="x", padx=10, pady=1)
                u_hdr = ttk.Label(u_frame, text=f"▸ {unit}", font=("Arial", 9, "italic"))
                u_hdr.pack(fill="x")

                char_list = ttk.Frame(u_frame)
                char_list.pack(fill="x", padx=10)
                char_list.pack_forget()

                for nm in sorted(names):
                    full = f"{unit}/{nm}"
                    ttk.Button(
                        char_list,
                        text=nm,
                        width=28,
                        command=lambda i=ip, c=full: self.enter_chat(i, c),
                    ).pack(padx=1, pady=1, anchor="w")

                u_hdr.bind(
                    "<Button-1>", lambda e, k_ip=ip, k_unit=unit: self.toggle_unit(k_ip, k_unit)
                )

                units_dict[unit] = {
                    "header": u_hdr,
                    "char_list": char_list,
                    "expanded": False,
                }

            self.ip_sections[ip] = {
                "header": hdr,
                "frame": unit_wrap,
                "expanded": False,
                "units": units_dict,
            }

    def toggle_ip(self, ip: str):
        sec = self.ip_sections[ip]
        if sec["expanded"]:
            sec["frame"].pack_forget()
            sec["header"].config(text=f"▸ {ip}")
        else:
            sec["frame"].pack(fill="x")
            sec["header"].config(text=f"▾ {ip}")
        sec["expanded"] = not sec["expanded"]

    def toggle_unit(self, ip: str, unit: str):
        unit_info = self.ip_sections[ip]["units"][unit]
        if unit_info["expanded"]:
            unit_info["char_list"].pack_forget()
            unit_info["header"].config(text=f"▸ {unit}")
        else:
            unit_info["char_list"].pack(fill="x")
            unit_info["header"].config(text=f"▾ {unit}")
        unit_info["expanded"] = not unit_info["expanded"]

    # ------------------------------------------------------------------
    #   Chat navigation
    # ------------------------------------------------------------------
    def enter_chat(self, ip: str, path: str):
        """Load the chosen character, gather story‑cards, then open chat‑room."""
        character = load_character(ip, path)

        # Pull in any user‑selected or auto‑extras ------------------------
        cards = gather_story_cards(ip, self.root)
        if cards:
            snippets: list[str] = []
            for c in cards:
                entry = (
                    c.get("entry")
                    or c.get("description")
                    or json.dumps(c, ensure_ascii=False)
                )
                tag = c.get("name") or c.get("type", "Info")
                snippets.append(f"*{tag}*: {entry}")

            character = character.copy()  # don’t mutate shared cache
            greeting = character.get("greeting", "")
            character["greeting"] = "\n\n".join(snippets + [greeting])

        # push onto history & open chat
        self.context_stack.append((ip, path))
        self.forward_stack.clear()
        open_chatroom(self.root, self, character, self.user_data,)

    # ------------------------------------------------------------------
    #   Misc helpers
    # ------------------------------------------------------------------
    def show_user_profile(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Your Preference Tags")
        win.geometry("420x320")
        center_window(win)

        ttk.Label(win, text="Inferred Tags", font=("Arial", 14, "bold")).pack(pady=10)

        from utils.user_data import extract_user_tags

        tags = extract_user_tags(self.user_data)
        if not tags:
            ttk.Label(win, text="No tags collected yet. Start chatting!").pack(pady=10)
            return

        tag_frame = ttk.Frame(win)
        tag_frame.pack(fill="both", expand=True, padx=15, pady=5)
        for tag in sorted(tags):
            ttk.Label(tag_frame, text=f"• {tag}", font=("Arial", 10)).pack(anchor="w")

    # Navigation stubs ---------------------------------------------------
    def go_back(self):
        for w in self.root.winfo_children():
            w.destroy()
        self.current_frame = None
        self.build_homepage()

    def go_forward(self):
        if self.forward_stack:
            self.enter_chat(*self.forward_stack.pop())
