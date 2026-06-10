import tkinter as tk
from tkinter import messagebox
import json
import os

# ── 파일 경로 ──
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CERT_FILE   = os.path.join(BASE_DIR, "certs_data.json")
SPEC_FILE   = os.path.join(BASE_DIR, "specs_data.json")
COURSE_FILE = os.path.join(BASE_DIR, "coursework_data.json")

# ── 기본 데이터 ──
DEFAULT_CERTS = []

DEFAULT_SPECS = {
    "basic": [],
    "education": [],
    "career": [],
    "projects": [],
}

# ── 색상 ──
BG       = "#0f1117"
SURFACE  = "#1a1d27"
SURFACE2 = "#22263a"
BORDER   = "#2e3350"
ACCENT   = "#5b6cff"
TEXT     = "#e8eaf0"
TEXT_MUT = "#7a80a0"
SUCCESS  = "#34d399"
DANGER   = "#f87171"
WHITE    = "#ffffff"
TAB_COLORS = ["#5b6cff","#34d399","#f59e0b","#f87171","#a78bfa","#22d3ee"]

FONT_MAIN  = ("맑은 고딕", 10)
FONT_BOLD  = ("맑은 고딕", 10, "bold")
FONT_SMALL = ("맑은 고딕", 9)
FONT_TITLE = ("맑은 고딕", 12, "bold")

