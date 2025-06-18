# FAQ y Troubleshooting — carousel_api

## Preguntas frecuentes (FAQs)

### 1. ¿Qué hago si la API responde 'PLC ocupado por otro proceso'?

- **Causa:** Otro proceso (GUI, app web, otro integrador) está usando el PLC.
- **Solución:** Espera unos segundos y reintenta. Evita enviar múltiples comandos simultáneos.

### 2. ¿Por qué la posición del carrusel no se actualiza?

- **Causa:** El PLC puede no estar enviando el dato correcto, o hay un problema de comunicación.
- **Solución:**
  - Verifica la conexión física y la configuración IP/puerto.
  - Consulta los logs de depuración para ver los bytes recibidos.
  - Si usas simulador, asegúrate de que esté activo.

### 3. ¿Cómo simulo el PLC para pruebas?

- **Solución:** Activa el modo simulador en la configuración (`simulator_enabled: true`) y reinicia la API.

### 4. ¿Cómo expongo la app web fuera de la red local?

- **Solución:** Usa ngrok o similar para exponer el puerto 8181. Asegúrate de que la API también sea accesible si se requiere control remoto.

### 5. ¿Qué hago si recibo error 500 o 409 en la API?

- **Causa:** Puede ser un error interno, parámetros inválidos o lock ocupado.
- **Solución:**
  - Revisa los logs del backend para detalles.
  - Valida los parámetros enviados.
  - Espera y reintenta si es un error de lock.

### 6. ¿Cómo ejecuto las pruebas de concurrencia y robustez?

- **Solución:** Ejecuta `pytest tests/` y revisa que todos los tests pasen.

### 7. ¿Cómo integro un WMS externo?

- **Solución:** Consulta la guía `docs/WMS_INTEGRACION.md` para ejemplos y recomendaciones.

---

## Problemas comunes y soluciones

| Problema                                 | Causa probable                        | Solución recomendada                  |
|------------------------------------------|---------------------------------------|---------------------------------------|
| No conecta al PLC                        | IP/puerto incorrecto, red caída       | Verifica red, IP, puerto y cableado   |
| Comando no ejecuta (sin error)           | PLC ocupado, lock no liberado         | Espera y reintenta, revisa logs       |
| Estado no cambia tras comando            | PLC no responde, error de hardware    | Revisa logs, consulta técnico         |
| App web no accede a la API               | CORS, firewall, red                   | Ajusta CORS, revisa firewall/red      |
| Error de seguridad en auditoría          | Dependencia de terceros               | Actualiza dependencias, revisa changelog |
| Logs no rotan y crecen mucho             | Falta rotación automática             | Configura rotación en logging         |

---

## Recomendaciones generales

- Mantén el sistema y dependencias actualizadas.
- Realiza auditorías de seguridad periódicas.
- Documenta cada cambio relevante.
- Consulta el `README.md` y `PLAN_ACCION.md` para detalles técnicos y de operación.
- Ante dudas, contacta a soporte técnico.
