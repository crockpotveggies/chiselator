"""Known-answer arithmetic and mutation controls for documentation fixtures."""
import copy
from fractions import Fraction
import unittest

from jsonschema import ValidationError

from validate_analysis_contracts import ROOT, read_bundle, validate_bundle


def fixture_fractions(graph, capture, events, probes):
    """Independent, deliberately small closed-window formula, not an analyzer.

    Only the hand-authored pipeline's complete, nonoverlapping lifecycles are
    supported. Never use this function to generate expected-result.json.
    """
    width = int(capture['window']['end_fs']) - int(capture['window']['start_fs'])
    answer = {}
    for channel in graph['channels']:
        cid = channel['id']
        if channel['sampling_policy'] is not None:
            counts = {c: 0 for c in ('transferred','backpressured','starved','idle')}
            for e in probes:
                if e['kind'] == 'interface.samples' and e['data']['channel_id'] == cid:
                    d = e['data']
                    counts[d['classification']] += int(d['edge_end']) - int(d['edge_start'])
            total = sum(counts.values())
            if not total:
                raise ValueError('fixture oracle has no sampled edges')
            answer[cid] = (Fraction(counts['backpressured'],total), Fraction(counts['starved'],total))
        else:
            lives = {}
            for e in events:
                if e['kind'].startswith('transaction.') and e['data']['channel_id'] == cid:
                    lives.setdefault(e['data']['transaction_id'], {})[e['kind'].split('.')[1]] = int(e['time']['fs'])
            if any(set(v) != {'offer','accept','complete'} for v in lives.values()):
                raise ValueError('fixture oracle needs complete lifecycles')
            waiting = sum(v['accept'] - v['offer'] for v in lives.values())
            occupied = sum(v['complete'] - v['offer'] for v in lives.values())
            answer[cid] = (Fraction(waiting,width), Fraction(width-occupied,width))
    return answer


def check_fixture_candidates(graph, capture, events, result, probes):
    fractions = fixture_fractions(graph,capture,events,probes)
    config = result['configuration']['flow.stage-bottleneck@1']
    bp, starve = [Fraction(int(config[k]['numerator']),int(config[k]['denominator'])) for k in ('input_backpressure','output_starvation')]
    observed = set()
    for node in graph['nodes']:
        inputs = [c['id'] for c in graph['channels'] if c['sink']['node'] == node['id']]
        outputs = [c['id'] for c in graph['channels'] if c['source']['node'] == node['id']]
        if len(inputs) == len(outputs) == 1 and fractions[inputs[0]][0] >= bp and fractions[outputs[0]][1] >= starve:
            observed.add(node['id'])
    expected = {f['scope'] for f in result['findings'] if f['rule'] == 'flow.stage-bottleneck@1'}
    if observed != expected:
        raise ValueError(f'bottleneck classification mismatch: expected {sorted(expected)}, observed {sorted(observed)}')
    return observed


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.graph, self.capture, self.events, self.result, self.probes = copy.deepcopy(read_bundle())

    def check(self):
        return validate_bundle(self.graph, self.capture, self.events, self.result, self.probes)

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


