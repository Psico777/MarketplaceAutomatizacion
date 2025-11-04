# Contributing to MarketplaceAutomatizacion

¡Gracias por tu interés en contribuir! 🎉

## 🤝 Cómo Contribuir

### Reportar Bugs

1. Verifica que el bug no esté ya reportado en [Issues](https://github.com/Psico777/MarketplaceAutomatizacion/issues)
2. Abre un nuevo issue con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Sistema operativo y versión de Python
   - Logs de error (si aplica)

### Sugerir Mejoras

- Abre un issue describiendo la mejora
- Explica por qué sería útil
- Si es posible, proporciona ejemplos de uso

### Pull Requests

1. Fork el repositorio
2. Crea una rama para tu feature:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. Haz tus cambios
4. Asegúrate de que el código funciona:
   ```bash
   python -m py_compile main.py src/**/*.py
   ```
5. Commit con mensaje descriptivo:
   ```bash
   git commit -m "Agregar: descripción de la funcionalidad"
   ```
6. Push a tu fork:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
7. Abre un Pull Request

## 📝 Guías de Estilo

### Código Python

- Sigue PEP 8
- Usa docstrings para funciones y clases
- Nombres descriptivos en español cuando sea apropiado
- Comentarios en español

Ejemplo:
```python
def analizar_imagen(self, ruta_imagen):
    """
    Analiza una imagen de producto con IA
    
    Args:
        ruta_imagen (str): Ruta al archivo de imagen
        
    Returns:
        dict: Información del producto extraída
    """
    # Implementación
    pass
```

### Documentación

- Archivos .md en español
- Usa títulos claros y descriptivos
- Incluye ejemplos de código
- Formatea código con ```bash o ```python

## 🧪 Testing

Antes de enviar un PR:

1. Ejecuta el test de sintaxis:
```bash
python -m py_compile main.py src/**/*.py
```

2. Verifica que test_setup.py funcione:
```bash
python test_setup.py
```

3. Prueba tu feature manualmente

## 🎯 Áreas de Contribución

### Prioridad Alta
- [ ] Tests unitarios automatizados
- [ ] Manejo de errores más robusto
- [ ] Optimización de selectores de Selenium
- [ ] Soporte para más categorías de productos

### Prioridad Media
- [ ] Integración con otras plataformas (Mercado Libre, etc)
- [ ] Interfaz gráfica (GUI)
- [ ] Análisis de múltiples páginas de PDF
- [ ] Configuración de prompts personalizados

### Prioridad Baja
- [ ] Traducción a otros idiomas
- [ ] Temas/estilos para documentación
- [ ] Scripts adicionales de automatización

## 🌟 Ideas de Nuevas Features

- **Scheduler**: Programar publicaciones para fechas específicas
- **Analytics**: Dashboard con estadísticas de publicaciones
- **Batch Processing**: Procesamiento masivo optimizado
- **Template System**: Plantillas de descripciones por categoría
- **Price Optimizer**: Sugerir precios basados en mercado
- **Auto-Reply**: Respuestas automáticas a mensajes

## 📋 Checklist para PRs

Antes de enviar tu PR, verifica:

- [ ] El código sigue las guías de estilo
- [ ] Agregaste docstrings a funciones nuevas
- [ ] Actualizaste la documentación si es necesario
- [ ] El código no rompe funcionalidad existente
- [ ] Probaste en tu entorno local
- [ ] El mensaje de commit es descriptivo

## 🔍 Proceso de Revisión

1. El maintainer revisará tu PR
2. Puede sugerir cambios
3. Una vez aprobado, se hará merge
4. Tu contribución aparecerá en la próxima release

## 🎓 Recursos

- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Gemini AI API](https://ai.google.dev/)
- [Python Best Practices](https://docs.python-guide.org/)

## 💬 Comunicación

- **Issues**: Para bugs y features
- **Pull Requests**: Para código
- **Discussions**: Para preguntas generales

## 📜 Código de Conducta

- Sé respetuoso con otros contribuidores
- Acepta críticas constructivas
- Enfócate en lo mejor para el proyecto
- Ayuda a otros cuando puedas

## 🙏 Reconocimientos

Todos los contribuidores serán agregados al README.

## ❓ Preguntas

Si tienes preguntas sobre cómo contribuir:
1. Revisa la documentación existente
2. Busca en issues cerrados
3. Abre un nuevo issue con tu pregunta

---

¡Gracias por hacer este proyecto mejor! 🚀
