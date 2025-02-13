import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import sqlite3
from threading import Thread

VOWELS = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"


class WordSearchApp:
    def __init__(self, root):
        self.root = root

        self.root.title("WordMask — Поиск слов по шаблону")
        self.root.iconbitmap('wordmask.ico')
    
        self.filtered_results = []  # Отфильтрованные слова
        self.search_thread = None  # Поток для выполнения поиска
        self.current_pattern = ""  # Текущий шаблон поиска
        
        self.create_ui()

    def create_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=(10,0), fill=tk.X)
        frame.grid_columnconfigure(1, weight=1)

        frame2 = tk.Frame(self.root)
        frame2.pack(padx=10, pady=(0, 10), fill=tk.X)

        # Поле для ввода шаблона
        tk.Label(frame, text="Шаблон:").grid(row=0, column=0, sticky="w")
        self.pattern_entry = tk.Entry(frame, width=30)
        self.pattern_entry.grid(row=0, column=1, sticky="we", padx=(0,5))
        self.pattern_entry.bind("<Return>", lambda event: self.start_search_thread())  # Обработка нажатия Enter

        # Кнопки "Поиск" и "Помощь"
        tk.Button(frame, text="Поиск", command=self.start_search_thread).grid(row=0, column=2, pady=5, padx=(0, 5))
        tk.Button(frame, text="?", command=self.show_help, width=2).grid(row=0, column=3, pady=5)  # Кнопка "Помощь"

        # Фильтры
        tk.Label(frame2, text="Длина слова:").grid(row=1, column=0, sticky="w")
        self.length_combo = ttk.Combobox(frame2, state="readonly", width=5)
        self.length_combo.grid(row=1, column=1, sticky="w")
        tk.Button(frame2, text="Сброс", command=lambda: self.reset_to_all(self.length_combo)).grid(
            row=1, column=2, sticky="w"
        )

        tk.Label(frame2, text="Макс. гласных:").grid(row=1, column=3, sticky="w")
        self.vowels_combo = ttk.Combobox(frame2, state="readonly", width=5)
        self.vowels_combo.grid(row=1, column=4, sticky="w")
        tk.Button(frame2, text="Сброс", command=lambda: self.reset_to_all(self.vowels_combo)).grid(
            row=1, column=5, sticky="w"
        )

        # Привязка событий комбобоксов
        self.length_combo.bind("<<ComboboxSelected>>", lambda event: self.update_vowels_for_length())
        self.vowels_combo.bind("<<ComboboxSelected>>", lambda event: self.update_lengths_for_vowels())

        # Поле вывода результатов
        self.output_text = scrolledtext.ScrolledText(
            self.root, width=80, height=20, wrap=tk.WORD, state=tk.DISABLED, font=("arial",11)
        )
        self.output_text.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
        
        # Разрешаем копирование через обработку события <Button-3> (правая кнопка мыши)
        self.output_text.bind("<Button-3>", self.show_context_menu)

        # Статусбар
        self.statusbar = tk.Label(self.root, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    def show_help(self):
        """Отображает краткую справку по использованию программы."""
        help_text = """
        Поиск слов по шаблону

        Шаблон:
        - Используйте символ '*' для замены любой последовательности символов.
        - Используйте символ '?' для замены одного символа.

        Примеры:
        - Шаблон "ко*" найдет все слова, начинающиеся на "ко".
        - Шаблон "?ок" найдет все слова из трех букв, оканчивающиеся на "ок".

        Фильтры:
        - Длина слова: ограничивает поиск словами определенной длины.
        - Макс. гласных: ограничивает поиск словами с определенным количеством гласных.

        Для начала поиска введите шаблон и нажмите Enter или кнопку "Поиск".
        """
        messagebox.showinfo("Справка", help_text)

    def pattern_to_sql(self, pattern):
        """Преобразует пользовательский шаблон в формат SQL LIKE."""
        sql_pattern = pattern.replace("*", "%").replace("?", "_")  # * → %, ? → _
        return f"{sql_pattern}"

    def search_words(self, pattern, length=None, max_vowels=None, limit=1000):
        """Выполняет поиск слов по шаблону и фильтрам в базе данных."""
        conn = sqlite3.connect("words.db")  # Создаем новое соединение
        cursor = conn.cursor()

        try:
            sql_pattern = self.pattern_to_sql(pattern)
            query = "SELECT word FROM words WHERE word LIKE ?"

            params = [sql_pattern]

            if length is not None:
                query += " AND length = ?"
                params.append(length)

            if max_vowels is not None:
                query += " AND vowel_count <= ?"
                params.append(max_vowels)

            # Добавляем LIMIT для ограничения количества результатов
            query += " LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            results = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить поиск: {e}")
            results = []
        finally:
            conn.close()  # Закрываем соединение

        return results

    def update_filters(self, pattern):
        """Обновление значений фильтров с учетом текущего шаблона."""
        conn = sqlite3.connect("words.db")
        cursor = conn.cursor()

        try:
            sql_pattern = self.pattern_to_sql(pattern)

            # Длины слов
            cursor.execute("SELECT DISTINCT length FROM words WHERE word LIKE ? ORDER BY length", (sql_pattern,))
            lengths = ["Все"] + [str(row[0]) for row in cursor.fetchall()]

            # Количество гласных
            cursor.execute("SELECT DISTINCT vowel_count FROM words WHERE word LIKE ? ORDER BY vowel_count", (sql_pattern,))
            vowels_counts = ["Все"] + [str(row[0]) for row in cursor.fetchall()]

            # Обновляем значения комбобоксов
            self.length_combo["values"] = lengths
            self.vowels_combo["values"] = vowels_counts

            # Сбрасываем фильтры на "Все"
            self.reset_to_all(self.length_combo)
            self.reset_to_all(self.vowels_combo)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить фильтры: {e}")
        finally:
            conn.close()

    def start_search_thread(self):
        """Запуск поиска в отдельном потоке."""
        if self.search_thread and self.search_thread.is_alive():
            messagebox.showwarning("Предупреждение", "Поиск уже выполняется.")
            return

        # Считываем шаблон
        pattern = self.pattern_entry.get().strip()
        if not pattern:
            messagebox.showwarning("Предупреждение", "Введите шаблон поиска.")
            return

        # Сохраняем текущий шаблон
        self.current_pattern = pattern

        # Обновляем статусбар
        self.statusbar.config(text="Идет поиск...")

        # Запуск поиска в отдельном потоке
        self.search_thread = Thread(target=self.perform_search, args=(pattern,))
        self.search_thread.start()

    def perform_search(self, pattern):
        """Выполнение поиска в отдельном потоке."""
        # Получаем значения фильтров
        length = self.length_combo.get()
        max_vowels = self.vowels_combo.get()

        # Преобразуем значения фильтров
        length = int(length) if length.isdigit() else None
        max_vowels = int(max_vowels) if max_vowels.isdigit() else None

        # Выполняем поиск с учетом фильтров
        self.filtered_results = self.search_words(pattern, length, max_vowels)

        # Обновляем UI в основном потоке
        self.root.after(0, self.update_ui_after_search, pattern)

    def update_ui_after_search(self, pattern):
        """Обновление интерфейса после завершения поиска."""
        self.update_filters(pattern)
        self.display_results()

    def display_results(self):
        """Отображение результатов поиска."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(
            tk.END, ", ".join(self.filtered_results) if self.filtered_results else "Слов не найдено."
        )
        self.output_text.config(state=tk.DISABLED)

        # Обновляем статусбар
        self.statusbar.config(text=f"Найдено слов: {len(self.filtered_results)}")

    def reset_to_all(self, combo):
        """Сброс фильтра на 'Все'."""
        if "Все" in combo["values"]:
            combo.current(0)  # Устанавливаем первое значение ("Все")
        else:
            combo.current(0)  # Если "Все" нет, сбрасываем на первый доступный элемент

        # Применяем фильтры после сброса
        self.apply_filters()

    def apply_filters(self):
        """Применение фильтров к результатам поиска."""
        pattern = self.pattern_entry.get().strip()
        if not pattern:
            self.display_results()
            return

        # Получаем значения фильтров
        length = self.length_combo.get()
        max_vowels = self.vowels_combo.get()

        # Преобразуем значения фильтров
        length = int(length) if length.isdigit() else None
        max_vowels = int(max_vowels) if max_vowels.isdigit() else None

        # Выполняем поиск с учетом фильтров
        self.filtered_results = self.search_words(pattern, length, max_vowels)
        self.display_results()

    def update_vowels_for_length(self):
        """Обновление списка максимального количества гласных при изменении длины слова."""
        selected_length = self.length_combo.get()
        if selected_length == "Все":  # Если выбрано "Все"
            self.update_filters(self.current_pattern)
            return

        conn = sqlite3.connect("words.db")
        cursor = conn.cursor()

        try:
            sql_pattern = self.pattern_to_sql(self.current_pattern)

            # Сохраняем текущее значение фильтра гласных
            current_vowels = self.vowels_combo.get()

            # Обновляем список гласных для выбранной длины
            cursor.execute(
                "SELECT DISTINCT vowel_count FROM words WHERE word LIKE ? AND length = ? ORDER BY vowel_count",
                (sql_pattern, selected_length),
            )
            vowels_counts = ["Все"] + [str(row[0]) for row in cursor.fetchall()]

            # Обновляем значения комбобокса гласных
            self.vowels_combo["values"] = vowels_counts

            # Если выбранное значение больше не существует, сбрасываем на "Все"
            if current_vowels not in vowels_counts:
                self.reset_to_all(self.vowels_combo)
            else:
                self.vowels_combo.current(vowels_counts.index(current_vowels))

            # Применяем фильтры
            self.apply_filters()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить фильтры: {e}")
        finally:
            conn.close()

    def update_lengths_for_vowels(self):
        """Обновление списка длин слов при изменении максимального количества гласных."""
        selected_vowels = self.vowels_combo.get()
        if selected_vowels == "Все":  # Если выбрано "Все"
            self.update_filters(self.current_pattern)
            return

        conn = sqlite3.connect("words.db")
        cursor = conn.cursor()

        try:
            sql_pattern = self.pattern_to_sql(self.current_pattern)

            # Сохраняем текущее значение фильтра длины
            current_length = self.length_combo.get()

            # Обновляем список длин для выбранного количества гласных
            cursor.execute(
                "SELECT DISTINCT length FROM words WHERE word LIKE ? AND vowel_count <= ? ORDER BY length",
                (sql_pattern, selected_vowels),
            )
            lengths = ["Все"] + [str(row[0]) for row in cursor.fetchall()]

            # Обновляем значения комбобокса длин
            self.length_combo["values"] = lengths

            # Если выбранное значение больше не существует, сбрасываем на "Все"
            if current_length not in lengths:
                self.reset_to_all(self.length_combo)
            else:
                self.length_combo.current(lengths.index(current_length))

            # Применяем фильтры
            self.apply_filters()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить фильтры: {e}")
        finally:
            conn.close()

    def show_context_menu(self, event):
        """Показывает контекстное меню только если есть выделенный текст"""
        if self.has_selected_text():
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Копировать", command=self.copy_text)
            menu.post(event.x_root, event.y_root)

    def has_selected_text(self):
        """Проверяет, есть ли выделенный текст"""
        try:
            # Пытаемся получить индексы выделенного текста
            self.output_text.tag_ranges(tk.SEL)
        except tk.TclError:
            return False  # Нет выделенного текста
        return True

    def copy_text(self):
        """Временно активирует виджет для копирования текста"""
        self.output_text.config(state=tk.NORMAL)  # Временно активируем
        self.output_text.event_generate("<<Copy>>")  # Генерируем событие копирования
        self.output_text.config(state=tk.DISABLED)  # Возвращаем обратно в DISABLED


if __name__ == "__main__":
    root = tk.Tk()
    app = WordSearchApp(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # Обработка прерывания программы через Ctrl+C
        print("Программа завершена.")