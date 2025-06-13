# PLAN DE ACCIÓN PARA MEJORAS EN `carousel_api`

## 1. Mejoras en la comunicación y robustez

- **Implementar reintentos y reconexión automática en la clase PLC**
  - Responsable: Backend
  - Prioridad: Alta
  - Criterio de aceptación: El sistema debe intentar reconectar y reintentar comandos ante fallos de red, con backoff exponencial.

- **Unificar validaciones entre simulador y PLC real**
  - Responsable: Backend
  - Prioridad: Media
  - Criterio de aceptación: Los argumentos y comandos aceptados deben ser consistentes en ambos modos.

## 2. Refactorización y eliminación de código muerto

- **Eliminar o refactorizar métodos no implementados o no usados**
  - Responsable: Backend
  - Prioridad: Media
  - Criterio de aceptación: No debe haber métodos huérfanos ni archivos sin uso en el repositorio.

- **Revisar y limpiar el archivo requirements.txt**
  - Responsable: Backend
  - Prioridad: Media
  - Criterio de aceptación: Solo deben estar las dependencias necesarias y actualizadas.

## 3. Pruebas y cobertura

- **Ampliar la cobertura de pruebas unitarias y de integración**
  - Responsable: QA/Backend
  - Prioridad: Alta
  - Criterio de aceptación: Cobertura mínima del 80% en lógica de negocio y API; incluir pruebas de integración y simulación de fallos de red.

- **Añadir pruebas para la API y la GUI**
  - Responsable: QA/Backend
  - Prioridad: Media
  - Criterio de aceptación: Deben existir tests automatizados para endpoints y flujos principales de la interfaz gráfica.

## 4. Seguridad y configuración

- **Migrar configuración sensible a variables de entorno**
  - Responsable: DevOps/Backend
  - Prioridad: Alta
  - Criterio de aceptación: No debe haber IPs ni credenciales en archivos de texto plano.

- **Validar la configuración al inicio de la aplicación**
  - Responsable: Backend
  - Prioridad: Media
  - Criterio de aceptación: La app debe rechazar configuraciones inválidas y mostrar mensajes claros.

## 5. Logging y monitoreo

- **Implementar logging estructurado y centralizado**
  - Responsable: Backend/DevOps
  - Prioridad: Media
  - Criterio de aceptación: Todos los errores y eventos relevantes deben quedar registrados en archivos o sistemas de monitoreo.

## 6. Documentación y despliegue

- **Actualizar y mejorar la documentación**
  - Responsable: Todos
  - Prioridad: Media
  - Criterio de aceptación: La documentación debe reflejar la estructura real del proyecto y buenas prácticas de despliegue seguro.

- **Añadir ejemplos de uso de variables de entorno y despliegue en producción**
  - Responsable: Backend/DevOps
  - Prioridad: Media
  - Criterio de aceptación: Debe existir un `.env.example` y una sección clara en el README.

## 7. Experiencia de usuario

- **Mejorar los mensajes de error y feedback en la GUI**
  - Responsable: Frontend
  - Prioridad: Media
  - Criterio de aceptación: El usuario debe recibir mensajes claros y útiles ante fallos de conexión o errores del sistema.

---

**Nota:** Se recomienda revisar este plan en reuniones de equipo y asignar responsables formales para cada tarea.
