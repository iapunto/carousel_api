"""
Códigos de error internos estándar para carousel_api.

Cada código tiene un identificador, descripción y uso recomendado.
"""

PLC_CONN_ERROR = "PLC_CONN_ERROR"
PLC_BUSY = "PLC_BUSY"
BAD_COMMAND = "BAD_COMMAND"
BAD_REQUEST = "BAD_REQUEST"
INTERNAL_ERROR = "INTERNAL_ERROR"

ERROR_CODES = {
    PLC_CONN_ERROR: "Error de comunicación o conexión con el PLC.",
    PLC_BUSY: "El PLC está ocupado procesando otra solicitud.",
    BAD_COMMAND: "Comando o argumento inválido.",
    BAD_REQUEST: "Solicitud malformada o no permitida.",
    INTERNAL_ERROR: "Error interno inesperado en el sistema."
}
