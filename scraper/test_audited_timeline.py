import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from audited_timeline import apply_audits


class AuditProjectionTests(unittest.TestCase):
    def project(self, shutdown=None, status='active', legacy=False, retry=False):
        with TemporaryDirectory() as tmp:
            data = Path(tmp)
            (data / 'identity.json').write_text(json.dumps({'startups': [{'name': 'Example', 'slug': 'example', 'status': status}]}))
            directory = data / 'audit/example'
            directory.mkdir(parents=True)
            phase = {'type': 'funding', 'date': '2024-03', 'source_url': 'https://example.org/program', 'product_prose': 'Producto probado.', 'investors': ['Programa'], 'funding_type': 'accelerator', 'amount_usd': None}
            artifact = {'founding': {'date': '2016-01', 'source_url': 'https://example.org/origin', 'product_prose': 'Inicio.'}, 'phases': [phase], 'shutdown': shutdown, 'live_state': {}, 'domains_chain': []}
            final = {'artefacto': artifact, 'verdicts': {'global_verdict': 'PASS', 'tick': 1}} if legacy else {'artefacto': artifact, 'global_verdict': 'PASS', 'verified_at_tick': 1}
            (directory / 'final.json').write_text(json.dumps(final))
            if retry:
                (directory / 'tick-2-critic.json').write_text(json.dumps({'global_verdict': 'RETRY'}))
                (directory / 'tick-2.json').write_text(json.dumps({'phases': [{'title': 'NO PUBLICAR'}]}))
            payload = {'meta': {}, 'startups': [{'name': 'Example', 'events': [], 'search_blob': '', 'aliases': []}]}
            return apply_audits(payload, data)

    def test_new_funding_is_created_without_a_legacy_event_or_standard_amount(self):
        result = self.project()
        events = result['startups'][0]['events']
        self.assertEqual([e['type'] for e in events], ['fundacion', 'capital'])
        self.assertNotIn('$', events[1]['prose'])
        self.assertEqual(result['meta']['range']['start'], 2016)

    def test_inferred_shutdown_is_not_published_as_confirmed(self):
        result = self.project({'confirmed': False, 'date_upper_bound': '2025-08', 'source_url': 'https://example.org/parked'})['startups'][0]
        self.assertEqual(result['status'], 'inactiva')
        self.assertEqual(result['events'][-1]['type'], 'inactivo')

    def test_acquisition_is_not_a_shutdown(self):
        result = self.project({'confirmed': True, 'basis': 'acquisition', 'date': '2025-08', 'source_url': 'https://example.org/acquired'})['startups'][0]
        self.assertEqual(result['status'], 'adquirida')
        self.assertEqual(result['events'][-1]['type'], 'adquisicion')

    def test_legacy_approved_schema_is_included(self):
        self.assertEqual(self.project(legacy=True)['meta']['audited_count'], 1)

    def test_later_retry_is_flagged_and_not_ingested(self):
        result = self.project(retry=True)['startups'][0]
        self.assertEqual(result['audit_status'], 'revision_pendiente')
        self.assertNotIn('NO PUBLICAR', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
