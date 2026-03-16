from serpapi import GoogleSearch
import json
import re 
import time

# Paso 1: Gemini genera las queries de búsqueda
def generar_queries(outfit_json,model=None):
    prompt = f"""
      Dado este outfit:
      {json.dumps(outfit_json["outfit"], ensure_ascii=False, indent=2)}

      Genera 3 búsquedas para encontrar prendas complementarias en tiendas online.
      Cada búsqueda debe ser específica: incluye color, tipo de prenda y "comprar".
      Piensa qué le falta al outfit para completarlo.

      Responde ÚNICAMENTE con este JSON, sin texto adicional ni bloques markdown:
      {{
        "queries": [
          "zapatos negros formales hombre comprar zara",
          "cinturón cuero negro formal comprar",
          "corbata seda azul marino comprar mango"
        ]
      }}
      """
    respuesta = model.generate_content(prompt)
    texto = re.sub(r"```json|```", "", respuesta.text).strip()
    return json.loads(texto)["queries"]

def buscar_en_google(query, num_resultados=5,SERPAPI_KEY=None):
  params = {
    "engine": "google",       # google normal, no google_shopping
    "q": query + " comprar",
    "api_key": SERPAPI_KEY,
    "gl": "es",
    "hl": "es",
    "num": num_resultados
  }
  search = GoogleSearch(params)
  data = search.get_dict()

  print(data)

  resultados = []
  for r in data.get("organic_results", [])[:num_resultados]:
      enlace = r.get("link", "")
      # Filtrar solo tiendas de ropa conocidas
      tiendas_validas = ["zara", "mango", "hm", "asos", "zalando",
                        "pull", "massimo", "corteingles", "bershka"]
      if any(t in enlace.lower() for t in tiendas_validas):
          resultados.append({
              "titulo": r.get("title", ""),
              "enlace": enlace,
              "descripcion": r.get("snippet", ""),
              "tienda": r.get("displayed_link", ""),
          })

  return resultados


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
  raise Exception("Se agotaron los reintentos")


def modulo3_seleccion_outfit(armario_json, instruccion_usuario, contexto={}, model=None, SERPAPI_KEY=None):

    # Paso 1: Gemini genera queries cortas y específicas
    prompt_queries = f"""
      Eres un estilista experto. Dado este armario y la instrucción del usuario,
      genera 3 búsquedas cortas para encontrar prendas complementarias en tiendas online.

      ## ARMARIO
      {json.dumps(armario_json, ensure_ascii=False, indent=2)}

      ## INSTRUCCIÓN
      {instruccion_usuario}

      Reglas para las queries:
      - Máximo 6 palabras cada una
      - Incluye tipo de prenda + color + tienda (zara, mango, zalando, asos, pull, corteingles)
      - Piensa qué le FALTA al armario para completar el outfit

      Responde ÚNICAMENTE con este JSON, sin texto adicional ni bloques markdown:
      {{
        "queries": [
          "zapatos negros formales hombre zara",
          "cinturón cuero negro formal mango",
          "corbata azul marino formal zalando"
        ]
      }}
    """
    texto_queries = llamar_gemini(prompt_queries, model=model)
    texto_queries = re.sub(r"```json|```", "", texto_queries).strip()
    queries = json.loads(texto_queries)["queries"]
    print(f"[Módulo 3] Queries generadas: {queries}")

    # Paso 2: Buscar en SerpAPI con las queries de Gemini
    todos_resultados = []
    for q in queries:
        todos_resultados.extend(buscar_en_google(q, SERPAPI_KEY=SERPAPI_KEY))

    print(f"[Módulo 3] Resultados de tiendas encontrados: {len(todos_resultados)}")

    # Paso 3: Gemini selecciona outfit y referencias
    prompt = f"""
      Eres un estilista experto. Dado este armario y contexto, haz TODO en una sola respuesta.

      ## ARMARIO
      {json.dumps(armario_json, ensure_ascii=False, indent=2)}

      ## INSTRUCCIÓN
      {instruccion_usuario}

      ## CONTEXTO
      Temperatura: {contexto.get('temperatura', 'no especificada')}
      Ocasión: {contexto.get('ocasion', 'no especificada')}

      ## RESULTADOS DE TIENDAS ONLINE (usa SOLO estos enlaces)
      {json.dumps(todos_resultados, ensure_ascii=False, indent=2)}

      Responde ÚNICAMENTE con este JSON:
      {{
        "outfit": {{
          "prendas": [{{"id": "id", "tipo": "tipo", "color": "color"}}],
          "estilo": "formal/casual/sport",
          "ocasion": "{contexto.get('ocasion', '')}",
          "temperatura": {contexto.get('temperatura', 0)}
        }},
        "prompt_imagen": "descripción en inglés para Stable Diffusion, full body, fashion photography, studio lighting",
        "referencias_tiendas": [
          {{
            "prenda": "título exacto de los resultados",
            "tienda": "tienda exacta",
            "enlace": "enlace exacto de los resultados",
            "por_que": "razón"
          }}
        ]
      }}
    """
    texto = llamar_gemini(prompt, model=model)
    texto = re.sub(r"```json|```", "", texto).strip()
    return json.loads(texto)
