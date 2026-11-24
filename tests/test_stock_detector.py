import json

from src.main import (
    detect_stock,
    check_product, 
    is_valid_product,
    load_products,
    has_restocked,
    load_stock_data,
    save_stock_data,
    IN_STOCK,
    OUT_OF_STOCK, 
    UNKNOWN,
)
from pathlib import Path
import httpx

"""
- (__file__) refers to the current Python file, test_stock_detector.py
- Path(__file__).parent represents the directory containing that file
- We append fixtures and the filename to build the path to the sample HTML

This is better than just assuming the terminal is always runnin from a particular directory
"""

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def load_html(filename):
    file_path = FIXTURES_DIR / filename
    return file_path.read_text(encoding="utf-8")

# Assert compara el resultado real con el esperado. Si no coinciden pytest muestra el fallo y donde ocurrió
def test_product_is_in_stock():
    html = '<p class ="stock in-stock">En stock</p>'  

    assert detect_stock(html) == IN_STOCK

def test_product_is_out_of_stock():
    html = '<p class ="stock out-of-stock">Agotado</p>'

    assert detect_stock(html) == OUT_OF_STOCK

def test_stock_status_is_missing():
    html = '<p class = "price"> 29.99 $</p>'

    assert detect_stock(html) == UNKNOWN

# Cuando encontramos un elemento con clase 'stock', pero no sabemos interpretar el estado.
def test_stock_status_is_unrecognized():
    html = '<p class="stock">Consultar Disponibilidad</p>'

    assert detect_stock(html) == UNKNOWN

def test_conflicting_classes_return_unknown():
    html = '<p class="stock in-stock out-of-stock">Consultar</p>'

    assert detect_stock(html) == UNKNOWN

def test_conflicting_elements_return_unknown():
    html = """
    <p class="stock in-stock">En stock</p>
    <p class="stock out-of-stock">Agotado</p>
    """

    assert detect_stock(html) == UNKNOWN

def test_check_product_returns_stock_status(monkeypatch):
    html = '<p class="stock in-stock">En stock</p>'

    monkeypatch.setattr(
        "src.main.fetch_page",
        lambda url: html,
    )

    result = check_product("https://example.com")

    assert result == {
        "status": IN_STOCK,
        "error": None,
    }

def test_check_product_handles_http_failure(monkeypatch):
    def fail_fetch(url):
        raise httpx.ConnectError("Connection failed")

    monkeypatch.setattr(
        "src.main.fetch_page",
        fail_fetch,
    )

    result = check_product("https://example.com")

    assert result["status"] is None
    assert "Connection failed" in result["error"]

def test_valid_product():
    product = {
        "name": "Booster Box",
        "url": "https://example.com"
    }

    assert is_valid_product(product) is True

def test_is_missing_url():
    product = {
        "name": "Booster Box"
    }

    assert is_valid_product(product) is False

def test_product_is_a_dictionary():
    product = "Booster Box"
    assert is_valid_product(product) is False

def test_load_products_file_not_found(tmp_path):
    missing_file = tmp_path / "missing_products.json"

    result = load_products(missing_file)

    assert result is None

def test_load_products_invalid_json(tmp_path):
    invalid_file = tmp_path / "invalid_products.json"

    invalid_data = {
        "name" : "Booster Box",
        "url" : "https://example.com"
    }

    invalid_file.write_text(
        json.dumps(invalid_data),
        encoding="utf-8"
    )

    result = load_products(invalid_file)

    assert result is None

def test_load_products_invalid_list(tmp_path):
    invalid_file = tmp_path / "invalid_list.json"

    invalid_file.write_text(
        '{' \
        '"name": "Booster Box",' \
        ' "url": "https://example.com"' \
        '}',
        encoding="utf-8"
    )

    result = load_products(invalid_file)

    assert result is None

def test_change_of_stock():
    result = has_restocked(OUT_OF_STOCK, IN_STOCK)

    assert result is True

def test_still_out_of_stock():
    result = has_restocked(OUT_OF_STOCK, OUT_OF_STOCK)

    assert result is False

def test_still_in_stock():
    result = has_restocked(IN_STOCK, IN_STOCK)

    assert result is False

def test_unknown_to_in_stock_is_not_restock():
    result = has_restocked(UNKNOWN, IN_STOCK)

    assert result is False

def test_valid_json_dictionary(tmp_path):
    stock_file = tmp_path / "stock_data.json"

    stock_file.write_text(
        '{"Booster Box": "OUT_OF_STOCK"}',
        encoding="utf-8"
    )

    result = load_stock_data(stock_file)

    assert result == {"Booster Box": OUT_OF_STOCK}

def test_load_stock_data_missing_file(tmp_path):
    missing_file = tmp_path / "missing_stock_data_file.json"

    result = load_stock_data(missing_file)

    assert result == {}

def test_invalid_json(tmp_path):
    invalid_json_file = tmp_path / "invalid_json_file.json"

    invalid_json_file.write_text(
        '{"Booster Box": "OUT_OF_STOCK"',
        encoding="utf-8"
    )

    result = load_stock_data(invalid_json_file)

    assert result is None

def test_save_stock_data_success(tmp_path):
    data_path = tmp_path / "invalid_stock_data.json"

    stock_data = {
        "Booster Box": OUT_OF_STOCK,
        "Booster Bundle": IN_STOCK
    }

    result = save_stock_data(data_path, stock_data)

    assert result is True

    saved_data = json.loads(data_path.read_text(encoding="utf-8"))

    assert saved_data == stock_data

    