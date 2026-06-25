#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='fixtures/private')
    args = parser.parse_args()
    source = Path(args.source)
    if not source.exists():
        print(f'Pasta não encontrada: {source}')
        return 1
    files = [p for p in source.rglob('*') if p.is_file()]
    print(f'Arquivos encontrados para validação local: {len(files)}')
    print('Implementar chamada dos parsers sem vazar dados sensíveis.')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
