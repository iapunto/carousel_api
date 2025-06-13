# utils.py

"""
Funciones utilitarias para interpretación de estados del PLC.

Incluye mapeo de bits a estados legibles y utilidades para el procesamiento de códigos de estado.
"""

ESTADOS_PLC = {
    "READY": {
        "bit": 0,
        "descripcion": {
            0: "El equipo no puede operar",
            1: "El equipo está listo para operar"
        }
    },
    "RUN": {
        "bit": 1,
        "descripcion": {
            0: "El equipo está detenido",
            1: "El equipo está en movimiento (comando de movimiento activo)"
        }
    },
    "MODO_OPERACION": {
        "bit": 2,
        "descripcion": {
            0: "Modo Manual",
            1: "Modo Remoto"
        }
    },
    "ALARMA": {
        "bit": 3,
        "descripcion": {
            0: "No hay alarma",
            1: "Alarma activa"
        }
    },
    "PARADA_EMERGENCIA": {
        "bit": 4,
        "descripcion": {
            0: "Sin parada de emergencia",
            1: "Parada de emergencia presionada y activa"
        }
    },
    "VFD": {
        "bit": 5,
        "descripcion": {
            0: "El variador de velocidad está OK",
            1: "Error en el variador de velocidad"
        }
    },
    "ERROR_POSICIONAMIENTO": {
        "bit": 6,
        "descripcion": {
            0: "No hay error de posicionamiento",
            1: "Ha ocurrido un error en el posicionamiento"
        }
    },
    "SENTIDO_GIRO": {
        "bit": 7,
        "descripcion": {
            0: "Ascendente",
            1: "Descendente"
        }
    }
}


def interpretar_estado_plc(status_code):
    """
    Interpreta el código de estado del PLC y devuelve un diccionario con los estados y sus descripciones.

    Args:
        status_code: El código de estado del PLC en formato entero (8 bits).

    Returns:
        Un diccionario donde las claves son los nombres de los estados y los valores son sus descripciones.
    """
    estados_activos = {}

    # Iterar sobre todos los estados definidos en ESTADOS_PLC
    for estado, detalles in ESTADOS_PLC.items():
        bit = detalles["bit"]
        # Extraer el valor del bit correspondiente
        valor_bit = (status_code >> bit) & 1
        estados_activos[estado] = determinar_bandera(estado, valor_bit)

    return estados_activos


def determinar_bandera(estado, valor_bit):
    """
    Determina el estado basándose en su descripción.

    Args:
        estado (str): Nombre del estado (por ejemplo, "ALARMA").
        valor_bit (int): Valor del bit correspondiente al estado.

    Returns:
        str: Descripción específica del estado.
    """
    if estado == "READY":
        return "OK" if valor_bit == 1 else "Inactivo"
    elif estado == "RUN":
        return "Moviendose" if valor_bit == 1 else "Parado"
    elif estado == "MODO_OPERACION":
        return "Manual" if valor_bit == 0 else "Remoto"
    elif estado == "ALARMA":
        return "Activa" if valor_bit == 1 else "Sin Alarma"
    elif estado == "PARADA_EMERGENCIA":
        return "Desactivada" if valor_bit == 1 else "Presionada"
    elif estado == "VFD":
        return "Fallo" if valor_bit == 1 else "OK"
    elif estado == "ERROR_POSICIONAMIENTO":
        return "Fallo" if valor_bit == 1 else "OK"
