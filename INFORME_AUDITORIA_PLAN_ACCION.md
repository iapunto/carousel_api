Perfecto. Elaboraré un informe completo que combine los hallazgos técnicos previos con el enfoque actualizado centrado en el uso exclusivo en red local. Incluiré también un plan de acción detallado que abarque todas las mejoras y correcciones necesarias, priorizadas y organizadas en fases semanales para que puedas implementarlas como único desarrollador.

Te entregaré un documento consolidado en cuanto esté listo.

# Informe del estado del proyecto `iapunto/carousel_api`

## 1. Diagnóstico Detallado del Sistema

**Resumen:** El sistema `carousel_api` es funcional pero presenta varios problemas críticos en su diseño y calidad que afectan su robustez, seguridad y mantenibilidad. A continuación se detallan las fallas principales identificadas:

### 1.1 Conexión PLC y Manejo de Errores

* **Confiabilidad de la conexión:** La comunicación TCP/IP con el PLC Delta AS Series es frágil. Si bien existe un método `PLC.connect()` con reintentos, este solo captura ciertos errores de red (`socket.timeout`, `ConnectionRefusedError`) e ignora otras excepciones posibles. No hay un mecanismo sólido de reconexión automática en caso de caída de la conexión; actualmente, si el PLC se desconecta, el sistema no intenta restablecer la comunicación de forma persistente más allá de los pocos reintentos inmediatos, lo que deja la API susceptible a fallos intermitentes.

* **Propagación de errores:** El método `get_current_status()` de la clase PLC atrapa excepciones y devuelve un diccionario con `'error'` en lugar de propagar adecuadamente la excepción. Esto hace que en la API los errores de comunicación queden ocultos dentro de la respuesta (p. ej. `{'error': 'mensaje de error'}`) en vez de generar códigos HTTP claros o logs detallados. Como resultado, los integradores podrían recibir respuestas de error poco estandarizadas (mensajes en texto libre) y es posible que les resulte difícil distinguir diferentes tipos de fallas (por ejemplo, tiempo de espera vs. conexión rechazada).

* **Dependencia de conexión en tiempo real:** En versiones previas, el endpoint REST `/v1/status` intentaba conectarse al PLC en **cada** solicitud para leer el estado actual. Esto generaba problemas cuando el PLC estaba inestable o con latencia, provocando errores intermitentes y respuestas lentas para los clientes. Aunque recientemente se introdujo un mecanismo de **cache** de estado con un hilo de monitoreo en segundo plano (ver sección de buenas prácticas), la arquitectura aún depende de consultas frecuentes al PLC y carece de una estrategia de **resiliencia** más allá de unos pocos intentos inmediatos.

### 1.2 Concurrencia y Acceso Simultáneo

* **Ejecución concurrente de la API:** Originalmente, la API Flask se lanzaba desde la GUI en modo desarrollo (single-thread), lo que podía causar problemas de concurrencia al atender múltiples solicitudes simultáneas o bloquear la interfaz. Aunque la implementación actual usa Flask-SocketIO con Eventlet (modelo asíncrono) para mejorar el manejo concurrente, aún existen consideraciones importantes:

  * Dentro del proceso del backend, se utiliza un **lock global** (`plc_access_lock`) para serializar el acceso al PLC, previniendo condiciones de carrera cuando varias peticiones o hilos intentan enviar comandos al mismo tiempo. Esto mitiga parcialmente los riesgos de concurrencia.
  * Sin embargo, la arquitectura actual lanza el **backend de la API y la GUI en procesos separados** sin sincronización entre ellos. La GUI mantiene su propia instancia de conexión PLC distinta del backend, lo que significa que, en teoría, el proceso de la interfaz gráfica podría intentar comunicarse con el PLC al mismo tiempo que el proceso backend (hilo de monitoreo o una petición API) lo hace. No existe un mecanismo inter-proceso para coordinar ese acceso, lo cual representa una posible condición de carrera a nivel de sistema (dos sockets distintos hablando al PLC a la vez). Esto es un **diseño propenso a fallos** de comunicación o lecturas incoherentes si ambos procesos hacen peticiones concurrentes al PLC.

* **Colisiones de comandos de múltiples clientes:** Actualmente, si dos clientes (ej. dos sistemas WMS distintos o GUI + WMS) intentan enviar comandos simultáneamente, el sistema gestiona parcialmente la situación con el lock en la API. Una segunda petición recibirá un error `409 - PLC ocupado` cuando el lock no esté disponible. Si bien esto impide corrupción de datos en el PLC, desde la perspectiva de integración esta situación puede considerarse un **punto de dolor**: los sistemas externos deben manejar reintentos cuando la API indica "PLC ocupado", y no existe una cola interna de comandos pendiente. Esto requiere que el integrador implemente lógica adicional de reintento y puede dificultar la integración con múltiples sistemas concurrentemente.

### 1.3 Diferencias entre Simulador y PLC Real

* **Inconsistencias de interfaz:** El módulo simulador (`PLCSimulator`) no refleja exactamente el comportamiento del PLC real, lo que genera incoherencias entre pruebas y producción. Por ejemplo, el simulador limita las posiciones válidas entre 0-9, mientras que el PLC real acepta un rango más amplio (0-255). Esto implica que los comandos probados con el simulador podrían no cubrir todos los casos reales (p. ej., posiciones altas), y ciertas validaciones o errores podrían manifestarse solo al conectar con el hardware real.

* **Divergencia en métodos y validaciones:** El simulador implementa métodos adicionales (como `move_to_position`) y lógica interna para emular demoras o estados, mientras que el PLC real utiliza un esquema de comando/respuesta más simple. Algunas funciones en el simulador (p. ej. `receive_status`, `receive_position`) están declaradas pero no se usan en la lógica principal, lo cual es **código muerto**. Estas discrepancias pueden confundir a los desarrolladores: métodos presentes en el simulador no existen en la clase real `PLC`, y viceversa (por ejemplo, el PLC real no tiene `move_to_position`). En suma, falta estandarización: la API/Controlador debe lidiar con dos implementaciones con diferencias sutiles, aumentando la complejidad y riesgo de bugs lógicos al no tener una capa de abstracción uniforme.

### 1.4 Código Redundante y Sectores Muertos

* Se identificaron secciones de código que no aportan funcionalidad o están duplicadas, lo que complica el mantenimiento:

  * **Funciones no utilizadas:** Métodos como `receive_status` y `receive_position` en `plc_simulator.py` están definidos pero nunca se utilizan en la lógica del sistema. Asimismo, el archivo completo `api_info.py` solo imprime información de versiones/autor y **no es usado en producción**, pudiendo eliminarse sin impacto.
  * **Lógica duplicada:** La obtención del estado del PLC se implementó de formas diferentes en distintas partes. Por ejemplo, el método `PLC.get_current_status()` devuelve un diccionario con códigos o error, mientras que el controlador `CarouselController.get_current_status()` internamente llama a `send_command(0)` y procesa la respuesta. Sin embargo, el endpoint `/v1/status` de la API no utiliza directamente ninguna de esas funciones de alto nivel, sino que depende del *cache* actualizado por un hilo separado. Esta heterogeneidad sugiere falta de alineación: se han creado utilidades y métodos que luego no se integraron al flujo principal. El resultado es código **muerto o redundante** que genera confusión a nuevos desarrolladores y riesgo de desincronización si partes del sistema evolucionan y otras no.

* **Impacto para desarrolladores:** La presencia de código no utilizado o duplicado es un claro punto de dolor para el mantenimiento. Cualquier desarrollador que se incorpore al proyecto deberá filtrar cuáles partes del código son relevantes. Esto aumenta la curva de aprendizaje y el riesgo de introducir errores al modificar funciones creyendo que están en uso cuando en realidad no afectan nada (o viceversa). Además, complica la implementación de mejoras: por ejemplo, para cambiar cómo se obtiene el estado del PLC habría que modificar múltiples sitios (`PLC.get_current_status`, `CarouselController`, y verificar la lógica del hilo de monitoreo), en lugar de un único punto claro.

### 1.5 Calidad de Pruebas Automatizadas

* **Cobertura muy limitada:** El proyecto actualmente solo cuenta con un archivo de pruebas automatizadas sustancial (`tests/test_plc_simulator.py`), enfocado en el simulador de PLC. Existe también un `tests/test_api.py` (según el repositorio), pero la auditoría indica que la cobertura es parcial y no incluye pruebas integrales de la API REST ni de la interfaz GUI. No se están probando casos críticos como comunicación real con el PLC (posiblemente simulada), concurrencia de comandos, ni escenarios de error.

