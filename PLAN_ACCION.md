# PLAN DE ACCIÓN PARA MEJORAS EN `carousel_api`

## Estado de avance

- [x] **Limpieza de dependencias** (`requirements.txt` optimizado)
- [x] **Mejoras de robustez y unificación en comunicación PLC/simulador**
- [x] **Eliminación de código muerto y métodos obsoletos**
- [x] **Ampliación y corrección de pruebas unitarias e integración para la API**

## Próximos pasos sugeridos

- [ ] **Mejoras de documentación**
  - Revisar y ampliar docstrings en módulos, clases y funciones clave.
  - Actualizar y enriquecer el README.md con ejemplos de uso, despliegue y pruebas.
  - Documentar el flujo de la API y los endpoints principales.

- [ ] **Refuerzo de seguridad y validaciones**
  - Revisar posibles vectores de ataque (inyección, DoS, etc.).
  - Mejorar validaciones de entrada y manejo de errores.
  - Revisar configuración de CORS y exponer solo lo necesario.

- [ ] **Refactorización y optimización**
  - Revisar duplicidades y oportunidades de modularización.
  - Mejorar la separación de responsabilidades entre controladores, modelos y utilidades.
  - Optimizar el rendimiento en operaciones críticas.

- [ ] **Automatización y CI/CD**
  - Añadir scripts de testing y despliegue automatizado.
  - Integrar herramientas de análisis estático y cobertura de código.

---

**Notas:**
- Los puntos completados están marcados con ✓.
- El siguiente paso recomendado es abordar la documentación y luego avanzar con seguridad/refactorización según prioridades del proyecto.
