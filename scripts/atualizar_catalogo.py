#!/usr/bin/env python3
"""Atualiza catalogo.js a partir dos nomes das imagens da coleção.

Convenção recomendada:
  nome-do-marcador.jpg
  nome-do-marcador-verso.jpg
  nome-do-marcador-autoria-Nome-Sobrenome.jpg
  nome-do-marcador-autoria-Nome-Sobrenome-link-URL-codificada.jpg

O sufixo -autoria- separa o crédito; -link- recebe uma URL codificada.
A automação preenche apenas campos ausentes ou vazios e preserva dados manuais.
Também corrige títulos antigos gerados automaticamente quando continham os sufixos.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
OBJECT_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)
TITLE_FIELD_RE = re.compile(r"\btitulo\s*:\s*([\"'])(.*?)\1")
IMAGE_FIELD_RE = re.compile(r"\bimagem\s*:\s*([\"'])(.*?)\1")
VERSO_FIELD_RE = re.compile(r"\bverso\s*:\s*([\"'])(.*?)\1")
AUTORIA_FIELD_RE = re.compile(r"\bautoria\s*:\s*([\"'])(.*?)\1")
AUTOR_URL_FIELD_RE = re.compile(r"\bautorUrl\s*:\s*([\"'])(.*?)\1")
FIELD_PATTERNS = {
    "verso": VERSO_FIELD_RE,
    "autoria": AUTORIA_FIELD_RE,
    "autorUrl": AUTOR_URL_FIELD_RE,
}

TITLE_REPLACEMENTS = {
    "agua": "água",
    "coracao": "coração",
    "coracoes": "corações",
    "criancas": "crianças",
    "degrade": "degradê",
    "eletronica": "eletrônica",
    "matematica": "matemática",
    "nao": "não",
    "voce": "você",
    "triangulos": "triângulos",
    "ce": "cê",
    "ta": "tá",
}
LOWERCASE_WORDS = {
    "a", "as", "ao", "aos", "à", "às", "de", "do", "dos", "da", "das",
    "e", "em", "no", "nos", "na", "nas", "o", "os", "para", "por", "que",
    "um", "uma", "uns", "umas",
}


def normalize_path(value: str) -> str:
    return Path(value.replace("\\", "/")).as_posix().casefold()


def humanize_metadata_text(value: str) -> str:
    """Converte hífens e sublinhados em espaços, preservando nomes já formatados."""
    text = re.sub(r"[_-]+", " ", value).strip()
    words = re.sub(r"\s+", " ", text).split()
    uniform_case = text.islower() or text.isupper()

    result = []
    for index, original in enumerate(words):
        word = original.lower()
        if index > 0 and word in LOWERCASE_WORDS:
            result.append(word)
        elif uniform_case:
            result.append(word[0].upper() + word[1:])
        else:
            result.append(original)

    return " ".join(result)


def parse_filename_metadata(filename: str) -> dict[str, str]:
    """Lê os sufixos -autoria-Nome e -link-URL codificada no nome do arquivo."""
    stem = Path(filename).stem
    stem = re.sub(r"-(verso|frente)$", "", stem, flags=re.IGNORECASE)
    markers = list(re.finditer(r"-(autoria|link)-", stem, flags=re.IGNORECASE))
    title = stem[:markers[0].start()] if markers else stem
    metadata = {"titulo": title}

    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(stem)
        value = stem[marker.end():end].strip("-_ ")
        if not value:
            continue

        if marker.group(1).lower() == "autoria":
            metadata["autoria"] = humanize_metadata_text(value)
        elif marker.group(1).lower() == "link":
            url = unquote(value).strip()
            if re.match(r"^https?://", url, flags=re.IGNORECASE):
                metadata["autorUrl"] = url

    return metadata


def humanize_title(filename: str) -> str:
    """Converte o nome principal do arquivo em título legível, sem separar códigos como 6x1."""
    stem = parse_filename_metadata(filename)["titulo"]
    stem = re.sub(
        r"([a-záàâãéêíóôõúç])([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ])",
        r"\1 \2",
        stem,
    )
    stem = re.sub(r"[_-]+", " ", stem)
    words = re.sub(r"\s+", " ", stem).strip().split()

    result = []
    for index, original in enumerate(words):
        word = original.lower()
        word = TITLE_REPLACEMENTS.get(word, word)

        if index > 0 and word in LOWERCASE_WORDS:
            result.append(word)
        elif re.fullmatch(r"\d+(?:x\d+)?", word):
            result.append(word)
        elif word:
            result.append(word[0].upper() + word[1:])
        else:
            result.append(word)

    return " ".join(result)


def legacy_humanize_title(filename: str) -> str:
    """Reproduz o título gerado pela versão anterior do workflow."""
    stem = Path(filename).stem
    stem = re.sub(r"-(verso|frente)$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(
        r"([a-záàâãéêíóôõúç])([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ])",
        r"\1 \2",
        stem,
    )
    stem = re.sub(r"[_-]+", " ", stem)
    words = re.sub(r"\s+", " ", stem).strip().split()

    result = []
    for index, original in enumerate(words):
        word = original.lower()
        word = TITLE_REPLACEMENTS.get(word, word)
        if index > 0 and word in LOWERCASE_WORDS:
            result.append(word)
        elif re.fullmatch(r"\d+(?:x\d+)?", word):
            result.append(word)
        elif word:
            result.append(word[0].upper() + word[1:])
        else:
            result.append(word)

    return " ".join(result)


def parse_catalog_entries(catalog: str) -> tuple[int, list[dict]]:
    array_match = re.search(r"window\.MARCADORES\s*=\s*\[", catalog)
    if not array_match:
        raise ValueError("Não foi encontrado o início de window.MARCADORES no catalogo.js.")

    array_end = catalog.find("];", array_match.end())
    if array_end < 0:
        raise ValueError("Não foi encontrado o fechamento ]; do catálogo.")

    entries = []
    body = catalog[array_match.end():array_end]
    for match in OBJECT_RE.finditer(body):
        image_match = IMAGE_FIELD_RE.search(match.group(0))
        if not image_match:
            continue

        title_match = TITLE_FIELD_RE.search(match.group(0))
        verso_match = VERSO_FIELD_RE.search(match.group(0))
        autoria_match = AUTORIA_FIELD_RE.search(match.group(0))
        autor_url_match = AUTOR_URL_FIELD_RE.search(match.group(0))
        entries.append({
            "start": array_match.end() + match.start(),
            "end": array_match.end() + match.end(),
            "object": match.group(0),
            "titulo": title_match.group(2) if title_match else "",
            "imagem": image_match.group(2),
            "verso": verso_match.group(2) if verso_match else "",
            "autoria": autoria_match.group(2) if autoria_match else "",
            "autorUrl": autor_url_match.group(2) if autor_url_match else "",
        })

    return array_end, entries


def build_image_index(image_paths: list[str]) -> dict[str, str]:
    index: dict[str, str] = {}
    for value in image_paths:
        path = Path(value.replace("\\", "/"))
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if path.parent.as_posix() != "imagens":
            continue
        index.setdefault(path.name.casefold(), path.as_posix())
    return index


def find_image_by_stem(stem: str, by_name: dict[str, str]) -> str | None:
    for extension in (".jpg", ".jpeg", ".png", ".webp"):
        found = by_name.get((stem + extension).casefold())
        if found:
            return found
    return None


def front_for_changed_image(path: str, by_name: dict[str, str]) -> str | None:
    filename = Path(path).name
    stem = Path(filename).stem

    if re.search(r"-verso$", stem, flags=re.IGNORECASE):
        base = re.sub(r"-verso$", "", stem, flags=re.IGNORECASE)
        # O app associa nome-verso apenas a uma frente chamada nome.ext.
        return find_image_by_stem(base, by_name)

    if re.search(r"-frente$", stem, flags=re.IGNORECASE):
        base = re.sub(r"-frente$", "", stem, flags=re.IGNORECASE)
        plain_front = find_image_by_stem(base, by_name)
        return plain_front or by_name.get(filename.casefold())

    return by_name.get(filename.casefold())


def find_verso(front_path: str, by_name: dict[str, str]) -> str | None:
    stem = Path(front_path).stem
    return find_image_by_stem(stem + "-verso", by_name)


def upsert_string_field(entry_object: str, field_name: str, value: str) -> tuple[str, bool]:
    """Preenche um campo ausente ou vazio, sem substituir conteúdo manual existente."""
    if not value:
        return entry_object, False

    field_pattern = FIELD_PATTERNS[field_name]
    match = field_pattern.search(entry_object)
    serialized = json.dumps(value, ensure_ascii=False)

    if match:
        if match.group(2).strip():
            return entry_object, False
        replacement = field_name + ": " + serialized
        return entry_object[:match.start()] + replacement + entry_object[match.end():], True

    closing = entry_object.rfind("}")
    if closing < 0:
        raise ValueError("Registro inválido no catálogo: falta }.")

    prefix = entry_object[:closing].rstrip()
    separator = "" if prefix.endswith(("{", ",")) else ","
    field = " " + field_name + ": " + serialized
    return prefix + separator + field + entry_object[closing:], True


def atualizar_catalogo(
    catalog: str,
    image_paths: list[str],
    changed_paths: list[str] | None = None,
) -> tuple[str, dict[str, int]]:
    """Retorna o catálogo atualizado e um resumo das alterações."""
    _, entries = parse_catalog_entries(catalog)
    by_name = build_image_index(image_paths)
    catalog_by_image = {
        normalize_path(entry["imagem"]): entry
        for entry in entries
    }

    if changed_paths is None:
        candidates_to_check = list(by_name.values())
    else:
        candidates_to_check = [
            path for path in changed_paths
            if Path(path).suffix.lower() in IMAGE_EXTENSIONS
            and Path(path).parent.as_posix() == "imagens"
        ]

    fronts: set[str] = set()
    ignored_versos = 0
    for changed in candidates_to_check:
        front = front_for_changed_image(changed, by_name)
        if front:
            fronts.add(front)
        elif re.search(r"-verso\.(jpe?g|png|webp)$", changed, flags=re.IGNORECASE):
            ignored_versos += 1

    replacements = []
    new_records = []
    linked_versos = 0
    metadata_updated = 0
    titles_corrected = 0

    for front in sorted(fronts, key=str.casefold):
        verso = find_verso(front, by_name)
        filename_metadata = parse_filename_metadata(Path(front).name)
        key = normalize_path(front)
        existing = catalog_by_image.get(key)

        if existing:
            updated_object = existing["object"]

            # Corrige somente o título que a versão anterior gerou a partir do nome inteiro.
            old_generated_title = legacy_humanize_title(Path(front).name)
            new_generated_title = humanize_title(Path(front).name)
            title_match = TITLE_FIELD_RE.search(updated_object)
            if title_match and title_match.group(2) == old_generated_title and new_generated_title != old_generated_title:
                replacement = "titulo: " + json.dumps(new_generated_title, ensure_ascii=False)
                updated_object = updated_object[:title_match.start()] + replacement + updated_object[title_match.end():]
                titles_corrected += 1

            # Preenche apenas campos ausentes ou vazios; nunca substitui dados manuais.
            if verso and not existing["verso"]:
                updated_object, changed = upsert_string_field(updated_object, "verso", verso)
                if changed:
                    linked_versos += 1

            for field_name in ("autoria", "autorUrl"):
                value = filename_metadata.get(field_name, "")
                if value and not existing[field_name]:
                    updated_object, changed = upsert_string_field(updated_object, field_name, value)
                    if changed:
                        metadata_updated += 1

            if updated_object != existing["object"]:
                replacements.append((existing["start"], existing["end"], updated_object))
            continue

        fields = [
            "titulo: " + json.dumps(humanize_title(Path(front).name), ensure_ascii=False),
            "imagem: " + json.dumps(front, ensure_ascii=False),
        ]
        if verso:
            fields.append("verso: " + json.dumps(verso, ensure_ascii=False))
        if filename_metadata.get("autoria"):
            fields.append("autoria: " + json.dumps(filename_metadata["autoria"], ensure_ascii=False))
        if filename_metadata.get("autorUrl"):
            fields.append("autorUrl: " + json.dumps(filename_metadata["autorUrl"], ensure_ascii=False))

        new_records.append("{ " + ", ".join(fields) + " }")
        catalog_by_image[key] = {
            "imagem": front,
            "verso": verso or "",
            "autoria": filename_metadata.get("autoria", ""),
            "autorUrl": filename_metadata.get("autorUrl", ""),
        }
    
    updated = catalog
    for start, end, replacement in sorted(replacements, reverse=True):
        updated = updated[:start] + replacement + updated[end:]

    if new_records:
        array_end, _ = parse_catalog_entries(updated)
        prefix = updated[:array_end].rstrip()
        array_start = re.search(r"window\.MARCADORES\s*=\s*\[", updated)
        assert array_start is not None
        last_character = prefix[-1:] if prefix else ""
        if last_character not in ("[", ","):
            prefix += ","
        insertion = "\n  " + ",\n  ".join(new_records) + "\n"
        updated = prefix + insertion + updated[array_end:]

    return updated, {
        "adicionados": len(new_records),
        "versos_associados": linked_versos,
        "metadados_atualizados": metadata_updated,
        "titulos_corrigidos": titles_corrected,
        "versos_sem_frente": ignored_versos,
    }


def changed_images_from_git(before: str, after: str) -> list[str] | None:
    if not before or set(before) == {"0"}:
        return None

    result = subprocess.run(
        [
            "git", "diff", "--name-only", "-z", "--diff-filter=AMR",
            before, after, "--", "imagens/",
        ],
        check=True,
        capture_output=True,
    )
    return [
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Atualiza automaticamente o catálogo de marcadores.")
    parser.add_argument(
        "--git-diff",
        nargs=2,
        metavar=("COMMIT_ANTERIOR", "COMMIT_ATUAL"),
        help="Processa somente imagens adicionadas/alteradas entre dois commits.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Caminhos de imagens a processar; sem caminhos, verifica toda a pasta imagens/.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    catalog_path = root / "catalogo.js"
    image_dir = root / "imagens"

    if not catalog_path.is_file() or not image_dir.is_dir():
        print("Erro: catalogo.js ou pasta imagens/ não encontrados.", file=sys.stderr)
        return 1

    image_paths = [
        path.relative_to(root).as_posix()
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if args.git_diff:
        changed_paths = changed_images_from_git(*args.git_diff)
    elif args.paths:
        changed_paths = args.paths
    else:
        changed_paths = None

    original = catalog_path.read_text(encoding="utf-8")
    updated, summary = atualizar_catalogo(original, image_paths, changed_paths)

    if updated != original:
        catalog_path.write_text(updated, encoding="utf-8", newline="\n")
        print(
            "Catálogo atualizado: "
            f"{summary['adicionados']} novo(s) marcador(es); "
            f"{summary['versos_associados']} verso(s) associado(s); "
            f"{summary['metadados_atualizados']} metadado(s) preenchido(s); "
            f"{summary['titulos_corrigidos']} título(s) corrigido(s)."
        )
    else:
        print("Catálogo já estava atualizado; nenhuma alteração necessária.")

    if summary["versos_sem_frente"]:
        print(
            f"Aviso: {summary['versos_sem_frente']} arquivo(s) de verso sem frente correspondente "
            "foram ignorados."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