* **Riesgo de regresión:** Sin pruebas de integración, es difícil garantizar que cambios en el código (por ejemplo, mejorar la lógica de comandos o refactorizar la comunicación) no rompan la funcionalidad existente. La falta de pruebas para la API significa que un integrador externo no tiene ejemplos concretos de uso esperado ni una garantía de estabilidad en los endpoints. Esto compromete la confiabilidad del sistema: problemas de concurrencia o bugs lógicos mencionados anteriormente podrían haberse detectado automáticamente con pruebas bien diseñadas, pero actualmente dependen solo de pruebas manuales o del entorno productivo para salir a la luz.

### 1.6 Despliegue, Ejecución Local y Concurrencia en Producción

* **Ejecución en entorno local:** El proyecto está pensado para uso en redes industriales locales, pero existen **problemas de despliegue y ejecución** derivados de su configuración actual:

  * El lanzamiento por defecto (`python main.py`) inicia tanto la API Flask (SocketIO) como la GUI Tkinter en un solo equipo. Si bien esto es útil para pruebas o demo, en producción podría ser deseable ejecutar solo la API en un servidor (por ejemplo, un PC conectado al PLC) y la GUI opcionalmente en estaciones separadas. Actualmente, el empaquetado no contempla claramente esta separación. Existe un archivo `wsgi.py` en el repositorio que sugiere soporte para ejecución de solo API bajo un servidor WSGI, pero la documentación no detalla su uso. La ausencia de instrucciones claras de despliegue puede llevar a instalaciones incorrectas o inseguras (por ejemplo, usuarios ejecutando la aplicación con privilegios innecesarios o sin configurar firewalls en la red local).
  * El script/instalador (setup) no valida requisitos del sistema industrial (p. ej., si el puerto está libre, si se tiene acceso a la red PLC, dependencias OS). Esto puede causar fallas en la instalación o la primera ejecución que no se detectan hasta el momento de la verdad.

* **Modo de servidor de la API:** Como se mencionó, la API en versiones anteriores corría en modo debug (desarrollo), lo cual no es seguro ni recomendado para entornos productivos. La versión actual usa un servidor eventlet integrado, que mejora la concurrencia, pero sigue corriendo dentro del contexto de la aplicación principal lanzada por un usuario. No se ha documentado la ejecución como servicio del sistema (por ejemplo, un servicio de Windows/Linux que arranque al encender la máquina del PLC). La falta de un despliegue robusto significa riesgo de **tiempo de inactividad**: si la aplicación se cierra accidentalmente (por un usuario cerrando la GUI, por ejemplo), la API dejaría de funcionar, interrumpiendo la comunicación con el WMS.

* **Concurrencia (repaso):** En producción local, múltiples subsistemas podrían acceder a la API simultáneamente (por ejemplo, Odoo lanzando una orden de movimiento mientras otro sistema consulta el estado). Actualmente, gracias al uso de Flask-SocketIO/eventlet, la API puede manejar varios clientes concurrentes, pero como se indicó, serializa los comandos al PLC. Esto evita condiciones de carrera en el PLC pero a costa de rechazar o retrasar solicitudes concurrentes. Si la demanda de comandos crece (e.g., dos WMS enviando secuencia de comandos), el sistema no escala más allá de ejecutar comandos uno por uno.

### 1.7 Configuración y Prácticas de Seguridad

* **Exposición de configuración sensible:** El sistema utiliza un archivo plano `config.json` para almacenar la IP y puerto del PLC, y la opción de modo simulador. Si bien estos datos no son contraseñas, podrían considerarse sensibles en ciertos contextos (direcciones IP internas de la red industrial). Dicho archivo, si no se protege adecuadamente, podría quedar expuesto a usuarios no autorizados en la máquina local. Además, no existe en el código una validación robusta de la configuración al inicio (por ejemplo, verificar que la IP tenga formato válido o que el puerto esté en rango); valores incorrectos en `config.json` podrían causar errores silenciosos o comportamientos inesperados.

* **Ausencia de variables de entorno:** El proyecto no soporta cargar configuración desde variables de entorno para credenciales u otros datos sensibles. Por ejemplo, en entornos industriales es común manejar contraseñas, tokens de API o IPs sensibles mediante variables de entorno o archivos de configuración fuera del repositorio (especialmente si se usa control de versiones). Actualmente, `carousel_api` no sigue esta práctica, lo que sugiere un riesgo de malas configuraciones (por ejemplo, si en el futuro se añade una clave API para autenticación, podría terminar hardcodeada en un archivo).

* **Políticas de CORS y seguridad API:** En la configuración actual, la API habilita CORS (intercambio de recursos de origen cruzado) solo para ciertos orígenes permitidos (por defecto localhost y rangos locales). Esto es positivo, pero vale aclarar que la restricción de CORS **no equivale a autenticación**. Dado que se imagina un uso exclusivamente en red local confinada, la API *no implementa autenticación/autorización de usuarios* ni cifrado de tráfico (no usa HTTPS de forma nativa). Esto en una red cerrada puede ser aceptable, pero representa un riesgo si la red local no es totalmente de confianza o si en algún momento se abriera la API a otra subred. Actualmente, cualquier cliente en la red local que conozca la IP/puerto podría invocar los endpoints libremente. Esto es un **riesgo de seguridad** si terceros no autorizados tuvieran acceso a la red industrial.

* **Gestión de errores y registros de seguridad:** El manejo global de errores de la API convierte excepciones no controladas en respuestas 500 genéricas. Si bien esto evita exponer trazas internas al cliente (buena práctica), el sistema no implementa alertas o logs centralizados de seguridad. Por ejemplo, repetidos intentos fallidos de conexión al PLC solo quedan registrados en un log local de archivo, sin mecanismo de alertar a un operador. Tampoco hay detección de posibles patrones anómalos (aunque en red local este riesgo es bajo). En resumen, la seguridad podría reforzarse incorporando autenticación local básica, uso de HTTPS en entornos donde sea viable y mejores alertas de evento.

### 1.8 Rendimiento y Otras Malas Prácticas

* **Polling vs. tiempo real:** La versión inicial del sistema empleaba un polling del estado del PLC bastante lento (se menciona un intervalo de 60 segundos en la GUI), lo que hacía la interfaz poco reactiva ante cambios. Aunque esto se ha mejorado con la introducción de **Socket.IO** para notificaciones en tiempo real (eliminando la necesidad de polling constante), es importante señalar que el hilo de monitoreo actual consulta el PLC cada \~1 segundo. Esto carga al PLC con una petición periódica; si bien 1 Hz es generalmente tolerable, es un equilibrio entre **reactividad** y **uso de recursos**. No está claro si esta frecuencia es configurable fácilmente. Un intervalo fijo podría ser ineficiente en ciertos escenarios (ej. podría incrementarse dinámicamente bajo carga o reducirse en reposo, etc.).

* **Logging y monitoreo insuficiente:** En la auditoría original se indicó la falta de *logging* estructurado centralizado. Actualmente el sistema escribe logs con nivel INFO/ERROR tanto a consola como a archivo (`carousel_api.log`), lo cual es una mejora. Sin embargo, estos logs podrían ser más detallados y estar mejor organizados. Por ejemplo, se loguean eventos de conexión y errores del PLC, pero no hay un dashboard o resumen de uso (p.ej. cuántos comandos ejecutados, uptime, etc.). Además, ciertos eventos importantes (como un error crítico de comunicación) no notifican al usuario más que con un mensaje genérico; la GUI muestra "Error de comunicación" sin detalles, y aunque eso evita abrumar al usuario final, para técnicos de soporte sería útil contar con más información de diagnóstico fácilmente accesible.

* **Interpretación de estado rígida:** El código que interpreta el byte de estado del PLC (los bits READY, RUN, ALARMA, etc.) funciona pero no está escrito de forma extensible. Está parcialmente duplicado entre un diccionario de definiciones (`ESTADOS_PLC`) y lógica condicional en la función `determinar_bandera`. Si en un futuro se agregan nuevos estados o se cambia la definición de alguno, hay que modificar código fuente en múltiples lugares en vez de actualizar una configuración. Esto es más una mejora de buenas prácticas que un error actual, pero conviene señalarlo: **la escalabilidad del sistema para nuevos tipos de PLC o nuevas señales es limitada** bajo la implementación actual.

### 1.9 Documentación y Usabilidad

* **Documentación desactualizada o incompleta:** Si bien existe documentación (README con descripción general y uso básico de la API) y documentación embebida tipo Swagger en el código, la auditoría señala que la documentación no estaba totalmente alineada con la estructura real del proyecto. Por ejemplo, puede carecer de detalles sobre cómo está organizado internamente (el README actual lista módulos principales, pero integradores podrían requerir más explicación de flujo de datos). No se proveen suficientes ejemplos de despliegue **seguro** (ej. cómo configurar la app en un servidor local de forma que arranque automáticamente, cómo proteger `config.json`, etc.) ni se mencionan las variables de entorno porque no se usan. Para un integrador industrial, también faltan guías de cómo conectar un WMS específico (no hay mención explícita de Odoo, Saint u otros en la doc pública).

