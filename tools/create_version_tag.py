#!/usr/bin/env python3
"""
Script para crear tags de versión automatizados en Git

Proyecto: Sistema de Control de Carrusel Industrial
Cliente: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas

Creado: 2025-06-24
Última modificación: 2025-06-24

Uso:
    python tools/create_version_tag.py

Este script:
1. Lee la versión actual de __version__.py
2. Crea un tag de Git con esa versión
3. Muestra información sobre el tag creado
"""

import os
import sys
import subprocess
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from __version__ import __version__, PROJECT_DESCRIPTION, VERSION_HISTORY
except ImportError:
    print("❌ Error: No se pudo importar información de versión.")
    print("   Asegúrate de que el archivo __version__.py existe en el directorio raíz.")
    sys.exit(1)


def run_git_command(command):
    """Ejecuta un comando de git y retorna el resultado."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando comando git: {command}")
        print(f"   Error: {e.stderr}")
        return None


def check_git_status():
    """Verifica el estado del repositorio Git."""
    status = run_git_command("git status --porcelain")
    if status is None:
        return False

    if status:
        print("⚠️  Advertencia: Hay cambios sin commitear:")
        print(status)
        response = input("¿Deseas continuar? (y/N): ")
        return response.lower() in ['y', 'yes', 'sí', 'si']

    return True


def tag_exists(tag_name):
    """Verifica si un tag ya existe."""
    result = run_git_command(f"git tag -l {tag_name}")
    return result is not None and result.strip() == tag_name


def create_version_tag():
    """Crea el tag de versión."""
    print(f"🏷️  Creando tag de versión para {PROJECT_DESCRIPTION}")
    print(f"📋 Versión actual: {__version__}")
    print(
        f"📝 Descripción: {VERSION_HISTORY.get(__version__, 'Nueva versión')}")
    print()

    # Verificar estado de Git
    if not check_git_status():
        print("❌ Operación cancelada.")
        return False

    tag_name = f"v{__version__}"

    # Verificar si el tag ya existe
    if tag_exists(tag_name):
        print(f"⚠️  El tag {tag_name} ya existe.")
        response = input("¿Deseas sobrescribirlo? (y/N): ")
        if response.lower() not in ['y', 'yes', 'sí', 'si']:
            print("❌ Operación cancelada.")
            return False

        # Eliminar tag existente
        run_git_command(f"git tag -d {tag_name}")
        print(f"🗑️  Tag {tag_name} eliminado localmente.")

    # Crear mensaje del tag
    tag_message = f"""Versión {__version__} - {VERSION_HISTORY.get(__version__, 'Nueva versión')}

{PROJECT_DESCRIPTION}

Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Rama: {run_git_command('git branch --show-current') or 'unknown'}
Commit: {run_git_command('git rev-parse HEAD')[:8] or 'unknown'}
"""

    # Crear el tag
    command = f'git tag -a {tag_name} -m "{tag_message}"'
    result = run_git_command(command)

    if result is not None:
        print(f"✅ Tag {tag_name} creado exitosamente!")
        print()
        print("📋 Información del tag:")
        tag_info = run_git_command(
            f"git show {tag_name} --no-patch --format='%ai %h %s'")
        if tag_info:
            print(f"   {tag_info}")
        print()

        # Mostrar instrucciones para push
        print("📤 Para subir el tag al repositorio remoto, ejecuta:")
        print(f"   git push origin {tag_name}")
        print()
        print("📤 Para subir todos los tags:")
        print("   git push --tags")

        return True
    else:
        print(f"❌ Error creando el tag {tag_name}")
        return False


def main():
    """Función principal."""
    print("=" * 60)
    print("🏷️  CREADOR DE TAGS DE VERSIÓN - Carousel API")
    print("=" * 60)
    print()

    success = create_version_tag()

    print()
    print("=" * 60)
    if success:
        print("✅ Proceso completado exitosamente!")
    else:
        print("❌ Proceso terminado con errores.")
    print("=" * 60)


if __name__ == "__main__":
    main()
