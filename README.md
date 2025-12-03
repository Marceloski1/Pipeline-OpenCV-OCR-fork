# Modelo OpenCV-OCR - Actor Detection API

Este repositorio contiene un sistema completo para la **detección de actores y casos de uso en diagramas de casos de uso del sistema** y extracción de texto asociado mediante **OCR (EasyOCR)**. El sistema incluye tanto el pipeline de procesamiento de imágenes como una API RESTful construida con FastAPI para generar reportes en PDF con los resultados.

---

## Archivos principales

| Archivo | Descripción |
|---------|-------------|
| `actor_detector.py` | Script principal para la detección de actores y extracción de texto. Implementa todo el pipeline de procesamiento de imágenes, detección de cabezas y OCR. |
| `main.py` | Aplicación FastAPI que expone endpoints REST para procesar imágenes y generar reportes PDF. |
| `pdf_builder.py` | Módulo para la generación de reportes PDF profesionales con los actores detectados. |

---

## Pipeline de Detección de Actores

El script sigue un flujo de trabajo estructurado en varias funciones, con estrategias de procesamiento y detección adaptadas a diagramas de Draw.io:

### 1. Inicialización (`__init__`)

* Carga la imagen desde disco.
* Maneja imágenes con transparencia (canal alfa), rellenando el fondo con blanco si es necesario.
* Obtiene dimensiones de la imagen para calcular las ROIs.

### 2. Preprocesamiento (`preprocess`)

* Convierte la imagen a escala de grises.
* Invierte colores si el fondo es claro para facilitar la detección.
* Aplica un umbral binario para resaltar las figuras de los actores.

### 3. Detección de actores por plantilla (`find_actors_by_template`)

* Genera plantillas de actores (cabeza, cuerpo, brazos) de varios tamaños.
* Aplica **template matching** (`cv2.matchTemplate`) para localizar coincidencias en la imagen.
* Filtra duplicados cercanos para evitar contar el mismo actor varias veces.

### 4. Verificación de cabeza (`verify_head_circle`)

* Define una ROI por encima del actor donde debería encontrarse la cabeza.
* Aplica **HoughCircles** para detectar círculos que representen la cabeza.
* Filtra círculos no alineados geométricamente con la posición del actor.
* Permite ajustar el **ancho y alto de la ROI** para mayor precisión.
* Devuelve la posición de la cabeza si existe.

### 5. Extracción de texto debajo del actor (`extract_text_below`)

* Define una ROI hacia abajo del actor (ancho fijo, altura configurable).
* Utiliza **EasyOCR** para reconocer texto dentro de la ROI.
* Devuelve el texto detectado junto con la posición del ROI.
* Ideal para diagramas de Draw.io donde el texto es legible y bien definido.

### 6. Pipeline principal (`detect_actors`)

* Combina detección por plantilla y verificación de cabeza.
* Genera un listado de actores validados.
* Para cada actor, extrae el texto debajo usando OCR.
* Produce resultados finales y dibuja una imagen de salida con:

  * Actor detectado
  * Cabeza detectada
  * ROI superior e inferior
  * Texto detectado

### 7. Salida y visualización (`draw_results`)

* Dibuja círculos sobre actores y cabezas detectadas.
* Dibuja rectángulos para ROIs superiores e inferiores.
* Inserta etiquetas de texto indicando "HEAD" o "NO HEAD" y el texto detectado debajo.
* Guarda la imagen final como `actors_debug_output.png`.

---

## API REST - FastAPI

### Endpoints Disponibles

| Método | Endpoint | Descripción | Parámetros |
|--------|----------|-------------|------------|
| `GET` | `/` | Información de la API | - |
| `GET` | `/health` | Verificación del estado del servicio | - |
| `POST` | `/detect-actors/` | Procesa imagen y devuelve resultados | `file`: Imagen, `debug`: Boolean, `format`: "pdf" o "json" |
| `POST` | `/detect-actors-simple/` | Versión simplificada solo para PDF | `file`: Imagen |
| `GET` | `/example-actors/` | Genera PDF de ejemplo sin subir imagen | - |

### Características de la API

* **Soporte para múltiples formatos**: PDF embebido o JSON estructurado
* **Manejo de archivos temporales**: Limpieza automática después del procesamiento
* **Modo debug**: Genera imágenes intermedias para diagnóstico
* **Validación de tipos de archivo**: PNG, JPG, JPEG, BMP, TIFF, WEBP
* **Respuestas estructuradas**: JSON con metadatos de procesamiento