* **Usabilidad para el usuario final:** Desde la perspectiva de un operador que use la GUI, la aplicación parece cubrir lo básico (monitoreo de estado, envío de comandos manuales). Sin embargo, algunos aspectos podrían ser confusos o poco prácticos:

  * La GUI depende de configuración manual previa (IP, puerto en `config.json` o a través de un diálogo) y muestra mensajes de error genéricos. Si el PLC no está disponible o mal configurado, el usuario sólo ve "Error de comunicación" sin pasos claros a seguir.
  * No hay confirmaciones de comandos enviados más allá del cambio en el estado; podría ser deseable un feedback más claro en la interfaz después de enviar un comando (por ejemplo, "Comando X enviado exitosamente" o en caso de error, detalles mínimamente técnicos).
  * Para un integrador que no use la GUI sino la API, la usabilidad depende de la consistencia de las respuestas JSON. Actualmente, los endpoints devuelven códigos numéricos y en algunos casos mensajes en español. **No hay estandarización de un formato de respuesta** (por ejemplo, un campo "status" textual universal o códigos de error numéricos). Esto obliga al integrador a leer la documentación o código para interpretar el significado del `status_code` devuelto y de posibles mensajes de error. Cualquier inconsistencia idiomática (por ejemplo, un error dice "PLC en movimiento" vs otro "Error de comunicacion") dificulta el desarrollo del cliente en el WMS, ya que debe contemplar múltiples cadenas.

* **Puntos de dolor adicionales para desarrolladores:** Además de la documentación escasa, un desarrollador que quiera extender o adaptar la API a múltiples WMS enfrentará algunos retos:

  * La lógica de negocio está algo dispersa (parte en el controlador, parte en la vista API). Debe tener cuidado de hacer cambios sincronizados en ambos lados.
  * No existe un mecanismo plug-and-play para soportar otro WMS con particularidades; cualquier diferencia debe manejarse externamente al API o a través de condicionales manuales.
  * Falta de comentarios en algunas secciones o de un documento de arquitectura que explique decisiones de diseño (por qué se usa multiproceso, cómo funciona el bloqueo, etc.). Aunque hay docstrings y comentarios en el código, un documento técnico de alto nivel brillaría por su ausencia, lo que obliga al desarrollador a leer todo el código para entender completamente el flujo.

En síntesis, el diagnóstico revela que **si bien el proyecto cumple su función básica de conectar el PLC con sistemas externos, adolece de problemas de robustez, mantenibilidad y estandarización**. Hay riesgos claros de fallos en comunicación concurrente, dificultades para integradores por documentación y formatos no homogéneos, así como deudas técnicas (código muerto, pruebas insuficientes) que deben abordarse para garantizar un uso confiable en entornos industriales locales.

## 2. Mejores Prácticas Actuales Implementadas

A pesar de los problemas descritos, el proyecto ha incorporado varias buenas prácticas y mejoras recientes que sientan una base positiva sobre la cual construir:

* **Arquitectura modular:** El código está organizado por responsabilidades en módulos claros (API Flask, controlador de carrusel, modelo PLC real, modelo simulador, utilidades comunes). Esta separación facilita ubicar la lógica de negocio vs. comunicación. Por ejemplo, la clase `CarouselController` actúa como orquestador entre la API y el PLC, encapsulando validaciones y la interpretación de estados, lo que es un buen enfoque de diseño MVC.

* **Comunicación robusta con el PLC:** La clase `PLC` implementa reintentos con **backoff exponencial** al conectar y enviar/recibir datos. Esto es una buena práctica que mejora la resiliencia ante fallos temporales de red. Cada intento fallido cierra el socket y espera un tiempo creciente antes de reintentar, lo cual queda registrado en logs. Asimismo, el uso de métodos mágicos `__enter__`/`__exit__` en `PLC` y `PLCSimulator` permite gestionar la conexión con un bloque `with`, garantizando cierre seguro del socket al terminar cada operación.

* **Mecanismo de caché de estado:** Para evitar consultas sin control directo al PLC en cada request HTTP, se introdujo un **hilo de monitoreo** continuo que actualiza el estado del PLC en caché. Este hilo emite eventos `plc_status` vía WebSocket (Socket.IO) cada vez que detecta un cambio y guarda el último estado en `plc_status_cache`. Gracias a esto, el endpoint `GET /v1/status` puede responder inmediatamente con el último estado conocido sin tener que comunicarse sincrónicamente con el PLC, mejorando la **responsividad** de la API y reduciendo la carga sobre el PLC. Esta técnica de **pub-sub** interno (PLC -> caché -> cliente suscrito) es acorde a sistemas en tiempo real y es preferible sobre polling constante agresivo.

* **Notificaciones en tiempo real (WebSocket):** El sistema utiliza Flask-SocketIO y un cliente SocketIO en la GUI para lograr actualizaciones instantáneas del estado del carrusel. Esto elimina retrasos y le permite a la interfaz gráfica (u otros clientes suscritos) reaccionar en cuanto ocurra un cambio (por ejemplo, movimiento completado, alarma activa). En la implementación actual, cuando cambia el estado, el evento `plc_status` es emitido a todos los clientes conectados, y la GUI actualiza sus indicadores casi al instante. Esta práctica de diseño **reactivo** es apropiada para entornos industriales donde la inmediatez es clave, y se destaca como una mejora significativa respecto al enfoque original de encuesta periódica cada 60s.

* **Control de concurrencia en comandos:** Como se mencionó, el uso de un **candado (lock) global** para el PLC en la API es una buena práctica para evitar condiciones de carrera durante la comunicación crítica. Cualquier petición al endpoint `/v1/command` adquiere este lock antes de interactuar con el PLC, impidiendo que dos hilos envíen comandos simultáneamente que pudieran interferir en el protocolo de respuesta. Además, la API maneja apropiadamente esta situación devolviendo un código HTTP 409 (Conflicto) con mensaje "PLC ocupado" cuando el recurso está en uso, informando claramente al cliente del porqué de la negativa en lugar de fallar silenciosamente.

* **Validación estricta de entradas:** Las entradas de la API (códigos de comando y sus argumentos) se validan rigurosamente. Se proveen funciones utilitarias como `validar_comando` y `validar_argumento` que lanzan errores si los valores están fuera de rango o no son del tipo esperado. Esto previene desde temprano el envío de comandos inválidos al PLC y asegura que los integradores respeten el contrato (0-255 para comando y argumento, aunque en la práctica el rango útil sea menor). Asimismo, el endpoint `/v1/command` verifica que el payload JSON exista y contenga el campo necesario antes de proceder, retornando 400 Bad Request si falta, lo cual sigue lineamientos REST correctos.

* **Medidas básicas de seguridad en la API:** A pesar de no tener autenticación, la API incluye algunas configuraciones de seguridad:

  * Límite de tamaño de petición configurado (2 KB) para evitar ataques de **DoS por payload excesivo**.
  * CORS restringido a orígenes de confianza locales (por defecto sólo `localhost`, `127.0.0.1` y rangos de red privada común), previniendo que navegadores clientes de dominios no autorizados consuman la API.
  * Manejo global de excepciones no controladas: cualquier excepción no capturada es registrada en log y resulta en una respuesta genérica 500\*\*\*\*, evitando fuga de información sensible (stacktrace) al cliente. Esto muestra preocupación por no exponer detalles internos en caso de errores inesperados.
  * Integración de herramientas de análisis de seguridad y calidad: El README indica que se usa **Bandit** (análisis estático de vulnerabilidades en Python) y **pip-audit** en cada commit, además de integrar pruebas unitarias en un flujo CI/CD. Si bien la cobertura es limitada, la presencia de estas herramientas sugiere que ya se corrigen automáticamente algunos problemas de seguridad comunes (por ejemplo, uso de funciones inseguras, dependencias con vulnerabilidades conocidas) y que el equipo tiene intención de mejorar la calidad continuamente.

* **Registro de eventos (logging):** Se estableció una configuración de logging que envía mensajes tanto a la consola como a un archivo de log rotativo (`carousel_api.log`) con formato consistente. El código hace uso de diferentes loggers por módulo (por ejemplo, `monitor_plc_status`, `api`, etc.), lo cual es bueno para filtrar la procedencia de los mensajes. Esto ayuda en diagnósticos posteriores: por ejemplo, todos los intentos de conexión y sus fallos quedan registrados con timestamps y niveles (INFO/WARNING/ERROR), facilitando depurar problemas en campo.

