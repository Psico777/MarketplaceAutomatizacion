# MarketplaceAutomatizacion

## 🚀 Sistema de Automatización para Facebook Marketplace con Gemini AI

Automatización completa para Facebook Marketplace usando Selenium y Gemini AI. Este sistema permite reconocer productos desde PDFs, analizarlos con inteligencia artificial, y publicarlos automáticamente en Facebook Marketplace con soporte para autenticación 2FA.

## 🌟 Características Principales

- **Extracción de imágenes desde PDF**: Convierte páginas de PDF en imágenes para análisis
- **Análisis con Gemini AI**: Utiliza Google Gemini AI para:
  - Reconocer y describir productos en imágenes
  - Generar títulos atractivos automáticamente
  - Crear descripciones detalladas
  - Sugerir precios basados en el producto
  - Generar tags/etiquetas relevantes
- **Autenticación 2FA**: Soporte completo para autenticación de dos factores de Facebook
- **Automatización con Selenium**: 
  - Crear publicaciones en Marketplace
  - Editar publicaciones existentes
  - Eliminar publicaciones
  - Listar todas tus publicaciones
- **Sin APIs oficiales**: Usa Selenium para evitar necesidad de permisos de API de Facebook

## 📋 Requisitos

- Python 3.8 o superior
- Google Chrome instalado
- Cuenta de Facebook
- API Key de Google Gemini AI

## 🔧 Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/Psico777/MarketplaceAutomatizacion.git
cd MarketplaceAutomatizacion
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura tus credenciales:
   - Copia `.env.example` a `.env`
   - Edita `.env` con tus credenciales:

```env
# Facebook Credentials
FACEBOOK_EMAIL=tu_email@ejemplo.com
FACEBOOK_PASSWORD=tu_contraseña

# 2FA Settings (opcional - para autenticador app)
FACEBOOK_2FA_SECRET=tu_secret_2fa

# Gemini API Key
GEMINI_API_KEY=tu_api_key_de_gemini

# Browser Settings
HEADLESS=False
IMPLICIT_WAIT=10

# AI Model Settings
AI_MODEL_IMAGE=gemini-2.5-flash
AI_MODEL_CHAT=gemini-2.5-pro
MAX_IMAGE_SIZE=2048
```

## 🎯 Uso

### Crear una publicación desde PDF

```bash
python main.py create --pdf producto.pdf --category Electronics --condition New --location "Ciudad, País"
```

### Editar una publicación existente

```bash
python main.py edit --url "https://facebook.com/marketplace/item/123456" --title "Nuevo Título" --price "150"
```

### Eliminar una publicación

```bash
python main.py delete --url "https://facebook.com/marketplace/item/123456"
```

### Listar todas tus publicaciones

```bash
python main.py list
```

## 📚 Estructura del Proyecto

```
MarketplaceAutomatizacion/
├── main.py                          # Script principal
├── requirements.txt                 # Dependencias
├── .env.example                     # Ejemplo de configuración
├── .gitignore                      # Archivos a ignorar
├── README.md                       # Este archivo
└── src/
    ├── config/
    │   └── settings.py             # Configuración
    └── modules/
        ├── pdf_extractor.py        # Extractor de imágenes PDF
        ├── ai_analyzer.py          # Análisis con Gemini AI
        ├── facebook_auth.py        # Autenticación Facebook
        └── marketplace_automation.py # Automatización Marketplace
```

## 🤖 Cómo Funciona

1. **Extracción**: El sistema convierte cada página del PDF en una imagen
2. **Análisis AI**: Gemini AI analiza las imágenes y genera:
   - Título del producto
   - Descripción detallada
   - Precio sugerido
   - Tags relevantes
3. **Autenticación**: Se conecta a Facebook con tus credenciales (con soporte 2FA)
4. **Publicación**: Crea automáticamente la publicación en Marketplace con toda la información

## 🔐 Seguridad y 2FA

### Configurar 2FA con Autenticador

1. Ve a Configuración de Seguridad de Facebook
2. Activa "Autenticación de dos factores"
3. Elige "App de autenticación"
4. Cuando te muestre el código QR, haz clic en "¿No puedes escanear?"
5. Copia el código secreto (será algo como: `JBSWY3DPEHPK3PXP`)
6. Añade este código a tu archivo `.env` como `FACEBOOK_2FA_SECRET`

## 🎨 Modelos de Gemini AI Utilizados

- **gemini-2.5-flash**: Para análisis de imágenes (rápido y eficiente)
- **gemini-2.5-pro**: Para chat y procesamiento avanzado

## ⚠️ Notas Importantes

- **Rate Limits**: Facebook puede detectar actividad automatizada. Usa con moderación.
- **Términos de Servicio**: Asegúrate de cumplir con los términos de servicio de Facebook.
- **Privacidad**: Nunca compartas tu archivo `.env` con credenciales.
- **Headless Mode**: Puedes activar modo sin interfaz gráfica configurando `HEADLESS=True` en `.env`

## 🐛 Solución de Problemas

### Error: "Chrome driver not found"
```bash
# El sistema descargará automáticamente el driver correcto
# Si falla, instala manualmente:
pip install --upgrade webdriver-manager
```

### Error: "Login failed"
- Verifica tus credenciales en `.env`
- Si usas 2FA, asegúrate de tener el código secreto correcto
- Facebook puede requerir verificación por primera vez desde una nueva ubicación

### Error: "Failed to create listing"
- Los selectores de Facebook pueden cambiar. El sistema intenta múltiples estrategias.
- Verifica que las imágenes existan y sean válidas
- Asegúrate de que el navegador tenga suficiente tiempo (aumenta `IMPLICIT_WAIT`)

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Si encuentras algún problema o tienes preguntas, por favor abre un issue en GitHub.

## ⭐ Agradecimientos

- Google Gemini AI por las capacidades de análisis de imágenes
- Selenium por la automatización web
- La comunidad de código abierto

---

**Nota**: Este software es para propósitos educativos. Úsalo responsablemente y respeta los términos de servicio de Facebook.

*Para llegar al éxito debes dar el primer paso y mantenerte en calma hasta que lo logres y cuando lo logres enseñar a que los demas lo puedan lograr, amen.*
