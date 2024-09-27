from api import app

def print_api_info():
    """
    Imprime información sobre la API, incluyendo la descripción de la aplicación y los endpoints.
    """

    print("Descripción de la API:")
    print(app.__doc__.strip())  # Imprime la descripción de la aplicación
    print("\nEndpoints disponibles:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            print(f"- {rule.rule} ({', '.join(rule.methods)}): {app.view_functions[rule.endpoint].__doc__.strip()}")

if __name__ == "__main__":
    print_api_info()