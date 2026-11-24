import json
from pathlib import Path

from bs4 import BeautifulSoup
import httpx

IN_STOCK = "IN_STOCK"
OUT_OF_STOCK = "OUT_OF_STOCK"
UNKNOWN = "UNKNOWN"

def save_stock_data(data_path, stock_data):
    if not isinstance(stock_data, dict):
        print("Error: stock_data.json must contain a dictionary")
        return False
    
    try:
        with open(data_path, 'w', encoding='utf-8') as file:
            json.dump(stock_data, file, indent=4)
            return True

    except OSError as error:
        print(f"Error: saving stock data: {error}")
        return False


def load_stock_data(data_path):
    try:
        with open(data_path, 'r', encoding='utf-8') as file:
            stock_data = json.load(file)
            if not isinstance(stock_data, dict):
                    print("Error: stock_data.json must contain a dictionary")
                    return None
    
        return stock_data
            
    except FileNotFoundError:
        print("File couldn't be found")
        return {}
    except json.JSONDecodeError:
        print("Error: products.json contains invalid JSON")
        return None



def has_restocked(previous_status, current_status):
    return previous_status == OUT_OF_STOCK and current_status == IN_STOCK

def is_valid_product(product): 
    
    if not isinstance(product, dict):
        return False
        
    name = product.get("name")
    url = product.get("url")

    if not (isinstance(name,str) and name.strip() != ""):
        return False

    if not (isinstance(url, str) and url.strip() != ""):
        return False

    return True


def check_product(url):
    try:
        html = fetch_page(url)
    except httpx.HTTPError as error:
        return {
            "status": None,
            "error": str(error),
        }

    return {
        "status": detect_stock(html),
        "error": None,
    }

""" 
- url is the webpage address we want to retrieve 
- httpx.get() sends an HTTP GET request
- raise_for_status() raises an HTTP error if the server returns an unsucccessful status
- return resonse.text gives the downloaded HTML back to the caller
"""
def fetch_page(url):
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.text

def detect_stock(html):
    soup = BeautifulSoup(html, "html.parser") # Interpreta esa cadena como HTML y Crea una estructura que Python puede recorrer

    stock_element = soup.select(".stock")

    if not stock_element: # Evitamos asumir que el producto está agotado
        return UNKNOWN

    detected_status = set()

    for element in stock_element: 
        classes = element.get("class", [])

        has_in_stock = "in-stock" in classes
        has_out_of_stock = "out-of-stock" in classes

        if has_in_stock and has_out_of_stock: # Conflicting signals in the same element
            return UNKNOWN
        if has_in_stock:
            detected_status.add(IN_STOCK)
        if has_out_of_stock:
            detected_status.add(OUT_OF_STOCK)

    # Not recognizable signal, or conflicting signals across elements
    if len(detected_status) != 1:
        return UNKNOWN

    return detected_status.pop()



# This function reads the JSON file and converts it into Python data. The result is a list of dictionaries
def load_products(config_path):
    try:
        with open(config_path, "r", encoding=" utf-8") as file: # This statement opens the file and automatically closes it when the block finishes
            products = json.load(file) # Parses the JSON content into Python objects
            if not isinstance(products, list):
                print("Error: products.json must contain a list")
                return None

            return products
        
    except FileNotFoundError:
            print("File couldn't be found")
            return None   
    except json.JSONDecodeError:
        print("Error: products.json contains invalid JSON")
        return None
    
def main():
    project_root = Path(__file__).resolve().parent.parent # It locates the project's root directory based on where main.py lives. .resolve() turns path into its absolute resolved form
    config_path = project_root / "config" / "products.json"

    products = load_products(config_path)

    if products is None:
        print("Error: Couldn't load products")
        return

    data_path = project_root / "data" / "stock_data.json"

    stock_data = load_stock_data(data_path) # If you load the data after the loop, you won't have the previous statuses available when checking each product. So we load the data before

    if stock_data is None:
        print("Error: Couldn't load stock data")
        return

    for product in products:
        if not is_valid_product(product):
            print("Invalid product configuration. Skipping")
            continue
        
        name = product["name"]
        url = product["url"]

        previous_status = stock_data.get(name)

        print(f"\nChecking: {name}")
        print(f"URL: {url}")

        result = check_product(url)

        current_status = result["status"]

        if result["error"] is not None:
            print(f"Check failed: {result['error']}")
        else:
            print(f"Availability: {result['status']}")


        if result["error"] is None:
            current_status = result["status"]

            if has_restocked(previous_status, current_status) is True:
                print(f"RESTOCKED: {name}")
            if current_status in (IN_STOCK, OUT_OF_STOCK):
                stock_data[name] = current_status
        else:
            print(f"Check failed: {result['error']}")

    if save_stock_data(data_path, stock_data):
        print("File saved succesfully")
    else: 
        print("Error: File couldn't be saved")



if __name__ == "__main__":
    main()






"""
html = """
"""
<html>
    <head>
        <title>Pokemon 30th Anniversary Box</title>
    </head>
    <body>
        <h1>Pokemon 30th Anniversary Box</h1>

        <div id="product">
            <p class="price">29.99 €</p>
            <p class="stock in-stock">Agotado</p>
            <button id="buy-button">Añadir al carrito</button>
        </div>
    </body>
</html>
"""
"""



# .text extrae el texto de una etiqueta, sin incluir sus etiquetas HTML
print(soup.title.text)
print(soup.h1.text)
print(soup.select_one(".price").text) # Encuentra el primer elemento cuya clase CSS es "price". El (.) indica que buscamos una clase
print(soup.select_one(".stock").text)


"""
"""
import httpx

def main():

    url = "https://www.carrefour.es/pokemon-caja-lote-6-sobres-30th-aniversario-juego-de-mesa-6-anos-unboxing/VC4A-34530762/p"

    try:

        response = httpx.get(url, timeout=10) # Solicita el contenido de la dirección web mediante HTTP Get

        print(f"Status Code: {response.status_code}") # Indica como ha respondido el servido 
        print(f"Successful response: {response.is_success}") # Indica si es una respuesta satisfactoria
        print(f"Content Type {response.headers.get('content-type')}") # Contiene metadatos 
        print(f"Response URL: {response.url}") # Devuelve la URL final ya que puede ser que la pagina redireccione en una URL diferente a la inicial
        print(f"Response type: {type(response.text)}") # Devuelve el tipo de que es 

        response.raise_for_status()

        print("\nFirst 500 characters of HTML:")
        print(response.text[:500]) # Contiene el cuerpo de la respuesta

    except httpx.HTTPError as error: 
        print(f"HTTP request failed: {error}")

"""
