import asyncio
import json
import re
import os
from datetime import datetime
from fastapi import FastAPI
from database import init_db, get_db, backup_db, empty_db
from pydantic import BaseModel

app = FastAPI()

async def handle_tcp_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"TCP: Nueva conexión desde {addr}")
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode('utf-8').strip()
            if not message:
                continue
            print(f"TCP: Recibido {message!r}")
            response = {"status": "error", "message": "Comando no reconocido o formato inválido"}
            match_insert = re.match(r'^\{insert:(.+)\}$', message)
            match_get = re.match(r'^\{get:(.+)\}$', message)
            conn = get_db()
            cursor = conn.cursor()
            try:
                if match_insert:
                    element = json.loads(match_insert.group(1))
                    table = element.get('table')
                    data_obj = element.get('data', {})
                    if table == 'authors' and 'name' in data_obj:
                        cursor.execute("INSERT INTO authors (name) VALUES (?)", (data_obj['name'],))
                        conn.commit()
                        response = {"status": "success", "message": "Author created via TCP"}
                    elif table == 'books' and 'title' in data_obj and 'author_id' in data_obj:
                        cursor.execute("INSERT INTO books (title, author_id) VALUES (?, ?)", (data_obj['title'], data_obj['author_id']))
                        conn.commit()
                        response = {"status": "success", "message": "Book created via TCP"}
                    elif table == 'borrowers' and 'name' in data_obj and 'book_id' in data_obj:
                        cursor.execute("INSERT INTO borrowers (name, book_id) VALUES (?, ?)", (data_obj['name'], data_obj['book_id']))
                        conn.commit()
                        response = {"status": "success", "message": "Borrower created via TCP"}
                    else:
                        response = {"status": "error", "message": "Invalid table or data"}
                elif match_get:
                    element = json.loads(match_get.group(1))
                    table = element.get('table')
                    item_id = element.get('id')
                    if table in ['authors', 'books', 'borrowers']:
                        if item_id:
                            cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,))
                            row = cursor.fetchone()
                            if row:
                                response = {"status": "success", "data": dict(row)}
                            else:
                                response = {"status": "error", "message": "Item not found"}
                        else:
                            cursor.execute(f"SELECT * FROM {table}")
                            rows = [dict(row) for row in cursor.fetchall()]
                            response = {"status": "success", "data": rows}
                    else:
                        response = {"status": "error", "message": "Invalid table"}
            except Exception as e:
                response = {"status": "error", "message": str(e)}
            finally:
                conn.close()
            writer.write(json.dumps(response).encode('utf-8') + b'\n')
            await writer.drain()
    except Exception as e:
        print(f"TCP: Error en conexión: {e}")
    finally:
        print(f"TCP: Cerrando conexión de {addr}")
        writer.close()
        await writer.wait_closed()

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    server = await asyncio.start_server(handle_tcp_client, '0.0.0.0', 6061)
    asyncio.create_task(server.serve_forever())
    print("TCP Server running on 0.0.0.0:6061")

def format_response(data):
    return {
        "statusCode": 200,
        "data": data
    }

class AuthorInput(BaseModel):
    name: str

class BookInput(BaseModel):
    title: str
    author_id: int

class BorrowerInput(BaseModel):
    name: str
    book_id: int

# 1. GET authors
@app.get("/api/authors")
def get_authors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authors")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return format_response(rows)

# 2. GET books
@app.get("/api/books")
def get_books():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return format_response(rows)

# 3. GET borrowers
@app.get("/api/borrowers")
def get_borrowers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM borrowers")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return format_response(rows)

# 4. POST author
@app.post("/api/authors")
def create_author(author: AuthorInput):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO authors (name) VALUES (?)", (author.name,))
    conn.commit()
    conn.close()
    return format_response([{"message": "Author created"}])

# 5. POST book
@app.post("/api/books")
def create_book(book: BookInput):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author_id) VALUES (?, ?)", (book.title, book.author_id))
    conn.commit()
    conn.close()
    return format_response([{"message": "Book created"}])

# 6. POST borrower
@app.post("/api/borrowers")
def create_borrower(borrower: BorrowerInput):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO borrowers (name, book_id) VALUES (?, ?)", (borrower.name, borrower.book_id))
    conn.commit()
    conn.close()
    return format_response([{"message": "Borrower created"}])

# 7. DELETE book
@app.delete("/api/books/{book_id}")
def delete_book(book_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    return format_response([{"message": "Book deleted"}])

# 8. DELETE borrower
@app.delete("/api/borrowers/{borrower_id}")
def delete_borrower(borrower_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM borrowers WHERE id = ?", (borrower_id,))
    conn.commit()
    conn.close()
    return format_response([{"message": "Borrower deleted"}])

# 9. POST backup db
@app.post("/api/database/backup")
def backup_database():
    backup_db()
    return format_response([{"message": "Database backup completed"}])

# 10. POST empty db
@app.post("/api/database/empty")
def empty_database():
    empty_db()
    return format_response([{"message": "Database emptied"}])

# 11. GET health
@app.get("/api/health")
def healthcheck():
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "¡Hola, Profesor! El pipeline CI/CD funciona correctamente en AWS EC2.",
        "environment": os.getenv("ENV", "development")
    }
