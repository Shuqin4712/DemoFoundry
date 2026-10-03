"""File helpers. Text is always UTF-8 with LF line endings, on every platform."""
import json
import os
import wave


def path(root, rel):
    return os.path.join(root, rel)


def read(root, rel):
    with open(path(root, rel), encoding='utf-8') as f:
        return f.read()


def write(root, rel, text):
    p = path(root, rel)
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def write_json(root, rel, obj, indent=2):
    write(root, rel, json.dumps(obj, indent=indent, ensure_ascii=False))


def load_json(root, rel):
    with open(path(root, rel), encoding='utf-8') as f:
        return json.load(f)


def load_words(root, rel):
    w = load_json(root, rel)
    return w['words'] if isinstance(w, dict) else w


def wav_duration(root, rel):
    with wave.open(path(root, rel)) as f:
        return round(f.getnframes() / f.getframerate(), 3)
