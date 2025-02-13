import sqlite3
import chardet
from chardet.universaldetector import UniversalDetector

# Путь к файлу со словами
file_path = "dict.txt"

# Функция для определения кодировки файла
def detect_encoding(file_path):
    detector = UniversalDetector()
    with open(file_path, 'rb') as f:
        for line in f:
            detector.feed(line)
            if detector.done:
                break
    detector.close()
    return detector.result['encoding']

# Функция для конвертации файла в UTF-8
def convert_to_utf8(file_path, original_encoding):
    with open(file_path, 'r', encoding=original_encoding) as f:
        content = f.read()
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Проверка кодировки файла
encoding = detect_encoding(file_path)
print(f"Определена кодировка файла: {encoding}")

# Если файл не в UTF-8, конвертируем его
if encoding.lower() != 'utf-8':
    print(f"Конвертация файла из {encoding} в UTF-8...")
    convert_to_utf8(file_path, encoding)
    print("Файл успешно конвертирован в UTF-8.")

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
