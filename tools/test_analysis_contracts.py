"""Known-answer arithmetic and mutation controls for documentation fixtures."""
import copy
import unittest

from jsonschema import ValidationError

from validate_analysis_contracts import read_bundle, validate_bundle


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.graph, self.capture, self.events, self.result = copy.deepcopy(read_bundle())

    def check(self):
        return validate_bundle(self.graph, self.capture, self.events, self.result)

    def rejects(self):
        with self.assertRaises((ValueError, ValidationError)):
            self.check()

    def test_known_answer_intervals(self):
        transactions = self.check()
        token = transactions['t:async:0:1']
        self.assertEqual(token['accept'] - token['offer'], 10_000_000)
        self.assertEqual(token['complete'] - token['accept'], 4_000_000)
        self.assertEqual(token['complete'] - token['offer'], 14_000_000)
        self.assertIsNone(transactions['t:clocked:0:1']['offer'])
        expected = {('c:async','accepted-count'): (1,1), ('c:async','completed-count'): (1,1), ('c:async','acceptance-rate'): (1,20_000_000), ('c:async','acceptance-latency'): (10_000_000,1), ('c:async','recovery-latency'): (4_000_000,1), ('c:async','completion-latency'): (14_000_000,1), ('c:clocked','accepted-count'): (1,1)}
        actual = {(m['scope'],m['id']):(int(m['numerator']),int(m['denominator'])) for m in self.result['metrics'] if m['status']=='known'}
        self.assertEqual(actual, expected)

    def test_duplicate_identity(self):
        self.graph['nodes'].append(copy.deepcopy(self.graph['nodes'][0]))
        self.rejects()

    def test_unknown_version(self):
        self.events[0]['schema_version'] = '2.0.0'
        self.rejects()

    def test_dropped_record(self):
        del self.events[2]
        self.rejects()

    def test_future_causal_reference(self):
        self.events[5]['data']['causes'] = ['99']
        self.rejects()

    def test_wrong_boundary_channel(self):
        self.events[5]['data']['destinations'] = ['t:async:0:1']
        self.rejects()

    def test_complete_before_accept(self):
        self.events[6]['kind'] = 'transaction.complete'
        self.rejects()

    def test_false_clock_capture(self):
        self.events[4]['data']['sampling']['edge_index'] = '4'
        self.rejects()

    def test_stale_epoch(self):
        self.events[6]['data']['epoch'] = '1'
        self.rejects()

    def test_time_reversal(self):
        self.events[6]['time']['fs'] = '1'
        self.rejects()

    def test_complete_with_gap(self):
        self.capture['coverage']['gaps'] = [{'start_fs':'0','end_fs':'1','reason':'lost'}]
        self.rejects()

    def test_unknown_is_not_zero(self):
        self.result['metrics'][-1]['numerator'] = '0'
        self.rejects()

    def test_float_timestamp(self):
        self.events[0]['time']['fs'] = 2_000_000.0
        self.rejects()

    def test_above_javascript_integer_precision(self):
        offset = 2**53 + 1
        for event in self.events:
            event['time']['fs'] = str(int(event['time']['fs']) + offset)
        # Shared window objects from JSON are independent; update all explicitly.
        for window in [self.capture['window'],self.result['window']] + [m['window'] for m in self.result['metrics']]:
            for field in ('start_fs','end_fs'):
                window[field] = str(int(window[field]) + offset)
        transactions = self.check()
        token = transactions['t:async:0:1']
        self.assertEqual(token['offer'], offset + 2_000_000)
        self.assertEqual(token['complete'] - token['offer'], 14_000_000)


if __name__ == '__main__':
    unittest.main()
