"""Narration providers. Local Kokoro is free; ElevenLabs uses the caller's key.

Models are downloaded explicitly with `tts setup`, never shipped with a skill.
Whole paragraphs are synthesized continuously, then passed to the existing voice pipeline.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.request import Request, urlopen
from urllib.parse import quote

from . import voice, which

RELEASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'
FILES = ('kokoro-v1.0.onnx', 'voices-v1.0.bin')


def model_dir():
    return Path(os.environ.get('DEMOFOUNDRY_MODEL_DIR', Path.home() / '.cache' / 'demofoundry'))


def setup():
    root = model_dir()
    root.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name in FILES:
        path = root / name
        if not path.exists():
            tmp = path.with_suffix('.partial')
            print(f'downloading {name}', flush=True)
            try:
                with urlopen(RELEASE + name, timeout=120) as response, tmp.open('wb') as out:
                    while chunk := response.read(1024 * 1024):
                        out.write(chunk)
                tmp.replace(path)
            finally:
                tmp.unlink(missing_ok=True)
        digest = hashlib.sha256()
        with path.open('rb') as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
        manifest[name] = {'url': RELEASE + name, 'sha256': digest.hexdigest()}
    manifest['license'] = 'Kokoro model: Apache-2.0; kokoro-onnx runtime: MIT; see upstream repository.'
    voice.write_json(str(root / 'sources.json'), manifest)
    print(root)


def character_words(alignment):
    chars = alignment['characters']
    starts = alignment['character_start_times_seconds']
    ends = alignment['character_end_times_seconds']
    if not len(chars) == len(starts) == len(ends):
        raise ValueError('inconsistent ElevenLabs character alignment')
    result = []
    # Build offsets over characters, whose elements are normally single code points.
    text = ''.join(chars)
    if any(len(c) != 1 for c in chars):
        raise ValueError('expected one code point per alignment entry')
    for match in re.finditer(r'\S+', text):
        result.append({'text': match.group(), 'start': starts[match.start()], 'end': ends[match.end() - 1]})
    return result


class Kokoro:
    def __init__(self, config):
        if config.get('language', 'en-us') not in ('en-us', 'en-gb'):
            raise ValueError('the local v1 transcription path supports English narration only')
        from kokoro_onnx import Kokoro as Runtime
        from faster_whisper import WhisperModel
        root = model_dir()
        if not all((root / name).exists() for name in FILES):
            raise ValueError('Kokoro files missing; run demofoundry tts setup first')
        self.runtime = Runtime(str(root / FILES[0]), str(root / FILES[1]))
        self.transcriber = WhisperModel(config.get('transcribe_model', 'small.en'), device='cpu', compute_type='int8')

    def synthesize(self, text, output, config):
        samples, rate = self.runtime.create(text, voice=config.get('voice_id') or 'af_sarah',
                                            speed=config.get('speed', 1.0), lang=config.get('language', 'en-us'))
        voice.write_wav(str(output), samples, rate)
        segments, _ = self.transcriber.transcribe(voice.whisper_samples(output), word_timestamps=True, language='en')
        return [{'text': w.word.strip(), 'start': w.start, 'end': w.end} for s in segments for w in s.words]


class ElevenLabs:
    def __init__(self, config):
        self.key = os.environ.get('ELEVENLABS_API_KEY')
        if not self.key or not config.get('voice_id'):
            raise ValueError('ElevenLabs requires ELEVENLABS_API_KEY and voice_id')

    def synthesize(self, text, output, config):
        body = {'text': text, 'model_id': config.get('model_id', 'eleven_multilingual_v2')}
        body['voice_settings'] = {'speed': config.get('speed', 1.0), **config.get('voice_settings', {})}
        req = Request('https://api.elevenlabs.io/v1/text-to-speech/' + quote(config['voice_id'], safe='') + '/with-timestamps',
                      data=json.dumps(body).encode(), headers={'xi-api-key': self.key, 'Content-Type': 'application/json'})
        with urlopen(req, timeout=120) as response:
            result = json.load(response)
        with tempfile.TemporaryDirectory() as td:
            mp3 = Path(td) / 'speech.mp3'
            mp3.write_bytes(base64.b64decode(result['audio_base64']))
            subprocess.run([which.ffmpeg(), '-y', '-v', 'error', '-i', str(mp3), '-ac', '1', '-ar', '24000', str(output)], check=True)
        return character_words(result.get('normalized_alignment') or result['alignment'])


PROVIDERS = {'kokoro': Kokoro, 'elevenlabs': ElevenLabs}


def generate(spec_path, take):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', take):
        raise ValueError('take names must contain only letters, digits, _ or -')
    config = voice.load_spec(spec_path)
    name = config['engine']
    if name not in PROVIDERS:
        raise ValueError('use engine kokoro or elevenlabs; imported recordings use voice import')
    _, target = voice.dirs(spec_path, take)
    raw = Path(target) / 'raw'
    if Path(target).exists():
        raise ValueError('take already exists; use a new take name to preserve recordings')
    provider = PROVIDERS[name](config)
    raw.mkdir(parents=True)
    notes = {}
    for paragraph, text in config['paragraphs'].items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+', paragraph):
            raise ValueError('paragraph IDs must contain only letters, digits, _ or -')
        print(f'{name}: {paragraph}', flush=True)
        heard = provider.synthesize(text, raw / f'para-{paragraph}.wav', config)
        if not heard:
            raise ValueError(f'no words transcribed for {paragraph}')
        words, differences = voice.align(paragraph, text, heard, config['aliases'])
        voice.write_words(str(raw / f'para-{paragraph}.words.json'), words)
        notes[paragraph] = differences
    voice.write_json(str(Path(target) / 'provider.json'), {'provider': name, 'voice_id': config.get('voice_id'),
                     'transcribe_model': config.get('transcribe_model', 'small.en'), 'alignment_warnings': notes,
                     'review_required': any(notes.values())})
    voice.cmd_build(config, str(raw), target)
    return target


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    subs = ap.add_subparsers(dest='cmd', required=True)
    subs.add_parser('setup')
    run = subs.add_parser('generate')
    run.add_argument('spec'); run.add_argument('--take', required=True)
    args = ap.parse_args(argv)
    if args.cmd == 'setup':
        setup()
    else:
        generate(args.spec, args.take)
