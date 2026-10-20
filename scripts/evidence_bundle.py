#!/usr/bin/env python3
"""Crea e verifica un inventario locale di evidenze selezionate esplicitamente."""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

KINDS = ('live-screenshot', 'ui-tree', 'store-screenshot', 'public-video',
         'live-video', 'video-frame', 'crop', 'asset', 'public-source', 'notes', 'rea-result')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path, data):
    fd, temporary = tempfile.mkstemp(prefix='.manifest-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def local_file(root, relative):
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError('Percorso relativo mancante')
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Richiesto un percorso relativo senza risalire alle cartelle superiori')
    target = (root / p).resolve(strict=True)
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError('Il file deve restare nel dossier')
    if target == root / 'manifest.json':
        raise ValueError('Il manifest non può registrare se stesso')
    return target


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def finite_nonnegative(value):
    try:
        n = float(value)
        if not math.isfinite(n) or n < 0:
            raise ValueError()
        return n
    except (TypeError, ValueError, OverflowError):
        raise argparse.ArgumentTypeError('Richiesti secondi finiti e non negativi')


def rectangle(value):
    try:
        parts = [int(x) for x in value.split(',')]
        if len(parts) != 4 or min(parts[:2]) < 0 or min(parts[2:]) <= 0:
            raise ValueError()
        return parts
    except ValueError:
        raise argparse.ArgumentTypeError('Richiesto x,y,larghezza,altezza in pixel')


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError('Il valore non può essere vuoto')
    return value


def valid_timestamp(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def schema_errors(data):
    if not isinstance(data, dict):
        return ['Il manifest deve essere un oggetto JSON']
    errors = []
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        errors.append('schema_version non supportata')
    app = data.get('app')
    if not isinstance(app, dict) or any(not isinstance(app.get(k), str) or not app[k].strip()
                                        for k in ('name', 'platform', 'id', 'version')):
        errors.append('Identità app mancante o malformata')
    if not isinstance(data.get('created_at'), str) or not data['created_at'].strip():
        errors.append('created_at mancante')
    artifacts = data.get('artifacts')
    if not isinstance(artifacts, list):
        return errors + ['artifacts deve essere una lista']
    for index, a in enumerate(artifacts):
        label = f'artifacts[{index}]'
        if not isinstance(a, dict):
            errors.append(f'{label}: richiesto un oggetto')
            continue
        for key in ('id', 'path', 'origin', 'observed_version', 'registered_at'):
            if not isinstance(a.get(key), str) or not a[key].strip():
                errors.append(f'{label}: {key} mancante o malformato')
        if a.get('kind') not in KINDS:
            errors.append(f'{label}: kind non valido')
        if not isinstance(a.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', a['sha256']):
            errors.append(f'{label}: SHA-256 non valido')
        if type(a.get('bytes')) is not int or a['bytes'] < 0:
            errors.append(f'{label}: bytes non valido')
        for key in ('parent', 'url', 'screen', 'note'):
            if key in a and (not isinstance(a[key], str) or not a[key].strip()):
                errors.append(f'{label}: {key} non valido')
        if 'timestamp' in a and not valid_timestamp(a['timestamp']):
            errors.append(f'{label}: timestamp non valido')
        if 'crop' in a:
            crop = a['crop']
            if (not isinstance(crop, list) or len(crop) != 4
                    or any(type(n) is not int for n in crop)
                    or min(crop[:2]) < 0 or min(crop[2:]) <= 0):
                errors.append(f'{label}: crop non valido')
        if ('timestamp' in a or 'crop' in a) and not a.get('parent'):
            errors.append(f'{label}: metadati derivati senza padre')
    return errors


def file_errors(root, artifacts):
    errors, ids, paths = [], set(), set()
    by_id = {a['id']: a for a in artifacts}
    for a in artifacts:
        label = a['id']
        if label in ids:
            errors.append(f'{label}: ID duplicato')
        ids.add(label)
        try:
            p = local_file(root, a['path'])
            canonical = p.relative_to(root).as_posix()
            if canonical in paths:
                errors.append(f'{label}: file duplicato tramite percorso equivalente')
            paths.add(canonical)
            if digest(p) != a['sha256'] or p.stat().st_size != a['bytes']:
                errors.append(f'{label}: file modificato dopo la registrazione')
        except (OSError, ValueError, RuntimeError) as exc:
            errors.append(f'{label}: {exc}')
        seen, parent = {label}, a.get('parent')
        while parent:
            if parent not in by_id or parent in seen:
                errors.append(f'{label}: padre mancante o ciclo nelle derivazioni')
                break
            seen.add(parent)
            parent = by_id[parent].get('parent')
    return errors


def read_manifest(path):
    if path.is_symlink():
        raise ValueError('Il manifest non può essere un collegamento simbolico')
    def reject_constant(value):
        raise ValueError(f'Costante JSON non valida: {value}')
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    init = subs.add_parser('init', help='Crea un nuovo dossier privato')
    init.add_argument('root', type=Path)
    init.add_argument('--app', required=True, type=nonempty)
    init.add_argument('--platform', required=True, choices=('ios', 'android', 'web', 'desktop', 'other'))
    init.add_argument('--app-id', default='unknown', type=nonempty)
    init.add_argument('--version', default='unknown', type=nonempty)
    add = subs.add_parser('add', help='Registra un file esistente senza copiarlo')
    add.add_argument('root', type=Path)
    add.add_argument('file')
    add.add_argument('--kind', choices=KINDS, required=True)
    add.add_argument('--origin', required=True, type=nonempty)
    for flag in ('url', 'screen', 'version', 'parent', 'note'):
        add.add_argument('--' + flag, type=nonempty, **({'default': 'unknown'} if flag == 'version' else {}))
    add.add_argument('--timestamp', type=finite_nonnegative)
    add.add_argument('--crop', type=rectangle)
    check = subs.add_parser('validate', help='Verifica schema, file e derivazioni')
    check.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = root / 'manifest.json'
    if args.command == 'init':
        root.mkdir(parents=True, exist_ok=False, mode=0o700)
        for folder in ('screenshots', 'ui-trees', 'videos', 'frames', 'crops', 'assets', 'public-sources', 'rea'):
            (root / folder).mkdir(mode=0o700)
        write_json(manifest, {'schema_version': 1, 'app': {'name': args.app, 'platform': args.platform,
                   'id': args.app_id, 'version': args.version}, 'created_at': now(), 'artifacts': []})
        print(str(root))
        return 0
    try:
        data = read_manifest(manifest)
        errors = schema_errors(data)
    except (OSError, ValueError, RuntimeError) as exc:
        data, errors = None, [str(exc)]
    if args.command == 'validate':
        if not errors:
            errors = file_errors(root, data['artifacts'])
        count = len(data['artifacts']) if isinstance(data, dict) and isinstance(data.get('artifacts'), list) else 0
        print(json.dumps({'valid': not errors, 'artifacts': count, 'errors': errors}, ensure_ascii=False))
        return 1 if errors else 0
    if errors:
        raise ValueError('; '.join(errors))
    artifacts = data['artifacts']
    errors = file_errors(root, artifacts)
    if errors:
        raise ValueError('Correggere prima il dossier: ' + '; '.join(errors))
    path = local_file(root, args.file)
    canonical = path.relative_to(root).as_posix()
    if any(local_file(root, a['path']) == path for a in artifacts):
        raise ValueError('File già registrato; conserva gli originali e registra un nuovo file')
    if args.parent and args.parent not in {a['id'] for a in artifacts}:
        raise ValueError('Registra prima il padre')
    if (args.crop is not None or args.timestamp is not None) and not args.parent:
        raise ValueError('Crop e timestamp richiedono un padre')
    record = {'id': 'art_' + uuid.uuid4().hex, 'path': canonical, 'kind': args.kind,
              'origin': args.origin, 'observed_version': args.version, 'registered_at': now(),
              'sha256': digest(path), 'bytes': path.stat().st_size}
    for key in ('url', 'screen', 'parent', 'timestamp', 'crop', 'note'):
        if getattr(args, key) is not None:
            record[key] = getattr(args, key)
    artifacts.append(record)
    write_json(manifest, data)
    print(record['id'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, OverflowError, RuntimeError) as exc:
        print(f'Errore: {exc}', file=sys.stderr)
        sys.exit(2)
