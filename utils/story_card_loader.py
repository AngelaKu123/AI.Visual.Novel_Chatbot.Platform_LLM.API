import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .character_loader import CHARACTER_ROOT_DIR
from .gui_helper import center_window

# ---------------------------------------------------------------------------
#   Story‑card loader / creator
# ---------------------------------------------------------------------------
# Provides three pathways for enriching the chat context with extra JSON
# cards:
#   1) Pre‑defined files living under   /characters/<IP>/_extras/**/*.json
#   2) Arbitrary files the user imports via a file‑dialog before chatting
#   3) Brand‑new cards composed through a “New Story Card” mini‑editor
#
# All three paths yield dicts that flow unchanged into the LLM chain so both
# narrator and character agents can read whatever keys you decide to put in.
# ---------------------------------------------------------------------------

_EXTRA_SUBDIR = "_extras"   # change this if you prefer a different folder

# ══════════════════════ utility helpers ════════════════════════════════════

def _safe_load(path: str):
    """Load *one* json file – silently skip and log on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: broad‑except – robustness over purity
        print(f"[story_card_loader] Cannot load {path}: {exc}")
        return None


def _find_json_files(base_dir: str):
    """Yield absolute paths of all *.json files under *base_dir* recursively."""
    for root, _dirs, files in os.walk(base_dir):
        for fn in files:
            if fn.lower().endswith(".json"):
                yield os.path.join(root, fn)

# ══════════════════════ predefined cards ══════════════════════════════════

def load_predefined_cards(ip_name: str):
    """Return a list of built‑in cards that ship with the selected IP."""
    extras_root = os.path.join(CHARACTER_ROOT_DIR, ip_name, _EXTRA_SUBDIR)
    cards: list[dict] = []
    if os.path.isdir(extras_root):
        for p in _find_json_files(extras_root):
            if (card := _safe_load(p)):
                cards.append(card)
    return cards

# ══════════════════════ user‑selected external cards ══════════════════════

def choose_external_cards(parent_win=None):
    """Open a picker so the user can select additional JSON files."""
    paths = filedialog.askopenfilenames(
        parent=parent_win,
        title="Select additional JSON world / lore files",
        filetypes=[("JSON files", "*.json")],
    )
    cards: list[dict] = []
    for p in paths:
        if (card := _safe_load(p)):
            cards.append(card)
    return cards

# ══════════════════════ “New Story Card” creator ══════════════════════════

_CARD_TYPES = [
    "Location                                   (places & settings)",       
    "Item                                       (props, gear, artifacts)",          
    "Lore                                       (bits of world‐history or backstory)",           
    "Event                                      (incidents, encounters, turning points)",          
    "NPC                                        (non-player characters such as allies, villains, neutrals)",            
    "Faction                                    (groups, organizations, guilds)",        
    "Creatures                                  (beasts, monsters, spirits etc.)",       
    "Concept                                    (magical systems, philosophies, ideologies)",        
    "Theme                                      (motifs, moods, narrative tones)",          
    "Plot Point                                 (twists, cliffhangers, revelations)",     
    "Quest                                      (goals, missions, tasks)",           
    "Secret                                     (hidden facts, mysteries, rumors)",         
    "Symbol                                     (motifs, sigils, art‐ifactual meaning)",         
    "Mechanisms                                 (game-specific rules or interactions)",       
    "Challenge                                  (puzzles, obstacles, riddles)",     
    "Emotion                                    (themes of feeling or atmosphere)",       
    "Other",          
]


def new_story_card_dialog(parent_win=None):
    """Modal editor that mirrors your mock‑ups. Returns a dict or None."""

    dlg = tk.Toplevel(parent_win)
    dlg.title("New Story Card")
    dlg.geometry("700x500")   # sensible working area
    center_window(dlg)
    dlg.grab_set()             # modal – user must finish or cancel

    # Notebook – DETAILS | GENERATOR SETTINGS -----------------------------
    nb = ttk.Notebook(dlg)
    nb.pack(fill="both", expand=True, padx=10, pady=10)

    details_tab = ttk.Frame(nb); nb.add(details_tab, text="DETAILS")
    gen_tab     = ttk.Frame(nb); nb.add(gen_tab, text="GENERATOR SETTINGS")

    # ── DETAILS TAB ────────────────────────────────────────────────────
    row = 0
    ttk.Label(details_tab, text="TYPE", font=("Arial", 8, "bold"))\
        .grid(row=row, column=0, sticky="w")
    type_var = tk.StringVar(value=_CARD_TYPES[0])
    ttk.Combobox(details_tab, textvariable=type_var, values=_CARD_TYPES,
                 state="readonly").grid(row=row, column=1, sticky="ew", pady=2)
    details_tab.columnconfigure(1, weight=1)

    row += 1
    ttk.Label(details_tab, text="NAME", font=("Arial", 8, "bold"))\
        .grid(row=row, column=0, sticky="w")
    name_var = tk.StringVar()
    ttk.Entry(details_tab, textvariable=name_var)\
        .grid(row=row, column=1, sticky="ew", pady=2)

    # Placeholder – generate with AI (disabled)
    row += 1
    ttk.Button(details_tab, text="Place Holder",
               state="disabled").grid(row=row, column=1, sticky="e", pady=(0, 6))

    # Entry textbox
    row += 1
    ttk.Label(details_tab, text="ENTRY", font=("Arial", 8, "bold"))\
        .grid(row=row, column=0, sticky="nw")
    entry_txt = tk.Text(details_tab, height=8, wrap="word")
    entry_txt.grid(row=row, column=1, sticky="nsew", pady=2)
    details_tab.rowconfigure(row, weight=1)

    # Another placeholder
    row += 1
    ttk.Button(details_tab, text="Place Holder",
               state="disabled").grid(row=row, column=1, sticky="e")

    # Triggers
    row += 1
    ttk.Label(details_tab, text="TRIGGERS", font=("Arial", 8, "bold"))\
        .grid(row=row, column=0, sticky="w", pady=(6, 0))
    triggers_var = tk.StringVar()
    ttk.Entry(details_tab, textvariable=triggers_var)\
        .grid(row=row, column=1, sticky="ew", pady=(6, 0))

    # ── GENERATOR SETTINGS TAB (stub) ──────────────────────────────────
    ttk.Label(gen_tab, text="Nothing here yet – add temperature, top‑p, etc.",
              foreground="gray").pack(padx=10, pady=20)

    # ── Bottom bar ─────────────────────────────────────────────────────
    bar = ttk.Frame(dlg); bar.pack(fill="x", pady=8)
    bar.columnconfigure(0, weight=1)

    out: dict | None = None

    def _finish():
        nonlocal out
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Please enter a name for the card.")
            return
        out = {
            "type": type_var.get(),
            "name": name,
            "entry": entry_txt.get("1.0", "end").strip(),
            "triggers": [t.strip() for t in triggers_var.get().split(',') if t.strip()],
        }
        dlg.destroy()

    ttk.Button(bar, text="FINISH", command=_finish)\
        .grid(row=0, column=1, sticky="e", padx=10)

    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    dlg.wait_window()
    return out

# ══════════════════════ public combo helper ═══════════════════════════════

def gather_story_cards(ip_name: str, parent_win=None):
    """Return a list[dict] of cards (pre‑built + user chosen / created)."""

    cards = load_predefined_cards(ip_name)

    ans = messagebox.askyesnocancel(
        "Extra world‑info",
        "Would you like to add or create additional story‑cards before the chat?",
        parent=parent_win,
    )
    if ans is None:  # Cancel pressed
        return None

    if ans:  # YES → open helper window
        helper = tk.Toplevel(parent_win)
        helper.title("Additional World Information")
        helper.geometry("700x500")
        center_window(helper)
        helper.grab_set()   # modal – prevents stacking new helpers

        ttk.Label(helper,
                  text="Add cards to enrich the context before chatting.",
                  font=("Arial", 10, "bold"))\
            .pack(pady=(10, 4), padx=10)

        card_box = ttk.Frame(helper); card_box.pack(fill="both", expand=True, padx=10)
        card_box.columnconfigure(0, weight=1)

        listbox = tk.Listbox(card_box, height=8, selectmode="browse")
        listbox.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(card_box, orient="vertical", command=listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        listbox.config(yscrollcommand=sb.set)

        def _refresh_list():
            listbox.delete(0, "end")
            for c in cards:
                listbox.insert("end", f"{c.get('type', 'Info')}: {c.get('name', '(no name)')}")
        _refresh_list()

        # ---- buttons ---------------------------------------------------
        btns = ttk.Frame(helper); btns.pack(pady=6)

        def _add_new_card():
            new = new_story_card_dialog(helper)
            if new:
                cards.append(new)
                _refresh_list()

        ttk.Button(btns, text="New…", width=12, command=_add_new_card)\
            .pack(side="left", padx=4)

        def _import_cards():
            imported = choose_external_cards(helper)
            if imported:
                cards.extend(imported)
                _refresh_list()

        ttk.Button(btns, text="Import…", width=12, command=_import_cards)\
            .pack(side="left", padx=4)

        ttk.Button(btns, text="Done", width=12, command=helper.destroy)\
            .pack(side="left", padx=4)

        helper.wait_window()
        # grab_set() automatically released when destroyed

    return cards  # could be empty – caller decides how to handle
