from setuptools import setup, find_packages

setup(
    name='carousel_api',  # Nombre del paquete
    version='0.1.0',      # Versión inicial
    description='API para el control del carrusel vertical  VERTICAL PIC de Industrias Pico a través de un PLC',  # Descripción breve
    author='IA Punto: Soluciones Integrales de Tecnología y Marketing',
    author_email='desarrollo@iapunto.com',  
    packages=find_packages(),  
    install_requires=[
        'Flask', 
        'flask-cors',
        'flasgger',
        'waitress' # Lista las dependencias de la API aquí
    ],
    entry_points={  # Define el punto de entrada de tla aplicación WSGI
        'console_scripts': [
            'carousel_api = carousel_api.wsgi:app',
        ],
    },
)