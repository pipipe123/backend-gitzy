"""
summary_service.py - Genera un resumen general del análisis de un repositorio

Evalúa popularidad, actividad, salud y genera una descripción textual
a partir de los datos obtenidos del proveedor (GitHub, GitLab, Azure).
"""

from datetime import datetime, timezone


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _evaluate_popularity(stars: int, forks: int) -> str:
    score = stars + forks * 2
    if score >= 10000:
        return "Muy popular"
    if score >= 1000:
        return "Popular"
    if score >= 100:
        return "Moderado"
    if score >= 10:
        return "Bajo"
    return "Nuevo"


def _evaluate_activity(updated_at: str) -> str:
    updated = _parse_date(updated_at)
    if not updated:
        return "Desconocido"

    now = datetime.now(timezone.utc)
    days_since = (now - updated).days

    if days_since <= 7:
        return "Muy activo"
    if days_since <= 30:
        return "Activo"
    if days_since <= 90:
        return "Moderado"
    if days_since <= 365:
        return "Bajo"
    return "Inactivo"


def _calculate_health_score(
    stars: int,
    forks: int,
    open_issues: int,
    languages: list,
    commits: list,
    updated_at: str,
) -> float:
    score = 0.0

    # Popularidad (max 30 puntos)
    pop = stars + forks * 2
    if pop >= 10000:
        score += 30
    elif pop >= 1000:
        score += 25
    elif pop >= 100:
        score += 15
    elif pop >= 10:
        score += 8
    else:
        score += 2

    # Actividad reciente (max 30 puntos)
    updated = _parse_date(updated_at)
    if updated:
        days = (datetime.now(timezone.utc) - updated).days
        if days <= 7:
            score += 30
        elif days <= 30:
            score += 25
        elif days <= 90:
            score += 15
        elif days <= 365:
            score += 8
        else:
            score += 2

    # Commits recientes (max 20 puntos)
    score += min(len(commits) * 4, 20)

    # Diversidad de lenguajes (max 10 puntos)
    score += min(len(languages) * 2, 10)

    # Ratio issues/estrellas (max 10 puntos) - menos issues relativo a estrellas = mejor
    if stars > 0:
        ratio = open_issues / stars
        if ratio < 0.01:
            score += 10
        elif ratio < 0.05:
            score += 8
        elif ratio < 0.1:
            score += 5
        elif ratio < 0.3:
            score += 3
        else:
            score += 1
    else:
        score += 5  # Sin datos suficientes, puntaje neutro

    return round(min(score, 100.0), 1)


def _generate_description(
    name: str,
    owner: str,
    provider: str,
    description: str | None,
    stars: int,
    forks: int,
    languages: list,
    popularity: str,
    activity: str,
    health_score: float,
) -> str:
    parts = [f"{owner}/{name} es un repositorio alojado en {provider}."]

    if description:
        parts.append(f"{description}.")

    if languages:
        if len(languages) == 1:
            parts.append(f"Está desarrollado en {languages[0]}.")
        else:
            langs = ", ".join(languages[:3])
            parts.append(f"Utiliza principalmente {langs}.")

    parts.append(f"Tiene {stars} estrellas y {forks} forks.")
    parts.append(f"Nivel de popularidad: {popularity}. Actividad: {activity}.")
    parts.append(f"Puntuación de salud: {health_score}/100.")

    return " ".join(parts)


def generate_repository_summary(repo_data: dict) -> dict:
    """Genera un resumen general a partir de los datos del repositorio analizado."""
    stars = repo_data.get("stars", 0)
    forks = repo_data.get("forks", 0)
    open_issues = repo_data.get("open_issues", 0)
    languages = repo_data.get("languages", [])
    commits = repo_data.get("commits", [])
    updated_at = repo_data.get("updated_at", "")

    popularity = _evaluate_popularity(stars, forks)
    activity = _evaluate_activity(updated_at)
    health_score = _calculate_health_score(
        stars, forks, open_issues, languages, commits, updated_at
    )
    primary_language = languages[0] if languages else None

    description = _generate_description(
        name=repo_data.get("name", ""),
        owner=repo_data.get("owner", ""),
        provider=repo_data.get("provider", ""),
        description=repo_data.get("description"),
        stars=stars,
        forks=forks,
        languages=languages,
        popularity=popularity,
        activity=activity,
        health_score=health_score,
    )

    return {
        "popularity_level": popularity,
        "activity_level": activity,
        "languages_count": len(languages),
        "primary_language": primary_language,
        "health_score": health_score,
        "description": description,
    }
