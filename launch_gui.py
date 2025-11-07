"""
Script optimizado para lanzar la interfaz gráfica
Con timeouts mínimos y máxima velocidad
"""
import subprocess
import sys
import os

# Agregar directorio al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Verificar dependencias
try:
    import tkinter
    from PIL import Image
    print("✓ Todas las dependencias instaladas")
except ImportError as e:
    print(f"✗ Falta dependencia: {e}")
    print("\nInstalando Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])

# Lanzar GUI
print("\n" + "="*60)
print("🚀 LANZANDO INTERFAZ GRÁFICA")
print("="*60)
print("\n📋 Características:")
print("  ✓ Vista previa de imágenes extraídas")
print("  ✓ Selección individual de productos")
print("  ✓ Caché de análisis IA (más rápido)")
print("  ✓ Progreso en tiempo real")
print("  ✓ Timeouts optimizados (0.1-0.2s)")
print("\n")

from marketplace_gui import main
main()
