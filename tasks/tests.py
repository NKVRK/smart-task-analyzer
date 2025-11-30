from django.test import TestCase
from .scoring import calculate_scores, detect_cycles

class ScoringTests(TestCase):

    def test_past_due_boost(self):
        tasks = [
            {"id":"a","title":"old","due_date":"2000-01-01","importance":5,"estimated_hours":2,"dependencies":[]},
            {"id":"b","title":"future","due_date":"2099-01-01","importance":10,"estimated_hours":1,"dependencies":[]}
        ]
        res = calculate_scores(tasks)
        scores = {t['id']: t['score'] for t in res['analyzed_tasks']}
        self.assertIn('a', scores)
        self.assertIn('b', scores)
        self.assertTrue(scores['a'] > 0)

    def test_cycle_detection(self):
        tasks = [
            {"id":"t1","dependencies":["t2"]},
            {"id":"t2","dependencies":["t1"]},
            {"id":"t3","dependencies":[]}
        ]
        cycles = detect_cycles(tasks)
        self.assertTrue(any('t1' in c and 't2' in c for c in cycles))

    def test_missing_fields_default(self):
        tasks = [
            {"id":"x"}
        ]
        res = calculate_scores(tasks)
        t = res['analyzed_tasks'][0]
        self.assertEqual(t['importance'], 5)
        self.assertIn('score_breakdown', t)
