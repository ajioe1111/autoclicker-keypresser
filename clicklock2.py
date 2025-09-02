
# Зависимости: pip install customtkinter keyboard mouse pywin32 pygetwindow

import time
import threading
import sys

import keyboard
import mouse
import customtkinter as ctk

import win32gui
import win32con
import win32api          # GetKeyState
import pygetwindow as gw

APP_TITLE = "Foxhole ClickLock Pro"
DEFAULT_INTERVAL_MS = 30

# ------------------- Global state -------------------
class State:
    # Classic
    is_holding = False
    active_action = None      # "LMB","W","S","E" or None
    hwnd = None
    win_title = ""
    holder_thread = None

    # Spam Shift+LMB (cursor-based)
    spam_active = False
    spam_hold_mode = False    # False=toggler, True=hold hotkey
    spam_hotkey = "f8"
    spam_interval = DEFAULT_INTERVAL_MS
    spam_thread = None
    spam_stop = threading.Event()

    # hooks
    kb_handles = []           # keyboard.add_hotkey handles
    mouse_hooks = []          # mouse.hook/on_button callbacks

S = State()

VK = {"W": 0x57, "S": 0x53, "E": 0x45}
VK_MENU = 0x12   # Alt (generic)
VK_LMENU = 0xA4  # Left Alt
VK_RMENU = 0xA5  # Right Alt

# ------------------- Helpers -------------------
def is_alt_down() -> bool:
    """Надёжная проверка зажатого Alt на Windows."""
    try:
        return any(win32api.GetKeyState(vk) < 0 for vk in (VK_MENU, VK_LMENU, VK_RMENU))
    except Exception:
        # запасной вариант, если что-то с WinAPI не так
        return keyboard.is_pressed("alt")

def find_game_window(title_part: str):
    wins = gw.getWindowsWithTitle(title_part)
    if wins:
        w = wins[0]
        return w._hWnd, w.title
    return None, ""

# ------------------- Classic (legacy LMB, как в старом скрипте) -------------------
def _holder_loop():
    try:
        if S.active_action == "LMB":
            # Шлём WM_LBUTTONDOWN (MK_LBUTTON) каждые ~100мс, при выключении — WM_LBUTTONUP
            while S.is_holding and S.active_action == "LMB" and S.hwnd:
                try:
                    win32gui.PostMessage(S.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)
                except Exception as e:
                    print(f"[ERR] LMB hold: {e}", file=sys.stderr)
                    break
                time.sleep(0.1)
            try:
                win32gui.PostMessage(S.hwnd, win32con.WM_LBUTTONUP, 0, 0)
            except Exception:
                pass

        elif S.active_action in ("W", "S", "E"):
            vk = VK[S.active_action]
            while S.is_holding and S.active_action in ("W", "S", "E") and S.hwnd:
                try:
                    win32gui.PostMessage(S.hwnd, win32con.WM_KEYDOWN, vk, 0)
                except Exception as e:
                    print(f"[ERR] Key hold {S.active_action}: {e}", file=sys.stderr)
                    break
                time.sleep(0.1)
            try:
                win32gui.PostMessage(S.hwnd, win32con.WM_KEYUP, vk, 0)
            except Exception:
                pass
    except Exception as e:
        print(f"[ERR] holder_loop: {e}", file=sys.stderr)

def _start_holder(kind: str):
    # Спам взаимоисключаем
    stop_spam()

    # Повтор по тому же действию = выключить
    if S.active_action == kind and S.is_holding:
        S.is_holding = False
        S.active_action = None
        return

    if not S.hwnd:
        print("Окно игры не привязано.")
        return

    S.is_holding = True
    S.active_action = kind
    S.holder_thread = threading.Thread(target=_holder_loop, daemon=True)
    S.holder_thread.start()

def toggle_hold_lmb():
    _start_holder("LMB")

def toggle_hold_key(name: str):
    _start_holder(name)

def stop_classic():
    S.is_holding = False
    S.active_action = None

# ------------------- Spam Shift+LMB (cursor-based) -------------------
def _do_shift_click_once():
    keyboard.press("shift")
    mouse.press(button="left")
    mouse.release(button="left")
    keyboard.release("shift")

def _spam_loop():
    try:
        while not S.spam_stop.is_set():
            running = (keyboard.is_pressed(S.spam_hotkey) if S.spam_hold_mode else S.spam_active)
            if running:
                _do_shift_click_once()
                time.sleep(max(1, int(S.spam_interval)) / 1000.0)
            else:
                time.sleep(0.01)
    except Exception as e:
        print(f"[ERR] spam_loop: {e}", file=sys.stderr)

def start_spam_thread_if_needed():
    if S.spam_thread is None or not S.spam_thread.is_alive():
        S.spam_stop.clear()
        S.spam_thread = threading.Thread(target=_spam_loop, daemon=True)
        S.spam_thread.start()

