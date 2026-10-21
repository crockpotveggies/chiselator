"""Check repository Markdown links, heading anchors and fenced-block balance."""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / 'README.md', *sorted((ROOT / 'docs').rglob('*.md'))]


def prose_and_anchors(text):
    prose, anchors, counts = [], set(), {}
    fence = None
    for line in text.splitlines():
        if re.match(r'^\s*(`{3,}|~{3,})', line):
            marker = line.strip()[0]
            fence = None if fence == marker else marker
            continue
        if fence:
            continue
        prose.append(line)
        heading = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if heading:
            slug = re.sub(r'[^\w\-\s]', '', heading[1].lower()).replace(' ', '-')
            suffix = counts.get(slug, 0)
            counts[slug] = suffix + 1
            anchors.add(slug + (f'-{suffix}' if suffix else ''))
    if fence:
        raise ValueError('unclosed code fence')
    return '\n'.join(prose), anchors


def main():
    parsed = {p.resolve(): prose_and_anchors(p.read_text(encoding='utf-8')) for p in FILES}
    errors = []
    checked = 0
    for path, (prose, _) in parsed.items():
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', prose):
            if re.match(r'^[a-z][a-z0-9+.-]*:', target, re.I):
                continue
            target = unquote(target.strip('<>'))
            filename, _, fragment = target.partition('#')
            dest = (path.parent / filename).resolve() if filename else path
            checked += 1
            if not dest.exists():
                errors.append(f'{path.relative_to(ROOT)}: missing {target}')
            elif fragment and dest.suffix == '.md':
                if dest not in parsed:
                    parsed_value = prose_and_anchors(dest.read_text(encoding='utf-8'))
                else:
                    parsed_value = parsed[dest]
                if fragment not in parsed_value[1]:
                    errors.append(f'{path.relative_to(ROOT)}: missing anchor {target}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Checked {len(FILES)} Markdown files, {checked} local links/anchors and code fences.')


if __name__ == '__main__':
    main()