* **Simulador integrado para pruebas:** La existencia de un simulador de PLC incorporado es una gran ventaja para desarrollo local y pruebas unitarias. Permite que los desarrolladores puedan ejecutar la aplicación en modo simulación (configurando `"simulator_enabled": true` en `config.json`) sin requerir el hardware físico. El simulador emula retardos, movimientos y errores de forma suficientemente realista, generando códigos de estado aleatorios y simulando movimiento con `time.sleep`. Esto no solo acelera el ciclo de desarrollo, sino que también es útil para **formación**: integradores pueden probar la integración con WMS contra el simulador antes de conectarse al PLC real, reduciendo riesgo en planta.

En resumen, el proyecto ya incorpora prácticas modernas como comunicación en tiempo real, separación por capas, validación de entrada, reintentos con backoff y ciertas medidas de seguridad. Estas sientan un punto de partida sólido para las mejoras propuestas, demostrando que el sistema tiene una base **consciente de buenas prácticas** que ahora debe reforzarse y pulirse en las áreas identificadas como débiles.

## 3. Recomendaciones de Mejora

A la luz del diagnóstico anterior y considerando el contexto de uso **exclusivamente local** como conector entre un PLC industrial y múltiples sistemas WMS (Odoo, SAINT, etc.), se proponen las siguientes mejoras específicas para robustecer y extender `carousel_api`:

### 3.1 Estructura del Código y Mantenimiento

* **Eliminar código muerto y duplicado:** Depurar el repositorio removiendo funciones no utilizadas (`receive_status`, `receive_position`, método `api_info.py`, etc.) para simplificar la base de código. Un código más limpio reduce confusiones y riesgos de mantenimiento. Antes de eliminar, confirmar mediante búsqueda estática que ninguna parte las invoca. Documentar en el changelog qué se removió y por qué (p. ej., "código sin uso desde versión X").

* **Unificar lógica de estado y comandos:** Consolidar en un solo lugar la lógica de obtención de estado y envío de comandos. Se recomienda aprovechar la clase `CarouselController` como punto central:

  * Implementar los endpoints de la API (`/v1/status` y `/v1/command`) utilizando los métodos del `CarouselController` en lugar de acceder directamente al objeto PLC. Por ejemplo, `GET /v1/status` podría simplemente hacer `return jsonify(controller.get_current_status())`, y el controlador internamente manejará la comunicación con el PLC de forma consistente. Esto garantizará que cualquier cambio en la forma de enviar comandos o interpretar respuestas sólo deba hacerse en el controlador, no en múltiples lugares.
  * De igual forma, la GUI al enviar comandos de prueba debería invocar a la API (ej. mediante una llamada HTTP local o un evento SocketIO de comando) en vez de usar directamente `self.plc`. Esta separación clara (GUI consume API, API utiliza controlador, controlador usa PLC) se alinea con principios RESTful y eliminará las rutas de código paralelo que actualmente existen para hacer lo mismo.

* **Mejorar la extensibilidad del interpretador de estados:** Reemplazar la lógica rígida de `interpretar_estado_plc`/`determinar_bandera` por un enfoque más declarativo. Por ejemplo, usar el diccionario `ESTADOS_PLC` ya definido para derivar automáticamente las descripciones:

  * Se podría almacenar en `ESTADOS_PLC` las descripciones para bit=0 y bit=1, y simplemente indexar según el valor del bit en vez de usar múltiples *ifs*. Esto haría más fácil agregar nuevos estados o cambiar textos sin tocar la lógica.
  * Alternativamente, permitir cargar la definición de estados desde un archivo de configuración o JSON externo. Así, si en el futuro se integra otro modelo de PLC con diferentes bits, se podría cambiar la configuración sin modificar el código fuente.
  * Asegurarse de documentar claramente el significado de cada bit y sus implicaciones operativas para los integradores (posiblemente en la documentación de API).

* **Refactorización para múltiples PLC (futuro):** Si bien actualmente se centra en un solo carrusel, contemplar en la estructura la posible necesidad de múltiples instancias (por ejemplo, dos carruseles controlados por la misma API). Esto puede implicar preparar la arquitectura para manejar **múltiples objetos PLC** diferenciados, quizás con identificadores. Si no es un requerimiento actual, al menos dejar la puerta abierta (por ejemplo, no usar variables globales estáticas para `plc` en todo el app, sino quizás un registro de dispositivos). Para soporte multi-WMS simultáneo (ver 3.5), no se prevé que varios PLC sean controlados a la vez, pero es una extensión natural en entornos industriales que podrían reutilizar la solución para más de un equipo.

### 3.2 Comunicación Segura y Confiable con el PLC

* **Centralizar y sincronizar el acceso al PLC:** Es crítico que **solo un proceso/hilo** interactúe con el PLC a la vez. Dado el escenario local, la solución recomendada es **unificar el acceso en el proceso backend**:

  * Modificar la GUI para que **no abra conexiones directas al PLC**. Cualquier acción de la GUI (p. ej. botón "Enviar comando") debe llamar internamente a la API (por HTTP local o emitir un evento SocketIO de control) en lugar de usar `self.plc`. De esta manera, el proceso backend (API) será el único que maneja la comunicación real, evitando condiciones de carrera inter-proceso. La GUI se convertiría en un cliente más de la API, igual que lo serían Odoo o SAINT.
  * Considerar incluso ejecutar la GUI en un equipo distinto conectándose a la API por red, lo que naturalmente impone esta separación. Si debe correr en el mismo equipo, puede comunicarse igual por loopback. Esto alinea la arquitectura con la idea de *un servidor central PLC <-> WMS* y *múltiples clientes*.

* **Mecanismo de reconexión automática:** Implementar una estrategia para mantener la conexión con el PLC **activa y estable**:

  * Una opción es cambiar el patrón *connect -> send -> close* por una conexión persistente con "keep-alive" mientras la aplicación esté activa. Por ejemplo, establecer la conexión TCP al iniciar el backend y conservarla abierta, realizando *pings* periódicos o usando el mismo hilo de monitoreo para verificar que siga viva. Esto evita el overhead de reconectar en cada comando y reduce posibilidades de fallo por repetidas aperturas/cierres de socket.
  * Complementariamente, si la conexión se pierde (detectado por una excepción en el hilo de monitoreo o al enviar un comando), implementar un **reintento automático en segundo plano**: el sistema podría intentar reconectar cada X segundos hasta lograrlo, emitiendo mientras tanto eventos de estado de error. Esto garantiza que ante una caída momentánea del PLC (o un reinicio), la API recuperará la comunicación tan pronto como sea posible sin intervención manual.
  * Registrar los eventos de reconexión en el log y quizás notificar a la GUI/WMS con un evento especial (e.g. `plc_reconnecting` y luego `plc_reconnected` cuando se logre), para que los usuarios tengan visibilidad.

* **Timeouts y manejo de bloqueos:** Asegurarse de que cualquier operación bloqueante hacia el PLC tenga un **timeout** razonable y controlado. Ya que se trata de red local, un timeout de 5s (como está en `PLC.timeout`) es probablemente adecuado. Confirmar que todas las interacciones (send/receive) respetan este timeout y, en caso de excederlo, liberen el lock y retornen un error manejable. Esto parece estar contemplado en los reintentos, pero conviene revisarlo. Asimismo, considerar si es necesario un **timeout global** para comandos encadenados (por ejemplo, si por lógica de PLC una acción podría colgarse sin respuesta, quizá conviene limitar cuánto espera la API antes de desistir).

* **Seguridad de red local:** Aunque la comunicación es en LAN, se recomienda:

  * **Cifrado opcional**: Evaluar si es necesario/posible habilitar SSL/TLS en la API REST (por ejemplo, soportar HTTPS con un certificado local) para proteger datos en tránsito dentro de la fábrica. Si la red es confiable quizá no sea prioritario, pero es bueno dejarlo documentado como opción para casos de políticas estrictas.
  * **Autenticación local**: Implementar al menos una autenticación básica para el API cuando es consumida por sistemas críticos. Por ejemplo, podría ser un token de API configurable vía entorno. Odoo y otros WMS normalmente pueden adjuntar un token en sus requests; configurar la API para que valide un header `Authorization` o una clave secreta en cada petición podría prevenir accesos no deseados incluso en red local (defensa en profundidad). Esta funcionalidad se puede dejar configurable (habilitarla o no según despliegue).
  * **Restricción de acceso por IP**: Como medida adicional, dado que los clientes son conocidos (el servidor Odoo, etc.), se podría integrar un filtrado por IP de origen en la API (ej. rechazar cualquier request que no provenga de las direcciones IP específicas de los WMS o de la subred interna). Esto endurece la API frente a dispositivos desconocidos en la red industrial.

* **Estandarizar cierre de conexiones PLC:** Revisar todos los puntos donde se cierra la comunicación (`plc.close()`). Actualmente se cierra después de cada comando en la API REST y en el hilo de monitoreo se cierra tras cada consulta. Si se adopta la conexión persistente, esta lógica cambiará. En cualquier caso, garantizar que **siempre** se libera el recurso (sock) incluso en casos de excepción, y que no queden conexiones abiertas colgando (posible fuga de sockets). El patrón with ya ayuda, pero hay que aplicarlo consistentemente.

