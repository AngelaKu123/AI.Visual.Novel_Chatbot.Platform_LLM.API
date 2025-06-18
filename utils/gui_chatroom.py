import json, os, sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from utils.chat_logic import build_character_chain, build_narrator_chain, process_turn, memory
from utils.user_data import update_user_tags
from utils.gui_helper import center_window

# ──────────── helper text editor ────────────
def big_text_dialog(parent, title, initial=""):
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.grab_set()
    txt = tk.Text(dlg, width=80, height=10, wrap="word", font=("Arial", 12))
    txt.pack(fill="both", expand=True)
    txt.insert("1.0", initial)

    out = {"val": None}
    btns = ttk.Frame(dlg); btns.pack(pady=4)
    ttk.Button(btns, text="OK",
               command=lambda: (out.update(val=txt.get("1.0","end").rstrip()), dlg.destroy())
    ).pack(side="left", padx=4)
    ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="left")
    dlg.bind("<Escape>", lambda e: dlg.destroy())
    dlg.wait_window()
    return out["val"]

# ──────────── debug: show memory ────────────
def show_memory_debug(root):
    win = tk.Toplevel(root)
    win.title("Memory Debug")
    win.geometry("800x600")
    center_window(win)

    # Rolling summary
    ttk.Label(win, text="Summary:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,0))
    summary_txt = tk.Text(win, height=5, wrap="word")
    summary_txt.pack(fill="x", padx=10)
    summary_txt.insert("1.0", memory.summary or "(empty)")
    summary_txt.config(state="disabled")

    # Extracted facts
    ttk.Label(win, text="Facts:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,0))
    facts_txt = tk.Text(win, height=10, wrap="word")
    facts_txt.pack(fill="both", expand=True, padx=10, pady=(0,10))
    facts_txt.insert("1.0", json.dumps(memory.fact_memory, indent=2, ensure_ascii=False))
    facts_txt.config(state="disabled")


# ──────────── message widgets ────────────
class UserBox(ttk.Frame):
    def __init__(self, parent, text, on_edit, on_del):
        super().__init__(parent)
        self.msg = tk.StringVar(value=text)
        ttk.Label(self, text="You:", style="User.TLabel").pack(anchor="w")
        ttk.Label(self, textvariable=self.msg, wraplength=600,
                  style="User.TLabel").pack(anchor="w", padx=5)
        bar = ttk.Frame(self); bar.pack(anchor="e")
        ttk.Button(bar, text="Edit",  width=6,
                   command=lambda: self._edit(on_edit)).pack(side="left")
        ttk.Button(bar, text="Delete",width=6,
                   command=lambda: on_del(self)).pack(side="left")

    def _edit(self, cb):
        new = big_text_dialog(self, "Edit message", self.msg.get())
        if new is not None:
            old = self.msg.get()
            self.msg.set(new)
            cb(self, old, new)

class ReplyBox(ttk.Frame):
    def __init__(self, parent, char_name, on_regen, on_edit, on_del):
        super().__init__(parent)
        self.vers, self.idx = [], -1

        self.narr_lbl = ttk.Label(self, style="Narr.TLabel",
                                  wraplength=600, justify="left")
        self.char_hdr = ttk.Label(self, text=f"{char_name}:", style="CharHdr.TLabel")
        self.reply_lbl= ttk.Label(self, style="Char.TLabel",
                                  wraplength=600, justify="left")

        self.narr_lbl.pack(anchor="w", padx=5)
        self.char_hdr.pack(anchor="w")
        self.reply_lbl.pack(anchor="w", padx=5)

        bar = ttk.Frame(self); bar.pack(anchor="e", pady=2)
        self.prev_b = ttk.Button(bar, text="◀", width=2, command=lambda: self._flip(-1))
        self.next_b = ttk.Button(bar, text="▶", width=2, command=lambda: self._flip(1))
        ttk.Button(bar, text="↻", width=2, command=lambda: on_regen(self)).pack(side="left")
        ttk.Button(bar, text="Edit", width=6, command=lambda: on_edit(self)).pack(side="left")
        ttk.Button(bar, text="Delete", width=6, command=lambda: on_del(self)).pack(side="left")
        self.prev_b.pack(side="left"); self.next_b.pack(side="left")

    def start_new_version(self):
        self.vers.append({"narr": "*", "reply": ""})
        self.idx = len(self.vers) - 1
        self._render()

    def append_narr(self, tok):
        self.vers[self.idx]["narr"] += tok
        self.narr_lbl.config(text=self.vers[self.idx]["narr"])

    def end_narr(self):
        self.vers[self.idx]["narr"] += "*"
        self.narr_lbl.config(text=self.vers[self.idx]["narr"])

    def append_reply(self, tok):
        self.vers[self.idx]["reply"] += tok
        self.reply_lbl.config(text=self.vers[self.idx]["reply"])

    def _flip(self, step):
        new = self.idx + step
        if 0 <= new < len(self.vers):
            self.idx = new
            self._render()

    def _render(self):
        narr = self.vers[self.idx]["narr"]
        rep  = self.vers[self.idx]["reply"]
        self.narr_lbl.config(text=narr)
        self.reply_lbl.config(text=rep)
        self.prev_b.state(["disabled"] if self.idx == 0 else ["!disabled"])
        self.next_b.state(["disabled"] if self.idx == len(self.vers)-1 else ["!disabled"])

# ──────────── Main Chatroom ────────────
def open_chatroom(root, app_gui, character, user_data):
    try: root.state("zoomed")
    except tk.TclError:
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    for w in root.winfo_children(): w.destroy()

    # Styles
    sty = ttk.Style(root)
    sty.configure("User.TLabel",   font=("Arial",12,"bold"))
    sty.configure("Narr.TLabel",   font=("Arial",12,"italic"), foreground="gray")
    sty.configure("CharHdr.TLabel",font=("Arial",12,"bold"))
    sty.configure("Char.TLabel",   font=("Arial",12))

    btn_memory = ttk.Button(
    root,
    text="View Memory",
    command=lambda: show_memory_debug(root)
    )
    # put it in the top-right corner:
    btn_memory.grid(row=1, column=2, sticky="e", padx=10, pady=5)


    # LLM chains
    chain      = build_character_chain(character)
    narr_chain = build_narrator_chain(character)

    # Initial greeting → raw context
    raw     = character.get("greeting","")
    lines   = raw.splitlines()
    hidden  = "\n".join([ln for ln in lines if ln.strip().startswith("*")])
    visible = "\n".join([ln for ln in lines if not ln.strip().startswith("*")]).strip()
    context = "\n\n".join(filter(None, [hidden, visible]))

    # layout grid: three columns → left spacer, chat, right spacer
    col_w = root.winfo_screenwidth() // 2
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=0)
    root.columnconfigure(2, weight=1)
    root.rowconfigure(0, weight=1)
    root.rowconfigure(1, weight=0)

    # feed frame goes in the middle column
    feed_wrap = ttk.Frame(root, width=col_w)
    feed_wrap.grid(row=0, column=1, sticky="nsew")
    feed_wrap.grid_propagate(False)
    canvas = tk.Canvas(feed_wrap, width=col_w, highlightthickness=0)
    vbar   = ttk.Scrollbar(feed_wrap, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)
    canvas.pack(side="left", fill="both", expand=True); vbar.pack(side="right", fill="y")

    feed = ttk.Frame(canvas, width=col_w)
    canvas.create_window((0,0), window=feed, anchor="nw")
    feed.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Show greeting
    ttk.Label(feed, text=f"{character['name']}:\n{visible}",
              style="Char.TLabel", wraplength=col_w-40, justify="left")\
        .pack(anchor="w", padx=5, pady=4)
    ttk.Separator(feed, orient="horizontal").pack(fill="x", pady=2)

    # Input
    inp = tk.Text(root, height=1, font=("Arial",12), wrap="word")
    inp.grid(row=1, column=1, sticky="ew", padx=10, pady=5); inp.focus_set()
    def _grow(_=None):
        lines = int(inp.index("end-1c").split('.')[0])
        inp.config(height=min(max(lines,1),10))
    inp.bind("<KeyRelease>", _grow)

    def scroll_bot():
        root.update_idletasks()
        canvas.yview_moveto(1.0)

    # ─── Context management & deletion ───
    def rebuild_context():
        nonlocal context
        pieces = [raw]
        for child in feed.winfo_children():
            if isinstance(child, UserBox):
                pieces.append(f"User: {child.msg.get()}")
            elif isinstance(child, ReplyBox):
                cur = child.vers[child.idx]
                pieces.append(f"{character['name']}: {cur['reply']}")
        context = "\n\n".join(pieces[-300:])

    def cascade_delete(box):
        idx = feed.winfo_children().index(box)
        for c in feed.winfo_children()[idx:][::-1]:
            c.destroy()
        rebuild_context()

    # ─── Adding boxes ───
    def add_user_box(txt):
        def _edit(b, old, new):
            nonlocal context
            context = context.replace(old, new)
            rebuild_context()
        def _del(b): cascade_delete(b)

        b = UserBox(feed, txt, _edit, _del)
        b.pack(anchor="w", fill="x", padx=5, pady=4)
        scroll_bot()
        return b

    active_reply = {"box": None}

    def add_reply_box():
        def _edit(b):
            cur = b.vers[b.idx]["reply"]
            new = big_text_dialog(root, "Edit reply", cur)
            if new:
                b.vers[b.idx]["reply"] = new
                b._render()
                rebuild_context()
        def _del(b): cascade_delete(b)

        rb = ReplyBox(feed, character['name'], regen, _edit, _del)
        rb.pack(anchor="e", fill="x", padx=5, pady=4)
        active_reply["box"] = rb
        return rb

    last_user = None

    # ─── Continue / Regenerate ───
    def continue_reply():
        rb = active_reply.get("box")
        if not rb or not rb.winfo_exists(): return
        narr_toks, char_toks, new_ctx = process_turn(
            character, chain, narr_chain, context, ""
        )
        for tok in char_toks:
            rb.append_reply(tok); scroll_bot()
        rebuild_context()

    def regenerate_after_delete():
        rb = add_reply_box(); rb.start_new_version()
        narr_toks, char_toks, new_ctx = process_turn(
            character, chain, narr_chain, context, ""
        )
        for tok in narr_toks:
            rb.append_narr(tok); scroll_bot()
        rb.end_narr(); scroll_bot()
        for tok in char_toks:
            rb.append_reply(tok); scroll_bot()
        rebuild_context()

    def regen(box):
        last = last_user.msg.get() if last_user else ""
        extra = big_text_dialog(root, "Regenerate instructions", "") or ""
        inp_text = last + (f"\n\n{extra}" if extra else "")
        box.start_new_version()
        narr_toks, char_toks, new_ctx = process_turn(
            character, chain, narr_chain, context, inp_text
        )
        for tok in narr_toks:
            box.append_narr(tok); scroll_bot()
        box.end_narr(); scroll_bot()
        for tok in char_toks:
            box.append_reply(tok); scroll_bot()
        rebuild_context()

    ########
    root_dir = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
    bg_photo = None

    def set_feed_background(img_name):
        nonlocal bg_photo
        try:
            img = Image.open(os.path.join(root_dir, img_name))
            bg_photo = ImageTk.PhotoImage(img)
            canvas.delete("bg")
            canvas.create_image(0, 0, anchor="nw", image=bg_photo, tags="bg")
            canvas.tag_lower("bg")  # keep text widgets on top
        except Exception as exc:
            print(f"failed to set background: {exc}")
    ########
    
    # ─── Send / key bindings ───
    def send(event=None):
        nonlocal last_user
        q = inp.get("1.0","end").strip()
        if not q:
            rb = active_reply.get("box")
            if rb and rb.winfo_exists(): continue_reply()
            elif last_user: regenerate_after_delete()
            return "break"

        inp.delete("1.0","end"); _grow()
        last_user = add_user_box(q)
        rb = add_reply_box(); rb.start_new_version()

        narr_toks, char_toks, new_ctx = process_turn(
            character, chain, narr_chain, context, q
        )
        for tok in narr_toks:
            rb.append_narr(tok); scroll_bot()
        rb.end_narr(); scroll_bot()
        for tok in char_toks:
            rb.append_reply(tok); scroll_bot()

        rebuild_context()
        update_user_tags(user_data, character)
        set_feed_background(f"{character['name']}_turn.png")  ######## or your image file name
        return "break"

    inp.bind("<Return>", send)
    root.bind_all("<Escape>",
                  lambda e: (root.unbind_all("<Escape>"), app_gui.go_back()),
                  add="+")
    
    center_window(root)
    scroll_bot()
