"""
llm_service.py - Cliente de Hugging Face Inference API para generar resúmenes y análisis de código

Usa modelos open-source gratuitos (Qwen/Mistral) a través de la Inference API de HF:
- Generar resúmenes inteligentes de repositorios
- Analizar calidad y patrones de código
- Generar sugerencias de mejora con diff simulado
"""

import json
import difflib
import re

from huggingface_hub import InferenceClient

from app.core.config import settings

_client: InferenceClient | None = None

MODEL_ID = "Qwen/Qwen2.5-Coder-32B-Instruct"


def _get_client() -> InferenceClient:
    global _client
    if _client is None:
        if not settings.HF_API_TOKEN:
            raise RuntimeError("HF_API_TOKEN no está configurada")
        _client = InferenceClient(provider="hf-inference", api_key=settings.HF_API_TOKEN)
    return _client


def _chat(prompt: str, max_tokens: int = 1024) -> str:
    """Envía un prompt al modelo y devuelve la respuesta como texto."""
    client = _get_client()
    response = client.chat_completion(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def _extract_json(text: str) -> dict | None:
    """Intenta extraer un JSON de la respuesta, limpiando markdown si es necesario."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


async def generate_ai_summary(repo_data: dict) -> str:
    """Genera un resumen inteligente del repositorio."""
    languages = ", ".join(repo_data.get("languages", [])) or "No detectados"
    commits_text = ""
    for c in repo_data.get("commits", [])[:5]:
        commits_text += f"- {c.get('message', '')}\n"

    prompt = f"""Analiza el siguiente repositorio y genera un resumen conciso en español (máximo 3 párrafos):

Nombre: {repo_data.get('owner', '')}/{repo_data.get('name', '')}
Proveedor: {repo_data.get('provider', '')}
Descripción: {repo_data.get('description') or 'Sin descripción'}
Lenguajes: {languages}
Estrellas: {repo_data.get('stars', 0)}
Forks: {repo_data.get('forks', 0)}
Issues abiertos: {repo_data.get('open_issues', 0)}
Rama principal: {repo_data.get('default_branch', '')}
Creado: {repo_data.get('created_at', '')}
Última actualización: {repo_data.get('updated_at', '')}

Últimos commits:
{commits_text or 'No disponibles'}

Incluye:
1. Qué hace el proyecto y su propósito probable
2. Estado del proyecto (actividad, popularidad, madurez)
3. Tecnologías principales y observaciones relevantes"""

    return _chat(prompt, max_tokens=512)


async def analyze_code_with_ai(file_path: str, code: str, language: str) -> dict:
    """Analiza un fragmento de código y devuelve observaciones sobre calidad."""
    prompt = f"""Analiza el siguiente código ({language}) del archivo "{file_path}" y responde en español con un JSON que tenga estas claves:
- "quality_score": número del 1 al 10
- "summary": resumen breve de qué hace el código (1-2 líneas)
- "strengths": lista de puntos fuertes (máximo 3)
- "improvements": lista de mejoras sugeridas (máximo 3)
- "patterns": patrones de diseño o prácticas detectadas (máximo 3)

Responde SOLO con el JSON, sin markdown ni texto adicional.

```{language}
{code}
```"""

    text = _chat(prompt, max_tokens=512)
    result = _extract_json(text)

    if result:
        return result

    return {
        "quality_score": 0,
        "summary": text,
        "strengths": [],
        "improvements": [],
        "patterns": [],
    }


def _extract_snippet(code: str, line_start: int, line_end: int) -> str:
    """Extrae un fragmento de código entre las líneas indicadas (1-indexed)."""
    lines = code.splitlines()
    start = max(0, line_start - 1)
    end = min(len(lines), line_end)
    return "\n".join(lines[start:end])


def _build_diff(original: str, improved: str, file_name: str) -> str:
    """Genera un unified diff entre el código original y el mejorado."""
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        improved.splitlines(keepends=True),
        fromfile=f"a/{file_name}",
        tofile=f"b/{file_name}",
    )
    return "".join(diff)


async def suggest_improvements_for_file(code: str, language: str, file_name: str) -> dict:
    """Genera sugerencias de mejora para un archivo individual."""
    prompt = f"""Analiza el siguiente código ({language}) del archivo "{file_name}" y responde en español con un JSON que tenga estas claves:

- "suggestions": lista de objetos, cada uno con:
  - "title": título corto de la sugerencia
  - "description": explicación de la mejora
  - "severity": "high", "medium" o "low"
  - "line_start": número de línea donde inicia el problema (1-indexed, entero)
  - "line_end": número de línea donde termina el problema (1-indexed, entero)
  - "suggested_snippet": fragmento de código corregido que reemplaza las líneas indicadas
- "improved_code": el código completo con TODAS las sugerencias aplicadas

Reglas:
- Máximo 6 sugerencias, enfócate en las más importantes
- line_start y line_end DEBEN ser números válidos dentro del rango del código (1 a {len(code.splitlines())})
- suggested_snippet debe contener SOLO el reemplazo para las líneas line_start a line_end
- El código mejorado debe ser funcional y respetar la lógica original
- Mejora nombres de variables, estructura, buenas prácticas, rendimiento y legibilidad
- No cambies la funcionalidad del código
- Responde SOLO con el JSON, sin markdown ni texto adicional

```{language}
{code}
```"""

    text = _chat(prompt, max_tokens=2048)
    result = _extract_json(text)

    if not result:
        return {
            "file_name": file_name,
            "language": language,
            "suggestions": [],
            "improved_code": code,
            "diff": "",
        }

    improved_code = result.get("improved_code", code)
    total_lines = len(code.splitlines())

    suggestions = []
    for s in result.get("suggestions", []):
        line_start = s.get("line_start", 1)
        line_end = s.get("line_end", line_start)
        line_start = max(1, min(line_start, total_lines))
        line_end = max(line_start, min(line_end, total_lines))

        suggestions.append({
            "file_name": file_name,
            "title": s.get("title", ""),
            "description": s.get("description", ""),
            "severity": s.get("severity", "low"),
            "line_start": line_start,
            "line_end": line_end,
            "original_snippet": _extract_snippet(code, line_start, line_end),
            "suggested_snippet": s.get("suggested_snippet", ""),
        })

    return {
        "file_name": file_name,
        "language": language,
        "suggestions": suggestions,
        "improved_code": improved_code,
        "diff": _build_diff(code, improved_code, file_name),
    }
