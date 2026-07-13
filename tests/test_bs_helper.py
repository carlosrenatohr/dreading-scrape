import os
import re

from services.bs_helper import get_lecture_pieces

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _read(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def _fixture():
    return _read(os.path.join(FIXTURE_DIR, 'reading_mec.html'))


def _event_fixture():
    return _read(os.path.join(FIXTURE_DIR, 'event_sunday.html'))


def test_parses_new_mec_dom():
    res = get_lecture_pieces(_fixture())

    assert res['title']
    assert re.match(r'^\d{4}-\d{2}-\d{2}T00:00:00Z$', res['date_raw'])

    titles = [l['title'] for l in res['lecturas']]
    assert len(res['lecturas']) == 3
    assert 'Primera Lectura' in titles
    assert 'Salmo' in titles
    assert 'Evangelio' in titles


def test_salmo_has_psalm_readings_have_last_line():
    res = get_lecture_pieces(_fixture())
    by_title = {l['title']: l for l in res['lecturas']}

    assert 'psalm' in by_title['Salmo']
    assert 'last_line' in by_title['Primera Lectura']
    assert 'last_line' in by_title['Evangelio']


def test_parses_event_page_with_second_reading():
    res = get_lecture_pieces(_event_fixture())

    assert res['title'] == 'Evangelio y Lecturas del XVI Domingo del Tiempo Ordinario'
    titles = [l['title'] for l in res['lecturas']]
    assert titles == ['Primera Lectura', 'Salmo', 'Segunda Lectura', 'Evangelio']

    by_title = {l['title']: l for l in res['lecturas']}
    assert 'psalm' in by_title['Salmo']
    assert 'last_line' in by_title['Segunda Lectura']
    assert 'last_line' in by_title['Evangelio']


def test_date_raw_override_sets_date_fields():
    res = get_lecture_pieces(_event_fixture(), date_raw='2026-07-19')

    assert res['date_raw'] == '2026-07-19T00:00:00Z'
    assert res['date_title'] == '19 de julio de 2026'


def test_returns_none_for_missing_reading():
    assert get_lecture_pieces(None) is None
    assert get_lecture_pieces('<html><body>no reading here</body></html>') is None


def test_old_layout_no_longer_matches():
    old_html = _read(os.path.join(os.path.dirname(__file__), '..', 'lectura.html'))
    assert get_lecture_pieces(old_html) is None
