import os
import io
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from rembg import remove


# ──────────────────────────────────────────────
#  Utilidades de imagen
# ──────────────────────────────────────────────

def cargar_imagen(path):
    """Carga imagen desde archivo local o URL."""
    if path.startswith("http"):
        r = requests.get(path)
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    return Image.open(path).convert("RGB")


def quitar_fondo_blanco(img):
    """Elimina el fondo de una imagen y lo reemplaza por blanco."""
    img_sin_fondo = remove(img)
    fondo_blanco = Image.new("RGB", img_sin_fondo.size, (255, 255, 255))
    fondo_blanco.paste(img_sin_fondo, mask=img_sin_fondo.split()[3])
    return fondo_blanco


def _cargar_fuentes():
    """Carga fuentes DejaVu si están disponibles, si no usa la fuente por defecto."""
    try:
        fuente        = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      14)
        fuente_titulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        fuente_link   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      12)
    except Exception:
        fuente        = ImageFont.load_default()
        fuente_titulo = fuente
        fuente_link   = fuente
    return fuente, fuente_titulo, fuente_link


# ──────────────────────────────────────────────
#  Descripción del outfit con Gemini
# ──────────────────────────────────────────────

def llamar_gemini(prompt, reintentos=3, model=None):
    for intento in range(reintentos):
        try:
            respuesta = model.generate_content(prompt)
            return respuesta.text
        except Exception as e:
            if "429" in str(e):
                espera = 35 * (intento + 1)
                print(f"Límite alcanzado, esperando {espera}s...")
                time.sleep(espera)
            else:
                raise e
    raise Exception("Se agotaron los reintentos de Gemini")


def describir_outfit(lista_prendas, estilo_ocasion, model=None):
    """Genera una descripción corta del outfit usando Gemini."""
    nombres_prendas = [
        f"{p.get('tipo', '')} {p.get('color', '')} ({p.get('formalidad', '')})"
        for p in lista_prendas
    ]
    lista_texto = "\n".join(f"- {n}" for n in nombres_prendas)

    prompt = f"""Eres un estilista de moda. Describe en máximo 15 palabras el ESTILO y AMBIENTE de este outfit.
Prendas: {lista_texto}
Ocasión: {estilo_ocasion}
IMPORTANTE: Empieza directamente describiendo el estilo. NO uses "Sí", "No", "Este outfit", "Es apropiado".
Ejemplo correcto: "Elegancia casual con toque profesional, ideal para brillar en la velada."
Solo la frase descriptiva."""

    descripcion = llamar_gemini(prompt, model=model).strip()
    print(f"\n📝 Descripción:\n{descripcion}")
    return descripcion


# ──────────────────────────────────────────────
#  Generación de la imagen del outfit
# ──────────────────────────────────────────────

