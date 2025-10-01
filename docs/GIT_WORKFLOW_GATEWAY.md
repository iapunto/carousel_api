# 🌿 Manual de Flujo de Trabajo GIT para Gateway Local

## 📋 Resumen Ejecutivo

Este documento establece el flujo de trabajo GIT para el desarrollo del Gateway Local, manteniendo compatibilidad con los sistemas en uso actual y siguiendo prácticas modernas de DevOps. El enfoque garantiza un desarrollo estructurado, versionado y testeado, alineado con la evolución hacia una arquitectura de microservicios.

## 🎯 Objetivos del Flujo de Trabajo

- Mantener compatibilidad con sistemas en producción
- Facilitar el desarrollo paralelo sin romper funcionalidades existentes
- Implementar control de versiones semántico
- Garantizar calidad mediante integración continua
- Facilitar despliegues seguros y reversibles

## 🏗️ Estructura del Repositorio

```
carousel_api/
├── docs/
│   ├── PRDs/
│   │   ├── WMS/           # PRDs del sistema WMS
│   │   └── GATEWAY/       # PRDs del Gateway Local
│   └── GIT_WORKFLOW_GATEWAY.md  # Este documento
├── gateway/               # Nuevo directorio para Gateway Local
│   ├── src/               # Código fuente del Gateway
│   ├── tests/             # Pruebas unitarias e integración
│   ├── docs/              # Documentación técnica del Gateway
│   ├── requirements.txt   # Dependencias de Python
│   └── README.md          # Instrucciones del Gateway
├── carousel/              # Código existente del Carousel API
│   ├── api.py
│   ├── plc_manager.py
│   └── ...                # Componentes existentes
└── shared/                # Librerías compartidas
    ├── protocols/         # Protocolos de comunicación
    ├── security/          # Componentes de seguridad
    └── utils/             # Utilidades comunes
```

## 🔧 Ramas del Repositorio

### Rama Principal

- **main**: Código en producción, estable y testeado
- **Solo se actualiza mediante merges de release branches**
- **Protegida - requiere pull request y aprobación**

### Ramas de Desarrollo

- **develop**: Integración de nuevas funcionalidades
- **Rama base para feature branches**
- **Actualizada continuamente con main**

### Ramas Temporales

- **feature/xxx**: Desarrollo de nuevas funcionalidades
- **release/xxx**: Preparación de nuevos releases
- **hotfix/xxx**: Corrección de errores críticos en producción

## 🔄 Flujo de Trabajo Detallado

### 1. Desarrollo de Nuevas Funcionalidades

#### 1.1 Crear Feature Branch

```bash
# Sincronizar con el repositorio remoto
git checkout develop
git pull origin develop

# Crear branch para la nueva funcionalidad
git checkout -b feature/gateway-comunicacion-wms
```

#### 1.2 Desarrollo e Implementación

