import pytest
from unittest.mock import patch

# Funciones de utilidad para insertar datos directamente en la BD temporal
def populate_author(mock_get_db, name="Gabriel Garcia Marquez"):
    conn = mock_get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO authors (name) VALUES (?)", (name,))
    conn.commit()
    author_id = cursor.lastrowid
    conn.close()
    return author_id

def populate_book(mock_get_db, title="Cien Años de Soledad", author_id=1):
    conn = mock_get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (title, author_id) VALUES (?, ?)", (title, author_id))
    conn.commit()
    book_id = cursor.lastrowid
    conn.close()
    return book_id

# --- 1. GET /api/authors ---
def test_get_authors_empty(client):
    response = client.get("/api/authors")
    assert response.status_code == 200
    assert response.json()["statusCode"] == 200
    assert response.json()["data"] == []

def test_get_authors_with_data(client, mock_get_db):
    populate_author(mock_get_db, "Isabel Allende")
    response = client.get("/api/authors")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Isabel Allende"

# --- 2. GET /api/books ---
def test_get_books(client, mock_get_db):
    author_id = populate_author(mock_get_db)
    populate_book(mock_get_db, "El Amor en los Tiempos del Cólera", author_id)
    
    response = client.get("/api/books")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "El Amor en los Tiempos del Cólera"

# --- 3. GET /api/borrowers ---
def test_get_borrowers(client, mock_get_db):
    author_id = populate_author(mock_get_db)
    book_id = populate_book(mock_get_db, "Book A", author_id)
    
    conn = mock_get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO borrowers (name, book_id) VALUES (?, ?)", ("Juan Perez", book_id))
    conn.commit()
    conn.close()

    response = client.get("/api/borrowers")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Juan Perez"
    assert data[0]["book_id"] == book_id

# --- 4. POST /api/authors ---
def test_create_author_happy_path(client, mock_get_db):
    response = client.post("/api/authors", json={"name": "Julio Cortazar"})
    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "Author created"
    
    conn = mock_get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authors WHERE name = ?", ("Julio Cortazar",))
    assert cursor.fetchone() is not None
    conn.close()

def test_create_author_validation_error(client):
    # Enviar payload sin el campo requerido 'name' (Edge Case 422)
    response = client.post("/api/authors", json={})
    assert response.status_code == 422
    assert "detail" in response.json()

# --- 5. POST /api/books ---
def test_create_book_happy_path(client, mock_get_db):
    author_id = populate_author(mock_get_db)
    response = client.post("/api/books", json={"title": "Rayuela", "author_id": author_id})
    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "Book created"

def test_create_book_validation_error(client):
    # Invalid data type for author_id
    response = client.post("/api/books", json={"title": "Libro sin Autor", "author_id": "not_an_int"})
    assert response.status_code == 422

# --- 6. POST /api/borrowers ---
def test_create_borrower(client, mock_get_db):
    response = client.post("/api/borrowers", json={"name": "Ana", "book_id": 1})
    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "Borrower created"

def test_create_borrower_missing_fields(client):
    response = client.post("/api/borrowers", json={"name": "Ana"})
    assert response.status_code == 422

# --- 7. DELETE /api/books/{book_id} ---
def test_delete_book(client, mock_get_db):
    author_id = populate_author(mock_get_db)
    book_id = populate_book(mock_get_db, "Libro a eliminar", author_id)

    response = client.delete(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "Book deleted"

    # Verificar que ya no exista
    conn = mock_get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    assert cursor.fetchone() is None
    conn.close()

def test_delete_book_invalid_type(client):
    # ID como string en lugar de int
    response = client.delete("/api/books/invalid_id")
    assert response.status_code == 422

def test_delete_book_not_found(client, mock_get_db):
    # El endpoint de FastAPI no retorna 404 al borrar algo inexistente. 
    # Solo retorna 'Book deleted'. Vamos a probar ese comportamiento esperado.
    response = client.delete("/api/books/999")
    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "Book deleted"

# --- 8. DELETE /api/borrowers/{borrower_id} ---
def test_delete_borrower(client, mock_get_db):
    # No verificaremos la BD aquí por brevedad, sólo el status code
    response = client.delete("/api/borrowers/1")
    assert response.status_code == 200
    assert response.json()["data"][0]["message"] == "Borrower deleted"

# --- 9. POST /api/database/backup ---
def test_backup_database_mocked(client):
    # Mockear backup_db que es una función pesada o toca el sistema de archivos real
    with patch("main.backup_db") as mock_backup:
        response = client.post("/api/database/backup")
        assert response.status_code == 200
        assert response.json()["data"][0]["message"] == "Database backup completed"
        mock_backup.assert_called_once()

# --- 10. POST /api/database/empty ---
def test_empty_database_mocked(client):
    # Mockear empty_db para aislar las pruebas de un vaciado real
    with patch("main.empty_db") as mock_empty:
        response = client.post("/api/database/empty")
        assert response.status_code == 200
        assert response.json()["data"][0]["message"] == "Database emptied"
        mock_empty.assert_called_once()

def test_404_not_found(client):
    # Ruta que no existe
    response = client.get("/api/no_existe")
    assert response.status_code == 404

# --- Escenarios Adicionales Avanzados (QA Extremo) ---

def test_sql_injection_protection(client):
    # Validamos que los parámetros protegidos por SQLite (?) eviten inyección de SQL.
    # Al inyectar sentencias, debería crearse el autor literalmente y NO dropear tablas.
    malicious_payload = "Malicioso'; DROP TABLE books;--"
    response = client.post("/api/authors", json={"name": malicious_payload})
    assert response.status_code == 200
    
    # Comprobamos que la tabla books sigue accesible (no se borró)
    response_books = client.get("/api/books")
    assert response_books.status_code == 200

def test_database_crash_simulation(client):
    # Simulamos que la base de datos o el disco fallan inesperadamente (Database locked o Connection Failed)
    with patch("main.get_db", side_effect=Exception("Simulated Database Failure")):
        # El TestClient de FastAPI (Starlette) propaga las excepciones no capturadas al entorno de pruebas por defecto.
        # En producción esto sería un HTTP 500, pero en testing atrapamos la excepción pura.
        with pytest.raises(Exception) as excinfo:
            client.post("/api/authors", json={"name": "Test DB Crash"})
        assert "Simulated Database Failure" in str(excinfo.value)

def test_delete_idempotent(client, mock_get_db):
    # Intentar eliminar el mismo registro dos veces para confirmar que la API lo tolera de forma segura
    author_id = populate_author(mock_get_db)
    book_id = populate_book(mock_get_db, "Libro Doble Borrado", author_id)
    
    # Primera eliminación (existe en BD)
    assert client.delete(f"/api/books/{book_id}").status_code == 200
    
    # Segunda eliminación del mismo ID (ya no existe en BD)
    assert client.delete(f"/api/books/{book_id}").status_code == 200

def test_healthcheck(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "¡Hola, Profesor!" in data["message"]
    assert "timestamp" in data
