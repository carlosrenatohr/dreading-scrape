from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

# Spanish month names for the human-readable date_title (no locale dependency).
_SPANISH_MONTHS = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


def get_lecture_pieces(content):
    if not content:
        return None
    body = BeautifulSoup(content, 'html.parser')

    # The reading now lives in the Modern Events Calendar accordion: a
    # `div.mec-single-event-description` whose body is a run of <h2> section
    # headings (Primera Lectura / Salmo / Evangelio) each followed by <p>s.
    desc = body.find('div', {'class': 'mec-single-event-description'})
    headings = desc.find_all('h2') if desc else []
    # Pages with no reading published yet (or an unrecognised layout) carry no
    # section headings; treat those as "nothing to store".
    if not desc or not headings:
        return None

    # Title: prefer the specific accordion toggle title ("Evangelio y Lecturas
    # del Lunes de la XV Semana..."), fall back to the generic page <h1>.
    toggle_title = body.find('h3', {'class': 'mec-toggle-title'})
    if toggle_title:
        title = toggle_title.get_text(' ', strip=True)
    else:
        h1 = body.find('h1')
        title = h1.get_text(strip=True) if h1 else ''

    # The new page has no <time datetime=...>: stamp with the current Madrid date.
    now_eu = datetime.now(ZoneInfo("Europe/Madrid"))
    res = {
        'title': title,
        'date_title': '%d de %s de %d' % (
            now_eu.day, _SPANISH_MONTHS[now_eu.month - 1], now_eu.year),
        'date_raw': now_eu.strftime("%Y-%m-%d 00:00:00"),
        'lecturas': [],
    }

    for heading in headings:
        # Collect the <p> paragraphs that belong to this section (up to next h2).
        paragraphs = []
        for sib in heading.find_next_siblings():
            if sib.name == 'h2':
                break
            if sib.name == 'p':
                paragraphs.append(sib)
        if not paragraphs:
            continue

        bolds = [b.get_text(' ', strip=True)
                 for p in paragraphs for b in p.find_all('b')]
        italics = [i.get_text(' ', strip=True)
                   for p in paragraphs for i in p.find_all('i')]
        content_text = '\n'.join(
            p.get_text(' ', strip=True) for p in paragraphs if p.get_text(strip=True))

        lectura_row = {
            'title': heading.get_text(' ', strip=True),
            'content': content_text,
            'first_line': bolds[0] if bolds else '',
        }
        # A psalm carries its sung response in an <i> (old markup used the same
        # cue); ordinary readings close with a bold "Palabra de Dios/del Señor".
        is_psalm = 'salmo' in lectura_row['title'].lower() or bool(italics)
        if is_psalm:
            lectura_row['psalm'] = italics[0] if italics else ''
        else:
            lectura_row['last_line'] = bolds[-1] if len(bolds) > 1 else ''

        res['lecturas'].append(lectura_row)

    return res
