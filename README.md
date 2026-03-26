# mIArmario – Asistente de moda personal

## Descripción General

**mIArmario** es un sistema inteligente que actúa como un asistente personal de moda, capaz de organizar un armario digital y generar recomendaciones de outfits junto con visualizaciones tipo lookbook.

El proyecto integra múltiples tecnologías de inteligencia artificial, incluyendo procesamiento de voz, visión por computador, razonamiento con modelos de lenguaje y generación de imágenes, todo dentro de una arquitectura modular.

---

## Características Principales

* Entrada multimodal: voz y texto
* Identificación automática de prendas a partir de imágenes
* Generación de recomendaciones inteligentes de outfits
* Enriquecimiento con búsquedas web
* Creación de lookbooks visuales (JPG y HTML)
* Panel de análisis con datos del armario

---

## Arquitectura del Sistema

El sistema se divide en cuatro módulos principales:

### Módulo 1 — Entrada

* Entrada por voz o texto
* Conversión de voz a texto mediante Whisper
* Salida en formato estructurado (JSON)

### Módulo 2 — Identificación

* Procesamiento de imágenes de ropa del usuario
* Uso de modelo Qwen2-VL-2B-Instruct para:

  * Detectar prendas
  * Extraer atributos (tipo, color, estilo, etc.)
* Generación de base de datos del armario (armario.json)

### Módulo 3 — Inteligencia y Búsqueda

* Razonamiento con modelo Gemini
* Integración de:

  * SerpAPI
  * Google Search API
* Generación de sugerencias de outfits contextualizadas

### Módulo 4 — Visualización

* Eliminación de fondo con rembg
* Generación de descripciones con IA
* Composición de imágenes usando Pillow / ImageDraw
* Salidas:

  * Lookbook en JPG (collage)
  * Lookbook en HTML (con enlaces/base64)

---

## Estructura del Proyecto

```
mIArmario/
│
├── Modulo1.py
├── Modulo2.py
├── Modulo3.py
├── Modulo4.py
├── main.ipynb
├── armario.json
│
├── lookbooks/
├── CARPETA SALIDA/
├── ARMARIO/
│
├── stylist_app.html
├── flask_server.py
│
├── mi_audio.wav
├── mi_audio.mp4
│
└── README.md
```

---

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/tu-usuario/mIArmario.git
cd mIArmario
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

3. Configura las variables de entorno necesarias:

* API Keys (Gemini, SerpAPI, etc.)

---

## Uso

### Ejecución por módulos

```bash
python Modulo1.py
python Modulo2.py
python Modulo3.py
python Modulo4.py
```

### Ejecución completa

```bash
python main.py
```

### Interfaz web

```bash
python flask_server.py
```

Luego abre en el navegador:

```
http://localhost:5000
```

---

## Tecnologías Utilizadas

* Whisper (Speech-to-Text)
* Qwen2-VL-2B-Instruct (visión multimodal)
* Gemini (modelo de lenguaje)
* SerpAPI / Google Search API
* rembg (eliminación de fondo)
* Pillow / ImageDraw (procesamiento de imágenes)
* Flask (backend web)

---

## Posibles Mejoras

* Sistema de recomendaciones basado en preferencias del usuario
* Integración con tiendas online
* Aplicación móvil
* Mejora del sistema de ranking de outfits
* Try-on realista.

---

## Licencia

Todos los derechos reservados.  
No se permite el uso, copia, modificación o distribución de este software sin autorización expresa del autor.
---

## Autor

Proyecto desarrollado como parte de un trabajo académico en la Universitat de València por María de los Ángeles Díaz Castro y Álvaro Nieva Valenzuela.
