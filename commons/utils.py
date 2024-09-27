# utils.py

ESTADOS_PLC = {
    0: {
        'nombre': 'READY',
        0: 'El equipo no puede operar',
        1: 'El equipo está listo para operar'
    },
    1: {
        'nombre': 'RUN',
        0: 'El equipo está detenido',
        1: 'El equipo está en movimiento (comando de movimiento activo)'
    },
    2: {
        'nombre': 'MODO_OPERACION',
        0: 'Remoto',
        1: 'Manual'
    },
    3: {
        'nombre': 'ALARMA',
        0: 'No hay alarma',
        1: 'Alarma activa'
    },
    4: {
        'nombre': 'PARADA_EMERGENCIA',
        0: 'Sin parada de emergencia',
        1: 'Parada de emergencia presionada y activa'
    },
    5: {
        'nombre': 'VFD',
        0: 'El variador de velocidad está OK',
        1: 'Error en el variador de velocidad'
    },
    6: {
        'nombre': 'ERROR_POSICIONAMIENTO',
        0: 'No hay error de posicionamiento',
        1: 'Ha ocurrido un error en el posicionamiento'
    },
    7: {
        'nombre': 'SENTIDO_GIRO',
        0: 'Ascendente',
        1: 'Descendente'
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

    estado_binario = format(status_code, '08b')
    estados_activos = {}

    # Iterar sobre los bits de derecha a izquierda (LSB a MSB)
    for i in range(8):  
        bit_value = (status_code >> i) & 1  # Extraer el valor del bit i
        estado = ESTADOS_PLC[i]
        estados_activos[estado['nombre']] = estado[bit_value]

    return estados_activos