def stop_spam():
    S.spam_active = False
    S.spam_stop.set()
    if S.spam_thread and S.spam_thread.is_alive():
        S.spam_thread.join(timeout=0.5)
    S.spam_thread = None
    try:
        keyboard.release("shift")
    except Exception:
        pass

def toggle_spam_toggler():
    if S.spam_hold_mode:
        return
    stop_classic()
    S.spam_active = not S.spam_active
    start_spam_thread_if_needed()

# ------------------- Hooks -------------------
def unbind_hotkeys_and_mouse():
    for h in S.kb_handles:
        try: keyboard.remove_hotkey(h)
        except Exception: pass
    S.kb_handles.clear()

    for cb in S.mouse_hooks:
        try: mouse.unhook(cb)
        except Exception: pass
    S.mouse_hooks.clear()

def bind_default_hotkeys():
    unbind_hotkeys_and_mouse()

    # Alt + ЛКМ — через глобальный mouse.hook + проверка Alt по WinAPI прямо в момент клика
    def on_mouse_event(event):
        # у mouse.hook разные типы событий, фильтруем только нажатие ЛКМ
        if getattr(event, "event_type", "") == "down" and getattr(event, "button", "") == "left":
            if is_alt_down():
                toggle_hold_lmb()
    mouse.hook(on_mouse_event)
    S.mouse_hooks.append(on_mouse_event)

    # Alt + W/S/E
    for key in ("w", "s", "e"):
        try:
            h = keyboard.add_hotkey(f"alt+{key}", lambda k=key: toggle_hold_key(k.upper()))
            S.kb_handles.append(h)
        except Exception as e:
            print(f"[WARN] cannot bind alt+{key}: {e}", file=sys.stderr)

    # Спам-хоткей (в тумблер-режиме)
    if not S.spam_hold_mode:
        try:
            h = keyboard.add_hotkey(S.spam_hotkey, toggle_spam_toggler)
            S.kb_handles.append(h)
        except Exception as e:
            print(f"[WARN] cannot bind spam hotkey '{S.spam_hotkey}': {e}", file=sys.stderr)

    start_spam_thread_if_needed()

