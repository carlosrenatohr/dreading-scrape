from services import enrich


def _reading():
    return {
        'title': 'Evangelio y Lecturas del XVI Domingo del Tiempo Ordinario',
        'date_raw': '2026-07-19T00:00:00Z',
        'lecturas': [
            {'title': 'Primera Lectura', 'content': 'Lectura del libro...', 'first_line': 'Lectura del libro...'},
            {'title': 'Evangelio', 'content': 'En aquel tiempo...', 'first_line': 'Lectura del santo evangelio según san Lucas'},
        ],
    }


def test_enrich_adds_all_supplementary_fields():
    res = enrich.enrich(_reading())

    for field in ('message', 'reflection', 'kids_reflection', 'questions', 'image_prompt'):
        assert res.get(field), f'missing {field}'
    assert isinstance(res['questions'], list) and len(res['questions']) == 2
    assert res['enrichment_provider'] == 'stub'
    assert res['source_version'] == enrich.SOURCE_VERSION


def test_stub_provider_is_deterministic():
    a = enrich.enrich(_reading())
    b = enrich.enrich(_reading())
    assert a['reflection'] == b['reflection']
    assert a['message'] == b['message']


def test_default_provider_is_the_offline_stub():
    assert enrich.get_provider().name == 'stub'


def test_image_prompt_references_the_gospel():
    res = enrich.enrich(_reading())
    assert 'evangelio' in res['image_prompt'].lower()
