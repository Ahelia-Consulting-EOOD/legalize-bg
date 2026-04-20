"""File Assembler — combines Markdown body with YAML frontmatter."""

import re
import yaml


# Bulgarian Cyrillic transliteration table (simplified)
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sht", "ъ": "a", "ь": "y", "ю": "yu", "я": "ya",
}


def generate_slug(title: str) -> str:
    """Generate a filesystem-safe slug from a Bulgarian title."""
    slug = title.lower().strip()
    result = []
    for ch in slug:
        if ch in _TRANSLIT:
            result.append(_TRANSLIT[ch])
        elif ch.isascii() and ch.isalnum():
            result.append(ch)
        elif ch in (" ", "-", "_"):
            result.append("-")
        # skip other characters
    slug = "".join(result)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug[:80]


def assemble_file(metadata: dict, body: str) -> str:
    """Combine YAML frontmatter and Markdown body into a complete file."""
    ordered = {}
    mandatory = [
        "titulo", "identificador", "pais", "rango",
        "fecha_publicacion", "ultima_actualizacion", "estado", "fuente",
    ]
    extensions = ["dv_issue", "dv_year", "effective_date", "category", "eli"]

    for key in mandatory:
        if key in metadata:
            ordered[key] = metadata[key]
    for key in extensions:
        if key in metadata:
            ordered[key] = metadata[key]
    if "amendment_history" in metadata:
        ordered["amendment_history"] = metadata["amendment_history"]

    yaml_str = yaml.dump(
        ordered,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    return f"---\n{yaml_str}---\n\n{body}"
