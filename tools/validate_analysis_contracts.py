"""Validate the draft documentation bundle, not RTL or production decoders."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'docs/schemas'
EXAMPLE = ROOT / 'docs/examples/hybrid-flow'
MAX_TIME = 2**63 - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(records, field='id'):
    result = {record[field]: record for record in records}
    require(len(result) == len(records), f'duplicate {field}')
    return result


def validate_shape(name, value):
    schema = json.loads((SCHEMAS / f'{name}.schema.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)


def validate_bundle(graph, capture, events, result=None, probes=None):
    """Selected cross-record invariants. Raw protocol/phase qualification is separate."""
    validate_shape('design-graph', graph)
    validate_shape('capture-manifest', capture)
    if result is not None:
        validate_shape('analysis-result', result)
    domains = unique(graph['domains'])
    nodes = unique(graph['nodes'])
    channels = unique(graph['channels'])
    boundaries = unique(graph['boundaries'])
    vocabularies = unique(graph['wait_vocabularies'])
    queues = unique(graph['queues'])
    require(capture['graph_id'] == graph['graph_id'], 'graph identity mismatch')
    lo, hi = (int(capture['window'][k]) for k in ('start_fs', 'end_fs'))
    require(0 <= lo < hi <= MAX_TIME, 'invalid capture window')
    coverage = capture['coverage']
    require(set(coverage['channels']) <= channels.keys(), 'unknown coverage channel')
    require(len(set(coverage['channels'])) == len(coverage['channels']), 'duplicate coverage channel')
    require(coverage['initial_state'] == 'known-idle', 'draft checker needs known-idle initial state')
    require(coverage['status'] != 'complete' or not coverage['gaps'], 'complete capture contains gaps')

    def domain(id, kind):
        require(id in domains and domains[id]['kind'] == kind, f'unknown/wrong {kind} domain: {id}')

    for node in nodes.values():
        require(set(node['domains']) <= domains.keys(), 'unknown node domain')
        unique(node['ports'])
        require(node['wait_vocabulary'] is None or node['wait_vocabulary'] in vocabularies, 'unknown wait vocabulary')
    for vocabulary in vocabularies.values():
        require('unknown' not in vocabulary['reasons'], 'unknown is reserved, not a vocabulary reason')
    for channel in channels.values():
        domain(channel['reset_domain'], 'reset')
        if 'clock_domain' in channel:
            domain(channel['clock_domain'], 'clock')
        policy = channel['sampling_policy']
        if channel['protocol'].startswith('rv.'):
            require(policy is not None and policy['domain_id'] == channel['clock_domain'], 'missing/wrong consumer sampling policy')
            require(domains[policy['domain_id']]['edge'] == policy['edge'], 'sampling edge polarity mismatch')
        else:
            require(policy is None, 'async channel has a sampling policy')
        for key, direction in [('source', 'output'), ('sink', 'input')]:
            end = channel[key]
            require(end['node'] in nodes, 'unknown endpoint node')
            ports = unique(nodes[end['node']]['ports'])
            require(end['port'] in ports and ports[end['port']]['direction'] == direction, 'invalid endpoint port')
    for boundary in boundaries.values():
        require(boundary['node'] in nodes, 'unknown boundary node')
        require(set(boundary['inputs'] + boundary['outputs']) <= channels.keys(), 'unknown boundary channel')
        domain(boundary['reset_domain'], 'reset')
        domain(boundary['effect_reset_domain'], 'reset')
    for queue in queues.values():
        require(queue['owner_node'] in nodes, 'unknown queue owner')
        cid = queue['channel_id']
        require(cid is None or cid in channels, 'unknown queue channel')
        cap = channels[cid]['capacity_tokens'] if cid else None
        require(cap is None or queue['capacity_tokens'] is None or cap == queue['capacity_tokens'], 'conflicting queue capacity')
        require(cap is not None or queue['capacity_tokens'] is not None, 'queue capacity unavailable')

    transactions = {}
    identities = set()
    last_ordinals = {}
    epochs = {id: 0 for id, d in domains.items() if d['kind'] == 'reset'}
    clock_edges = {}
    edge_records, clock_states, state_records = {}, {}, {}
    effects = set()
    previous_time = -1
    for index, event in enumerate(events, 1):
        validate_shape('flow-event', event)
        require(event['seq'] == str(index), 'noncontiguous sequence')
        require(event['graph_id'] == graph['graph_id'] and event['run_id'] == capture['run_id'], 'event identity mismatch')
        time = int(event['time']['fs'])
        require(lo <= time < hi and time <= MAX_TIME and time >= previous_time, 'event time outside range/order')
        require(coverage['phase_precision'] != 'exact' or event['time']['phase'] != 'unknown', 'unknown phase in exact capture')
        previous_time = time
        kind, data = event['kind'], event['data']
        for cause in data.get('causes', []):
            require(0 < int(cause) < index, 'missing/future causal event')
        if kind.startswith('transaction.'):
            id, channel_id = data['transaction_id'], data['channel_id']
            require(channel_id in channels and channel_id in coverage['channels'], 'unknown/uncovered channel')
            channel = channels[channel_id]
            protocol = channel['protocol']
            # Other declared protocols require their own reference fixtures and checks.
            require(protocol in ('bd.four-phase.held-return@1', 'rv.sampled@1'), 'protocol outside draft semantic checker')
            identity = (channel_id, data['epoch'], data['ordinal'])
            if kind != 'transaction.abort':
                require(int(data['epoch']) == epochs[channel['reset_domain']], 'stale transaction epoch')
            if kind in ('transaction.offer', 'transaction.transfer'):
                require(id not in transactions and identity not in identities, 'duplicate transaction identity')
                key = identity[:2]
                require(int(data['ordinal']) > last_ordinals.get(key, 0), 'nonincreasing transaction ordinal')
                last_ordinals[key] = int(data['ordinal'])
                identities.add(identity)
                require((kind == 'transaction.transfer') == (protocol == 'rv.sampled@1'), 'wrong lifecycle for protocol')
                if kind == 'transaction.offer':
                    require(not any(t['identity'][0] == channel_id and t['state'] in ('offered', 'accepted') for t in transactions.values()), 'multiple outstanding four-phase transactions')
                else:
                    sampling = data['sampling']
                    require(sampling['domain_id'] == channel['clock_domain'], 'wrong sampling clock')
                    require(clock_edges.get(sampling['domain_id']) == (int(sampling['edge_index']), time), 'transfer without actual clock edge')
                transactions[id] = {'identity': identity, 'state': 'complete' if kind == 'transaction.transfer' else 'offered', 'offer': None if kind == 'transaction.transfer' else time, 'accept': time if kind == 'transaction.transfer' else None, 'complete': time if kind == 'transaction.transfer' else None}
            else:
                require(id in transactions, 'unknown transaction')
                transaction = transactions[id]
                require(transaction['identity'] == identity, 'transaction identity changed')
                if kind == 'transaction.accept':
                    require(transaction['state'] == 'offered', 'accept outside offered state')
                    transaction.update(state='accepted', accept=time)
                elif kind == 'transaction.complete':
                    require(transaction['state'] == 'accepted', 'complete before accept')
                    transaction.update(state='complete', complete=time)
                else:
                    require(transaction['state'] in ('offered', 'accepted'), 'abort outside active state')
                    transaction['state'] = 'aborted'
        elif kind == 'clock.edge':
            domain(data['domain_id'], 'clock')
            prior = clock_edges.get(data['domain_id'], (0, 0))[0]
            require(int(data['edge_index']) > prior, 'nonincreasing clock edge')
            pc = capture['probes']['coverage'] if capture['probes'] else None
            sampled_domains = {channels[c]['sampling_policy']['domain_id'] for c in pc['samples'] if c in channels and channels[c]['sampling_policy'] is not None} if pc else set()
            if prior and pc and pc['status'] == 'complete' and data['domain_id'] in sampled_domains:
                require(int(data['edge_index']) == prior + 1, 'noncontiguous consumer edges in complete probe capture')
            clock_edges[data['domain_id']] = (int(data['edge_index']), time)
            edge_records[(data['domain_id'], int(data['edge_index']))] = (event, clock_states.get(data['domain_id']))
        elif kind == 'clock.state':
            domain(data['domain_id'], 'clock')
            old = clock_states.get(data['domain_id'])
            if old is not None:
                before = state_records[old]['data']['managed_generation']
                after = data['managed_generation']
                require((before is None) == (after is None), 'clock generation availability changed')
                require(before is None or int(after) >= int(before), 'clock generation reversed')
            clock_states[data['domain_id']] = event['seq']
            state_records[event['seq']] = event
        elif kind == 'boundary.link':
            require(data['boundary_id'] in boundaries, 'unknown boundary')
            boundary = boundaries[data['boundary_id']]
            sources, targets = data['sources'], data['destinations']
            require(len(set(sources)) == len(sources) and len(set(targets)) == len(targets) and not set(sources) & set(targets), 'duplicate/self lineage')
            for ids, ports in [(sources, boundary['inputs']), (targets, boundary['outputs'])]:
                require(all(id in transactions and transactions[id]['identity'][0] in ports for id in ids), 'invalid boundary lineage')
            relation = data['relation']
            if relation in ('forward', 'convert', 'select'):
                valid_cardinality = len(sources) == len(targets) == 1
            elif relation == 'fork':
                valid_cardinality = len(sources) == 1 and len(targets) > 1
            else:
                valid_cardinality = len(sources) > 1 and len(targets) == 1
            require(valid_cardinality, 'wrong relation cardinality')
        elif kind == 'effect.commit':
            require(data['effect_id'] not in effects, 'duplicate effect')
            effects.add(data['effect_id'])
            require(data['owner_node'] in nodes, 'unknown effect owner')
            domain(data['reset_domain'], 'reset')
            require(int(data['epoch']) == epochs[data['reset_domain']], 'stale effect epoch')
            require(all(t in transactions for t in data['transactions']), 'unknown effect transaction')
            # This kit does not certify retained ownership after reset.
            require(all(transactions[t]['state'] != 'aborted' for t in data['transactions']), 'retained effect needs a separate qualified ownership checker')
        elif kind == 'domain.reset':
            domain(data['domain_id'], 'reset')
            require(int(data['new_epoch']) == epochs[data['domain_id']] + 1, 'invalid reset epoch')
            epochs[data['domain_id']] += 1
        elif kind == 'coverage.gap':
            require(coverage['status'] == 'partial', 'unreported gap in complete capture')
            require(time <= int(data['end_fs']) <= hi, 'invalid gap interval')

    for transaction in transactions.values():
        channel_id, epoch, _ = transaction['identity']
        if transaction['state'] in ('offered', 'accepted'):
            require(int(epoch) == epochs[channels[channel_id]['reset_domain']], 'old-epoch transaction left open')
    validate_probes(graph, capture, probes or [], edge_records, state_records, events)
    if result is not None:
        require(result['run_id'] == capture['run_id'] and result['graph_id'] == graph['graph_id'], 'result identity mismatch')
        require(result['window'] == capture['window'], 'fixture result window mismatch')
        require(result['inputs'] == {'graph_sha256':capture['graph']['sha256'],'events_sha256':capture['events']['sha256'],'probes_sha256':capture['probes']['artifact']['sha256'] if capture['probes'] else None}, 'result input hashes mismatch')
        require(result['status'] != 'COMPLETE' or coverage['status'] == 'complete', 'complete result from partial capture')
        keys = [(m['scope'],m['id']) for m in result['metrics']]
        require(len(set(keys)) == len(keys), 'duplicate scoped metric')
        for metric in result['metrics']:
            require(metric['scope'] in channels or metric['scope'] in queues or metric['scope'] in nodes, 'unknown metric scope')
            require(metric['window'] == capture['window'], 'metric window mismatch')
            require(metric['status'] != 'known' or metric['coverage'] != 'unavailable', 'known metric with unavailable coverage')
            if metric['definition'].startswith('async-'):
                require(metric['coverage'] != 'complete' or (metric['scope'] in coverage['channels'] and coverage['status'] == 'complete'), 'async metric without complete flow coverage')
            if metric['definition'].startswith(('sample-', 'queue-', 'wait-')):
                pc = capture['probes']['coverage'] if capture['probes'] else None
                category = 'samples' if metric['definition'].startswith('sample-') else 'queues' if metric['definition'].startswith('queue-') else 'waits'
                covered = pc is not None and metric['scope'] in pc[category]
                require(metric['status'] != 'known' or covered, 'probe metric without declared probe coverage')
                require(metric['coverage'] != 'complete' or (covered and pc['status'] == 'complete'), 'complete probe metric without complete probe coverage')
                if category == 'samples' and metric['status'] == 'known':
                    count = sum(int(p['data']['edge_end'])-int(p['data']['edge_start']) for p in probes or [] if p['kind']=='interface.samples' and p['data']['channel_id']==metric['scope'])
                    require(int(metric['samples']) == count, 'sample metric count mismatch')
                    if metric['unit'] == 'fraction':
                        require(count > 0, 'sample fraction unavailable without edges')
                        require(int(metric['denominator']) == count, 'sample fraction denominator must count edges')
        metric_map = {(m['scope'], m['id']): m for m in result['metrics']}
        for finding in result['findings']:
            if finding['rule'] == 'flow.stage-bottleneck@1':
                require(finding['scope'] in nodes, 'unknown bottleneck stage')
                require(finding['rule'] in result['configuration'], 'missing bottleneck configuration')
                node = finding['scope']
                inputs = [c['id'] for c in channels.values() if c['sink']['node'] == node]
                outputs = [c['id'] for c in channels.values() if c['source']['node'] == node]
                require(len(inputs) == len(outputs) == 1, 'bottleneck rule requires single input and output')
                required_refs = {(inputs[0], 'backpressure-fraction'), (outputs[0], 'starvation-fraction')}
                refs = {(r['scope'], r['id']) for r in finding['metric_refs']}
                require(required_refs <= refs <= metric_map.keys(), 'missing bottleneck metric evidence')
                for key in required_refs:
                    metric = metric_map[key]
                    require(metric['status'] == 'known' and metric['coverage'] == 'complete', 'bottleneck candidate needs complete known metrics')
                config = result['configuration'][finding['rule']]
                for key in ('input_backpressure', 'output_starvation'):
                    require(int(config[key]['numerator']) <= int(config[key]['denominator']), 'threshold outside zero to one')
    return transactions


def validate_probes(graph, capture, probes, edges, states, events):
    """Validate normalized records only; this is not a raw-probe decoder."""
    declaration = capture['probes']
    if declaration is None:
        require(not probes, 'probe stream without manifest coverage')
        return
    coverage = declaration['coverage']
    require(not any(e['kind'] == 'domain.reset' for e in events), 'probe reset snapshots outside draft checker')
    channels, nodes, queues = (unique(graph[k]) for k in ('channels','nodes','queues'))
    vocab = unique(graph['wait_vocabularies'])
    lo, hi = (int(capture['window'][k]) for k in ('start_fs','end_fs'))
    for category, table in [('samples',channels),('queues',queues),('waits',nodes)]:
        require(set(coverage[category]) <= table.keys(), 'unknown probe coverage scope')
    require(coverage['status'] != 'complete' or not coverage['gaps'], 'complete probe coverage contains gaps')
    require(not coverage['waits'] or coverage['status'] != 'complete' or coverage['initial_wait_state'] == 'known-idle', 'complete waits need known initial state')
    for gap in coverage['gaps']:
        require(lo <= int(gap['start_fs']) < int(gap['end_fs']) <= hi, 'invalid manifest probe gap')
    if coverage['status'] == 'complete':
        for cid in coverage['samples']:
            policy = channels[cid]['sampling_policy']
            require(policy is not None, 'sample coverage on async channel')
            require(any(s['data']['domain_id']==policy['domain_id'] and int(s['time']['fs'])==lo for s in states.values()), 'complete samples need initial clock state')
    sampled, previous_end, occupancy, waits, seen_waits = {}, {}, {}, {}, set()
    snapshots, seen_tokens = set(), {}
    previous_time = lo
    transfers = {(e['data']['channel_id'], int(e['data']['sampling']['edge_index'])) for e in events if e['kind'] == 'transaction.transfer'}
    for index, event in enumerate(probes, 1):
        validate_shape('probe-event', event)
        require(event['seq'] == str(index), 'noncontiguous probe sequence')
        require(event['graph_id'] == graph['graph_id'] and event['run_id'] == capture['run_id'], 'probe identity mismatch')
        t = int(event['time']['fs'])
        require(lo <= t < hi and t >= previous_time, 'probe time outside range/order')
        require(coverage['phase_precision'] != 'exact' or event['time']['phase'] != 'unknown', 'unknown phase in exact probe capture')
        previous_time = t
        kind, d = event['kind'], event['data']
        if kind == 'interface.samples':
            cid = d['channel_id']
            require(cid in coverage['samples'], 'sample without declared probe coverage')
            policy = channels[cid]['sampling_policy']
            require(policy is not None and d['domain_id'] == policy['domain_id'], 'sample on undeclared consumer clock')
            start, end = int(d['edge_start']), int(d['edge_end'])
            require(start < end and start >= previous_end.get(cid, 0), 'empty/overlapping sample interval')
            previous_end[cid] = end
            ref = d['clock_state_seq']
            require(ref in states and states[ref]['data']['domain_id'] == d['domain_id'], 'invalid clock state reference')
            state = states[ref]['data']
            require(state['state'] == 'running', 'sample on paused/gated consumer edge')
            # Bound work by recorded edges, not an untrusted ordinal range.
            selected = [(i, e, s) for (dom, i), (e, s) in edges.items() if dom == d['domain_id'] and start <= i < end]
            require(len(selected) == end - start, 'sample without actual consumer edge')
            require(all(s == ref for _, _, s in selected), 'sample spans a clock state change')
            require(t == max(int(e['time']['fs']) for _, e, _ in selected), 'sample interval must close at its last edge')
            for i, _, _ in selected:
                require(((cid, i) in transfers) == (d['classification'] == 'transferred'), 'sample/transfer mismatch')
                sampled.setdefault(cid, set()).add(i)
        elif kind.startswith('queue.'):
            qid = d['queue_id']
            require(qid in coverage['queues'], 'queue without declared probe coverage')
            queue = queues[qid]
            cap = queue['capacity_tokens']
            if cap is None:
                cap = channels[queue['channel_id']]['capacity_tokens']
            if kind == 'queue.snapshot':
                require(t == lo and qid not in snapshots, 'snapshot must appear once at capture start')
                require(d['occupancy'] == len(d['tokens']), 'snapshot occupancy/token mismatch')
                occupancy[qid] = list(d['tokens'])
                seen_tokens[qid] = set(d['tokens'])
                snapshots.add(qid)
            else:
                require(qid in occupancy, 'queue operation without known snapshot/state')
                token = d['token_id']
                if kind == 'queue.enqueue':
                    require(token not in seen_tokens[qid], 'duplicate queue token identity')
                    seen_tokens[qid].add(token)
                    occupancy[qid].append(token)
                else:
                    require(bool(occupancy[qid]), 'dequeue from empty queue')
                    require(token in occupancy[qid], 'dequeue of unknown queue token')
                    require(queue['ordering'] != 'fifo' or occupancy[qid][0] == token, 'FIFO token order mismatch')
                    occupancy[qid].remove(token)
            require(0 <= len(occupancy[qid]) <= cap, 'queue occupancy outside capacity')
        elif kind.startswith('wait.'):
            node, reason, wid = d['node_id'], d['reason'], d['wait_id']
            require(node in coverage['waits'], 'wait without declared probe coverage')
            ref = nodes[node]['wait_vocabulary']
            require(reason == 'unknown' or (ref is not None and reason in vocab[ref]['reasons']), 'undeclared wait reason')
            if kind == 'wait.begin':
                require(wid not in seen_waits, 'duplicate wait identity')
                seen_waits.add(wid)
                waits[wid] = (node, reason, t)
            else:
                require(wid in waits and waits[wid][:2] == (node, reason), 'unmatched wait end')
                require(waits[wid][2] <= t, 'reversed wait interval')
                del waits[wid]
        else:
            require(coverage['status'] == 'partial', 'probe gap in complete coverage')
            require(t < int(d['end_fs']) <= hi, 'invalid probe gap interval')
            for category in ('samples','queues','waits'):
                require(set(d[category]) <= set(coverage[category]), 'uncovered probe gap scope')
            require(any(int(g['start_fs']) <= t and int(d['end_fs']) <= int(g['end_fs']) for g in coverage['gaps']), 'probe gap missing from manifest')
            for qid in d['queues']:
                occupancy.pop(qid, None)
    if coverage['status'] == 'complete':
        require(set(coverage['queues']) <= snapshots, 'complete queue coverage needs starting snapshot')
        for cid in coverage['samples']:
            policy = channels[cid]['sampling_policy']
            require(policy is not None, 'sample coverage on async channel')
            actual = {i for (dom,i) in edges if dom == policy['domain_id']}
            require(sampled.get(cid, set()) == actual, 'complete sample coverage omits consumer edges')


def read_bundle(directory=EXAMPLE):
    capture = json.loads((directory / 'capture-manifest.json').read_text(encoding='utf-8'))
    descriptors = [capture['graph'], capture['events']]
    if capture['probes'] is not None:
        descriptors.append(capture['probes']['artifact'])
    for descriptor in descriptors:
        path = (directory / descriptor['path']).resolve()
        require(path.is_relative_to(directory.resolve()), 'artifact path escapes bundle')
        content = path.read_bytes()
        require(len(content) == int(descriptor['bytes']), 'artifact size mismatch')
        require(hashlib.sha256(content).hexdigest() == descriptor['sha256'], 'artifact hash mismatch')
    graph = json.loads((directory / capture['graph']['path']).read_text(encoding='utf-8'))
    events = [json.loads(line) for line in (directory / capture['events']['path']).read_text(encoding='utf-8').splitlines()]
    result = json.loads((directory / 'expected-result.json').read_text(encoding='utf-8'))
    probes = [] if capture['probes'] is None else [json.loads(line) for line in (directory / capture['probes']['artifact']['path']).read_text(encoding='utf-8').splitlines()]
    return graph, capture, events, result, probes


def main():
    for path in SCHEMAS.glob('*.schema.json'):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding='utf-8')))
    bundles = [EXAMPLE, ROOT / 'docs/examples/pipeline-bottleneck/async', ROOT / 'docs/examples/pipeline-bottleneck/hybrid']
    for directory in bundles:
        bundle = read_bundle(directory)
        validate_bundle(*bundle)
        print(f'Validated {directory.relative_to(ROOT)}: {len(bundle[2])} flow and {len(bundle[4])} probe records.')
    validate_shape('plugin-manifest', json.loads((EXAMPLE / 'plugin-manifest.json').read_text(encoding='utf-8')))
    print('Validated 6 draft schemas, three bundles and the example plugin manifest.')
    print('Documentation contract checks only; no RTL simulation or complete decoder qualification.')


if __name__ == '__main__':
    main()
