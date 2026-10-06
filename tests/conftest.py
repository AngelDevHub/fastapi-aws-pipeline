import pytest
from fastapi.testclient import TestClient
import sqlite3
import tempfile
import os
from unittest.mock import patch

from main import app

@pytest.fixture(scope="function")
def test_db_path():
    """
    Crea una base de datos SQLite temporal en memoria / archivo para aislar las pruebas.
    """
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Inicializa el esquema en la base de datos temporal
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT NOT NULL, 
            author_id INTEGER, 
            FOREIGN KEY (author_id) REFERENCES authors (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE borrowers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            book_id INTEGER, 
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
    ''')
    conn.commit()
    conn.close()
    
    yield path
    
    # Limpia la base de datos temporal después de la prueba
    os.unlink(path)

@pytest.fixture(scope="function")
def mock_get_db(test_db_path):
    """
    Mockea la función get_db en main.py para que devuelva una conexión a la DB temporal.
    """
    def _mock_get_db():
        conn = sqlite3.connect(test_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    with patch("main.get_db", side_effect=_mock_get_db):
        yield _mock_get_db

@pytest.fixture(scope="function")
def client(mock_get_db):
    """
    Retorna el cliente de pruebas de FastAPI con la base de datos ya mockeada.
    """
    with TestClient(app) as test_client:
        yield test_client
