import sqlite3

# Путь к файлу со словами
file_path = "dict.txt"

# Подключение к базе данных
conn = sqlite3.connect("words.db")
cursor = conn.cursor()

# Создание таблицы words
cursor.execute("""
CREATE TABLE IF NOT EXISTS words (
    word TEXT PRIMARY KEY,
    length INTEGER,
    vowel_count INTEGER
)
""")

# Создание индексов для оптимизации поиска
cursor.execute("CREATE INDEX IF NOT EXISTS idx_length ON words (length)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_vowel_count ON words (vowel_count)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON words (word)")

# Функция для подсчета гласных в слове
def count_vowels(word):
    vowels = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
    return sum(1 for c in word if c in vowels)

# Заполнение таблицы данными из файла
with open(file_path, "r", encoding="utf-8") as f:
    words = []
    for line in f:
        word = line.strip()
        if word:
            length = len(word)
            vowel_count = count_vowels(word)
            words.append((word, length, vowel_count))
    cursor.executemany("INSERT OR IGNORE INTO words (word, length, vowel_count) VALUES (?, ?, ?)", words)

# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()

print("База данных успешно создана!")