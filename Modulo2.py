from qwen_vl_utils import process_vision_info
import json
import torch
import re

from pathlib import Path
from google.colab import drive

def analizar_prenda(imagen_url, id_prenda):
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": imagen_url},
                {"type": "text", "text": """Eres un experto en moda. Analiza la imagen y lista SOLO las prendas principales que se ven claramente, máximo 4.
                Los tipos de prenda posibles son: camisa, camiseta, pantalon, vestido, zapatos, corbata, chaqueta, sudadera, jersey, bañador, falda, abrigo, bolso, gorro o lo que consideres oportun

                Para cada prenda devuelve SOLO una lista JSON con este formato exacto:
                [
                    {
                        "tipo": "camisa",
                        "color": "blanco",
                        "estampado": "liso",
                        "formalidad": "formal",
                        "temporada": ["primavera", "verano"]
                    }
                ]
                No inventes prendas que no veas claramente. No repitas prendas. No escribas nada más, solo el JSON."""}
            ]
        }
    ]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(text=[text], images=image_inputs, return_tensors="pt").to(model.device)

    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=1024)

    respuesta = processor.batch_decode(output, skip_special_tokens=True)[0]
    texto = respuesta.split("assistant")[-1].strip().replace("```json", "").replace("```", "").strip()

    if not texto.endswith("]"):
        texto = texto[:texto.rfind("}") + 1] + "]"

    try:
        prendas = json.loads(texto)
    except json.JSONDecodeError:
        objetos = re.findall(r'\{[^{}]+\}', texto)
        prendas = [json.loads(o) for o in objetos]

    resultado = []
    for i, prenda in enumerate(prendas):
        prenda["id"] = f"{id_prenda}_{i+1}"
        prenda["imagen_path"] = imagen_url
        resultado.append(prenda)

    return resultado

