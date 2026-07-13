"""Discover ciudadredonda.org reading-event URLs and their dates.

The 2026 site exposes dated reading pages at
`/events/lecturas-<liturgical-slug>_YYYY-MM-DD/`. The liturgical slug is not
derivable from a date, so event URLs must be *discovered* from the page links
rather than constructed:

  - `/evangelio-de-manana/` links to tomorrow's reading event (one `lecturas-`
    link, no skip param).
  - each `/events/…` page links to the adjacent days' reading events: the
    *next* day carries an `nskip` query param, the *previous* day a `pskip` one.

Walking those next/prev links traverses the calendar day by day, which restores
the per-date fetching that was lost when the old `?f=YYYY-MM-DD` param stopped
working.
"""

import re

from bs4 import BeautifulSoup

# Matches a reading-event path and captures its embedded date, e.g.
# /events/lecturas-del-xvi-domingo-del-tiempo-ordinario_2026-07-19/
_EVENT_RE = re.compile(r'/events/lecturas-[^"\s/]+_(\d{4}-\d{2}-\d{2})/')


def date_from_event_url(url):
    match = _EVENT_RE.search(url or '')
    return match.group(1) if match else None


def _lecturas_links(html):
    # Yield (date, url, kind) for every reading-event link on the page, where
    # kind is 'next' (nskip), 'prev' (pskip) or 'self' (neither — e.g. the single
    # link on the "tomorrow" teaser page).
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        match = _EVENT_RE.search(href)
        if not match:
            continue
        kind = 'next' if 'nskip' in href else ('prev' if 'pskip' in href else 'self')
        links.append((match.group(1), href, kind))
    return links


def tomorrow_event_url(manana_html):
    # The "tomorrow" teaser carries a single reading-event link (no skip param).
    for _date, url, kind in _lecturas_links(manana_html):
        if kind == 'self':
            return url
    return None


def next_event_url(event_html):
    for _date, url, kind in _lecturas_links(event_html):
        if kind == 'next':
            return url
    return None


def prev_event_url(event_html):
    for _date, url, kind in _lecturas_links(event_html):
        if kind == 'prev':
            return url
    return None
