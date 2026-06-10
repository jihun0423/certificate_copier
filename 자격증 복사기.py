import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os

# ── 데이터 ──
DEFAULT_CERTS = []

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs_data.json")

def load_certs():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [c.copy() for c in DEFAULT_CERTS]

def save_certs(certs):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(certs, f, ensure_ascii=False, indent=2)

# ── 색상 팔레트 ──
BG        = "#0f1117"
SURFACE   = "#1a1d27"
SURFACE2  = "#22263a"
BORDER    = "#2e3350"
ACCENT    = "#5b6cff"
ACCENT_H  = "#7080ff"
TEXT      = "#e8eaf0"
TEXT_MUT  = "#7a80a0"
SUCCESS   = "#34d399"
DANGER    = "#f87171"
WHITE     = "#ffffff"

FONT_MAIN  = ("맑은 고딕", 10)
FONT_BOLD  = ("맑은 고딕", 10, "bold")
FONT_SMALL = ("맑은 고딕", 9)
FONT_TITLE = ("맑은 고딕", 12, "bold")

FIELD_LABELS = [("자격증명", "name"), ("번호", "number"), ("취득일", "date"), ("발급기관", "issuer")]


class CertApp:
    def __init__(self, root):
        self.root = root
        self.certs = load_certs()
        self.expanded = set()
        self.always_on_top = tk.BooleanVar(value=True)

        self._setup_window()
        self._build_ui()
        self._render_list()

    # ── 창 설정 ──
    def _setup_window(self):
        self.root.title("자격증 복사기")
        self.root.configure(bg=BG)
        self.root.geometry("500x700+100+100")
        self.root.minsize(450, 375)
        self.root.attributes("-topmost", True)
        self.root.resizable(True, True)

    # ── UI 골격 ──
    def _build_ui(self):
        # 헤더
        header = tk.Frame(self.root, bg=SURFACE, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        tk.Label(header, text="📋  자격증 복사기", bg=SURFACE, fg=TEXT,
                 font=FONT_TITLE).pack(side="left", padx=14, pady=14)

        btn_frame = tk.Frame(header, bg=SURFACE)
        btn_frame.pack(side="right", padx=10, pady=10)

        # 항상 위 토글
        self.pin_btn = tk.Button(
            btn_frame, text="📌 고정 ON", bg=ACCENT, fg=WHITE,
            font=FONT_SMALL, bd=0, padx=8, pady=4, cursor="hand2",
            command=self._toggle_pin, relief="flat"
        )
        self.pin_btn.pack(side="left", padx=(0, 6))

        tk.Button(
            btn_frame, text="+ 추가", bg=ACCENT, fg=WHITE,
            font=FONT_SMALL, bd=0, padx=8, pady=4, cursor="hand2",
            command=self._open_add_dialog, relief="flat"
        ).pack(side="left")

        # 구분선
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # 스크롤 영역
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.list_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        self.list_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 토스트 레이블
        self.toast_label = tk.Label(
            self.root, text="", bg=SUCCESS, fg="#0a1a10",
            font=FONT_SMALL, padx=12, pady=4
        )
        self._toast_after = None

    def _on_frame_configure(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfig(self.canvas_window, width=e.width)

    def _on_mousewheel(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    # ── 항상 위 토글 ──
    def _toggle_pin(self):
        current = self.root.attributes("-topmost")
        new_val = not current
        self.root.attributes("-topmost", new_val)
        if new_val:
            self.pin_btn.config(text="📌 고정 ON", bg=ACCENT)
        else:
            self.pin_btn.config(text="📌 고정 OFF", bg=SURFACE2)

    # ── 토스트 ──
    def _show_toast(self, msg):
        self.toast_label.config(text=f"  ✓  {msg}  ")
        self.toast_label.place(relx=0.5, y=8, anchor="n")
        if self._toast_after:
            self.root.after_cancel(self._toast_after)
        self._toast_after = self.root.after(1600, self.toast_label.place_forget)

    # ── 클립보드 복사 ──
    def _copy(self, value, btn):
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update()
        original = btn.cget("text")
        btn.config(text="✓", bg=SUCCESS, fg="#0a1a10")
        self._show_toast(f"복사됨: {value}")
        self.root.after(1400, lambda: btn.config(text=original, bg=SURFACE2, fg=ACCENT))

    # ── 리스트 렌더링 ──
    def _render_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not self.certs:
            tk.Label(self.list_frame, text="자격증이 없습니다.\n+ 추가 버튼으로 추가하세요.",
                     bg=BG, fg=TEXT_MUT, font=FONT_MAIN, justify="center").pack(pady=40)
            return

        for idx, cert in enumerate(self.certs):
            self._build_cert_card(idx, cert)

        # 하단 여백
        tk.Frame(self.list_frame, bg=BG, height=10).pack()

    def _build_cert_card(self, idx, cert):
        is_open = idx in self.expanded

        # 카드 외곽
        card = tk.Frame(self.list_frame, bg=SURFACE, bd=0, highlightthickness=1,
                        highlightbackground=ACCENT if is_open else BORDER)
        card.pack(fill="x", padx=8, pady=(6, 0))

        # 헤더 행
        header_row = tk.Frame(card, bg=SURFACE)
        header_row.pack(fill="x")

        # 이름 + 부제
        info = tk.Frame(header_row, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        tk.Label(info, text=cert["name"], bg=SURFACE, fg=TEXT,
                 font=FONT_BOLD, anchor="w").pack(fill="x")
        tk.Label(info, text=f"{cert['issuer']}  ·  {cert['date']}",
                 bg=SURFACE, fg=TEXT_MUT, font=FONT_SMALL, anchor="w").pack(fill="x")

        # 버튼들
        btns = tk.Frame(header_row, bg=SURFACE)
        btns.pack(side="right", padx=8, pady=8)

        tk.Button(btns, text="✎", bg=SURFACE, fg=TEXT_MUT,
                  font=FONT_SMALL, bd=0, cursor="hand2", relief="flat", padx=6,
                  command=lambda i=idx: self._open_edit_dialog(i)).pack(side="left")

        tk.Button(btns, text="✕", bg=SURFACE, fg=DANGER,
                  font=FONT_SMALL, bd=0, cursor="hand2", relief="flat", padx=6,
                  command=lambda i=idx: self._delete(i)).pack(side="left")

        # 카드 헤더 전체(자식 위젯 포함) 클릭으로 토글
        def bind_toggle(widget, i=idx):
            widget.bind("<Button-1>", lambda e, idx=i: self._toggle(idx))
            widget.configure(cursor="hand2")
            for child in widget.winfo_children():
                bind_toggle(child, i)

        bind_toggle(header_row)
        bind_toggle(info)

        # 펼쳐진 필드들
        if is_open:
            sep = tk.Frame(card, bg=BORDER, height=1)
            sep.pack(fill="x", padx=6)

            fields_frame = tk.Frame(card, bg=SURFACE)
            fields_frame.pack(fill="x", padx=8, pady=6)

            for label, key in FIELD_LABELS:
                row = tk.Frame(fields_frame, bg=SURFACE2)
                row.pack(fill="x", pady=2)

                tk.Label(row, text=label, bg=SURFACE2, fg=TEXT_MUT,
                         font=FONT_SMALL, width=7, anchor="w").pack(side="left", padx=(8,4), pady=5)

                tk.Label(row, text=cert.get(key, ""), bg=SURFACE2, fg=TEXT,
                         font=FONT_SMALL, anchor="w").pack(side="left", fill="x", expand=True)

                copy_btn = tk.Button(
                    row, text="복사", bg=SURFACE2, fg=ACCENT,
                    font=FONT_SMALL, bd=0, cursor="hand2", relief="flat",
                    padx=8, pady=3
                )
                copy_btn.config(command=lambda v=cert.get(key,""), b=copy_btn: self._copy(v, b))
                copy_btn.pack(side="right", padx=6, pady=4)

    def _toggle(self, idx):
        if idx in self.expanded:
            self.expanded.discard(idx)
        else:
            self.expanded.add(idx)
        self._render_list()

    def _delete(self, idx):
        name = self.certs[idx]["name"]
        if messagebox.askyesno("삭제 확인", f'"{name}" 을(를) 삭제할까요?', parent=self.root):
            self.expanded.discard(idx)
            # expanded 인덱스 재조정
            self.expanded = {i if i < idx else i - 1 for i in self.expanded if i != idx}
            self.certs.pop(idx)
            save_certs(self.certs)
            self._render_list()
            self._show_toast(f'"{name}" 삭제됐어요')

    # ── 추가 다이얼로그 ──
    def _open_add_dialog(self):
        self._open_form_dialog("새 자격증 추가", None)

    def _open_edit_dialog(self, idx):
        self._open_form_dialog("자격증 수정", idx)

    def _open_form_dialog(self, title, idx):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=BG)
        dialog.geometry("340x260")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        existing = self.certs[idx] if idx is not None else {}

        tk.Label(dialog, text=title, bg=BG, fg=TEXT, font=FONT_TITLE).pack(pady=(16,10))

        entries = {}
        for label, key in FIELD_LABELS:
            row = tk.Frame(dialog, bg=BG)
            row.pack(fill="x", padx=20, pady=3)
            tk.Label(row, text=label, bg=BG, fg=TEXT_MUT,
                     font=FONT_SMALL, width=7, anchor="w").pack(side="left")
            e = tk.Entry(row, bg=SURFACE2, fg=TEXT, font=FONT_SMALL,
                         insertbackground=TEXT, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT)
            e.pack(side="left", fill="x", expand=True, ipady=5, padx=(4,0))
            if existing.get(key):
                e.insert(0, existing[key])
            entries[key] = e

        entries["name"].focus()

        def save():
            data = {k: e.get().strip() for k, e in entries.items()}
            if not data["name"]:
                entries["name"].focus()
                return
            if idx is not None:
                self.certs[idx] = data
                msg = f'"{data["name"]}" 수정 완료!'
            else:
                self.certs.append(data)
                msg = f'"{data["name"]}" 추가됐어요!'
            save_certs(self.certs)
            self._render_list()
            self._show_toast(msg)
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.pack(pady=14)
        tk.Button(btn_row, text="저장", bg=ACCENT, fg=WHITE, font=FONT_BOLD,
                  bd=0, padx=20, pady=6, cursor="hand2", relief="flat",
                  command=save).pack(side="left", padx=6)
        tk.Button(btn_row, text="취소", bg=SURFACE2, fg=TEXT_MUT, font=FONT_MAIN,
                  bd=0, padx=20, pady=6, cursor="hand2", relief="flat",
                  command=dialog.destroy).pack(side="left", padx=6)

        dialog.bind("<Return>", lambda e: save())
        dialog.bind("<Escape>", lambda e: dialog.destroy())


if __name__ == "__main__":
    root = tk.Tk()
    app = CertApp(root)
    root.mainloop()
