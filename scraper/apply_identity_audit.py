"""Apply the status corrections accepted in IDENTITY_DEFECTS.md.

Run on the workspace dataset; does not mutate audit verdicts or other checkouts.
The source records remain in data/audit/<slug>/final.json.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / 'data/identity.json'
data = json.loads(path.read_text())
rows = {s['slug']: s for s in data['startups']}
changed = []
for slug in ('crema', 'gopa', 'nodek', 'sendmage', 'grandpa', 'telaio', 'trutix', 'signature-api'):
    final = json.loads((ROOT / f'data/audit/{slug}/final.json').read_text())
    verdict = final.get('global_verdict', (final.get('verdicts') or {}).get('global_verdict'))
    assert verdict == 'PASS', slug
    audit = final['artefacto']
    shutdown = audit.get('shutdown')
    row = rows[slug]
    before = json.dumps(row, sort_keys=True)
    if shutdown:
        row['status'] = 'shutdown'
        row['shutdown_basis'] = 'confirmed' if shutdown['confirmed'] else 'inferred'
        label = 'Cierre confirmado.' if shutdown['confirmed'] else 'Sin señal reciente; cierre no confirmado.'
        row['status_detail'] = f"{label} {shutdown['basis']} Fuente: {shutdown['source_url']}"
    else:
        row['status'] = 'active'
        row.pop('shutdown_basis', None)
        row['status_detail'] = 'SignatureAPI sigue operando; Superposition Labs coexiste con el producto. Fuentes: https://signatureapi.com/ y https://superposition.company/; data/audit/signature-api/final.json.'
    if slug == 'nodek':
        if not any(d['domain'] == 'nodek.co' for d in row['domains']):
            row['domains'].insert(0, {
                'domain': 'nodek.co', 'archived': True, 'confirmed': True,
                'role': 'primary / original', 'first_snapshot': '20211219',
                'source': audit['founding']['source_url'],
                'note': 'Primer dominio. Redirección archivada desde 2021-12-19; primer cuerpo 2022-01-06. Marketplace mayorista hasta 2024-04. No es una señal de actividad actual.'
            })
        row['chain'] = ['nodek.co (2021-12 → 2024-04)', 'nodekbrands.com (desde 2024-04; sin registro ni DNS al 2026-09-23)']
        row['domains'][-1]['note'] = audit['live_state']['product_prose']
    if slug == 'sendmage':
        row['domains'][0]['note'] = 'Eras ajenas: 2014-2015 SendMage de envíos masivos; 2016-2018 Dermal Response; 2019 parking y lotería. No pertenecen a esta startup. Era propia documentada desde 2023-11. Último cuerpo 2025-02-23; registro nuevo 2025-11-07 y sin DNS al 2026-09-23. Cierre no confirmado. Fuente: data/audit/sendmage/final.json.'
    if slug in ('crema', 'gopa'):
        row['domains'][0]['note'] = audit['live_state']['product_prose']
        row['chain'] = audit['domains_chain']
    if slug == 'grandpa':
        row['chain'][-1] = 'Jun 2026: dominio aparcado en venta, sin anuncio de cierre. Spaceship en la captura de junio; GoDaddy/Afternic en la revisión de septiembre. Cierre inferido, no confirmado.'
        for domain in row['domains']:
            domain['note'] = domain.get('note', '').replace('= shutdown.', '= señal de inactividad, no cierre confirmado.')
    if slug == 'telaio':
        row['domains'] = [d for d in row['domains'] if d['domain'] != 'lummy.ai']
        if not any(d['domain'] == 'kapibara.cl' for d in row['domains']):
            row['domains'].insert(1, {'domain': 'kapibara.cl', 'confirmed': True, 'role': 'intermediate', 'source': 'data/audit/telaio/final.json'})
        row['chain'] = audit['domains_chain']
    if slug == 'trutix':
        row['chain'][-1] = {'date': '2026-02', 'event': 'Cierre anunciado por el CEO el 2026-02-17 y corroborado por el CTO.', 'source': shutdown['source_url']}
        for d in row['domains']:
            d['role'] = 'historical product domain'
            d['note'] = audit['live_state']['product_prose']
    if json.dumps(row, sort_keys=True) != before:
        changed.append(slug)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'changed': changed}, ensure_ascii=False))