- Seguir los PRDs definidos en [docs/PRDs/GATEWAY/](file:///C:/laragon/www/carousel_api/docs/PRDs/GATEWAY/)
- Implementar en Python manteniendo compatibilidad con Tkinter
- Escribir pruebas unitarias para nueva funcionalidad
- Documentar código y cambios

#### 1.3 Commit y Push

```bash
# Commits atómicos y descriptivos
git add .
git commit -m "feat(gateway): implementar módulo de comunicación con WMS"
git push origin feature/gateway-comunicacion-wms
```

#### 1.4 Pull Request

- Crear PR hacia develop
- Asignar revisores del equipo
- Esperar aprobación y pasar pruebas automáticas
- Hacer merge una vez aprobado

### 2. Preparación de Releases

#### 2.1 Crear Release Branch

```bash
# Desde develop, crear branch de release
git checkout develop
git pull origin develop
git checkout -b release/v2.7.0
```

#### 2.2 Preparación del Release

- Actualizar números de versión
- Actualizar CHANGELOG.md
- Realizar pruebas finales
- Preparar documentación del release

#### 2.3 Merge a Main

```bash
# Merge a main
git checkout main
git pull origin main
git merge release/v2.7.0

# Crear tag del release
git tag -a v2.7.0 -m "Release v2.7.0 - Gateway Local Inicial"

# Push a main y tags
git push origin main
git push origin --tags

# Merge de vuelta a develop
git checkout develop
git merge release/v2.7.0
git push origin develop

# Eliminar branch de release
git branch -d release/v2.7.0
```

### 3. Hotfixes para Producción

#### 3.1 Crear Hotfix Branch

```bash
# Desde main, crear branch de hotfix
git checkout main
git pull origin main
git checkout -b hotfix/corregir-fallo-conexion
```

#### 3.2 Implementar Corrección

- Implementar fix mínimo necesario
- Escribir pruebas para prevenir regresión
- Actualizar versión (patch increment)

#### 3.3 Merge y Deploy

```bash
# Merge a main
git checkout main
git pull origin main
git merge hotfix/corregir-fallo-conexion

# Crear tag
git tag -a v2.6.1 -m "Hotfix v2.6.1 - Corrección de fallo de conexión"

# Push a main y tags
git push origin main
git push origin --tags

# Merge a develop
git checkout develop
git merge hotfix/corregir-fallo-conexion
git push origin develop

# Eliminar branch de hotfix
git branch -d hotfix/corregir-fallo-conexion
```

## 📊 Convenciones de Commits

### Tipos de Commits

- **feat**: Nueva funcionalidad
- **fix**: Corrección de errores
- **chore**: Tareas de mantenimiento
- **docs**: Cambios en documentación
- **style**: Cambios de formato (sin afectar código)
- **refactor**: Refactorización de código
- **test**: Adición o modificación de pruebas
- **perf**: Mejoras de performance
- **ci**: Cambios en integración continua
- **build**: Cambios en sistema de build

### Ejemplos

```bash
git commit -m "feat(gateway): implementar autenticación con WMS"
git commit -m "fix(gateway): corregir timeout en conexión PLC"
git commit -m "docs(gateway): actualizar documentación de API"
git commit -m "test(gateway): añadir pruebas para módulo de seguridad"
```

## 🔒 Protección de Ramas

### Rama Main

- Protegida contra pushes directos
- Requiere pull request para cambios
- Requiere revisión de al menos 1 aprobador
- Requiere paso de todas las pruebas automáticas
- Requiere actualización de CHANGELOG.md

### Rama Develop

- Protegida contra pushes directos a ciertos archivos
- Requiere pull request para cambios significativos
- Requiere pruebas unitarias para nueva funcionalidad
- Permite commits más frecuentes que main

## 🧪 Integración Continua

### Pipeline de CI

1. **Linting**: Verificación de estilo de código
2. **Pruebas Unitarias**: Ejecución de tests unitarios
3. **Pruebas de Integración**: Tests de integración entre módulos
4. **Análisis de Seguridad**: Escaneo de vulnerabilidades
5. **Build**: Construcción del paquete
6. **Pruebas de Regresión**: Verificación de funcionalidades existentes

### Configuración de GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r gateway/requirements.txt
      - name: Run linting
        run: |
          # Comandos de linting
      - name: Run tests
        run: |
          # Comandos de pruebas
```

## 📦 Versionado Semántico

### Formato de Versiones

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Cambios incompatibles en API
- **MINOR**: Nuevas funcionalidades retrocompatibles
- **PATCH**: Correcciones de errores retrocompatibles

### Ejemplos de Versiones

- **v2.7.0**: Nueva versión mayor con Gateway Local
- **v2.7.1**: Corrección de errores en v2.7.0
- **v2.8.0**: Nuevas funcionalidades en Gateway

## 📝 Documentación de Releases

### CHANGELOG.md

```markdown
# Changelog

## [v2.7.0] - 2024-01-15

### Added

- Implementación inicial del Gateway Local
- Módulo de comunicación con WMS
- Módulo de comunicación con PLCs
- Sistema de autenticación y seguridad

### Changed

- Refactorización de Carousel API para modo Gateway
- Actualización de documentación técnica

### Fixed

- Corrección de timeouts en conexiones PLC
```

## 🛡️ Compatibilidad con Sistemas Existentes

### Estrategias de Compatibilidad

1. **API Compatibles**: Mantener endpoints existentes
2. **Configuración Dual**: Soportar modos legacy y nuevo
3. **Migración Gradual**: Permitir transición progresiva
4. **Documentación Clara**: Guías de migración para usuarios

### Pruebas de Retrocompatibilidad

- Verificar funcionamiento de Carousel API existente
- Probar integraciones con sistemas externos
- Validar formatos de datos existentes
- Confirmar performance equivalente o mejorada

## 🚀 Despliegue y Rollback

### Estrategia de Despliegue

1. **Despliegue en Staging**: Validación en ambiente de prueba
2. **Despliegue Canario**: Rollout progresivo a subset de usuarios
3. **Despliegue Completo**: Release a todos los usuarios
4. **Monitoreo Post-Deploy**: Verificación continua de salud

### Plan de Rollback

1. **Detección de Problemas**: Monitoreo de métricas y alertas
2. **Decisión de Rollback**: Evaluación de impacto
3. **Ejecución de Rollback**: Reversión a versión anterior
4. **Análisis Post-Mortem**: Documentación de incidente

## 📊 Métricas de Seguimiento

### Métricas de Desarrollo

- **Tiempo de Ciclo**: Desde feature branch hasta producción
- **Tasa de Éxito de Builds**: Porcentaje de builds exitosos
- **Tiempo Medio de Revisión**: Tiempo promedio de PR reviews
- **Cobertura de Pruebas**: Porcentaje de código cubierto por tests

### Métricas de Producción

- **Tiempo de Actividad**: Uptime del sistema
- **Tiempo de Respuesta**: Latencia de operaciones
- **Tasa de Errores**: Número de errores por período
- **Satisfacción del Usuario**: Métricas de experiencia

## 📋 Proceso de Revisión de Código

### Checklist de Pull Request

- [ ] Código sigue estándares de estilo
- [ ] Pruebas unitarias incluidas y pasan
- [ ] Documentación actualizada
- [ ] No hay breaking changes sin justificación
- [ ] Código revisado por al menos 1 compañero
- [ ] Todas las pruebas automáticas pasan

### Roles en Revisión

- **Autor**: Desarrollador que crea el PR
- **Revisor**: Desarrollador que revisa el código
- **Aprobador**: Desarrollador con permisos para merge
- **Observador**: Stakeholders interesados en el cambio

## 🎓 Buenas Prácticas

### Desarrollo

1. **Commits Atómicos**: Cada commit debe representar un cambio lógico completo
2. **Mensajes Claros**: Usar convenciones de commits establecidas
3. **Pruebas Continuas**: Escribir tests junto con el código
4. **Documentación Paralela**: Actualizar docs mientras se desarrolla

### Colaboración

1. **Comunicación Proactiva**: Notificar bloqueadores temprano
2. **Respeto a Procesos**: Seguir el flujo de trabajo establecido
3. **Feedback Constructivo**: Proveer comentarios útiles en revisiones
4. **Aprendizaje Continuo**: Compartir conocimientos y mejores prácticas

## 📞 Contacto y Soporte

### Equipos Responsables

- **Líder Técnico**: [Nombre del líder técnico]
- **Equipo de Desarrollo**: [Lista de desarrolladores]
- **Equipo de QA**: [Lista de testers]
- **Equipo de Operaciones**: [Lista de operaciones]

### Canales de Comunicación

- **Slack**: Canal #gateway-development
- **Email**: gateway-team@empresa.com
- **Reuniones**: Weekly sync los lunes 10:00 AM

## 📅 Actualizaciones del Documento

### Historial de Versiones

- **v1.0.0** (2024-01-15): Versión inicial del flujo de trabajo
- **v1.1.0** (2024-01-20): Adición de estrategias de compatibilidad

### Próximas Actualizaciones

- Incorporación de métricas específicas del equipo
- Adición de templates de PR y issues
- Inclusión de guías de troubleshooting
