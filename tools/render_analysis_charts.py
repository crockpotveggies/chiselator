"""Render clearly labeled, synthetic contract diagrams from the worked fixture."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/examples/hybrid-flow'
OUT = ROOT / 'docs/images'
COLORS = {'async':'#2165a8', 'clocked':'#ad4e00', 'effect':'#317650'}
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11, 'svg.fonttype':'none', 'svg.hashsalt':'chiselator-draft-0.1.0'})


def save(fig, name, preview):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{name}.svg'
    fig.savefig(path, bbox_inches='tight', metadata={'Date':None})
    # Matplotlib emits trailing spaces in path data; normalize portable text output.
    svg = '\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines()) + '\n'
    path.write_bytes(svg.encode('utf-8'))
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        fig.savefig(preview / f'{name}.png', dpi=140, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    events = [json.loads(line) for line in (DATA / 'flow-events.jsonl').read_text().splitlines()]
    times = {e['kind']: int(e['time']['fs']) / 1_000_000 for e in events}
    offer, accept, complete = (times[k] for k in ('transaction.offer','transaction.accept','transaction.complete'))
    fig, ax = plt.subplots(figsize=(12,5.6))
    ax.set_title('One operation across an async → clocked boundary',loc='left',pad=34,fontsize=17,weight='bold')
    ax.text(0,1.04,'SYNTHETIC CONTRACT FIXTURE · not measured MCU or simulator performance',transform=ax.transAxes,fontsize=10,color='#555555')
    # Request return is explanatory raw-waveform information from fixture README, not a normalized event.
    ax.step([0,offer,13,20],[3.0,3.55,3.0,3.0],where='post',color=COLORS['async'],lw=2.5)
    ax.step([0,accept,complete,20],[2.0,2.55,2.0,2.0],where='post',color=COLORS['async'],lw=2.5)
    clocks = [int(e['time']['fs'])/1_000_000 for e in events if e['kind']=='clock.edge']
    ax.vlines(clocks,0.94,1.44,color=COLORS['clocked'],lw=1.8)
    ax.scatter([times['transaction.transfer']],[1.19],s=95,color=COLORS['clocked'],zorder=4)
    ax.scatter([times['effect.commit']],[0.35],s=95,marker='D',color=COLORS['effect'],zorder=4)
    ax.annotate('Actual consumer fire',xy=(12,1.19),xytext=(14,1.5),arrowprops={'arrowstyle':'->','color':'#444444'},fontsize=10)
    ax.annotate('Capture effect: later delta at the same 12 ns',xy=(12,0.35),xytext=(1,-0.25),arrowprops={'arrowstyle':'->','color':'#444444'},fontsize=10)
    for start,end,y,label in [(offer,accept,4.1,'10 ns to acceptance'),(accept,complete,4.1,'4 ns recovery')]:
        ax.annotate('',xy=(start,y),xytext=(end,y),arrowprops={'arrowstyle':'<->','color':'#333333'})
        ax.text((start+end)/2,y+0.12,label,ha='center',fontsize=10)
    ax.set_yticks([3.25,2.25,1.19,0.35],['Async request','Async acknowledge','Consumer clock / fire','Committed effect'])
    ax.set_xticks(range(0,21,2)); ax.set_xlim(0,20); ax.set_ylim(-0.55,4.6)
    ax.set_xlabel('Simulated time (ns); delta order retained in the event file')
    ax.grid(axis='x',alpha=.18); ax.tick_params(axis='y',length=0)
    for spine in ['top','right','left']: ax.spines[spine].set_visible(False)
    save(fig,'hybrid-timeline',args.preview_dir)

    result = json.loads((DATA / 'expected-result.json').read_text())
    known = {m['id']:int(m['numerator'])/int(m['denominator'])/1_000_000 for m in result['metrics'] if m['scope']=='c:async' and m['unit']=='fs'}
    fig, ax = plt.subplots(figsize=(10.5,4.8))
    labels = ['Offer → acceptance','Acceptance → return idle','Offer → return idle (total)']
    values = [known[x] for x in ['acceptance-latency','recovery-latency','completion-latency']]
    bars=ax.barh(labels,values,color=['#2165a8','#ad4e00','#526575'],height=.55)
    ax.invert_yaxis()
    for bar,value in zip(bars,values): ax.text(value+.2,bar.get_y()+bar.get_height()/2,f'{value:g} ns',va='center',weight='bold')
    ax.set_xlim(0,16); ax.set_xlabel('Simulated duration (ns)')
    ax.set_title('Exact interval arithmetic for one synthetic transaction',loc='left',pad=28,fontsize=15,weight='bold')
    ax.text(0,1.04,'ILLUSTRATION · total overlaps the first two intervals; do not sum all three bars',transform=ax.transAxes,fontsize=10,color='#555555')
    ax.text(0,-.28,'Clocked sampled offer latency: unavailable. A fire event does not reveal an earlier stable offer.\nOne accepted operation in [0, 20 ns); no performance or physical timing claim.',transform=ax.transAxes,fontsize=10,color='#444444',linespacing=1.7)
    ax.grid(axis='x',alpha=.15); ax.set_axisbelow(True)
    for spine in ['top','right','left']: ax.spines[spine].set_visible(False)
    save(fig,'hybrid-metrics',args.preview_dir)
    print('Rendered two synthetic SVG charts from the documented fixture.')


if __name__ == '__main__':
    main()
