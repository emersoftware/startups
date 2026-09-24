"""Sourced product lineages, kept separate from the original audit artifacts."""
import json
from copy import deepcopy
from pathlib import Path


def all_events(startup):
    return startup.get('lineage', {}).get('parent', {}).get('events', []) + startup['events']


def apply_lineages(payload):
    corrections = json.loads(Path(__file__).with_name('lineages.json').read_text())
    by_name = {s['name']: s for s in payload['startups']}
    for correction in corrections:
        startup = by_name.get(correction['startup'])
        if startup is None:
            continue
        lineage = deepcopy(correction)
        lineage.pop('startup')
        replacement = lineage.pop('event')
        keys = {tuple(k) for k in lineage['parent'].pop('event_keys')}
        # An audit rebuild restores the original events; direct reapplication
        # must also preserve the parent events without duplicating them.
        events = list(startup['events'])
        restored_keys = {(e['date'], e['type']) for e in events}
        rebuilt = bool(keys & restored_keys) or (lineage['date'], 'pivot') in restored_keys
        if not rebuilt:
            events += startup.get('lineage', {}).get('parent', {}).get('events', [])
        present_keys = {(e['date'], e['type']) for e in events}
        missing = keys - present_keys
        if missing:
            raise ValueError(f'Missing parent evidence for {startup["name"]}: {missing}')
        parent_events = [e for e in events if (e['date'], e['type']) in keys]
        child_events = [e for e in events if (e['date'], e['type']) not in keys]
        candidates = [e for e in child_events if e['date'] == lineage['date'] and e['type'] in ('pivot', 'spinoff')]
        if len(candidates) != 1:
            raise ValueError(f'Expected one lineage origin for {startup["name"]}')
        child_events[child_events.index(candidates[0])] = replacement
        lineage['parent']['events'] = sorted(parent_events, key=lambda e: e['date'])
        startup['events'] = sorted(child_events, key=lambda e: e['date'])
        startup['lineage'] = lineage
        parent_aliases = {a.casefold() for a in lineage['parent'].pop('aliases')}
        startup['aliases'] = [a for a in startup.get('aliases', []) if a.casefold() not in parent_aliases]
        terms = [startup.get('search_blob', ''), lineage['parent']['name'], lineage['parent']['domain'], 'spin-off']
        startup['search_blob'] = ' '.join(dict.fromkeys(' '.join(terms).lower().split()))
    return payload
