import win32gui
import win32con
import pygetwindow as gw
import time
import threading
import mouse
import tkinter as tk
import keyboard

# Глобальные переменные для управления зажатием
is_holding = False
active_action = None  # Для отслеживания текущего действия ("LMB", "W", "S", "E")


def toggle_holding(hwnd):
    """Включение/отключение удержания ЛКМ."""
    global is_holding, active_action
    if active_action and active_action != "LMB":
        print("Уже выполняется другое действие!")
        return

    is_holding = not is_holding
    if is_holding:
        active_action = "LMB"
        update_active_actions()
        threading.Thread(target=click_inactive_window, args=(hwnd,), daemon=True).start()
    else:
        active_action = None
        update_active_actions()


def click_inactive_window(hwnd):
    """Эмуляция бесконечного зажатия ЛКМ в окне без его активации."""
    global is_holding
    while is_holding:
        try:
            win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)
            time.sleep(0.1)
        except Exception as e:
            print(f"Ошибка при зажатии ЛКМ: {e}")
            break

    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, None, 0)


def press_inactive_key(hwnd, key_code):
    """Эмуляция бесконечного зажатия клавиши в окне без его активации."""
    global is_holding
    while is_holding:
        try:
            win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(0.1)
        except Exception as e:
            print(f"Ошибка при зажатии клавиши {key_code}: {e}")
            break

    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, key_code, 0)


def toggle_key(hwnd, key, key_code):
    """Включение/отключение удержания клавиш W, S, E."""
    global is_holding, active_action
    if active_action and active_action != key:
        print("Уже выполняется другое действие!")
        return

    if active_action == key:
        active_action = None
        is_holding = False
        update_active_actions()
    else:
        active_action = key
        is_holding = True
        update_active_actions()
        threading.Thread(target=press_inactive_key, args=(hwnd, key_code), daemon=True).start()


def setup_mouse_and_key_hooks(hwnd):
    """Настройка горячих клавиш для мыши и клавиатуры."""
    mouse.on_button(
        lambda: toggle_holding(hwnd) if keyboard.is_pressed('alt') else None,
        buttons=('left',),
        types=('down',)
    )

    keyboard.add_hotkey("alt+w", lambda: toggle_key(hwnd, "W", 0x57))  # VK_CODE для W
    keyboard.add_hotkey("alt+s", lambda: toggle_key(hwnd, "S", 0x53))  # VK_CODE для S
    keyboard.add_hotkey("alt+e", lambda: toggle_key(hwnd, "E", 0x45))  # VK_CODE для E


def reset_all():
    """Сброс всех активных действий."""
    global is_holding, active_action
    is_holding = False
    active_action = None
    update_active_actions()
    print("Все действия сброшены.")


def update_active_actions():
    """Обновление списка текущих активных действий."""
    active_list.delete(0, tk.END)  # Очистка списка
    if active_action:
        active_list.insert(tk.END, f"Активное действие: {active_action}")
    else:
        active_list.insert(tk.END, "Нет активных действий")


def create_interface(hwnd):
    """Создание графического интерфейса."""
    global status_label, active_list

    # Основное окно
    root = tk.Tk()
    root.title("Clicklock by AJIOE1111")
    root.geometry("350x400")  # Увеличение высоты
    root.resizable(False, False)  # Запрет на изменение размера

    # Метка состояния
    status_label = tk.Label(root, text="Статус: Управление", font=("Arial", 14), fg="blue")
    status_label.pack(pady=10)

    # Список активных действий
    active_list = tk.Listbox(root, font=("Arial", 12), height=5, width=40)
    active_list.pack(pady=10)
    update_active_actions()

    # Кнопка для ручного переключения удержания ЛКМ
    toggle_button = tk.Button(
        root, text="Включить/Выключить ЛКМ", font=("Arial", 12),
        command=lambda: toggle_holding(hwnd)
    )
    toggle_button.pack(pady=5)

    # Кнопка для сброса всех удержаний
    reset_button = tk.Button(
        root, text="Сбросить все", font=("Arial", 12), fg="red",
        command=reset_all
    )
    reset_button.pack(pady=5)

    # Инструкции
    instructions = tk.Label(
        root,
        text="Hotkeys:\nAlt + LMB: Toggle LMB\nAlt + W: Toggle W\nAlt + S: Toggle S\nAlt + E: Toggle E",
        font=("Arial", 10),
        justify="left"
    )
    instructions.pack(pady=10)

    # Запуск интерфейса
    root.mainloop()


def find_game_window(title_substring):
    """Найти окно игры по части названия."""
    windows = gw.getWindowsWithTitle(title_substring)
    return windows[0] if windows else None


def main():
    game_title = "War"  # Укажите часть названия окна игры
    window = find_game_window(game_title)

    if not window:
        print("Игра не найдена. Убедитесь, что окно запущено.")
        return

    hwnd = window._hWnd
    print(f"Найдено окно: {window.title}")

    # Настраиваем горячие клавиши мыши и клавиатуры
    setup_mouse_and_key_hooks(hwnd)

    # Запускаем интерфейс
    create_interface(hwnd)


if __name__ == "__main__":
    main()