def generar_outfit_vertical(lista_prendas, ocasion, descripcion="", referencias=None, ruta_salida="/content/outfit_temp.jpg"):
    """
    Genera una imagen vertical con las prendas del outfit apiladas
    y un apartado de enlaces a tiendas al final.

    Args:
        lista_prendas (list[dict]): Prendas con 'tipo', 'color', 'imagen_path'.
        ocasion       (str)       : Texto de la ocasión para el encabezado.
        descripcion   (str)       : Frase descriptiva generada por Gemini.
        referencias   (list[dict]): Referencias de tiendas con 'prenda', 'tienda', 'enlace'.
        ruta_salida   (str)       : Ruta donde se guardará la imagen resultante.

    Returns:
        str: Ruta de la imagen guardada.
    """
    referencias = referencias or []
    fuente, fuente_titulo, fuente_link = _cargar_fuentes()

    ANCHO        = 600
    ALTO_PRENDA  = 400
    PADDING      = 30
    COLOR_FONDO  = (255, 255, 255)
    COLOR_LINEA  = (235, 235, 235)
    COLOR_GRIS   = (150, 150, 150)
    COLOR_ACENTO = (30, 30, 30)
    COLOR_LINK   = (60, 100, 200)

    alto_referencias = (60 + len(referencias) * 30) if referencias else 0
    alto_total = (ALTO_PRENDA + PADDING) * len(lista_prendas) + 250 + alto_referencias

    canvas = Image.new("RGB", (ANCHO, alto_total), COLOR_FONDO)
    draw   = ImageDraw.Draw(canvas)

    # ── Encabezado ──────────────────────────────
    draw.text((ANCHO // 2, 38), "OUTFIT COMPLETO",
              fill=COLOR_ACENTO, anchor="mm", font=fuente_titulo)
    draw.text((ANCHO // 2, 62), f"PARA: {ocasion.upper()}",
              fill=COLOR_GRIS, anchor="mm", font=fuente)
    draw.line([(PADDING * 2, 80), (ANCHO - PADDING * 2, 80)],
              fill=COLOR_LINEA, width=1)

    y_actual = 100

    # ── Prendas ──────────────────────────────────
    for i, prenda in enumerate(lista_prendas):
        y_celda = y_actual

        if i > 0:
            draw.line(
                [(PADDING * 3, y_celda - PADDING // 2), (ANCHO - PADDING * 3, y_celda - PADDING // 2)],
                fill=COLOR_LINEA, width=1
            )

        try:
            ruta = prenda.get("imagen_path")
            if not ruta:
                raise ValueError("Sin imagen")

            img_prenda = cargar_imagen(ruta)
            img_prenda = quitar_fondo_blanco(img_prenda)

            max_w = ANCHO - PADDING * 2
            max_h = ALTO_PRENDA - 50
            ratio = min(max_w / img_prenda.width, max_h / img_prenda.height)
            pw    = int(img_prenda.width  * ratio)
            ph    = int(img_prenda.height * ratio)
            img_prenda = img_prenda.resize((pw, ph), Image.LANCZOS)

            px = (ANCHO - pw) // 2
            py = y_celda + (max_h - ph) // 2
            canvas.paste(img_prenda, (px, py))

        except Exception as e:
            draw.text((ANCHO // 2, y_celda + ALTO_PRENDA // 2),
                      f"[{prenda.get('tipo', 'prenda')}]",
                      fill=COLOR_GRIS, anchor="mm", font=fuente)
            print(f"⚠️  Error con {prenda.get('imagen_path')}: {e}")

        etiqueta = f"{prenda.get('tipo', '').upper()}  ·  {prenda.get('color', '').upper()}"
        draw.text((ANCHO // 2, y_celda + ALTO_PRENDA - 25),
                  etiqueta, fill=COLOR_GRIS, anchor="mm", font=fuente)

        y_actual += ALTO_PRENDA + PADDING

    # ── Descripción ──────────────────────────────
    if descripcion:
        draw.line([(PADDING * 2, y_actual), (ANCHO - PADDING * 2, y_actual)],
                  fill=COLOR_LINEA, width=1)
        palabras     = descripcion.split()
        lineas       = []
        linea_actual = ""
        for palabra in palabras:
            if len(linea_actual) + len(palabra) + 1 <= 70:
                linea_actual += (" " if linea_actual else "") + palabra
            else:
                lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)

        y_texto = y_actual + 20
        for linea in lineas[:6]:
            draw.text((ANCHO // 2, y_texto), linea,
                      fill=COLOR_GRIS, anchor="mm", font=fuente)
            y_texto += 22
        y_actual = y_texto + 10

    # ── Apartado de enlaces a tiendas ────────────
    if referencias:
        draw.line([(PADDING * 2, y_actual + 10), (ANCHO - PADDING * 2, y_actual + 10)],
                  fill=COLOR_LINEA, width=1)
        draw.text((PADDING * 2, y_actual + 22),
                  "Enlaces a productos que podrian interesarte:",
                  fill=COLOR_ACENTO, font=fuente_titulo)

        y_links = y_actual + 50
        for ref in referencias:
            tienda = ref.get("tienda", "Tienda").upper()
            prenda = ref.get("prenda", "")
            texto_link = f"• {tienda} — {prenda}"
            if len(texto_link) > 65:
                texto_link = texto_link[:62] + "..."
            draw.text((PADDING * 2, y_links), texto_link,
                      fill=COLOR_LINK, font=fuente_link)
            y_links += 28

    canvas.save(ruta_salida, quality=95)
    return ruta_salida


def generar_lookbook(lista_outfits, ocasion, referencias=None, carpeta_salida="/content", model=None):
    """
    Genera un lookbook combinando uno o varios outfits en una imagen horizontal.

    Args:
        lista_outfits  (list[list[dict]]): Lista de outfits.
        ocasion        (str)             : Descripción de la ocasión.
        referencias    (list[dict])      : Referencias de tiendas a mostrar al pie.
        carpeta_salida (str)             : Carpeta de salida.
        model                            : Instancia de GenerativeModel de Gemini.

    Returns:
        str: Ruta del lookbook final.
    """
    referencias = referencias or []
    imagenes = []
    for i, outfit in enumerate(lista_outfits):
        descripcion = describir_outfit(outfit, ocasion, model=model)
        ruta_temp   = os.path.join(carpeta_salida, f"outfit_{i + 1}.jpg")
        generar_outfit_vertical(
            outfit, ocasion, descripcion,
            referencias = referencias,
            ruta_salida = ruta_temp,
        )
        imagenes.append(Image.open(ruta_temp))

    ancho_total = sum(img.width  for img in imagenes)
    alto_total  = max(img.height for img in imagenes)

    lookbook = Image.new("RGB", (ancho_total, alto_total), (255, 255, 255))
    x = 0
    for img in imagenes:
        lookbook.paste(img, (x, 0))
        x += img.width

    ruta_lookbook = os.path.join(carpeta_salida, "lookbook_final.jpg")
    lookbook.save(ruta_lookbook, quality=95)
    print(f"[Módulo 4] Lookbook guardado en: {ruta_lookbook}")
    return ruta_lookbook


# ──────────────────────────────────────────────
#  Punto de entrada principal
# ──────────────────────────────────────────────

def modulo4_generar_imagen(resultado_mod3, armario, carpeta_salida="/content", model=None):
    """
    Punto de entrada del Módulo 4.

    Args:
        resultado_mod3 (dict)      : JSON de salida del Módulo 3.
        armario        (list[dict]): Lista de prendas del armario (Módulo 2).
        carpeta_salida (str)       : Carpeta donde se guarda el lookbook.
        model                      : Instancia de GenerativeModel de Gemini.

    Returns:
        str: Ruta del lookbook final.
    """
    ids_armario    = {p["id"]: p for p in armario}
    prendas_outfit = []

    for prenda in resultado_mod3["outfit"]["prendas"]:
        if prenda["id"] in ids_armario:
            prendas_outfit.append(ids_armario[prenda["id"]])
        else:
            print(f"⚠️  '{prenda['id']}' no está en el armario, se omite.")

    referencias = resultado_mod3.get("referencias_tiendas", [])

    # Imprimir enlaces en consola
    if referencias:
        print("\n🛍  Enlaces a productos que podrían interesarte:")
        for ref in referencias:
            print(f"   • {ref.get('tienda', '').upper()} — {ref.get('prenda', '')}")
            print(f"     {ref.get('enlace', '')}")

    ocasion       = resultado_mod3["outfit"]["ocasion"]
    ruta_lookbook = generar_lookbook(
        lista_outfits  = [prendas_outfit],
        ocasion        = ocasion,
        referencias    = referencias,
        carpeta_salida = carpeta_salida,
        model          = model,
    )
    return ruta_lookbook