### 3.3 Estandarización de Respuestas de la API

* **Formato consistente de respuesta:** Definir un esquema JSON uniforme que todas las respuestas de la API deberían seguir, para facilitar la integración en múltiples WMS. Por ejemplo, adoptar un envoltorio del estilo:

  ```json
  {
    "success": true/false,
    "data": {...},
    "error": "mensaje de error si aplica",
    "code": 0  // opcional, código numérico de error o 0 si success
  }
  ```

  Actualmente, `/v1/status` devuelve directamente un objeto con el estado o un objeto con `'error'`, mientras `/v1/command` devuelve el diccionario del PLC o un JSON de error similar. Homogeneizando, siempre habría una clave fija para comprobar éxito (así los integradores no tienen que diferenciar por endpoint). Por ejemplo, en caso de error siempre incluir `"success": false` y un campo `"error"` con un mensaje claro; en caso exitoso, `"success": true` y la clave `"data"` conteniendo `status_code` y `position` u otros datos.

* **Incluir interpretaciones de estado**: Dado que se espera que **diferentes WMS** usen esta API, puede ser útil que la API proporcione no solo códigos crudos sino también una interpretación amigable de los mismos, evitando duplicar lógica en cada WMS. Dos enfoques posibles:

  * **Campo adicional en la respuesta**: Por ejemplo, cuando se solicita el estado, además de `status_code` numérico, incluir un objeto `status` con las banderas interpretadas (similar a como hace internamente el controlador). Esto permitiría que, por ejemplo, Odoo muestre directamente "Manual" o "Remoto" o "Fallo" según corresponda, sin tener que conocer el detalle de bits. Si se hace, conviene internacionalizar los textos o al menos documentar que vienen en español.
  * **Endpoint de referencia**: Alternativamente, proporcionar un endpoint como `/v1/status_definitions` que devuelva la definición de los bits (lo que básicamente está en `ESTADOS_PLC`). Así un WMS podría consultar esa info y tener certeza de cómo interpretar el `status_code`. Esto es más útil si los WMS van a implementar su propia interpretación por flexibilidad.

* **Estandarizar mensajes de error:** Ahora mismo, los mensajes de error son cadenas de texto en español generadas en distintas partes ("PLC en movimiento", "No se pudo conectar al PLC", "Error: \<excepción>", etc.). Se recomienda definir **categorías de error** con mensajes claros y quizás códigos. Por ejemplo:

  * Error de conexión al PLC: código `PLC_CONN_ERROR`, mensaje "Fallo de comunicación con PLC".
  * PLC ocupado: código `PLC_BUSY`, mensaje "El PLC está ocupado ejecutando otro comando".
  * Comando inválido: código `BAD_COMMAND`, mensaje "Parámetro de comando inválido".
  * Y así sucesivamente.

  Los clientes (WMS) podrían manejar el código para tomar decisiones (reintentar, notificar al operario, etc.) mientras que el mensaje puede mostrarse al usuario final. Incluir estos códigos en la documentación y, de ser posible, mantenerlos consistentes en eventos WebSocket también (por ejemplo, un evento de error podría llevar `{'error_code': 'PLC_CONN_ERROR', 'error': 'Fallo de comunicación con PLC'}`).

* **Uso consistente de idiomas:** Decidir si las respuestas serán en español (dado el entorno local colombiano, es lo más probable) y mantenerlo así en todas las respuestas. Actualmente casi todos los mensajes están en español, lo cual está bien, pero hay que garantizar que no haya mezcla con inglés en algunas partes (por ejemplo, asegurarse de traducir mensajes por defecto de librerías si aparecen, etc.). Documentar el idioma de las respuestas para que integradores lo sepan. Si se piensa en escalabilidad internacional, podría hacerse los textos en inglés, pero dado el alcance actual, español es adecuado.

### 3.4 Documentación y Soporte para Integradores

* **Guía de integración detallada:** Desarrollar documentación específica orientada a integradores de WMS, más allá del README genérico. Esta guía debería incluir:

  * **Descripción de casos de uso:** Ejemplos completos de cómo un WMS debe interactuar con la API para operaciones comunes (consultar estado antes de una operación, enviar comando de mover a posición, manejo de errores típicos). Incluir ejemplos concretos para Odoo y SAINT: por ejemplo, en Odoo puede haber un módulo Python que haga requests HTTP; proveer pseudocódigo o fragmentos ilustrativos.
  * **Explicación de la interfaz WebSocket:** Muchos integradores podrían aprovechar los eventos en tiempo real. Documentar cómo conectarse al socket (URL, eventos `plc_status` y `plc_status_error` que existen, formato de los datos emitidos). Un integrador de Odoo podría usar esta info para actualizar en su sistema el estado del carrusel en vivo.
  * **Detalles de protocolo PLC:** Incluir en un anexo técnico cómo funciona la comunicación con el PLC (qué significa cada bit de `status_code`, qué comandos existen actualmente: 0 = solicitar estado, 1 = mover, etc.). Esto brinda confianza a integradores de qué hay detrás y les permite entender las limitaciones (por ejemplo, no se puede enviar otro comando mientras RUN esté activo).
  * **Configuración inicial:** Paso a paso para configurar `config.json` con la IP del PLC en el entorno local, habilitar/deshabilitar simulador para pruebas, y cómo arrancar el sistema. Incluir también cómo cambiar el puerto de la API (`api_port`) en caso de conflicto, posiblemente mediante variable de entorno o editando config.
  * **Despliegue en producción local:** Recomendaciones para instalar el sistema en una máquina industrial: sugerir correrlo como servicio (incluir un ejemplo de script de inicio en Linux – systemd unit, o en Windows – tarea programada al inicio de sesión), para que arranque automáticamente. Instrucciones para ejecutar solo la API si la GUI no es necesaria en ese equipo (usando quizás `wsgi.py` con gunicorn eventlet, o una opción CLI tipo `--no-gui` que podría implementarse).
  * **Seguridad y mejores prácticas locales:** Consejos como: "mantenga el sistema operativo actualizado, use una VLAN separada para el PLC, cambie la configuración por defecto de allowed\_origins para restringirla solo a las IPs de sus WMS", etc., para que el integrador/cliente final tenga una referencia de cómo mantener esto seguro aun siendo local.
  * **Resolución de problemas comunes:** Una sección de FAQs o troubleshooting: qué hacer si "Estado no disponible" (verificar conexión PLC, firewall), qué hacer si "PLC ocupado" (asegurarse de no enviar comandos concurrentes, etc.), cómo interpretar un error de comunicación (revisar cableado, IP, etc.). Esto reduce la dependencia de soporte directo.

* **Actualización del README y comentarios:** Asegurarse de que el README principal refleje la nueva estructura y capacidades tras las mejoras. Por ejemplo, si se añaden nuevos endpoints o formatos de respuesta, incluirlos en la tabla de endpoints. También añadir en el README un breve resumen de la arquitectura orientada a este uso local (quizás un diagrama mejorado mostrando PLC, API, WMS 1, WMS 2, GUI). Mantener los comentarios dentro del código actualizados conforme se modifiquen las funciones, para que sigan siendo útiles y no induzcan a error.

* **Ejemplos prácticos y pruebas:** Incluir en el repositorio (o la documentación) ejemplos de clientes. Podría ser un pequeño script Python de muestra que se conecte al API, envíe un comando y espere el evento de confirmación por WebSocket. O un ejemplo de integración con Odoo (quizás una referencia a usar la librería `requests` en Odoo). Además, ampliar las pruebas automatizadas para que sirvan casi como documentación ejecutable: por ejemplo, un test que muestre que al enviar comando 1 (mover) el estado cambia de READY a RUN y luego nuevamente a READY con posición actualizada en simulador – esto ilustra el flujo esperado.

### 3.5 Soporte para Múltiples Sistemas WMS

* **Diseño agnóstico del WMS:** Asegurar que la API permanezca **independiente del WMS** que la consuma. Esto significa evitar hardcodes o supuestos específicos de un sistema externo. En su lugar, mantener la API genérica y configurable. Por ejemplo, si Odoo requiere consumir la API de cierta forma, documentarlo o agregar opciones configurables, pero no cambiar la lógica central solo para Odoo. El objetivo es que tanto Odoo como SAINT (u otro) puedan integrarse sin necesidad de modificar el código fuente, idealmente solo mediante configuración o adaptadores externos.

