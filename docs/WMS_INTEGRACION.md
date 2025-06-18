# Guía de Integración WMS — carousel_api

## Objetivo

Facilitar la integración de sistemas de gestión de almacenes (WMS) con el carrusel industrial controlado por `carousel_api`, asegurando robustez, trazabilidad y operación segura.

---

## Endpoints principales

### 1. Consultar estado del carrusel

- **GET** `/v1/status`
- **Respuesta:**

```json
{
  "success": true,
  "data": {
    "status": { ... },
    "position": 2,
    "raw_status": 218
  },
  "error": null,
  "code": null
}
```

### 2. Enviar comando de movimiento

- **POST** `/v1/command`
- **Body:**

```json
{
  "command": 1,
  "argument": 3
}
```

- **Respuesta:**

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "code": null
}
```

---

## Formatos de datos

- **Comando:**
  - `command`: entero (1 = mover)
  - `argument`: entero (0-5, representa cangilón 1-6)
- **Estado:**
  - `position`: entero (posición actual, 0-5)
  - `status`: diccionario con estados interpretados
  - `raw_status`: entero (byte de estado crudo)

---

## Recomendaciones de seguridad y concurrencia

- Solo un proceso puede controlar el PLC a la vez (lock interproceso).
- Si recibe error 409 (PLC ocupado), reintente tras unos segundos.
- Valide siempre la respuesta de la API antes de asumir éxito.
- Use HTTPS si expone la API fuera de la red local.
- Limite el rango de comandos y argumentos a los documentados.

---

## Flujo típico de integración

1. **Consultar estado actual:**
   - GET `/v1/status`
2. **Enviar comando de movimiento:**
   - POST `/v1/command` con el cangilón destino
3. **Esperar confirmación de movimiento:**
   - Polling a `/v1/status` hasta que `position` coincida con el destino
4. **Registrar logs y manejar errores:**
   - Si ocurre error, registrar y reintentar según política del WMS

---

## Troubleshooting para integradores

- **409 PLC ocupado:**
  - Espere y reintente. No haga múltiples requests simultáneos.
- **500 Error interno:**
  - Revise logs del backend y valide parámetros enviados.
- **Timeouts:**
  - Aumente el timeout de su cliente si la red es lenta o el carrusel está en movimiento.
- **Datos inesperados:**
  - Verifique que el firmware del PLC y la versión de la API sean compatibles.

---

## Contacto y soporte

- Para soporte técnico o integración avanzada, contacte a: [soporte@iapunto.com](mailto:soporte@iapunto.com)
- Consulte el README y el PLAN_ACCION.md para detalles adicionales.
