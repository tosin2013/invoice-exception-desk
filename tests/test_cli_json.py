"""CLI `--json` output contracts (specs/001-cli-json)."""
import importlib
import io
import json
import sys
from unittest.mock import patch

cli = importlib.import_module('slugify.__main__')


def run_json(capsys, argv):
    cli.main(['slugify', *argv])
    return capsys.readouterr().out


def test_json_prints_input_and_slug(capsys):
    out = run_json(capsys, ['--json', 'Hello', 'World'])
    assert out == '{"input": "Hello World", "slug": "hello-world"}\n'


def test_json_slug_reflects_options(capsys):
    out = run_json(capsys, ['--json', '--separator', '_', 'Hello', 'World'])
    assert out == '{"input": "Hello World", "slug": "hello_world"}\n'


def test_json_stdin_preserves_exact_input(capsys):
    stdin = 'Hi There\n'
    with patch.object(sys, 'stdin', io.StringIO(stdin)):
        out = run_json(capsys, ['--json', '--stdin'])
    assert out == json.dumps({'input': stdin, 'slug': 'hi-there'}) + '\n'


def test_json_empty_input(capsys):
    out = run_json(capsys, ['--json'])
    assert out == '{"input": "", "slug": ""}\n'


def test_json_non_ascii_is_escaped_by_default(capsys):
    out = run_json(capsys, ['--json', 'Café'])
    assert out == '{"input": "Caf\\u00e9", "slug": "cafe"}\n'


def test_without_json_output_is_unchanged(capsys):
    out = run_json(capsys, ['Hello', 'World'])
    assert out == 'hello-world\n'


def test_without_json_argument_shape_is_unchanged():
    legacy_defaults = dict(text='', entities=True, decimal=True, hexadecimal=True,
                           max_length=0, word_boundary=False, save_order=False, separator='-',
                           stopwords=None, lowercase=True, replacements=None, allow_unicode=False)
    for argv, expected in (([], legacy_defaults),
                           (['Hello'], dict(legacy_defaults, text='Hello'))):
        args = cli.parse_args(['slugify', *argv])
        assert 'json' not in vars(args)
        assert cli.slugify_params(args) == expected
