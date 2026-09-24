"""Project approved audit artifacts into the public timeline, without audit notes."""
import json
import re
from datetime import date as calendar_date
from urllib.parse import urlparse
from lineages import all_events, apply_lineages


def source_label(url):
    host = urlparse(url or '').netloc.removeprefix('www.')
    return 'Wayback Machine' if host == 'web.archive.org' else host or 'Fuente'


def event(phase, kind, title):
    date = phase.get('date')
    url = phase.get('source_url')
    if not re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?', date or '') or not url:
        raise ValueError(f'Approved event without date/source: {title}: {date}, {url}')
    return {'type': kind, 'date': date[:7], 'title': title,
            'prose': phase.get('product_prose') or title,
            'source': f'{source_label(url)} · {date[:7]}', 'source_url': url,
            'quote': '', 'basis': '', 'wayback_url': None}


def apply_audits(payload, data_dir):
    # Editorial exclusion requested by the owner; keep research in the archive.
    payload['startups'] = [s for s in payload['startups'] if s['name'].strip().casefold() != 'fiscoclic']
    identities = {s['name'].strip(): s for s in json.loads((data_dir / 'identity.json').read_text())['startups']}
    contact_file = data_dir / 'audit/contactos-ampliacion-2026-09-14/estado-completo.json'
    contacts = {r['slug']: r for r in json.loads(contact_file.read_text())} if contact_file.exists() else {}
    reviewed = 0
    for startup in payload['startups']:
        ident = identities.get(startup['name'].strip(), {})
        slug = ident.get('slug', '')
        path = data_dir / 'audit' / slug / 'final.json'
        startup['audit_status'] = 'pendiente'
        if not path.exists():
            continue
        final = json.loads(path.read_text())
        verdict = final.get('verdicts') if isinstance(final.get('verdicts'), dict) else {}
        if final.get('global_verdict', verdict.get('global_verdict')) != 'PASS':
            continue
        audit = final['artefacto']
        reviewed += 1
        shutdown = audit.get('shutdown') or {}
        acquired = ident.get('status') == 'acquired' or shutdown.get('basis') == 'acquisition' or bool(shutdown.get('acquirer'))
        # Acquisition is an exit, not a shutdown. Inferred shutdowns must stay distinct.
        startup['status'] = 'adquirida' if acquired else 'cerrada' if shutdown.get('confirmed') else 'inactiva' if shutdown else 'activa'
        startup['audit_status'] = 'revisada'
        startup['reviewed_on'] = final.get('verified_on')
        # A later review may be pending; do not ingest that unapproved candidate.
        for critic in path.parent.glob('tick-*-critic.json'):
            tick = int(critic.name.split('-')[1])
            if tick > final.get('verified_at_tick', verdict.get('tick', 0)):
                result = json.loads(critic.read_text())
                if result.get('global_verdict') == 'RETRY':
                    startup['audit_status'] = 'revision_pendiente'
        events = [event(audit['founding'], 'fundacion', 'Inicio documentado')]
        for phase in audit['phases']:
            typ = phase['type']
            kind = {'funding': 'capital', 'shutdown': 'adquisicion' if acquired else 'cierre' if shutdown.get('confirmed') else 'inactivo'}.get(typ, typ)
            investors = ', '.join(phase.get('investors') or [])
            title = phase.get('title') or (('Programa: ' if phase.get('funding_type') == 'accelerator' else 'Financiamiento: ') + investors if typ == 'funding' else kind.capitalize())
            ev = event(phase, kind, title)
            # Funding details must come from this event's approved evidence, never a standard deal.
            if typ == 'funding':
                amount = phase.get('amount_usd')
                lead = title
                if amount is not None and not re.search(r'\$|USD|US\b', title):
                    lead += f' · US${amount:,.0f}'
                ev['prose'] = f'{lead}. {ev["prose"]}'
            if kind == 'inactivo':
                ev['basis'] = 'Sin confirmación de cierre; fecha de la señal documentada.'
            events.append(ev)
        # Retain a sourced acquisition if the audit records it outside phases (Konstruedu).
        if acquired and not any(e['type'] == 'adquisicion' for e in events):
            events += [e for e in startup['events'] if e['type'] == 'adquisicion' and e.get('source_url')]
        if shutdown and not any(e['type'] in ('cierre', 'inactivo', 'adquisicion') for e in events):
            date = next((shutdown[k] for k in ['date', 'date_upper_bound', 'upper_bound_date', 'last_signal_date', 'last_signal'] if shutdown.get(k)), None)
            if date and shutdown.get('source_url'):
                kind = 'adquisicion' if acquired else 'cierre' if shutdown.get('confirmed') else 'inactivo'
                phrase = 'Adquisición documentada' if acquired else 'Cierre confirmado' if shutdown.get('confirmed') else 'La continuidad de la empresa no está confirmada. Hay señales de inactividad, pero no un anuncio de cierre.'
                ev = event({'date': date, 'source_url': shutdown['source_url'], 'product_prose': phrase}, kind, 'Sin señal reciente' if kind == 'inactivo' else phrase)
                if kind == 'inactivo':
                    ev['basis'] = 'Fecha de una señal de inactividad, no de un cierre confirmado.'
                events.append(ev)
        startup['events'] = sorted(events, key=lambda e: e['date'])
        live = audit.get('live_state') or {}
        startup['current_product'] = live.get('product_prose') or ''
        live_source = next((u for u in live.get('confirmed_by', []) if u.startswith('https://')), None)
        startup['current_source'] = live_source.split()[0] if live_source else None
        contact = contacts.get(slug, {})
        links = []
        if contact.get('cuenta_empresa'):
            h = contact['cuenta_empresa']; links.append({'name': startup['name'], 'handle': h, 'url': 'https://x.com/' + h})
        for person in contact.get('personas', []):
            if person.get('x_handle') and person.get('estado') == 'confirmada':
                h = person['x_handle']; links.append({'name': person['nombre'], 'handle': h, 'url': 'https://x.com/' + h})
        startup['x_profiles'] = links
        # Current brands remain searchable without breaking existing public URLs.
        display = audit.get('display_name')
        if display and display != startup['name'] and display not in startup.get('aliases', []):
            startup.setdefault('aliases', []).append(display)
        startup['search_blob'] += ' ' + ' '.join(audit.get('domains_chain', [])) + ' ' + (display or '').lower()
    apply_lineages(payload)
    dates = [e['date'] for s in payload['startups'] for e in all_events(s)]
    first, last = min(int(d[:4]) for d in dates), max(int(d[:4]) for d in dates)
    payload['meta'].update({'count': len(payload['startups']), 'audited_count': reviewed, 'updated_on': calendar_date.today().isoformat(),
                            'note': 'Trayectorias con fuentes.',
                            'range': {'start': first, 'end': last + 1},
                            'ticks': list(range(first, last + 2, 2))})
    payload['startups'].sort(key=lambda s: min((e['date'] for e in all_events(s)), default='9999'))
    return payload
