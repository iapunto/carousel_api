# Requerimientos para el Programador del PLC — Vertical PIC

**Proyecto:** IA Punto WMS — Industrias Pico S.A.S
**Fecha:** Octubre 2025
**Equipo:** Carrusel vertical Vertical PIC — PLC Delta AS218P (confirmar modelo)
**Software que se comunica con el PLC:** `carousel_api` (servicio Windows)

---

## 1. Contexto — cómo nos comunicamos hoy

El software del WMS habla con el PLC por dos vías:

| Vía | Puerto | Uso actual |
|---|---|---|
| Protocolo propietario (socket TCP) | `:3200` | Comandos de movimiento (2 bytes: comando + posición) y byte de estado |
| Modbus TCP | `:502` | Telemetría: posición física, posición objetivo |

**Flujo actual de un comando:** Odoo → API → socket `:3200` → PLC ejecuta movimiento → responde byte de estado.

---

## 2. Lo que ya encontramos en los registros Modbus

Escaneamos el banco de registros holding (D0–D2000) y esto es lo que el programa publica hoy:

| Registro | Valor observado | Interpretación nuestra (¿confirmar?) |
|---|---|---|
| `D0` | posición actual | Posición física real, 0-indexada — la usamos como posición verdadera |
| `D2` | posición destino | Posición objetivo/comandada |
| `D20` | 352 (`0x0160`) | ¿Palabra de estado secundaria? Desconocido |
| `D22` | 1 | ¿Espejo de posición/target? |
| `D4–D16` | 48, 38, 2, 37, 1, 4, 6 | ¿Tabla de configuración de cangilones/niveles? |
| `D100` | pulso transitorio 0→1 | Cambió al manipular la barrera/reset — ¿flag de alarma tipo latch? |
| `D1000` | 21 | **Parece el byte de estado del protocolo :3200 espejado** (bits: READY, RUN, MODO, ALARMA, PARADA_EMERG, VFD, ERROR_POS, SENTIDO) |
| `D1001` | 1 | ¿Posición actual espejada? |

Todo lo demás (X, Y, M0–M2047, T, C) lee en cero — **las entradas físicas no están espejadas a Modbus**.

---

## 3. Objetivo — a lo que queremos llegar

1. **Toda la telemetría por Modbus** (un solo canal `:502`): estado completo, posición, target, alarmas, barrera. Hoy el socket `:3200` solo devuelve 2 bytes y es lento.
2. **Alertas reales en el WMS**: cuando suene una alarma o se dispare la barrera, el operario debe ver *qué* pasó en pantalla, no solo "equipo no disponible".
3. **Diagnóstico del variador (VFD)** si es accesible desde el PLC.
4. **Datos de mantenimiento**: contadores de ciclos, horas de operación.
5. (Opcional, evaluar) **Comandos de movimiento por Modbus** con enclavamientos de seguridad intactos — solo si existe una interfaz documentada y segura.

---

## 4. Preguntas para el programador

### 4.1 Mapa de registros
1. ¿Puede compartir el **mapa de registros D** del programa actual (qué registro guarda qué)?
2. ¿Qué contiene `D20` (valor 352)? ¿Es una palabra de estado? ¿Qué significa cada bit?
3. ¿Qué contiene la tabla `D4–D16`? ¿Son parámetros de cangilones/niveles?
4. `D1000` parece el byte de estado del `:3200`. ¿Puede confirmar el **significado de cada bit** (bit 0–7)?
5. ¿Qué es `D100`? Lo vimos cambiar 0→1 al manipular la barrera/reset.

### 4.2 Barrera / cortina de seguridad (prioridad alta)
6. La **barrera/cortina de seguridad** está activa pero **no aparece en ningún registro**. ¿Entra al PLC como una entrada física `X`? ¿O corta el motor por hardware (relé de seguridad) sin pasar por el PLC?
7. Si entra al PLC: ¿puede espejarla a un registro? Ejemplo mínimo (1 rung de ladder):
   ```
   LD  X<barrera>  →  OUT M<barrera>   ó   SET/RST D50.bit0
   ```