# ── 저장/불러오기 ──
def load_certs():
    if os.path.exists(CERT_FILE):
        try:
            with open(CERT_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("certs", d) if isinstance(d, dict) else d
        except Exception:
            pass
    return list(DEFAULT_CERTS)

def save_certs(certs):
    existing = {}
    if os.path.exists(CERT_FILE):
        try:
            with open(CERT_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict):
                    existing = d
        except Exception:
            pass
    existing["certs"] = certs
    with open(CERT_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def load_specs():
    if os.path.exists(SPEC_FILE):
        try:
            with open(SPEC_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                specs = d.get("specs", {})
                geometry = d.get("geometry", None)
                return specs, geometry
        except Exception:
            pass
    return {k: list(v) for k, v in DEFAULT_SPECS.items()}, None

def save_specs(specs, geometry=None):
    existing = {}
    if os.path.exists(SPEC_FILE):
        try:
            with open(SPEC_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing["specs"] = specs
    if geometry:
        existing["geometry"] = geometry
    with open(SPEC_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def load_coursework():
    if os.path.exists(COURSE_FILE):
        try:
            with open(COURSE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("coursework", [])
        except Exception:
            pass
    return []

def save_coursework(courses):
    with open(COURSE_FILE, "w", encoding="utf-8") as f:
        json.dump({"coursework": courses}, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════
class App:
    def __init__(self, root):
        self.root = root
        self.certs = load_certs()
        self.specs, saved_geo = load_specs()
        self.courses = load_coursework()
        self.expanded = {}   # tab -> set of expanded indices
        self.current_tab = 0
        self._toast_after = None

        self._setup_window(saved_geo)
        self._build_shell()
        self._switch_tab(0)

    # ── 창 설정 ──
    def _setup_window(self, geo=None):
        self.root.title("스펙 복사기")
        self.root.configure(bg=BG)
        self.root.geometry(geo or "420x600+100+100")
        self.root.minsize(380, 320)
        self.root.attributes("-topmost", True)
        self.root.resizable(True, True)
        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if event.widget == self.root:
            geo = self.root.geometry()
            specs = self.specs
            save_specs(specs, geo)

    # ── 셸 (헤더 + 탭바 + 콘텐츠 영역) ──
    def _build_shell(self):
        # 헤더
        header = tk.Frame(self.root, bg=SURFACE, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="📋  스펙 복사기", bg=SURFACE, fg=TEXT,
                 font=FONT_TITLE).pack(side="left", padx=14)
        self.pin_btn = tk.Button(header, text="📌 ON", bg=ACCENT, fg=WHITE,
                                 font=FONT_SMALL, bd=0, padx=8, pady=4,
                                 cursor="hand2", relief="flat",
                                 command=self._toggle_pin)
        self.pin_btn.pack(side="right", padx=10)

        # 탭바
        tab_bar = tk.Frame(self.root, bg=SURFACE2, height=36)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        self.tab_names  = ["자격증", "기본정보", "학력", "경력/봉사", "프로젝트", "교육사항"]
        self.tab_btns   = []
        for i, name in enumerate(self.tab_names):
            btn = tk.Button(tab_bar, text=name, bg=SURFACE2, fg=TEXT_MUT,
                            font=FONT_SMALL, bd=0, relief="flat",
                            padx=10, pady=8, cursor="hand2",
                            command=lambda i=i: self._switch_tab(i))
            btn.pack(side="left")
            self.tab_btns.append(btn)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

        # 콘텐츠 + 토스트
        self.content_frame = tk.Frame(self.root, bg=BG)
        self.content_frame.pack(fill="both", expand=True)

        self.toast_label = tk.Label(self.root, text="", bg=SUCCESS, fg="#0a1a10",
                                    font=FONT_SMALL, padx=12, pady=4)

    def _switch_tab(self, idx, scroll_to_widget=None):
        self.current_tab = idx
        color = TAB_COLORS[idx % len(TAB_COLORS)]
        for i, btn in enumerate(self.tab_btns):
            if i == idx:
                btn.config(bg=color, fg=WHITE)
            else:
                btn.config(bg=SURFACE2, fg=TEXT_MUT)

        for w in self.content_frame.winfo_children():
            w.destroy()

        # 스크롤 캔버스 생성
        canvas = tk.Canvas(self.content_frame, bg=BG, highlightthickness=0, bd=0)
        self._canvas = canvas
        sb = tk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e, w=win_id: canvas.itemconfig(w, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # 탭별 렌더
        builders = [
            self._render_certs,
            self._render_basic,
            self._render_education,
            self._render_career,
            self._render_projects,
            self._render_courses,
        ]
        builders[idx](inner)
        tk.Frame(inner, bg=BG, height=12).pack()

        # 클릭한 카드 위치로 스크롤
        if scroll_to_widget is not None:
            def _scroll_to(w=scroll_to_widget):
                try:
                    inner.update_idletasks()
                    canvas.update_idletasks()
                    card_y = w.winfo_y()
                    total_h = inner.winfo_reqheight()
                    view_h = canvas.winfo_height()
                    if total_h > view_h:
                        frac = max(0.0, min(card_y / total_h, 1.0))
                        canvas.yview_moveto(frac)
                except Exception:
                    pass
            canvas.after(10, _scroll_to)

    # ── 핀 토글 ──
    def _toggle_pin(self):
        val = not self.root.attributes("-topmost")
        self.root.attributes("-topmost", val)
        self.pin_btn.config(text="📌 ON" if val else "📌 OFF",
                            bg=ACCENT if val else SURFACE2)

    # ── 토스트 ──
    def _toast(self, msg):
        self.toast_label.config(text=f"  ✓  {msg}  ")
        self.toast_label.place(relx=0.5, y=8, anchor="n")
        if self._toast_after:
            self.root.after_cancel(self._toast_after)
        self._toast_after = self.root.after(1600, self.toast_label.place_forget)

    # ── 복사 ──
    def _copy(self, value, btn):
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update()
        orig_text = btn.cget("text")
        orig_bg   = btn.cget("bg")
        orig_fg   = btn.cget("fg")
        btn.config(text="✓", bg=SUCCESS, fg="#0a1a10")
        self._toast(f"복사됨: {value[:30]}{'...' if len(value)>30 else ''}")
        self.root.after(1400, lambda: btn.config(text=orig_text, bg=orig_bg, fg=orig_fg))

    # ════ 공통 카드 빌더 ════
    def _make_scroll_card(self, parent, title, subtitle="", tab_key=None, idx=None,
                          on_edit=None, on_delete=None, accent=ACCENT):
        key = (tab_key, idx)
        is_open = key in self.expanded.get(tab_key, set())

        card = tk.Frame(parent, bg=SURFACE, bd=0, highlightthickness=1,
                        highlightbackground=accent if is_open else BORDER)
        card.pack(fill="x", padx=8, pady=(6, 0))

        hdr = tk.Frame(card, bg=SURFACE)
        hdr.pack(fill="x")

        # 버튼을 먼저 pack해야 긴 제목에 밀리지 않음
        btns_frame = tk.Frame(hdr, bg=SURFACE)
        btns_frame.pack(side="right", padx=8, pady=8)
        if on_edit:
            tk.Button(btns_frame, text=" ✎ 수정 ", bg=SURFACE2, fg=TEXT_MUT,
                      font=FONT_SMALL, bd=0, relief="flat", padx=6, pady=4,
                      cursor="hand2", command=on_edit).pack(side="left", padx=2)
        if on_delete:
            tk.Button(btns_frame, text=" ✕ 삭제 ", bg=DANGER, fg=WHITE,
                      font=FONT_SMALL, bd=0, relief="flat", padx=6, pady=4,
                      cursor="hand2", command=on_delete).pack(side="left", padx=2)

        info = tk.Frame(hdr, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True, padx=10, pady=8)
        tk.Label(info, text=title, bg=SURFACE, fg=TEXT,
                 font=FONT_BOLD, anchor="w", wraplength=180, justify="left").pack(fill="x")
        if subtitle:
            tk.Label(info, text=subtitle, bg=SURFACE, fg=TEXT_MUT,
                     font=FONT_SMALL, anchor="w", wraplength=180).pack(fill="x")

        # 구분선 + 필드 영역 항상 생성, 초기엔 숨김
        sep = tk.Frame(card, bg=BORDER, height=1)
        fields_frame = tk.Frame(card, bg=SURFACE)

        if is_open:
            card.config(highlightbackground=accent)
            sep.pack(fill="x", padx=6)
            fields_frame.pack(fill="x", padx=8, pady=6)
        else:
            card.config(highlightbackground=BORDER)

        def do_toggle(tk_key=tab_key, tk_idx=idx,
                      tk_card=card, tk_sep=sep, tk_ff=fields_frame,
                      tk_accent=accent):
            if tk_key not in self.expanded:
                self.expanded[tk_key] = set()
            key = (tk_key, tk_idx)
            if key in self.expanded[tk_key]:
                self.expanded[tk_key].discard(key)
                tk_sep.pack_forget()
                tk_ff.pack_forget()
                tk_card.config(highlightbackground=BORDER)
            else:
                self.expanded[tk_key].add(key)
                tk_sep.pack(fill="x", padx=6)
                tk_ff.pack(fill="x", padx=8, pady=6)
                tk_card.config(highlightbackground=tk_accent)

        def bind_toggle(w):
            w.bind("<Button-1>", lambda e: do_toggle())
            w.configure(cursor="hand2")
            for c in w.winfo_children():
                bind_toggle(c)

        bind_toggle(hdr)
        bind_toggle(info)
        btns_frame.unbind("<Button-1>")
        for c in btns_frame.winfo_children():
            c.unbind("<Button-1>")

        return card, fields_frame

    def _toggle_card(self, tab_key, idx, card_widget=None):
        # 하위 호환용 (현재는 do_toggle 직접 사용)
        pass

    def _field_row(self, parent, label, value, accent=ACCENT, wrap=False):
        if not value:
            return
        row = tk.Frame(parent, bg=SURFACE2)
        row.pack(fill="x", pady=2)
        # 복사 버튼 먼저 pack → 텍스트가 길어도 버튼이 밀리지 않음
        btn = tk.Button(row, text="복사", bg=SURFACE2, fg=accent,
                        font=FONT_SMALL, bd=0, relief="flat", padx=8, pady=3, cursor="hand2")
        btn.config(command=lambda v=value, b=btn: self._copy(v, b))
        btn.pack(side="right", padx=6, pady=4)
        tk.Label(row, text=label, bg=SURFACE2, fg=TEXT_MUT,
                 font=FONT_SMALL, width=8, anchor="nw").pack(side="left", padx=(8,4), pady=5)
        tk.Label(row, text=value, bg=SURFACE2, fg=TEXT, font=FONT_SMALL,
                 anchor="w", wraplength=200, justify="left").pack(side="left", fill="x",
                 expand=True, pady=5)

    def _all_copy_btn(self, parent, text, accent=ACCENT):
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill="x", padx=8, pady=(4, 0))
        btn = tk.Button(row, text="📋 전체 복사", bg=accent, fg=WHITE,
                        font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=5,
                        cursor="hand2")
        btn.config(command=lambda v=text, b=btn: self._copy(v, b))
        btn.pack(fill="x")

    # ════ 탭 1: 자격증 ════
    def _render_certs(self, parent):
        color = TAB_COLORS[0]
        # 추가 버튼
        add_row = tk.Frame(parent, bg=BG)
        add_row.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(add_row, text="+ 자격증 추가", bg=color, fg=WHITE,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=self._add_cert).pack(fill="x")

        if not self.certs:
            tk.Label(parent, text="자격증이 없습니다.\n위 버튼으로 추가하세요.",
                     bg=BG, fg=TEXT_MUT, font=FONT_MAIN, justify="center").pack(pady=30)
            return

        for idx, cert in enumerate(self.certs):
            card, ff = self._make_scroll_card(
                parent,
                title=cert.get("name", ""),
                subtitle=f"{cert.get('issuer','')}  ·  {cert.get('date','')}",
                tab_key="certs", idx=idx,
                on_edit=lambda i=idx: self._edit_cert(i),
                on_delete=lambda i=idx: self._del_cert(i),
                accent=color,
            )
            if ff:
                for label, key in [("자격증명","name"),("번호","number"),("취득일","date"),("발급기관","issuer")]:
                    self._field_row(ff, label, cert.get(key,""), accent=color)

    def _add_cert(self):
        self._cert_dialog("새 자격증 추가", None)

    def _edit_cert(self, idx):
        self._cert_dialog("자격증 수정", idx)

    def _del_cert(self, idx):
        name = self.certs[idx].get("name","")
        if messagebox.askyesno("삭제 확인", f'"{name}" 을(를) 삭제할까요?', parent=self.root):
            self.certs.pop(idx)
            save_certs(self.certs)
            self._switch_tab(self.current_tab, keep_scroll=True)
            self._toast(f'"{name}" 삭제됐어요')

    def _cert_dialog(self, title, idx):
        fields = [("자격증명","name"),("번호","number"),("취득일","date"),("발급기관","issuer")]
        existing = self.certs[idx] if idx is not None else {}
        self._generic_dialog(title, fields, existing,
            on_save=lambda data, i=idx: self._save_cert(data, i))

    def _save_cert(self, data, idx):
        if idx is not None:
            self.certs[idx] = data
        else:
            self.certs.append(data)
        save_certs(self.certs)
        self._switch_tab(self.current_tab, keep_scroll=True)
        self._toast(f'"{data["name"]}" {"수정" if idx is not None else "추가"}됐어요!')

    # ════ 탭 2: 기본정보 ════
    def _render_basic(self, parent):
        color = TAB_COLORS[1]
        add_row = tk.Frame(parent, bg=BG)
        add_row.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(add_row, text="+ 항목 추가", bg=color, fg=WHITE,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=lambda: self._add_basic()).pack(fill="x")

        for idx, item in enumerate(self.specs.get("basic", [])):
            card, ff = self._make_scroll_card(
                parent,
                title=item.get("label",""),
                subtitle=item.get("value",""),
                tab_key="basic", idx=idx,
                on_edit=lambda i=idx: self._edit_basic(i),
                on_delete=lambda i=idx: self._del_basic(i),
                accent=color,
            )
            if ff:
                self._field_row(ff, "항목명", item.get("label",""), accent=color)
                self._field_row(ff, "값",    item.get("value",""), accent=color)

    def _add_basic(self):
        self._generic_dialog("항목 추가", [("항목명","label"),("값","value")], {},
            on_save=lambda data: self._save_basic(data, None))

    def _edit_basic(self, idx):
        existing = self.specs["basic"][idx]
        self._generic_dialog("항목 수정", [("항목명","label"),("값","value")], existing,
            on_save=lambda data, i=idx: self._save_basic(data, i))

    def _del_basic(self, idx):
        label = self.specs["basic"][idx].get("label","")
        if messagebox.askyesno("삭제 확인", f'"{label}" 항목을 삭제할까요?', parent=self.root):
            self.specs["basic"].pop(idx)
            save_specs(self.specs)
            self._switch_tab(self.current_tab, keep_scroll=True)

    def _save_basic(self, data, idx):
        if idx is not None:
            self.specs["basic"][idx] = data
        else:
            self.specs.setdefault("basic", []).append(data)
        save_specs(self.specs)
        self._switch_tab(self.current_tab, keep_scroll=True)

    # ════ 탭 3: 학력 ════
    def _render_education(self, parent):
        color = TAB_COLORS[2]
        add_row = tk.Frame(parent, bg=BG)
        add_row.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(add_row, text="+ 학력 추가", bg=color, fg=WHITE,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=lambda: self._add_edu()).pack(fill="x")

        for idx, edu in enumerate(self.specs.get("education", [])):
            card, ff = self._make_scroll_card(
                parent,
                title=edu.get("name",""),
                subtitle=edu.get("period",""),
                tab_key="education", idx=idx,
                on_edit=lambda i=idx: self._edit_edu(i),
                on_delete=lambda i=idx: self._del_edu(i),
                accent=color,
            )
            if ff:
                fields = [
                    ("학교명",   "name"),
                    ("재학기간", "period"),
                    ("전체학점", "gpa_total"),
                    ("전공학점", "gpa_major"),
                    ("이수학점", "credits_total"),
                    ("전공이수", "credits_major"),
                    ("장학금",   "scholarship"),
                ]
                for label, key in fields:
                    self._field_row(ff, label, edu.get(key,""), accent=color)

                # 전체 복사
                all_text = "\n".join(
                    f"{l}: {edu.get(k,'')}" for l, k in fields if edu.get(k,"")
                )
                self._all_copy_btn(ff, all_text, accent=color)

    def _add_edu(self):
        fields = [("학교명","name"),("재학기간","period"),("전체학점","gpa_total"),
                  ("전공학점","gpa_major"),("이수학점","credits_total"),
                  ("전공이수","credits_major"),("장학금","scholarship")]
        self._generic_dialog("학력 추가", fields, {},
            on_save=lambda data: self._save_edu(data, None))

    def _edit_edu(self, idx):
        fields = [("학교명","name"),("재학기간","period"),("전체학점","gpa_total"),
                  ("전공학점","gpa_major"),("이수학점","credits_total"),
                  ("전공이수","credits_major"),("장학금","scholarship")]
        self._generic_dialog("학력 수정", fields, self.specs["education"][idx],
            on_save=lambda data, i=idx: self._save_edu(data, i))

    def _del_edu(self, idx):
        name = self.specs["education"][idx].get("name","")
        if messagebox.askyesno("삭제 확인", f'"{name}" 항목을 삭제할까요?', parent=self.root):
            self.specs["education"].pop(idx)
            save_specs(self.specs)
            self._switch_tab(self.current_tab, keep_scroll=True)

    def _save_edu(self, data, idx):
        if idx is not None:
            self.specs["education"][idx] = data
        else:
            self.specs.setdefault("education", []).append(data)
        save_specs(self.specs)
        self._switch_tab(self.current_tab, keep_scroll=True)

    # ════ 탭 4: 경력/봉사 ════
    def _render_career(self, parent):
        color = TAB_COLORS[3]
        add_row = tk.Frame(parent, bg=BG)
        add_row.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(add_row, text="+ 경력/봉사 추가", bg=color, fg=WHITE,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=lambda: self._add_career()).pack(fill="x")

        for idx, c in enumerate(self.specs.get("career", [])):
            card, ff = self._make_scroll_card(
                parent,
                title=f"[{c.get('type','')}] {c.get('org','')}",
                subtitle=c.get("period",""),
                tab_key="career", idx=idx,
                on_edit=lambda i=idx: self._edit_career(i),
                on_delete=lambda i=idx: self._del_career(i),
                accent=color,
            )
            if ff:
                self._field_row(ff, "기관명", c.get("org",""), accent=color)
                self._field_row(ff, "구분",   c.get("type",""), accent=color)
                self._field_row(ff, "기간",   c.get("period",""), accent=color)
                self._field_row(ff, "업무내용", c.get("desc",""), accent=color, wrap=True)

                if c.get("desc"):
                    all_text = f"{c.get('org','')} ({c.get('type','')}) {c.get('period','')}\n{c.get('desc','')}"
                    self._all_copy_btn(ff, all_text, accent=color)

    def _add_career(self):
        fields = [("기관명","org"),("구분","type"),("기간","period"),("업무내용","desc")]
        self._generic_dialog("경력/봉사 추가", fields, {},
            on_save=lambda data: self._save_career(data, None))

    def _edit_career(self, idx):
        fields = [("기관명","org"),("구분","type"),("기간","period"),("업무내용","desc")]
        self._generic_dialog("경력/봉사 수정", fields, self.specs["career"][idx],
            on_save=lambda data, i=idx: self._save_career(data, i))

    def _del_career(self, idx):
        name = self.specs["career"][idx].get("org","")
        if messagebox.askyesno("삭제 확인", f'"{name}" 항목을 삭제할까요?', parent=self.root):
            self.specs["career"].pop(idx)
            save_specs(self.specs)
            self._switch_tab(self.current_tab, keep_scroll=True)

    def _save_career(self, data, idx):
        if idx is not None:
            self.specs["career"][idx] = data
        else:
            self.specs.setdefault("career", []).append(data)
        save_specs(self.specs)
        self._switch_tab(self.current_tab, keep_scroll=True)

    # ════ 탭 5: 프로젝트 ════
    def _render_projects(self, parent):
        color = TAB_COLORS[4]
        add_row = tk.Frame(parent, bg=BG)
        add_row.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(add_row, text="+ 프로젝트 추가", bg=color, fg=WHITE,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=lambda: self._add_proj()).pack(fill="x")

        for idx, p in enumerate(self.specs.get("projects", [])):
            card, ff = self._make_scroll_card(
                parent,
                title=p.get("name",""),
                subtitle=f"{p.get('period','')}  ·  {p.get('stack','')}",
                tab_key="projects", idx=idx,
                on_edit=lambda i=idx: self._edit_proj(i),
                on_delete=lambda i=idx: self._del_proj(i),
                accent=color,
            )
            if ff:
                fields = [
                    ("프로젝트명", "name"),
                    ("기간",       "period"),
                    ("기술스택",   "stack"),
                    ("역할",       "role"),
                    ("목표",       "goal"),
                    ("성과",       "result"),
                    ("진행내용",   "desc"),
                    ("URL",        "url"),
                ]
                for label, key in fields:
                    self._field_row(ff, label, p.get(key,""), accent=color,
                                    wrap=(key in ("desc","result","goal","role")))

                # 전체 복사
                all_lines = []
                for label, key in fields:
                    v = p.get(key,"")
                    if v:
                        all_lines.append(f"[{label}] {v}")
                if all_lines:
                    self._all_copy_btn(ff, "\n".join(all_lines), accent=color)

    def _add_proj(self):
        fields = [("프로젝트명","name"),("기간","period"),("기술스택","stack"),
                  ("역할","role"),("목표","goal"),("성과","result"),
                  ("진행내용","desc"),("URL","url")]
        self._generic_dialog("프로젝트 추가", fields, {},
            on_save=lambda data: self._save_proj(data, None))

    def _edit_proj(self, idx):
        fields = [("프로젝트명","name"),("기간","period"),("기술스택","stack"),
                  ("역할","role"),("목표","goal"),("성과","result"),
                  ("진행내용","desc"),("URL","url")]
        self._generic_dialog("프로젝트 수정", fields, self.specs["projects"][idx],
            on_save=lambda data, i=idx: self._save_proj(data, i))

    def _del_proj(self, idx):
        name = self.specs["projects"][idx].get("name","")
        if messagebox.askyesno("삭제 확인", f'"{name}" 을(를) 삭제할까요?', parent=self.root):
            self.specs["projects"].pop(idx)
            save_specs(self.specs)
            self._switch_tab(self.current_tab, keep_scroll=True)
            self._toast(f'"{name}" 삭제됐어요')

    def _save_proj(self, data, idx):
        if idx is not None:
            self.specs["projects"][idx] = data
        else:
            self.specs.setdefault("projects", []).append(data)
        save_specs(self.specs)
        self._switch_tab(self.current_tab, keep_scroll=True)
        self._toast(f'"{data["name"]}" {"수정" if idx is not None else "추가"}됐어요!')

    # ════ 공통 다이얼로그 ════
    def _generic_dialog(self, title, fields, existing, on_save):
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.configure(bg=BG)
        h = min(80 + len(fields) * 42 + 60, 520)
        dlg.geometry(f"360x{h}")
        dlg.resizable(False, True)
        dlg.attributes("-topmost", True)
        dlg.grab_set()

        tk.Label(dlg, text=title, bg=BG, fg=TEXT, font=FONT_TITLE).pack(pady=(14,8))

        # 스크롤 가능한 폼
        canvas = tk.Canvas(dlg, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=(0,0))

        form = tk.Frame(canvas, bg=BG)
        win = canvas.create_window((0,0), window=form, anchor="nw")
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        entries = {}
        for label, key in fields:
            row = tk.Frame(form, bg=BG)
            row.pack(fill="x", padx=16, pady=3)
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

        if entries:
            list(entries.values())[0].focus()

        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(side="bottom", pady=10)

        def save():
            data = {k: e.get().strip() for k, e in entries.items()}
            first_key = fields[0][1]
            if not data.get(first_key):
                entries[first_key].focus()
                return
            on_save(data)
            dlg.destroy()

        tk.Button(btn_row, text="저장", bg=ACCENT, fg=WHITE, font=FONT_BOLD,
                  bd=0, padx=20, pady=6, cursor="hand2", relief="flat",
                  command=save).pack(side="left", padx=6)
        tk.Button(btn_row, text="취소", bg=SURFACE2, fg=TEXT_MUT, font=FONT_MAIN,
                  bd=0, padx=20, pady=6, cursor="hand2", relief="flat",
                  command=dlg.destroy).pack(side="left", padx=6)

        dlg.bind("<Return>", lambda e: save())
        dlg.bind("<Escape>", lambda e: dlg.destroy())


    # ════ 탭 6: 교육사항 ════
    def _render_courses(self, parent):
        color = TAB_COLORS[5]
        add_row = tk.Frame(parent, bg=BG)
        add_row.pack(fill="x", padx=8, pady=(8, 0))
        tk.Button(add_row, text="+ 교육사항 추가", bg=color, fg=WHITE,
                  font=FONT_SMALL, bd=0, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=lambda: self._add_course()).pack(fill="x")

        if not self.courses:
            tk.Label(parent, text="교육사항이 없습니다.\n위 버튼으로 추가하세요.",
                     bg=BG, fg=TEXT_MUT, font=FONT_MAIN, justify="center").pack(pady=30)
            return

        for idx, c in enumerate(self.courses):
            subtitle = f"{c.get('period','')}  ·  {c.get('grade','')} ({c.get('score','')}) / {c.get('credits','')}학점"
            card, ff = self._make_scroll_card(
                parent,
                title=c.get("name",""),
                subtitle=subtitle,
                tab_key="courses", idx=idx,
                on_edit=lambda i=idx: self._edit_course(i),
                on_delete=lambda i=idx: self._del_course(i),
                accent=color,
            )
            if ff:
                self._field_row(ff, "과목명",  c.get("name",""),    accent=color)
                self._field_row(ff, "수강기간", c.get("period",""),  accent=color)
                self._field_row(ff, "성적",    c.get("grade",""),   accent=color)
                self._field_row(ff, "평점",    c.get("score",""),   accent=color)
                self._field_row(ff, "학점",    c.get("credits",""), accent=color)
                self._field_row(ff, "내용",    c.get("desc",""),    accent=color, wrap=True)

                all_text = f"{c.get('name','')} ({c.get('period','')}) 성적: {c.get('grade','')}({c.get('score','')}점) {c.get('credits','')}학점\n{c.get('desc','')}"
                self._all_copy_btn(ff, all_text, accent=color)

    def _add_course(self):
        fields = [("과목명","name"),("수강기간","period"),("성적","grade"),
                  ("평점","score"),("학점","credits"),("내용","desc")]
        self._generic_dialog("교육사항 추가", fields, {},
            on_save=lambda data: self._save_course(data, None))

    def _edit_course(self, idx):
        fields = [("과목명","name"),("수강기간","period"),("성적","grade"),
                  ("평점","score"),("학점","credits"),("내용","desc")]
        self._generic_dialog("교육사항 수정", fields, self.courses[idx],
            on_save=lambda data, i=idx: self._save_course(data, i))

    def _del_course(self, idx):
        name = self.courses[idx].get("name","")
        if messagebox.askyesno("삭제 확인", f'"{name}" 을(를) 삭제할까요?', parent=self.root):
            self.courses.pop(idx)
            save_coursework(self.courses)
            self._switch_tab(self.current_tab, keep_scroll=True)
            self._toast(f'"{name}" 삭제됐어요')

    def _save_course(self, data, idx):
        if idx is not None:
            self.courses[idx] = data
        else:
            self.courses.append(data)
        save_coursework(self.courses)
        self._switch_tab(self.current_tab, keep_scroll=True)
        self._toast(f'"{data["name"]}" {"수정" if idx is not None else "추가"}됐어요!')


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