# ------------------- UI -------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("800x680")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.pulse_jobs = {}   # widget -> after_id
        self.btn_defaults = {} # widget -> {"fg":..., "hover":...}

        # Header
        ctk.CTkLabel(self, text="Foxhole ClickLock Pro",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(16, 2))
        ctk.CTkLabel(self, text="Чебурпели! >O<").pack(pady=(0, 12))

        # Window binding
        self.card_win = ctk.CTkFrame(self)
        self.card_win.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(self.card_win, text="Окно игры (часть названия)").grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        self.title_var = ctk.StringVar(value="War")
        self.win_entry = ctk.CTkEntry(self.card_win, width=300, textvariable=self.title_var)
        self.win_entry.grid(row=0, column=1, padx=8, pady=(12, 6), sticky="w")
        ctk.CTkButton(self.card_win, text="Найти", width=120, command=self.on_bind_window).grid(row=0, column=2, padx=12, pady=(12, 6))
        self.win_status = ctk.CTkLabel(self.card_win, text="Статус: окно не привязано")
        self.win_status.grid(row=1, column=0, columnspan=3, padx=12, pady=(0, 12), sticky="w")

        # Classic actions
        self.card_classic = ctk.CTkFrame(self)
        self.card_classic.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(self.card_classic, text="Классические действия (в окно без фокуса)").grid(row=0, column=0, columnspan=5, padx=12, pady=(12, 8), sticky="w")

        self.btn_lmb = ctk.CTkButton(self.card_classic, text="Toggle ЛКМ (Alt+LMB)", command=self._ui_toggle_lmb)
        self.btn_w   = ctk.CTkButton(self.card_classic, text="Toggle W (Alt+W)",    command=lambda: self._ui_toggle_key("W"))
        self.btn_s   = ctk.CTkButton(self.card_classic, text="Toggle S (Alt+S)",    command=lambda: self._ui_toggle_key("S"))
        self.btn_e   = ctk.CTkButton(self.card_classic, text="Toggle E (Alt+E)",    command=lambda: self._ui_toggle_key("E"))

        self.btn_lmb.grid(row=1, column=0, padx=12, pady=6, sticky="w")
        self.btn_w.grid(  row=1, column=1, padx=12, pady=6, sticky="w")
        self.btn_s.grid(  row=1, column=2, padx=12, pady=6, sticky="w")
        self.btn_e.grid(  row=1, column=3, padx=12, pady=6, sticky="w")

        self.classic_status = ctk.CTkLabel(self.card_classic, text=self.get_classic_status())
        self.classic_status.grid(row=2, column=0, columnspan=5, padx=12, pady=(4, 12), sticky="w")

        # Spam card
        self.card_spam = ctk.CTkFrame(self)
        self.card_spam.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(self.card_spam, text="Shift+ЛКМ спам под курсором").grid(row=0, column=0, columnspan=5, padx=12, pady=(12, 8), sticky="w")

        ctk.CTkLabel(self.card_spam, text="Интервал (мс)").grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")
        self.interval_slider = ctk.CTkSlider(self.card_spam, from_=1, to=200, number_of_steps=199, command=self.on_interval_change)
        self.interval_slider.set(S.spam_interval)
        self.interval_slider.grid(row=1, column=1, columnspan=2, padx=8, pady=(0, 6), sticky="we")

        self.interval_entry = ctk.CTkEntry(self.card_spam, width=90)
        self.interval_entry.insert(0, str(S.spam_interval))
        self.interval_entry.grid(row=1, column=3, padx=12, pady=(0, 6), sticky="w")
        self.interval_entry.bind("<Return>", lambda e: (self.sync_interval_from_entry(), self.focus()))
        self.interval_entry.bind("<FocusOut>", lambda e: self.sync_interval_from_entry())

        ctk.CTkLabel(self.card_spam, text="Режим").grid(row=2, column=0, padx=12, pady=(6, 6), sticky="w")
        self.mode_switch = ctk.CTkSegmentedButton(self.card_spam, values=["Тумблер", "Удержание"], command=self.on_mode_change)
        self.mode_switch.set("Удержание" if S.spam_hold_mode else "Тумблер")
        self.mode_switch.grid(row=2, column=1, padx=8, pady=(6, 6), sticky="w")

        ctk.CTkLabel(self.card_spam, text="Горячая клавиша").grid(row=2, column=2, padx=12, pady=(6, 6), sticky="e")
        self.hotkey_entry = ctk.CTkEntry(self.card_spam, width=110)
        self.hotkey_entry.insert(0, S.spam_hotkey)
        self.hotkey_entry.configure(state="disabled")
        self.hotkey_entry.grid(row=2, column=3, padx=8, pady=(6, 6), sticky="w")

        self.btn_bind = ctk.CTkButton(self.card_spam, text="Назначить…", width=130, command=self.start_binding)
        self.btn_bind.grid(row=3, column=3, padx=8, pady=(0, 10), sticky="w")

        self.btn_toggle_spam = ctk.CTkButton(self.card_spam, text="Старт/Стоп (тумблер)", command=self.on_toggle_spam)
        self.btn_toggle_spam.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="w")

        self.spam_status = ctk.CTkLabel(self.card_spam, text=self.get_spam_status())
        self.spam_status.grid(row=4, column=0, columnspan=5, padx=12, pady=(2, 12), sticky="w")

        # Footer
        self.card_footer = ctk.CTkFrame(self)
        self.card_footer.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(self.card_footer, text="Сбросить всё", fg_color="#455A64", hover_color="#37474F", command=self.reset_all).grid(row=0, column=0, padx=12, pady=12, sticky="w")
        ctk.CTkButton(self.card_footer, text="Выход", fg_color="#e53935", hover_color="#c62828", command=self.on_close).grid(row=0, column=1, padx=12, pady=12, sticky="w")
        ctk.CTkLabel(self.card_footer, text="Подсказка: для спама выбери уникальную клавишу (например, F9), чтобы случайно не перехватывать управление.").grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="w")

        # Сохраняем дефолтные цвета кнопок
        for b in (self.btn_lmb, self.btn_w, self.btn_s, self.btn_e, self.btn_toggle_spam):
            self.btn_defaults[b] = {"fg": b.cget("fg_color"), "hover": b.cget("hover_color")}

        self.after(120, self.refresh_status)
        bind_default_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._sync_classic_buttons()
        self._sync_spam_button()

    # ---------- Visual helpers ----------
    def _set_active_style(self, btn: ctk.CTkButton, active: bool):
        if active:
            btn.configure(fg_color="#2e7d32", hover_color="#1b5e20")
            self._start_pulse(btn)
        else:
            self._stop_pulse(btn)
            orig = self.btn_defaults.get(btn)
            if orig:
                btn.configure(fg_color=orig["fg"], hover_color=orig["hover"])

    def _start_pulse(self, btn: ctk.CTkButton):
        if btn in self.pulse_jobs: return
        shades = ["#2e7d32", "#388e3c", "#43a047", "#388e3c"]
        idx = {"i": 0}
        def step():
            i = idx["i"]
            try:
                btn.configure(fg_color=shades[i])
            except Exception:
                return
            idx["i"] = (i + 1) % len(shades)
            self.pulse_jobs[btn] = self.after(300, step)
        step()

    def _stop_pulse(self, btn: ctk.CTkButton):
        job = self.pulse_jobs.pop(btn, None)
        if job:
            try: self.after_cancel(job)
            except Exception: pass

    def _sync_classic_buttons(self):
        self._set_active_style(self.btn_lmb, S.is_holding and S.active_action == "LMB")
        self._set_active_style(self.btn_w,   S.is_holding and S.active_action == "W")
        self._set_active_style(self.btn_s,   S.is_holding and S.active_action == "S")
        self._set_active_style(self.btn_e,   S.is_holding and S.active_action == "E")

    def _sync_spam_button(self):
        running = (keyboard.is_pressed(S.spam_hotkey) if S.spam_hold_mode else S.spam_active)
        self._set_active_style(self.btn_toggle_spam, running)

    # ---------- Classic UI callbacks ----------
    def _ui_toggle_lmb(self):
        toggle_hold_lmb()
        self.classic_status.configure(text=self.get_classic_status())
        self._sync_classic_buttons()

    def _ui_toggle_key(self, k):
        toggle_hold_key(k)
        self.classic_status.configure(text=self.get_classic_status())
        self._sync_classic_buttons()

    def on_bind_window(self):
        title_part = self.title_var.get().strip()
        S.hwnd, S.win_title = find_game_window(title_part) if title_part else (None, "")
        if S.hwnd:
            self.win_status.configure(text=f"Статус: привязано к «{S.win_title}» (hwnd={S.hwnd})")
        else:
            self.win_status.configure(text="Статус: окно не найдено")
        bind_default_hotkeys()

    def get_classic_status(self):
        if not S.hwnd:
            return "Классика: окно не привязано"
        if S.is_holding and S.active_action:
            return f"Классика: удержание {S.active_action}"
        return "Классика: не активно"

    # ---------- Spam UI callbacks ----------
    def on_interval_change(self, val):
        ms = max(1, min(200, int(float(val))))
        S.spam_interval = ms
        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, str(ms))
        self.spam_status.configure(text=self.get_spam_status())

    def sync_interval_from_entry(self):
        try:
            ms = int(self.interval_entry.get())
        except ValueError:
            ms = S.spam_interval
        ms = max(1, min(200, ms))
        S.spam_interval = ms
        self.interval_slider.set(ms)
        self.spam_status.configure(text=self.get_spam_status())

    def on_mode_change(self, value):
        S.spam_hold_mode = (value == "Удержание")
        S.spam_active = False
        bind_default_hotkeys()
        self.spam_status.configure(text=self.get_spam_status())
        self._sync_spam_button()

    def on_toggle_spam(self):
        toggle_spam_toggler()
        self.spam_status.configure(text=self.get_spam_status())
        self._sync_spam_button()

    def start_binding(self):
        self.btn_bind.configure(text="Нажми любую клавишу…")
        self.spam_status.configure(text="Ожидание клавиши для спама…")
        def worker():
            try:
                ev = keyboard.read_event(suppress=False)
                if ev.event_type == keyboard.KEY_DOWN:
                    S.spam_hotkey = ev.name
            except Exception as e:
                print(f"[ERR] key capture: {e}", file=sys.stderr)
            finally:
                bind_default_hotkeys()
                self.after(0, self.finish_binding_ui)
        threading.Thread(target=worker, daemon=True).start()

    def finish_binding_ui(self):
        self.hotkey_entry.configure(state="normal")
        self.hotkey_entry.delete(0, "end")
        self.hotkey_entry.insert(0, S.spam_hotkey)
        self.hotkey_entry.configure(state="disabled")
        self.btn_bind.configure(text="Назначить…")
        self.spam_status.configure(text=self.get_spam_status())
        self._sync_spam_button()

    def get_spam_status(self):
        mode = "Удержание" if S.spam_hold_mode else "Тумблер"
        running = (keyboard.is_pressed(S.spam_hotkey) if S.spam_hold_mode else S.spam_active)
        return f"Спам: {('АКТИВЕН' if running else 'выключен')} • Режим: {mode} • Клавиша: {S.spam_hotkey.upper()} • Интервал: {S.spam_interval} мс"

    # ---------- General ----------
    def reset_all(self):
        stop_spam()
        stop_classic()
        self.classic_status.configure(text=self.get_classic_status())
        self.spam_status.configure(text=self.get_spam_status())
        self._sync_classic_buttons()
        self._sync_spam_button()

    def refresh_status(self):
        self.classic_status.configure(text=self.get_classic_status())
        self.spam_status.configure(text=self.get_spam_status())
        self._sync_classic_buttons()
        self._sync_spam_button()
        self.after(120, self.refresh_status)

    def on_close(self):
        try:
            unbind_hotkeys_and_mouse()
        except Exception:
            pass
        stop_spam()
        stop_classic()
        self.destroy()

# ------------------- Run -------------------
if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        pass
