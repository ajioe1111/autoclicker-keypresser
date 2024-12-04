
## Описание

**AutoClicker & Key Presser** — это удобный инструмент для автоматизации нажатий мыши (ЛКМ) и удержания клавиш (`W`, `S`, `E`) в фоновом режиме. Подходит для игр или приложений, где требуется долгое удержание действий.

Программа имеет графический интерфейс, который позволяет:
- Включать/выключать удержание ЛКМ.
- Удерживать клавиши `W`, `S`, и `E` с помощью сочетаний клавиш.
- Отображать текущие активные действия.
- Сбрасывать все удержания одной кнопкой.
- Поддерживает горячие клавиши для управления.

---

## Скриншот интерфейса

![Интерфейс программы](interface.jpg)

---

## Возможности

- **ЛКМ**: Удержание нажатия ЛКМ в указанном окне.
- **Горячие клавиши**:
  - `Alt + ЛКМ`: Включает/выключает удержание ЛКМ.
  - `Alt + W`: Удержание клавиши `W`.
  - `Alt + S`: Удержание клавиши `S`.
  - `Alt + E`: Удержание клавиши `E`.
- **Список активных действий**: Интуитивный интерфейс показывает, какие действия активны.
- **Кнопка сброса**: Быстро завершает все удержания.
- **Автопроверка окон**: Программа продолжит работать даже если целевое окно не найдено.

---

## Установка и запуск

Вы можете скачать готовую сборку в разделе **Releases** или использовать Python для запуска программы.

### 1. Скачивание готовой версии (.exe)
1. Перейдите в раздел **[Releases](https://github.com/ajioe1111/autoclicker-keypresser/releases)**.
2. Скачайте последний релиз (например, `AutoClicker-KeyPresser-v1.0.0.zip`).
3. Распакуйте архив.
4. Запустите файл `AutoClicker-KeyPresser.exe`.

### 2. Запуск из исходного кода
Если вы хотите запустить программу из исходного кода, выполните следующие шаги:

#### Клонирование репозитория:
```bash
git clone https://github.com/ajioe1111/autoclicker-keypresser
cd autoclicker-keypresser
```

#### Установка зависимостей:
Убедитесь, что у вас установлен Python 3.8+.
```bash
pip install -r requirements.txt
```

#### Запуск программы:
```bash
python script.py
```

---

## Использование

1. Запустите программу, откроется интерфейс.
2. В окне выберите нужное действие:
   - **Включить/выключить ЛКМ**: Используйте кнопку или горячую клавишу `Alt + ЛКМ`.
   - **Удержание `W`, `S`, или `E`**: Используйте горячие клавиши `Alt + W`, `Alt + S`, или `Alt + E`.
3. Чтобы завершить все действия, нажмите кнопку `Сбросить все`.
4. Минимизируйте окно, программа продолжит работать в фоне.

---

## Горячие клавиши

- **Alt + ЛКМ**: Включить/выключить удержание ЛКМ.
- **Alt + W**: Удержание клавиши `W`.
- **Alt + S**: Удержание клавиши `S`.
- **Alt + E**: Удержание клавиши `E`.

---

## Зависимости

Список используемых библиотек:
- `pywin32` — для работы с окнами и событиями клавиатуры/мыши.
- `PyGetWindow` — для получения списка окон.
- `mouse` — для обработки событий мыши.
- `keyboard` — для горячих клавиш.
- `tkinter` — для создания графического интерфейса.

---

## Известные проблемы

- Если окно игры не найдено, программа продолжит работать, но удержание ЛКМ или клавиш не будет активным.
- В некоторых играх античиты могут блокировать взаимодействие с эмуляцией событий клавиатуры и мыши.

---

## Лицензия

MIT License © 2024 [AJIOE1111](https://github.com/ajioe1111)