* **Considerar un módulo "connector":** Si los sistemas WMS a integrar tienen particularidades muy diferentes (formatos de datos, protocolos), evaluar la implementación de un capa de **conectores**:

  * Por ahora, Odoo y SAINT probablemente consumirán la API REST estándar y usarán los eventos WebSocket estándar, lo cual no requiere ningún cambio especial. Pero si, hipotéticamente, un WMS necesitara que la API le envíe solicitudes de vuelta (por ejemplo, que `carousel_api` notifique a un endpoint HTTP de SAINT cuando ocurra algo), se podría habilitar un mecanismo de **webhooks** configurables. Esto permitiría registrar una URL de callback por cada WMS para ciertos eventos. Aunque no es un requerimiento actual explícito, es una funcionalidad útil en contextos de integración múltiple.
  * Otra posibilidad es que un WMS legacy no pueda consumir WebSocket ni quiera hacer polling REST, sino que prefiera, digamos, leer desde una base de datos o archivo compartido. En ese caso extremo, un conector podría ser un componente que escuche los eventos de `carousel_api` y los vuelque en la forma requerida (por ejemplo, escribir en una tabla o archivo CSV). Estos casos deben evaluarse según las necesidades reales; de no ser necesarias ahora, al menos dejar diseño preparado para extensión.

* **Concurrente vs. Secuencial multi-WMS:** Definir políticas en caso de múltiples WMS enviando comandos:

  * Si solo un sistema externo tendrá control maestro (escenario más común: un WMS principal emite comandos y quizá otro solo lee estados), entonces clarificar eso en documentación y quizá permitir marcar ciertas peticiones como de solo lectura vs de control.
  * Si dos sistemas pudieran emitir comandos (poco usual sin coordinación, pero posible si, por ejemplo, dos subsistemas diferentes gestionan distintos tipos de movimientos), habría que implementar un **sistema de arbitraje**. La recomendación general es evitar dualidad de control; pero si fuera necesario, podría implementarse una cola global de comandos entrantes donde peticiones de distintos orígenes se encolen y se ejecuten en orden. Dado que actualmente la API simplemente rechaza el segundo comando entrante con "PLC ocupado", una mejora sería permitir una opción de *queue*: en lugar de retornar 409 inmediatamente, podría aceptarse el comando y guardarse en cola, retornando una respuesta como "queued" y luego ejecutarlo automáticamente. Esto complicaría la lógica (habría que notificar cuando se ejecute más tarde), por lo que solo se recomienda si la integración lo exige. En la mayoría de escenarios industriales, un único orquestador (WMS principal) debe secuenciar los comandos.

* **Configuración específica por WMS:** Si se necesitan adaptaciones menores por WMS (por ejemplo, quizá Odoo espera que las unidades de posición sean 1-10 en vez de 0-9), manejarlo mediante configuración para no bifurcar la API. Por ejemplo, podría haber un parámetro de configuración "position\_offset" o "use\_one\_based\_index" que si se habilita adapta las respuestas. Igualmente, si SAINT manejara algún código especial, incluir banderas configurables. La idea es evitar "forks" del código para cada cliente; en su lugar, hacer la aplicación configurable y documentar a los integradores cómo ajustar esas opciones.

### 3.6 Otras Funcionalidades Nuevas Propuestas

En el contexto industrial local, más allá de los puntos críticos anteriores, se sugieren las siguientes funcionalidades que podrían añadir valor al sistema:

* **Bitácora de operaciones:** Implementar un **log de alto nivel de operaciones** del carrusel, registrando en un archivo o base de datos ligera cada comando ejecutado y su resultado (timestamp, usuario/sistema que lo solicitó, comando, posición, resultado o error). Esto serviría para trazabilidad (saber qué se ha hecho durante el turno, útil ante incidencias) y para analítica básica de uso (por ejemplo, cuántas veces se movió el carrusel a cierta posición en un día). Dado que estamos en entorno local, se puede usar un simple archivo CSV o SQLite para no añadir complejidad de servidores externos.

* **Sistema de alertas y monitoreo:** Extender el manejo de alarmas del PLC. Actualmente, si ocurre una alarma (bit ALARMA o VFD de fallo) el sistema lo refleja en el estado pero podría:

  * Enviar notificaciones activas: por ejemplo, integrar con un servicio de correo local o simplemente destacar más visiblemente en la GUI (un sonido, un popup persistente). Para entornos industriales, incluso se podría pensar en integrarse con una torre de luz o sirena mediante otro PLC/GPIO si estuviera disponible.
  * Ofrecer un endpoint o comando específico para **acknowledge/reset** de alarmas si el PLC lo soporta, para que el WMS o el operario puedan indicar que se ha atendido la alarma.

* **Soporte para múltiples posiciones pre-configuradas:** Si el carrusel almacena artículos en posiciones fijas, se podría añadir una capa en la API para permitir referenciar **ubicaciones lógicas**. Por ejemplo, en vez de enviar `command=1, argument=5`, un WMS podría llamar `/v1/moveTo?location=SKU123`. Esta capa traduciría `SKU123` a la posición numérica (5) a partir de una tabla de configuración de ubicaciones. Esto haría la integración más amigable para sistemas de inventario que manejan identificadores de ubicación o SKU en vez de números de posición. Sería una funcionalidad opcional, pero útil para entornos donde la correspondencia entre posición física y contenido es fija.

* **Interfaz web de administración:** Si bien existe la GUI de escritorio, podría valorarse en el futuro una **pequeña interfaz web** ofrecida por la misma API para configuración y monitoreo básico. Por ejemplo, una página web alojada en `http://<api>:5000/admin` que muestre el estado actual, logs recientes, opción de cargar nueva config, etc. Esto permitiría acceder desde cualquier PC en la red con un navegador para verificar el sistema sin necesidad de la aplicación GUI instalada. Dado que Flask ya está presente, se podría habilitar un blueprint para esto con mínima sobrecarga. Es una mejora de conveniencia para integradores/soporte, manteniendo el enfoque de uso local.

* **Pruebas de conexión y diagnóstico:** Añadir endpoints o comandos de **health check**:

  * Un endpoint `/v1/health` que verifique que la comunicación con el PLC está operativa (podría internamente llamar `get_current_status` y devolver algo como `"plc_connected": true/false, "last_status_ts": <timestamp>`).
  * Un endpoint para obtener información del sistema: versión de software, uptime de la API, quizás estadísticas de comandos enviados, etc., útil para monitorizar.
  * Esto ayuda a integradores a tener monitoreado el conector en sus sistemas (por ejemplo, Odoo podría periodicamente llamar `/v1/health` y alertar si no responde o indica fallo).

* **Extensibilidad a otros PLC o protocolos:** Si bien el alcance actual es PLC Delta AS series, se podría pensar en el futuro en hacer la solución más general. Por ejemplo, soportar PLCs de otra marca mediante implementar otra clase modelo con la misma interfaz. Tener el diseño preparado para eso (quizá renombrando `PLC` a algo como `PLCDelta` e introduciendo una interfaz base `AbstractPLC`). Esto permitiría reutilizar el conector para otros proyectos locales con hardware distinto simplemente adicionando clases y configuraciones, sin reescribir todo. Aunque no es prioridad ahora, es una visión estratégica que se puede mencionar en documentación para mostrar que el sistema no es totalmente rígido.

Todas estas nuevas funcionalidades deben evaluarse según las necesidades inmediatas de **Industrias Pico S.A.S** y sus integradores. Es recomendable priorizar inicialmente aquellas que aporten directamente a la **confiabilidad y facilidad de integración**, que son los objetivos principales en este momento, y planificar las demás como posibles evoluciones futuras.

## 4. Plan de Acción (Hasta 4 semanas)

A continuación se detalla un plan de acción escalonado en un máximo de 4 semanas para implementar las correcciones y mejoras propuestas. Las tareas se agrupan por prioridad (Alta, Media, Baja) dentro de cada semana, de modo que un solo desarrollador pueda organizarlas y ejecutarlas secuencialmente. Este plan asume una dedicación intensiva en cada semana a las tareas indicadas:

### **Semana 1: Estabilización Crítica y Limpieza Inicial**