8. Si es hardwired: ¿el relé de seguridad tiene **contacto auxiliar** disponible para llevarlo a una entrada del PLC?
9. ¿La **HMI/pantalla Delta DOP** muestra la alarma de barrera? Si sí, ¿qué dirección lee el proyecto DOPSoft? (nosotros podemos leer la misma).

### 4.3 Byte de estado y posición del protocolo :3200
10. El segundo byte de la respuesta (posición) **siempre llega en 0** — ¿es un bug conocido del programa o la posición nunca se escribe ahí?
11. Confirmar la semántica exacta de los 8 bits del byte de estado (¿bit 2 = modo remoto? ¿bit 4 = parada de emergencia OK?).
12. El PLC tarda **~0.8s en responder** cada comando por `:3200`. ¿Es normal (scan cycle) o hay algo mejorable?

### 4.4 Conexiones TCP
13. ¿Cuántas **conexiones TCP simultáneas** admite el PLC en `:3200`? Observamos que tarda ~2s en liberar una sesión cerrada.
14. ¿Hay algún timeout de sesión idle configurado? (nuestra app ahora mantiene el socket persistente y queremos confirmar que el PLC lo tolera).
15. ¿Límite de conexiones Modbus `:502` simultáneas?

### 4.5 Alarmas y diagnóstico
16. ¿Existe un **registro de código de alarma** (número de falla)? Hoy solo vemos "hay alarma" sin saber cuál.
17. ¿Se pueden distinguir por software: **parada de emergencia física** vs **barrera** vs **alarma de programa**?

### 4.6 Variador de velocidad (VFD)
18. ¿El VFD está conectado al PLC (RS-485/Modbus)? Si sí, ¿puede exponer:
    - Frecuencia de salida actual
    - Corriente del motor
    - Código de falla del variador
19. ¿Tiempo de rampa de aceleración configurado? (evaluando latencia percibida clic→movimiento).

### 4.7 Contadores y mantenimiento
20. ¿El programa lleva **contadores**: ciclos de movimiento, horas de operación, conteo por cangilón? Si no, ¿puede agregarlos a registros D?
21. ¿Registro de últimos errores / historial de fallas?

### 4.8 Comandos por Modbus (opcional — evaluar juntos)
22. ¿Existe ya una interfaz de comando por Modbus (escribir target + bit de trigger) con enclavamientos? Si no, ¿es viable agregar una **manteniendo todas las validaciones de seguridad del programa actual**?
    - Propuesta si la implementan: `D60` = posición destino, `D61.bit0` = trigger, `D61.bit1` = busy/ack, `D62` = código de resultado.
    - **Importante:** hoy NO escribimos registros de movimiento — solo lo haríamos con una interfaz documentada y validada por usted.

### 4.9 Documentación general
23. Versión/modelo exacto del PLC y firmware.
24. Copia del programa ladder actual o al menos las rutinas de comunicación/estado.
25. ¿Existe documentación del protocolo `:3200` (qué comandos acepta además de 0=status y 1=mover)?

---

## 5. Entregable esperado del técnico

1. **Tabla de registros Modbus** documentada: dirección, tipo, bit/byte, significado, unidad.
2. Si aplica: **rung(s) agregados** para publicar barrera (y datos de VFD/contadores si aplica).
3. Confirmación del protocolo de comandos vigente y sus límites.
4. Datos de conexión definitivos (IP, puertos, límites de sesiones).

---

## 6. Nota técnica para nosotros (referencia interna)

Con `D1000` confirmado como byte de estado completo, la API puede pasar toda la telemetría a Modbus (1 lectura ~50ms vs ~1s del socket). El socket `:3200` quedaría **solo para comandos de movimiento**, o se eliminaría del todo si el técnico implementa la interfaz de comando Modbus del punto 4.8.
