"""Validate and copy only the public static explanation into a fresh directory."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
FILES = frozenset({'index.html', 'style.css', 'appearance.js',
                   'mechanism-obscur-wide.png', 'mechanism-obscur-wide.svg',
                   'mechanism-obscur-narrow.png', 'mechanism-obscur-narrow.svg'})


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.dark_root = False
        self.images = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                raise ValueError('Duplicate document ID')
            self.ids.add(attrs['id'])
        if tag == 'html':
            self.dark_root = attrs.get('data-theme') == 'Obscur' and attrs.get('lang') == 'en'
        if tag == 'img':
            self.images += 1
            if not attrs.get('alt') or not attrs.get('width') or not attrs.get('height'):
                raise ValueError('The infographic needs alternative text and dimensions')
        for name in ('href', 'src'):
            if attrs.get(name):
                self.links.append(attrs[name])
        if attrs.get('srcset'):
            self.links.extend(item.strip().split()[0] for item in attrs['srcset'].split(','))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    entries = list(SITE.iterdir())
    if any(p.is_symlink() or not p.is_file() for p in entries) or {p.name for p in entries} != FILES:
        raise ValueError('Unexpected or missing static source: only the declared seven files are publishable')
    document = Document()
    document.feed((SITE / 'index.html').read_text(encoding='utf-8'))
    if not document.dark_root or document.images != 1:
        raise ValueError('Expected an Obscur no-JavaScript root and one explanatory picture')
    for target in document.links:
        parsed = urlsplit(target)
        if parsed.scheme:
            if parsed.scheme != 'https' or not parsed.netloc:
                raise ValueError('Unsupported external route')
            continue
        if parsed.netloc:
            raise ValueError('Protocol-relative routes are not supported')
        path = unquote(parsed.path)
        if path and path not in FILES | {'build-identity.json'}:
            raise ValueError('Static route leaves the declared payload: ' + target)
        if not path and parsed.fragment and unquote(parsed.fragment) not in document.ids:
            raise ValueError('Broken document anchor: ' + target)
    receipt_path = ROOT / 'docs/mechanism-rendering.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    expected = {'site/' + name for name in FILES if name.endswith(('.png', '.svg'))}
    if set(receipt['outputs_sha256']) != expected or receipt['application_or_scientific_execution'] is not False:
        raise ValueError('The explanatory-figure receipt has an unexpected scope')
    for name, value in receipt['outputs_sha256'].items():
        if digest(ROOT / name) != value:
            raise ValueError('Figure bytes do not match the retained receipt')
    for name, value in receipt['inputs_sha256_lf'].items():
        parts = PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts or '\\' in name:
            raise ValueError('Invalid receipt source path')
        path = ROOT / name
        if path.is_symlink():
            raise ValueError('Linked receipt source')
        data = path.read_bytes()
        if path.suffix in {'.py', '.json', '.md', '.css'}:
            data = path.read_text(encoding='utf-8').replace('\r\n', '\n').encode()
        if hashlib.sha256(data).hexdigest() != value:
            raise ValueError('Figure source changed: ' + name)
    return {name: digest(SITE / name) for name in sorted(FILES)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / '_site')
    parser.add_argument('--revision', help='Exact checkout revision supplied by the checked delivery workflow')
    args = parser.parse_args()
    if args.revision is not None and not re.fullmatch('[0-9a-f]{40}', args.revision):
        parser.error('--revision must be a complete lowercase Git SHA')
    hashes = validate()
    if args.check:
        print('Static source, local routes and retained figure identities agree')
        return
    output = args.output.resolve()
    # A fresh output prevents accidental replacement or broad workspace copying.
    if output.exists():
        raise ValueError('Choose a new output directory; existing outputs are preserved')
    if output == ROOT or output in SITE.parents or SITE == output or SITE in output.parents:
        raise ValueError('Output must be outside the maintained static source')
    output.mkdir(parents=True, exist_ok=False)
    for name in sorted(FILES):
        shutil.copyfile(SITE / name, output / name)
    record = {'kind': 'static explanation, not a hosted application',
              'checkout_revision': args.revision,
              'revision_source': 'delivery argument' if args.revision else 'not supplied for local candidate',
              'files_sha256': hashes}
    (output / 'build-identity.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    print('Built nine public files from the explicit static whitelist')


if __name__ == '__main__':
    main()