* **Prioridad Alta:**

  1. **Eliminar código muerto y duplicado:** Remover funciones y archivos no utilizados (`receive_status`, `receive_position`, `api_info.py`, método `move_to_position` del simulador si no se usa, etc.). Probar que la app corre igual tras quitarlos. \*(*Resultado esperado:* base de código más limpia sin afectar funcionalidad)\_
  2. **Corrección de manejo de errores PLC:** Revisar `PLC.connect()` y `PLC.get_current_status()`. Asegurarse de capturar **todas** las excepciones relevantes de conexión (incluir `socket.gaierror`, etc.) y retornar/propagar errores claramente. Implementar que `get_current_status` no coma la excepción por completo: podría dejar que el controlador/API maneje la excepción o al menos loguearla con detalle. \*(*Resultado:* comunicación con PLC no falla en silencio, errores bien registrados)\_
  3. **Confinar acceso PLC al backend:** Modificar la GUI para quitar cualquier acceso directo a `self.plc`. En `MainWindow.send_test_command`, en lugar de usar `self.plc`, llamar al endpoint REST `/v1/command` (se puede usar `requests` o el mismo SocketIO emitiendo un evento de comando que la API atienda). Probar que enviar un comando de prueba desde la GUI sigue funcionando. \*(*Resultado:* solo el proceso backend toca el PLC)\_
  4. **Bloqueo inter-proceso (hotfix):** Mientras se completa lo anterior, implementar un bloqueo rudimentario entre GUI y backend para evitar colisiones (por ejemplo, GUI podría chequear un archivo de lock o similar antes de usar PLC). *Esta es una medida temporal por si la GUI aún necesita tocar PLC en esta semana.* Idealmente, al final de la semana ya no será necesario porque GUI no llamará PLC directamente.

* **Prioridad Media:**
  5\. **Unificar `/v1/status` con caché/controlador:** Adaptar la ruta GET `/v1/status` para que utilice el controlador en lugar de leer `plc_status_cache` directamente, o al menos para que incluya campos interpretados. Por ejemplo, devolver `{'status_code': X, 'position': Y, 'status': <dict interpretado>}`. Verificar que la GUI sigue mostrando correctamente los datos (podría requerir ajustar la función que procesa el evento SocketIO si cambia el formato). \*(*Resultado:* respuestas de status más informativas y consistentes)\_
  6\. **Standardizar respuesta de `/v1/command`:** Modificar la ruta POST `/v1/command` para envolver la respuesta en el formato unificado definido (success, data, error). Manejar casos de error devolviendo códigos y mensajes estándar. Actualizar tests o crear nuevos tests unitarios para verificar este formato. \*(*Resultado:* integradores reciben formato consistente al enviar comandos)\_
  7\. **Documentar cambios en README:** Añadir al README los cambios de esta semana (p.ej., formato de respuesta nuevo, eliminación de partes obsoletas). Asegurarse de que las instrucciones de instalación y uso rápido siguen válidas tras eliminar código. \*(*Resultado:* documentación sincronizada con el estado actual del código)\_

* **Prioridad Baja:**
  8\. **Auditoría de dependencias:** Ejecutar herramientas de seguridad (Bandit, pip-audit) y revisar `requirements.txt`. Actualizar cualquier dependencia obsoleta menor si es seguro hacerlo (ej. parches de Flask, etc.). Verificar compatibilidad tras actualizar. \*(*Resultado:* componentes al día, sin vulnerabilidades conocidas)\_
  9\. **Plan de pruebas inicial:** Escribir 1 o 2 pruebas simples nuevos en `tests/test_api.py` para los endpoints (por ejemplo, probar que GET `/v1/status` en modo simulador retorna código 200 y campos esperados). Estas pruebas sentarán la base para expandir en semanas siguientes. *(*Resultado:* inicio de mejora en cobertura de pruebas)*

### **Semana 2: Robustez de Comunicación y Estandarización**

* **Prioridad Alta:**

  1. **Reconexión automática PLC:** Implementar un **hilo de reconexión** o ampliar el de monitoreo para que, si detecta 3 fallos consecutivos de lectura, inicie un proceso de reconexión periódica. Esto puede lograrse reintentando `plc.connect()` en loop con demoras crecientes hasta que tenga éxito, emitiendo eventos `plc_status_error` con mensajes como "Reintentando conexión...". Probar desconectando el PLC (o simulador) y volviéndolo a conectar para ver que el sistema se recupera sin reiniciar la app. \*(*Resultado:* mayor resiliencia ante caídas de conexión)\_
  2. **Persistir conexión abierta:** Ajustar el flujo de `send_command` para que **no cierre** el socket PLC inmediatamente después de cada operación, a menos que sea necesario. Por ejemplo, mantener `self.sock` abierto para comandos subsecuentes y cerrar solo en casos de error grave o al apagar la app. Cuidar sincronización con el hilo de estado (que ahora también usará la conexión persistente). \*(*Resultado:* menor latencia en comandos consecutivos, menos carga de establecer conexión repetidamente)\_
  3. **Autenticación básica de API:** Agregar soporte para un token de API. Ejemplo: leer de `config.json` o variable de entorno un campo `api_token`. Si está presente, la API requerirá que en cada request venga un header `Authorization: Bearer <token>`. Implementar un middleware sencillo o verificación en cada ruta protegida. Hacerlo opcional (si no se configura token, sigue abierto como antes). Documentar esta nueva opción. \*(*Resultado:* capa de seguridad adicional disponible para entornos que lo requieran)\_
  4. **HTTPS (si viable en entorno):** Investigar la posibilidad de ejecutar Flask-SocketIO en SSL local. Si el entorno lo permite (p.ej. generando un certificado autofirmado), proporcionar instrucciones para configurar `CERT_FILE` y `KEY_FILE` en variables de entorno y hacer que `socketio.run()` las use. Esto puede quedar como documentación/soporte más que implementación compleja. \*(*Resultado:* posibilidad de comunicaciones cifradas en la red local)\_

* **Prioridad Media:**
  5\. **Formato de error unificado:** Introducir códigos de error internos (enum o constantes). Modificar los sitios donde se generan errores para incluir dichos códigos. Por ejemplo, en caso de timeout al enviar comando, en lugar de `{'error': 'Error enviando datos: ...'}` devolver `{'error': 'Error enviando datos al PLC', 'code': 'PLC_CONN_ERROR'}`. Actualizar tanto respuestas REST como eventos SocketIO de error para incluir esta info. \*(*Resultado:* errores más predecibles y manejables por clientes)\_
  6\. **Interpretación de estado en API:** Decidir e implementar si la API devolverá las descripciones de estado (bit flags) directamente. Si se opta por sí, añadir el campo `status` con el diccionario interpretado en las respuestas de estado/comando. Verificar que esto no rompe nada (los clientes existentes, como la GUI, pueden simplemente ignorarlo si no lo usan). \*(*Resultado:* integradores tienen info de estado lista para usar)\_
  7\. **Mejorar logs y monitoreo interno:** Añadir logs INFO/DEBUG adicionales para eventos importantes: cuando se envía un comando, loggear cuál y por quién (si es posible identificar cliente); cuando se recibe respuesta, loggear brevemente el estado; cuando entra una conexión SocketIO, indicarlo. Configurar rotación de logs (si el file handler no lo hace, usar RotatingFileHandler para que no crezca indefinidamente). \*(*Resultado:* mayor capacidad de diagnosticar comportamientos en producción)\_

* **Prioridad Baja:**
  8\. **Extender pruebas unitarias:** Escribir pruebas para el simulador y el PLC (este último, simulado mediante monkeypatch del socket). Por ejemplo, simular que `PLC.sock.recv` devuelve menos de 2 bytes para probar que `receive_response` lanza RuntimeError. Probar que `send_command` lanza RuntimeError si no conectado. También pruebas del controlador: que `CarouselController.send_command(1, arg)` devuelve estructura correcta dada una respuesta simulada. \*(*Resultado:* cobertura de casos críticos, evitando regresiones en comunicación)\_
  9\. **Prueba de carga ligera:** Si es posible, escribir un pequeño script o prueba que lance múltiples hilos o procesos simulando 2 WMS enviando comandos concurrentes y verificando que uno recibe 409 y otro 200, y que no hay corrupción. Esto podría no integrarse en suite automatizada, pero sirve manualmente para validar la solidez de la sincronización. \*(*Resultado:* verificación manual de concurrencia controlada)\_

### **Semana 3: Documentación, Configuración y Compatibilidad Multi-Sistema**

* **Prioridad Alta:**

  1. **Completar documentación para integradores:** Empezar a redactar la **Guía de Integración** detallada (puede ser un archivo `INTEGRADORES.md` en el repo, o documentación PDF aparte). Incluir todos los puntos mencionados en 3.4: explicación de endpoints, ejemplos de uso, interpretación de estados, consejos de despliegue, etc. Recolectar feedback interno si es posible (por ejemplo, del equipo que manejará Odoo) para asegurar que las dudas que tengan queden respondidas en este documento. \*(*Resultado:* documentación lista para ser entregada a equipos externos)\_
  2. **Validación de configuración inicial:** Mejorar el arranque para validar `config.json`. Implementar que al cargar config, si algún campo es inválido (IP mal formateada, puerto fuera de rango, etc.), se registre un error claro y/o se notifique al usuario (si está la GUI, quizás mostrar messagebox de error de config). Incluir default sensible para `api_port` si no está (p.ej. 5000 por defecto). \*(*Resultado:* arranque más robusto que detecta misconfiguraciones al inicio)\_
  3. **Soporte de variables de entorno:** Modificar la carga de configuración para permitir override por entorno. Por ejemplo, si existe env `CAROUSEL_PLC_IP` usarlo en lugar de lo del JSON, etc. Documentar estas variables en el README/Guía. Esto preparará el terreno para despliegues más flexibles (p. ej. en contenedores Docker o simplemente para no tener IPs en texto plano). \*(*Resultado:* flexibilidad en manejo de configuraciones sensibles)\_
  4. **Configuración por WMS (si aplica):** Consultar con stakeholders si se anticipan ajustes específicos para Odoo/SAINT. De ser así, implementar flags configurables. Un caso concreto: si SAINT requiere un formato distinto de algunos datos, ver posibilidad de añadir un parámetro `"mode": "saint"` en config que haga pequeñas adaptaciones (p. ej., campos renombrados). *Mantener por defecto el comportamiento estándar*. Si no hay requerimientos explícitos, dejar esta capacidad en la documentación como posible extensión.

