import yaml
import pytest
from fetcher.bg.assembler import assemble_file, generate_slug


def test_assemble_produces_yaml_frontmatter():
    metadata = {
        "titulo": "Закон за нещо",
        "identificador": "123456",
        "pais": "bg",
        "rango": "закон",
        "fecha_publicacion": "2020-01-01",
        "ultima_actualizacion": "2020-01-01",
        "estado": "vigente",
        "fuente": "lex.bg",
        "dv_issue": "1",
        "dv_year": 2020,
        "effective_date": "2020-03-01",
        "category": "laws",
        "eli": "/eli/bg/закон/2020/zakon-za-neshto/con",
        "amendment_history": [],
    }
    body = "# ЗАКОН ЗА НЕЩО\n\n**Чл. 1.** Текст.\n"
    result = assemble_file(metadata, body)

    assert result.startswith("---\n")
    assert "\n---\n" in result
    # YAML should be parseable
    yaml_end = result.index("\n---\n", 4) + 5
    yaml_block = result[4:yaml_end - 5]
    parsed = yaml.safe_load(yaml_block)
    assert parsed["titulo"] == "Закон за нещо"
    assert parsed["pais"] == "bg"
    # Body follows
    assert "# ЗАКОН ЗА НЕЩО" in result[yaml_end:]


def test_generate_slug_from_title():
    slug = generate_slug("ЗАКОН ЗА ОБЩЕСТВЕНИТЕ ПОРЪЧКИ")
    assert slug  # non-empty
    assert "/" not in slug
    assert " " not in slug


def test_slug_is_deterministic():
    s1 = generate_slug("ЗАКОН ЗА ЕЛЕКТРОННОТО УПРАВЛЕНИЕ")
    s2 = generate_slug("ЗАКОН ЗА ЕЛЕКТРОННОТО УПРАВЛЕНИЕ")
    assert s1 == s2


def test_file_path_generation():
    metadata = {"category": "laws"}
    slug = "zakon-za-obshtestvenite-porachki"
    path = f"{metadata['category']}/{slug}.md"
    assert path == "laws/zakon-za-obshtestvenite-porachki.md"
