import unittest
from copy import deepcopy

from lineages import all_events, apply_lineages


class LineageTests(unittest.TestCase):
    def payload(self):
        events = [{'date': date, 'type': kind, 'source_url': f'https://example.org/{date}', 'prose': date}
                  for date, kind in [('2021-01', 'fundacion'), ('2021-09', 'capital'), ('2022-01', 'capital'), ('2022-06', 'pivot')]]
        return {'startups': [{'name': 'Salduu', 'events': events, 'aliases': ['Profe Social'], 'search_blob': 'salduu profe social'},
                             {'name': 'Other', 'events': [], 'aliases': []}]}

    def test_parent_history_is_preserved_and_not_attributed_to_child(self):
        payload = self.payload()
        original = deepcopy(payload)
        apply_lineages(payload)
        salduu = payload['startups'][0]
        self.assertEqual(salduu['lineage']['parent']['events'], original['startups'][0]['events'][:3])
        self.assertEqual([e['type'] for e in salduu['events']], ['spinoff'])
        self.assertEqual(len(all_events(salduu)), 4)
        self.assertEqual(salduu['aliases'], [])
        self.assertIn('profe.social', salduu['search_blob'])
        self.assertEqual(payload['startups'][1], original['startups'][1])
        self.assertEqual(salduu['lineage']['date_precision'], 'first_documented')

    def test_reapplying_does_not_duplicate_or_lose_sources(self):
        payload = apply_lineages(self.payload())
        previous = deepcopy(payload)
        self.assertEqual(apply_lineages(payload), previous)
        # Rebuilding the approved audit restores the original four events.
        payload['startups'][0]['events'] = self.payload()['startups'][0]['events']
        self.assertEqual(apply_lineages(payload), previous)

    def test_changed_audit_evidence_requires_review(self):
        payload = self.payload()
        payload['startups'][0]['events'].pop(1)
        with self.assertRaisesRegex(ValueError, 'Missing parent evidence'):
            apply_lineages(payload)
        # A fresh audit must not silently borrow evidence from the old lineage.
        previous = apply_lineages(self.payload())
        previous['startups'][0]['events'] = payload['startups'][0]['events']
        with self.assertRaisesRegex(ValueError, 'Missing parent evidence'):
            apply_lineages(previous)

    def test_separate_events_in_same_month_keep_both_sources(self):
        payload = self.payload()
        second = deepcopy(payload['startups'][0]['events'][1])
        second['source_url'] = 'https://example.org/second-source'
        payload['startups'][0]['events'].append(second)
        apply_lineages(payload)
        self.assertEqual(len(all_events(payload['startups'][0])), 5)
        self.assertIn(second, payload['startups'][0]['lineage']['parent']['events'])


if __name__ == '__main__':
    unittest.main()
