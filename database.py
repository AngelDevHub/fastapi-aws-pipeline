import sqlite3
import shutil

DB_FILE = 'library.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabla Authors
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    
    # Tabla Books
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES authors (id)
        )
    ''')
    
    # Tabla Borrowers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS borrowers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            book_id INTEGER,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def backup_db():
    backup_file = 'library_backup.db'
    shutil.copy2(DB_FILE, backup_file)
    return True

def empty_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM borrowers')
    cursor.execute('DELETE FROM books')
    cursor.execute('DELETE FROM authors')
    conn.commit()
    conn.close()
    return True

if __name__ == '__main__':
    init_db()
