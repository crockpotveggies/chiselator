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


def validate_bundle(graph, capture, events, result=None):
    """Selected cross-record invariants. Raw protocol/phase qualification is separate."""
    validate_shape('design-graph', graph)
    validate_shape('capture-manifest', capture)
    if result is not None:
        validate_shape('analysis-result', result)
    domains = unique(graph['domains'])
    nodes = unique(graph['nodes'])
    channels = unique(graph['channels'])
    boundaries = unique(graph['boundaries'])
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
    for channel in channels.values():
        domain(channel['reset_domain'], 'reset')
        if 'clock_domain' in channel:
            domain(channel['clock_domain'], 'clock')
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

    transactions = {}
    identities = set()
    last_ordinals = {}
    epochs = {id: 0 for id, d in domains.items() if d['kind'] == 'reset'}
    clock_edges = {}
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
            clock_edges[data['domain_id']] = (int(data['edge_index']), time)
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
    if result is not None:
        require(result['run_id'] == capture['run_id'] and result['graph_id'] == graph['graph_id'], 'result identity mismatch')
        require(result['window'] == capture['window'], 'fixture result window mismatch')
        require(result['inputs'] == {'graph_sha256':capture['graph']['sha256'],'events_sha256':capture['events']['sha256']}, 'result input hashes mismatch')
        require(result['status'] != 'COMPLETE' or coverage['status'] == 'complete', 'complete result from partial capture')
        keys = [(m['scope'],m['id']) for m in result['metrics']]
        require(len(set(keys)) == len(keys), 'duplicate scoped metric')
        for metric in result['metrics']:
            require(metric['scope'] in channels, 'unknown metric scope')
            require(metric['window'] == capture['window'], 'metric window mismatch')
    return transactions


def read_bundle(directory=EXAMPLE):
    capture = json.loads((directory / 'capture-manifest.json').read_text(encoding='utf-8'))
    for key in ('graph','events'):
        descriptor = capture[key]
        path = (directory / descriptor['path']).resolve()
        require(path.is_relative_to(directory.resolve()), 'artifact path escapes bundle')
        content = path.read_bytes()
        require(len(content) == int(descriptor['bytes']), 'artifact size mismatch')
        require(hashlib.sha256(content).hexdigest() == descriptor['sha256'], 'artifact hash mismatch')
    graph = json.loads((directory / capture['graph']['path']).read_text(encoding='utf-8'))
    events = [json.loads(line) for line in (directory / capture['events']['path']).read_text(encoding='utf-8').splitlines()]
    result = json.loads((directory / 'expected-result.json').read_text(encoding='utf-8'))
    return graph, capture, events, result


def main():
    for path in SCHEMAS.glob('*.schema.json'):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding='utf-8')))
    bundle = read_bundle()
    validate_bundle(*bundle)
    validate_shape('plugin-manifest', json.loads((EXAMPLE / 'plugin-manifest.json').read_text(encoding='utf-8')))
    print(f'Validated 5 draft schemas, {len(bundle[2])} events, graph, capture, expected result and plugin manifest.')
    print('Documentation contract checks only; no RTL simulation or complete decoder qualification.')


if __name__ == '__main__':
    main()
