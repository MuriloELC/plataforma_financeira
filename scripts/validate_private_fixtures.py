#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".pdf"}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida estrutura de fixtures privadas sem imprimir nomes nem conteudo."
    )
    parser.add_argument("--source", default="fixtures/private")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print("Pasta privada nao encontrada.")
        return 1
    if not source.is_dir():
        print("Origem privada nao e uma pasta.")
        return 1

    files = [path for path in source.rglob("*") if path.is_file()]
    by_extension = Counter(path.suffix.lower() or "<sem_extensao>" for path in files)
    unsupported = sum(
        count for extension, count in by_extension.items() if extension not in SUPPORTED_EXTENSIONS
    )
    total_size = sum(path.stat().st_size for path in files)

    print(f"Arquivos privados encontrados: {len(files)}")
    print(f"Tamanho total em bytes: {total_size}")
    for extension in sorted(SUPPORTED_EXTENSIONS):
        print(f"{extension}: {by_extension[extension]}")
    print(f"Extensoes nao suportadas: {unsupported}")

    return 0 if unsupported == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
