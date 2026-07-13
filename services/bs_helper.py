from datetime import datetime, timezone

from bs4 import BeautifulSoup

# Spanish month names for the human-readable date_title (no locale dependency).
_SPANISH_MONTHS = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

# ciudadredonda.org (2026) renders the readings inside a Modern Events Calendar /
# Divi wrapper whose class depends on the page:
#   - /evangelio-lecturas-hoy/        -> div.mec-single-event-description (accordion, "today")
#   - /events/lecturas-..._DATE/      -> div.mec-divi-content              (dated event page)
# Both share the same inner shape: a run of <h2> section headings ("Primera
# Lectura" / "Salmo" / "Segunda Lectura" on Sundays / "Evangelio"), each followed
# by the section's <p> paragraphs up to the next <h2>. mec-event-content is kept
# as a defensive fallback for layout variants.
_CONTAINER_CLASSES = ('mec-single-event-description', 'mec-divi-content', 'mec-event-content')

# A heading counts as a reading section when its text names one of these.
_SECTION_KEYWORDS = ('lectura', 'salmo', 'evangelio')


def _is_section_heading(h2):
    text = h2.get_text(' ', strip=True).lower()
    return any(keyword in text for keyword in _SECTION_KEYWORDS)


def _find_reading_container(body):
    # Return the wrapper that actually holds the reading <h2> sections, trying the
    # known classes in order. Returning None (rather than falling back to the whole
    # page) keeps unrelated pages — e.g. the pre-2026 layout — correctly unparsed.
    for css_class in _CONTAINER_CLASSES:
        for candidate in body.find_all('div', class_=css_class):
            if any(_is_section_heading(h2) for h2 in candidate.find_all('h2')):
                return candidate
    return None


def _resolve_date(date_raw):
    # date_raw is supplied by the fetch layer when the source URL carries the
    # date (the /events/ pages embed it); otherwise we stamp the current UTC
    # date, since the "today" accordion page has no date marker of its own.
    if date_raw:
        day = datetime.strptime(date_raw[:10], '%Y-%m-%d').date()
    else:
        day = datetime.now(timezone.utc).date()
    # Store the calendar date at UTC midnight in ISO-8601 so multi-timezone
    # consumers (apps, analytics) read it unambiguously.
    date_raw = day.strftime('%Y-%m-%dT00:00:00Z')
    date_title = '%d de %s de %d' % (day.day, _SPANISH_MONTHS[day.month - 1], day.year)
    return date_raw, date_title


def _extract_section(heading):
    # Collect the <p> paragraphs that belong to this section (up to the next <h2>).
    paragraphs = []
    for sibling in heading.find_next_siblings():
        if sibling.name == 'h2':
            break
        if sibling.name == 'p':
            paragraphs.append(sibling)
    if not paragraphs:
        return None

    bolds = [b.get_text(' ', strip=True) for p in paragraphs for b in p.find_all('b')]
    italics = [i.get_text(' ', strip=True) for p in paragraphs for i in p.find_all('i')]
    content_text = '\n'.join(
        p.get_text(' ', strip=True) for p in paragraphs if p.get_text(strip=True))

    title = heading.get_text(' ', strip=True)
    row = {
        'title': title,
        'content': content_text,
        'first_line': bolds[0] if bolds else '',
    }
    # Only the psalm is classified by its heading (its sung response is the <i>);
    # ordinary readings close with the bold "Palabra de Dios / del Señor".
    if 'salmo' in title.lower():
        row['psalm'] = italics[0] if italics else ''
    else:
        row['last_line'] = bolds[-1] if len(bolds) > 1 else ''
    return row


def get_lecture_pieces(content, date_raw=None):
    if not content:
        return None
    body = BeautifulSoup(content, 'html.parser')

    container = _find_reading_container(body)
    if not container:
        return None
    headings = [h2 for h2 in container.find_all('h2') if _is_section_heading(h2)]
    if not headings:
        return None

    # Title: prefer the accordion toggle title, fall back to the page <h1>.
    toggle_title = body.find('h3', {'class': 'mec-toggle-title'})
    if toggle_title:
        title = toggle_title.get_text(' ', strip=True)
    else:
        h1 = body.find('h1')
        title = h1.get_text(strip=True) if h1 else ''

    date_raw, date_title = _resolve_date(date_raw)
    res = {
        'title': title,
        'date_title': date_title,
        'date_raw': date_raw,
        'lecturas': [],
    }
    for heading in headings:
        row = _extract_section(heading)
        if row:
            res['lecturas'].append(row)
    return res