### Ejemplo de Uso con cURL

```bash
# Subir imagen y obtener PDF
curl -X POST "http://localhost:8000/detect-actors/" \
  -F "file=@diagrama.png" \
  -F "debug=false" \
  -o reporte_actores.pdf

# Subir imagen y obtener JSON
curl -X POST "http://localhost:8000/detect-actors/?format=json" \
  -F "file=@diagrama.png" \
  -H "accept: application/json"
```

---

## Generación de Reportes PDF

El módulo `pdf_builder.py` genera reportes profesionales que incluyen:

1. **Información del reporte**: Fecha y hora de procesamiento
2. **Resumen ejecutivo**: Conteo total de actores detectados
3. **Tabla de actores**: Lista organizada con ID y nombre
4. **Imagen procesada**: Vista de la imagen con anotaciones (modo debug)
5. **Formato profesional**: Estilos consistentes, colores y branding

### Características del PDF

* **Diseño responsive**: Se adapta al contenido
* **Tablas formateadas**: Con colores alternados para mejor lectura
* **Inclusión de imágenes**: Opcional, muestra la imagen procesada
* **Metadatos**: Información de generación y sistema
* **Múltiples estilos**: Títulos, subtítulos y contenido diferenciados

---

## Instalación y Configuración

### Dependencias de Python

```bash
pip install fastapi[standard] python-multipart reportlab opencv-python numpy easyocr Pillow python-dateutil
```

### Estructura del Proyecto

```
project/
├── main.py              # Aplicación FastAPI
├── actor_detector.py    # Lógica de detección de actores
├── pdf_builder.py       # Generación de PDFs
├── requirements.txt     # Dependencias
├── requirements.txt     # Archivos temporales subidos
```

### Ejecución

```bash
# Ejecutar la aplicación
python main.py

# La API estará disponible en:
# http://localhost:8000
# Documentación Swagger/OpenAPI:
# http://localhost:8000/docs
```

---

## Estrategias y Consideraciones Técnicas

### Robustez en la Detección

* **ROI adaptables**: Permite ajustar alto y ancho para mejorar precisión en distintos diagramas
* **Filtro de duplicados**: Evita detectar múltiples veces el mismo actor en áreas cercanas
* **Verificación geométrica**: Valida que la cabeza esté correctamente posicionada sobre el actor
* **Múltiples escalas**: Template matching con diferentes tamaños de plantilla

### Procesamiento de Imágenes

* **Manejo de transparencia**: Conversión automática de imágenes con canal alfa
* **Umbralización adaptativa**: Inversión automática basada en el brillo promedio
* **Preprocesamiento optimizado**: Operaciones específicas para diagramas Draw.io

### OCR y Extracción de Texto

* **Multi-idioma**: Soporte para español e inglés
* **ROI específica**: Enfoque en la región debajo del actor para reducir falsos positivos
* **Sin GPU requerida**: Configuración optimizada para CPU

### API y Manejo de Errores

* **Validación exhaustiva**: Verificación de tipos de archivo y parámetros
* **Limpieza de recursos**: Eliminación automática de archivos temporales
* **Respuestas informativas**: Mensajes de error claros y útiles
* **Formatos múltiples**: Flexibilidad en el tipo de respuesta

---

## Ejemplo de Salida

### PDF de Reporte

El PDF generado incluye:
- Encabezado con título y fecha
- Tabla con todos los actores detectados
- Imagen anotada (opcional, modo debug)
- Pie de página informativo

### JSON Response

```json
{
  "status": "success",
  "detection_time": "2024-01-15T10:30:45",
  "total_actors": 4,
  "actors": [
    {"actor_id": 1, "name": "Usuario del Sistema"},
    {"actor_id": 2, "name": "Administrador"},
    {"actor_id": 3, "name": "Sistema de Pagos"},
    {"actor_id": 4, "name": "Base de Datos"}
  ],
  "positions": [
    {"x": 150, "y": 200},
    {"x": 450, "y": 200},
    {"x": 150, "y": 400},
    {"x": 450, "y": 400}
  ]
}
```

### Imagen de Debug

Cuando se activa el modo debug, se generan:
1. `actors_debug_output.png` - Imagen completa con anotaciones
2. Archivos ROI individuales por actor
3. Imágenes de círculos detectados

---

## Licencia y Contribuciones

Este proyecto está diseñado para procesamiento académico y profesional de diagramas de casos de uso. Las contribuciones son bienvenidas para mejorar la precisión de detección o añadir nuevas funcionalidades.

---
