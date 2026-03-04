"""
format_dynamodb.py

Reads a DynamoDB scan JSON from stdin and writes
a fully readable plain-text report to stdout.
Long lines are wrapped at 100 characters with indentation.

Usage (from TerraDriftGuard/):
    aws dynamodb scan \
        --table-name terradriftguard-incidents \
        --output json --no-cli-pager \
        | python3 scripts/format_dynamodb.py \
        > evidence/cli/dynamodb-all-incidents.txt
"""

import json
import sys
import textwrap

MAX_WIDTH = 100


def unwrap_dynamodb(obj):
    if isinstance(obj, dict):
        if len(obj) == 1:
            key = list(obj.keys())[0]
            if key == 'S':
                return obj[key]
            if key == 'N':
                return float(obj[key]) if '.' in obj[key] else int(obj[key])
            if key == 'BOOL':
                return obj[key]
            if key == 'NULL':
                return None
            if key == 'L':
                return [unwrap_dynamodb(item) for item in obj[key]]
            if key == 'M':
                return {k: unwrap_dynamodb(v) for k, v in obj[key].items()}
        return {k: unwrap_dynamodb(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [unwrap_dynamodb(item) for item in obj]
    return obj


def try_parse_json(val):
    if not isinstance(val, str):
        return None
    stripped = val.strip()
    if (stripped.startswith('{') and stripped.endswith('}')) or \
       (stripped.startswith('[') and stripped.endswith(']')):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return None
    return None


def wrap_text(text, indent):
    pad = '  ' * indent
    return textwrap.fill(
        text,
        width=MAX_WIDTH,
        initial_indent=pad,
        subsequent_indent=pad + '  '
    )


def render_value(val, indent):
    parsed = try_parse_json(val)
    if parsed is not None:
        return render_obj(parsed, indent)
    if isinstance(val, str) and '\n' in val:
        pad = '  ' * indent
        lines = []
        for subline in val.split('\n'):
            lines.append(pad + subline)
        return '\n'.join(lines)
    if isinstance(val, dict):
        return render_obj(val, indent)
    if isinstance(val, list):
        return render_obj(val, indent)
    return wrap_text(str(val), indent)


def render_obj(obj, indent):
    pad = '  ' * indent
    lines = []
    if isinstance(obj, dict):
        for key, val in obj.items():
            parsed = try_parse_json(val)
            if parsed is not None:
                lines.append(pad + str(key) + ':')
                lines.append(render_obj(parsed, indent + 1))
            elif isinstance(val, dict):
                lines.append(pad + str(key) + ':')
                lines.append(render_obj(val, indent + 1))
            elif isinstance(val, list):
                lines.append(pad + str(key) + ':')
                for item in val:
                    lines.append(render_value(item, indent + 1))
            elif isinstance(val, str) and '\n' in val:
                lines.append(pad + str(key) + ':')
                for subline in val.split('\n'):
                    lines.append(pad + '  ' + subline)
            elif isinstance(val, str) and len(pad + key + ': ' + val) > MAX_WIDTH:
                lines.append(pad + str(key) + ':')
                lines.append(wrap_text(val, indent + 1))
            else:
                lines.append(pad + str(key) + ': ' + str(val))
    elif isinstance(obj, list):
        for item in obj:
            lines.append(render_value(item, indent))
    else:
        lines.append(wrap_text(str(obj), indent))
    return '\n'.join(lines)


def main():
    data = json.load(sys.stdin)
    items = data.get('Items', [])
    clean = [unwrap_dynamodb(item) for item in items]

    output = []
    output.append('TABLE: terradriftguard-incidents')
    output.append('ITEMS: ' + str(len(clean)))
    output.append('')

    for i, item in enumerate(clean, 1):
        output.append('--- INCIDENT ' + str(i) + ' ---')
        output.append(render_obj(item, 0))
        output.append('')

    print('\n'.join(output))


if __name__ == '__main__':
    main()