class PipelineTests(unittest.TestCase):
    def bundle(self, form='hybrid'):
        return copy.deepcopy(read_bundle(ROOT / 'docs/examples/pipeline-bottleneck' / form))

    def test_pipeline_hand_arithmetic(self):
        expected = {
            'async': [(Fraction(1,24),Fraction(22,24)),(Fraction(16,24),Fraction(7,24)),(Fraction(1,24),Fraction(22,24)),(Fraction(1,24),Fraction(22,24))],
            'hybrid': [(Fraction(2,24),Fraction(20,24)),(Fraction(5,9),Fraction(1,9)),(Fraction(0,9),Fraction(7,9)),(Fraction(1,24),Fraction(22,24))],
        }
        for form in expected:
            with self.subTest(form=form):
                g,c,e,r,p = self.bundle(form)
                validate_bundle(g,c,e,r,p)
                actual = fixture_fractions(g,c,e,p)
                self.assertEqual([actual[f'c:{i}'] for i in range(4)],expected[form])
                for m in r['metrics']:
                    if m['id'] in ('backpressure-fraction','starvation-fraction'):
                        pos = 0 if m['id']=='backpressure-fraction' else 1
                        self.assertEqual(Fraction(int(m['numerator']),int(m['denominator'])), actual[m['scope']][pos])
                        self.assertEqual(m['censoring'],{'left':'0','right':'0','aborted':'0'})
                self.assertEqual(check_fixture_candidates(g,c,e,r,p), {'n:s2'})

    def test_sample_class_counts_and_pause(self):
        g,c,e,r,p = self.bundle()
        counts = {(cid,cls):0 for cid in ('c:1','c:2') for cls in ('transferred','backpressured','starved','idle')}
        for probe in p:
            if probe['kind']=='interface.samples':
                d=probe['data']
                counts[d['channel_id'],d['classification']] += int(d['edge_end'])-int(d['edge_start'])
        self.assertEqual([counts['c:1',k] for k in ('transferred','backpressured','starved','idle')],[2,5,1,1])
        self.assertEqual([counts['c:2',k] for k in ('transferred','backpressured','starved','idle')],[1,0,7,1])
        self.assertEqual([int(v['time']['fs'])//1_000_000 for v in e if v['kind']=='clock.edge'],[2,4,6,12,14,16,18,20,22])
        for metric in r['metrics']:
            if metric['definition']=='sample-class-count@1':
                self.assertEqual(int(metric['numerator']), counts[metric['scope'],metric['id'].removesuffix('-edges')])
                self.assertEqual(metric['samples'],'9')

    def test_queue_area_from_snapshot(self):
        g,c,e,r,p = self.bundle()
        q = [v for v in p if v['kind'].startswith('queue.')]
        self.assertEqual(q[0]['kind'],'queue.snapshot')
        occupancy = q[0]['data']['occupancy']
        previous, area, full, empty = 0,0,0,0
        for v in q[1:] + [{'time':{'fs':c['window']['end_fs']},'kind':'end'}]:
            now = int(v['time']['fs'])
            area += occupancy * (now-previous)
            full += (now-previous) if occupancy==2 else 0
            empty += (now-previous) if occupancy==0 else 0
            occupancy += 1 if v['kind']=='queue.enqueue' else -1 if v['kind']=='queue.dequeue' else 0
            previous = now
        self.assertEqual((area,full,empty),(40_000_000,18_000_000,2_000_000))
        m = next(m for m in r['metrics'] if m['id']=='mean-occupancy')
        self.assertEqual(Fraction(int(m['numerator']),int(m['denominator'])),Fraction(5,3))

    def test_moved_stage_changes_classification(self):
        g,c,e,r,p = self.bundle('async')
        times = {'c:0':{'offer':0,'accept':16,'complete':17},'c:1':{'offer':17,'accept':18,'complete':19}}
        for event in e:
            cid = event['data']['channel_id']
            if cid in times:
                event['time']['fs'] = str(times[cid][event['kind'].split('.')[1]] * 1_000_000)
        e.sort(key=lambda v:int(v['time']['fs']))
        for i,event in enumerate(e,1): event['seq']=str(i)
        # Move the explicit service-wait observation too; it is not a cause link.
        g['nodes'][1]['wait_vocabulary']='v:synthetic-service'
        c['probes']['coverage']['waits']=['n:s1','n:s3']
        for v in p:
            if v['data']['node_id']=='n:s2':
                v['data']['node_id']='n:s1'
                v['time']['fs']='0' if v['kind']=='wait.begin' else '16000000'
        p.sort(key=lambda v:int(v['time']['fs']))
        for i,v in enumerate(p,1): v['seq']=str(i)
        for m in r['metrics']:
            if m['scope']=='n:s2': m['scope']='n:s1'
        validate_bundle(g,c,e,r,p)  # Valid records; stale expected classification is the only failure below.
        with self.assertRaisesRegex(ValueError, r"bottleneck classification mismatch: expected \['n:s2'\], observed \['n:s1'\]"):
            check_fixture_candidates(g,c,e,r,p)

    def test_sample_on_gated_edge(self):
        g,c,e,r,p = self.bundle()
        next(v for v in e if v['kind']=='clock.state')['data']['state']='paused'
        with self.assertRaisesRegex(ValueError,'sample on paused/gated consumer edge'):
            validate_bundle(g,c,e,r,p)

    def test_dequeue_from_empty_queue(self):
        g,c,e,r,p = self.bundle()
        bad = copy.deepcopy(next(v for v in p if v['kind']=='queue.dequeue'))
        bad.update(seq=str(len(p)+1),time={'fs':'23000000','delta':0,'phase':'active'})
        bad['data']['token_id']='qtoken:never-present'
        p.append(bad)
        with self.assertRaisesRegex(ValueError,'dequeue from empty queue'):
            validate_bundle(g,c,e,r,p)

    def test_undeclared_wait_reason(self):
        g,c,e,r,p = self.bundle()
        for v in p:
            if v['kind'].startswith('wait.') and v['data']['node_id']=='n:s2': v['data']['reason']='invented-from-a-signal-name'
        with self.assertRaisesRegex(ValueError,'undeclared wait reason'):
            validate_bundle(g,c,e,r,p)

    def test_complete_metric_without_probe_coverage(self):
        g,c,e,r,p = self.bundle()
        c['probes']=None
        r['inputs']['probes_sha256']=None
        with self.assertRaisesRegex(ValueError,'probe metric without declared probe coverage'):
            validate_bundle(g,c,e,r,[])

    def test_overlapping_sample_interval(self):
        g,c,e,r,p = self.bundle()
        v=next(v for v in p if v['kind']=='interface.samples' and v['data']['classification']=='backpressured')
        v['data']['edge_start']='1'
        with self.assertRaisesRegex(ValueError,'empty/overlapping sample interval'):
            validate_bundle(g,c,e,r,p)

    def test_queue_over_capacity(self):
        g,c,e,r,p = self.bundle()
        snapshot=next(v for v in p if v['kind']=='queue.snapshot')
        snapshot['data'].update(occupancy=3,tokens=['qtoken:A','qtoken:X','qtoken:Y'])
        with self.assertRaisesRegex(ValueError,'queue occupancy outside capacity'):
            validate_bundle(g,c,e,r,p)

    def test_partial_coverage_cannot_claim_complete_metric(self):
        g,c,e,r,p = self.bundle()
        c['probes']['coverage']['status']='partial'
        with self.assertRaisesRegex(ValueError,'complete probe metric without complete probe coverage'):
            validate_bundle(g,c,e,r,p)

    def test_unknown_wait_cause_remains_legal(self):
        bundle=self.bundle()
        validate_bundle(*bundle)
        g,c,e,r,p=bundle
        self.assertIsNone(next(n for n in g['nodes'] if n['id']=='n:s3')['wait_vocabulary'])
        self.assertEqual({v['data']['reason'] for v in p if v['kind'].startswith('wait.') and v['data']['node_id']=='n:s3'},{'unknown'})

    def test_closed_flow_union_rejects_probe_kind(self):
        g,c,e,r,p=self.bundle()
        e[0]['kind']='queue.snapshot'
        e[0]['data']={'queue_id':'q:middle','occupancy':0,'tokens':[]}
        with self.assertRaises(ValidationError): validate_bundle(g,c,e,r,p)


if __name__ == '__main__':
    unittest.main()
