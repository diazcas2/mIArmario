import requests

def transcribir_voz(ruta_audio):

    resultado = whisper(ruta_audio)
    return resultado["text"].strip()


def llamar_gemini(prompt, reintentos=3,model=None):

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


def normalizar_texto(texto_crudo,model=None):

    prompt = f"""
      Eres el preprocesador de un asistente de moda personal.
      Recibirás una frase del usuario describiendo qué outfit quiere.
      Tu tarea es:
      1. Corregir errores ortográficos o de transcripción de voz.
      2. Eliminar muletillas, ruidos o palabras sin sentido.
      3. Reformular la frase de forma clara y concisa, manteniendo la intención original.
      4. NO añadas información que el usuario no haya dado.

      Responde ÚNICAMENTE con la frase normalizada, sin explicaciones ni texto extra.

      Frase original: {texto_crudo}
      """
    return llamar_gemini(prompt,model=model).strip()


def detectar_idioma(texto):

    try:
        from langdetect import detect
        return detect(texto)
    except Exception:
        return "es"
    

def modulo1_entrada(fuente, texto=None, ruta_audio=None, ciudad=None, model=None):
    """
    Punto de entrada del Módulo 1.

    Acepta texto directo o audio, normaliza el input con Gemini T2T,
    obtiene la temperatura actual de la ciudad y devuelve el JSON
    estandarizado para el Módulo 3.

    Args:
        fuente (str)     : 'texto' | 'voz'
        texto (str)      : Texto escrito por el usuario  (si fuente='texto')
        ruta_audio (str) : Ruta al archivo de audio      (si fuente='voz')
        ciudad (str)     : Ciudad para obtener temperatura (ej: 'Sevilla')

    Returns:
        dict: JSON contrato Módulo 1 → Módulo 3:
              {
                  "texto"    : str,
                  "fuente"   : str,
                  "idioma"   : str,
                  "contexto" : {
                      "ciudad"      : str,
                      "temperatura" : float,
                      "unidad"      : 'celsius'
                  }
              }
    """

    # Paso 1: Obtener texto crudo según la fuente
    if fuente == "voz":
        texto_crudo = transcribir_voz(ruta_audio)

    elif fuente == "texto":
        texto_crudo = texto.strip()

    else:
        raise ValueError(f"'fuente' debe ser 'texto' o 'voz', recibido: '{fuente}'")

    # Paso 2: Normalizar con Gemini T2T
    texto_normalizado = normalizar_texto(texto_crudo,model=model)

    # Paso 3: Detectar idioma
    idioma = detectar_idioma(texto_normalizado)

    # Paso 4: Obtener temperatura de internet
    contexto = {}
    if ciudad:
        datos_temperatura = obtener_temperatura(ciudad)
        if datos_temperatura:
            contexto = datos_temperatura

    # Paso 5: Construir JSON de salida
    salida = {
        "texto"    : texto_normalizado,
        "fuente"   : fuente,
        "idioma"   : idioma,
        "contexto" : contexto
    }

    return salida

def obtener_temperatura(ciudad):
    """
    Obtiene la temperatura actual de una ciudad usando la API gratuita de Open-Meteo.
    No requiere API key.

    Flujo:
        1. Geocodifica la ciudad con la API de Open-Meteo Geocoding.
        2. Consulta la temperatura actual con las coordenadas obtenidas.

    Args:
        ciudad (str): Nombre de la ciudad (ej: 'Sevilla', 'Madrid', 'Barcelona').

    Returns:
        dict: { 'ciudad': str, 'temperatura': float, 'unidad': 'celsius' }
              Devuelve None si no se puede obtener la temperatura.
    """
    try:
        # Paso 1: Obtener coordenadas de la ciudad
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": ciudad, "count": 1, "language": "es", "format": "json"}
        geo_resp = requests.get(geo_url, params=geo_params, timeout=5)
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            print(f"[Temperatura] Ciudad '{ciudad}' no encontrada.")
            return None

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        nombre_ciudad = geo_data["results"][0]["name"]

        # Paso 2: Obtener temperatura actual
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m",
            "timezone": "auto"
        }
        weather_resp = requests.get(weather_url, params=weather_params, timeout=5)
        weather_data = weather_resp.json()

        temperatura = weather_data["current"]["temperature_2m"]

        return {
            "ciudad": nombre_ciudad,
            "temperatura": temperatura,
            "unidad": "celsius"
        }

    except Exception as e:
        print(f"[Temperatura] Error al obtener temperatura: {e}")
        return None