* **Prioridad Media:**
  5\. **Mejoras en GUI (usabilidad):** Ajustar la interfaz gráfica para reflejar cambios y mejorar experiencia:

  * Si la API ahora provee mensajes de error más detallados o códigos, la GUI podría capturar eso y mostrar mensajes más específicos al usuario en vez de siempre "Error de comunicación". Por ejemplo, distinguir "Conexión perdida con PLC" vs "Tiempo de espera agotado".
  * Agregar confirmación visual al enviar comando manual: quizá cambiar el color de algún indicador o mostrar un pequeño mensaje "Comando enviado" para feedback inmediato.
  * Verificar que la GUI pueda reconectarse sola si el backend se reinicia (el loop de SocketIO ya reintenta cada 5s, quizás añadir límite de reintentos o un botón "Reconnectar ahora").
  * Incorporar en la ventana de configuración la opción de *API Token* si se implementó auth, para que el usuario pueda ingresarlo si la GUI se separa y lo requiere para conectar.
    \*(*Resultado:* GUI alineada con backend y más amigable para operadores finales)\_

  6. **Webhook o notificación externa (opcional):** Si se ve factible y útil, implementar un mecanismo para realizar una llamada HTTP saliente o ejecutar una acción cuando ocurran ciertos eventos. Por ejemplo, si el carrusel termina un movimiento (`READY` vuelve a 1 tras RUN), opcionalmente hacer un GET/POST a una URL configurable (podría ser un endpoint de Odoo notificando "movimiento completado"). Esto podría configurarse en `config.json` como `"webhook_on_complete": "http://odoo.local/..."`. Si se implementa, hacerlo de forma que no bloquee el hilo principal (usar thread o async) y loguear si falla. *(*Resultado:* integraciones reactivas posibles sin polling desde WMS)*

* **Prioridad Baja:**
  7\. **Revisar soporte múltiples posiciones:** Analizar la viabilidad de la sugerencia de ubicaciones lógicas. Si se decide implementarla, bosquejar cómo integrar un mapa de posiciones (quizá un archivo JSON de mapeo SKU->posición). Esto probablemente quede fuera del alcance inmediato, pero sentar las bases (por ejemplo, diseñar la estructura de datos aunque no se use todavía). \*(*Resultado:* diseño preparado para características futuras)\_
  8\. **Test de integración end-to-end:** Con la documentación lista, realizar una prueba completa: simular un pequeño flujo como lo haría un WMS. Por ejemplo, escribir un script que:

  * Obtiene estado (espera READY),
  * Envía un comando de movimiento,
  * Recibe confirmación por SocketIO o espera cierto tiempo y consulta estado de nuevo,
  * Verifica que la posición cambió.

  Esto se puede hacer con el simulador activo. Asegurarse de que los resultados coinciden con lo esperado y refinar detalles finales (mensajes, tiempos). *(*Resultado:* verificación de que la API se comporta correctamente en un escenario realista de uso)*

### **Semana 4: Pulido Final y Nuevas Funcionalidades Menores**

* **Prioridad Alta:**

  1. **Implementar bitácora de operaciones:** Tomando la idea propuesta, desarrollar el módulo de logging de alto nivel:

     * Decidir el formato (ej. CSV o SQLite). Para simplicidad, quizás CSV: cada línea con timestamp, tipo de evento, detalles.
     * Registrar en este log cada vez que se ejecuta un comando (desde `/v1/command` exitoso) con quién lo pidió (si es posible identificar el origen; quizá incluir un campo en la petición para ID de cliente o user).
     * Registrar también eventos de error importantes (pérdida de conexión PLC, etc.).
     * Esta bitácora complementará al log técnico existente con un enfoque más funcional. Probar que al enviar varios comandos, el archivo se va llenando correctamente.
       \*(*Resultado:* registro histórico disponible para auditoría de operaciones)\_
  2. **Endpoint /v1/health:** Implementar un nuevo endpoint que devuelva el estado general:

     * Puede incluir `"plc_connected": true/false` (quizá basado en si en el último intervalo de monitoreo hubo error),
     * `"uptime": tiempo corriendo de la API`,
     * Versión de la aplicación.
     * Documentarlo en Swagger y probar su salida. Esto ayuda a monitorear la API misma.
       \*(*Resultado:* capacidad de monitoreo remoto de salud del conector)\_
  3. **Testing de error scenarios:** Escribir pruebas unitarias o de integración simulando condiciones de error:

     * Forzar un `PLC.send_command` a lanzar un BrokenPipe (simulado) y ver que la API devuelve el código de error estándar definido.
     * Simular PLC ocupado (hacer que lock falle) y ver que se obtiene 409.
     * Simular alarmas: en modo simulador, quizá manipular el estado para provocar bit de ALARMA y ver que se refleja correctamente en la respuesta/evento.
       \*(*Resultado:* asegurar que los caminos de error están controlados y testeados)\_

* **Prioridad Media:**
  4\. **Optimización de rendimiento:** Revisar si el intervalo de 1s en monitor es apropiado. Hacer pruebas con 0.5s vs 2s para ver impacto. Si 1s está bien, dejarlo pero hacer que sea configurable (por ejemplo, en `config.json` permitir `status_interval`). Documentar esa opción. \*(*Resultado:* posible ajuste fino del rendimiento según necesidad del cliente)\_
  5\. **Rotación/archivado de logs:** Si los logs (archivo principal y bitácora) pueden crecer mucho, implementar rotación: por ejemplo, mantener máximo X MB o Y días. Python `logging` lo soporta; configurar para que semanalmente rote el archivo de log técnico, y quizás archivar la bitácora mensualmente. \*(*Resultado:* mantenimiento automatizado de logs, preveniendo consumo excesivo de disco en largo plazo)\_
  6\. **Revisar tolerancia a fallos de GUI:** Hacer pruebas desconectando el PLC real mientras la GUI está abierta, ver manejo. También probar cerrar y reabrir la GUI mientras backend sigue corriendo (debería reconectar). Si algo falla en esas transiciones, corregirlo (por ejemplo, reintentar conexión SocketIO indefinidamente, o permitir reabrir GUI sin colgar el proceso backend). *(*Resultado:* UX mejorada en situaciones de reconexión)*

* **Prioridad Baja:**
  7\. **Feedback con el cliente:** Presentar la documentación y la versión casi final al equipo de Ind. Pico o integradores piloto (Odoo). Recopilar sus comentarios: ¿Entienden bien las respuestas? ¿Necesitan algún ajuste en la API? ¿La documentación responde sus dudas? Recopilar esos feedback y planificar pequeñas correcciones de última hora.
  8\. **Plan de despliegue piloto:** Coordinar una prueba en un entorno controlado (por ejemplo, en la planta pero en horario de mantenimiento) donde se instale esta versión mejorada y se conecte con un WMS (simulado o real). Monitorear su comportamiento por unas horas, usando el endpoint /health y los logs para verificar estabilidad. Documentar cualquier incidente o ajuste necesario. Esto quizás va más allá del desarrollo de 4 semanas, pero es un paso crítico antes de declarar el sistema listo para producción.

Al finalizar estas cuatro semanas, el objetivo es haber transformado `carousel_api` en una plataforma **estable, segura y bien documentada**, apta para su confiable uso en redes industriales locales. El API deberá ser capaz de operar continuamente con mínima intervención, facilitando la integración con uno o varios sistemas WMS y proporcionando a usuarios finales y desarrolladores la confianza en que el sistema de carrusel funcionará de forma predecible, visible y mantenible en el tiempo. Cada semana de trabajo va construyendo sobre la anterior para reducir riesgos: primero saneando la base, luego mejorando la comunicación, después documentando y finalmente añadiendo extras valiosos. Con este plan de acción implementado, `carousel_api` quedará robustecido y extendido según las necesidades identificadas, cumpliendo su rol como **conector confiable en entornos industriales locales** para Industrias Pico S.A.S. y sus sistemas asociados.
