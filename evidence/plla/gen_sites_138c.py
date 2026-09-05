"""P1.T17 generator: enumerate 138C PLL sites from the shipped .fse/.dat tables."""
import os, json, collections, hashlib, datetime
from apycula import fse_parser, dat_parser, chipdb, attrids
from pathlib import Path

G = os.environ['GOWINHOME']
OUT = Path(__file__).resolve().parent
BIG = 100          # rows in shortval table 35 that mark a real PLL config tile
PLL_TABLE = 35     # `_known_tables[35] == 'PLL'`

def load(dev):
    p = f"{G}/IDE/share/device/{dev}/{dev}.fse"
    with open(p, 'rb') as f:
        fse = fse_parser.read_fse(f, dev)
    return fse

def pll_tiles(fse):
    t35 = {t: v['shortval'][PLL_TABLE] for t, v in fse.items()
           if isinstance(t, int) and PLL_TABLE in v.get('shortval', {})}
    grid = fse['header']['grid'][61]
    out = []
    for r, row in enumerate(grid):
        for c, tt in enumerate(row):
            if tt in t35 and len(t35[tt]) >= BIG:
                tab = t35[tt]
                out.append(dict(row=r, col=c, ttyp=tt, rows=len(tab),
                                attr_ids=sorted({x[0] for x in tab}),
                                pairs=len({(x[0], x[1]) for x in tab})))
    return out, t35, grid

res = {}
for dev in ("GW5AST-138C", "GW5A-25A"):
    fse = load(dev)
    tiles, t35, grid = pll_tiles(fse)
    # group horizontally-adjacent tiles of the same row into one site
    sites = []
    for t in sorted(tiles, key=lambda t: (t['row'], t['col'])):
        if sites and sites[-1][-1]['row'] == t['row'] and sites[-1][-1]['col'] + 1 == t['col']:
            sites[-1].append(t)
        else:
            sites.append([t])
    res[dev] = dict(fse=fse, tiles=tiles, sites=sites, t35=t35, grid=grid,
                    pseudo=[t for t in fse if isinstance(t, int) and t >= 1024],
                    has_drpfuse='drpfuse' in fse['header'])

d138 = res['GW5AST-138C']
d25 = res['GW5A-25A']

# .dat side
def dat_of(dev):
    return dat_parser.Datfile(Path(f"{G}/IDE/share/device/{dev}/{dev}.dat"))
dats = {d: dat_of(d) for d in res}

def named_tables(dat):
    st = dat.gw5aStuff
    return {k: sum(1 for r in st[k] if r != [0xffff] * 3)
            for k in ('PllLTIns', 'PllLTOuts', 'PllLBIns', 'PllLBOuts',
                      'PllRTIns', 'PllRTOuts', 'PllRBIns', 'PllRBOuts')}

def old_style(dat):
    st = dat.gw5aStuff
    ins = [nam for idx, nam in chipdb._plla_inputs if st['PllIn'][idx] not in (-1, 0xffff)]
    outs = [nam for idx, nam in chipdb._plla_outputs if st['PllOut'][idx] not in (-1, 0xffff)]
    return ins, outs

# ---- sites JSON -------------------------------------------------------
sides = []
def side_of(r, c, rows, cols):
    if r == rows - 1: return 'B'
    return 'L' if c < cols / 2 else 'R'

rows_n, cols_n = len(d138['grid']), len(d138['grid'][0])
records = []
for i, site in enumerate(d138['sites']):
    anchor = site[0]
    ids = sorted(set().union(*[set(t['attr_ids']) for t in site]))
    records.append(dict(
        pll_idx=i,
        side=side_of(anchor['row'], anchor['col'], rows_n, cols_n),
        row=anchor['row'], col=anchor['col'],
        tiles=[[t['row'], t['col'], t['ttyp'], t['rows']] for t in site],
        slot_idx=None,
        source='fse',
        ports_source='dat_old_style_partial',
        needs_trace=True,
        attr_id_count=len(ids), attr_id_min=min(ids), attr_id_max=max(ids),
        table_rows=sum(t['rows'] for t in site)))

ins138, outs138 = old_style(dats['GW5AST-138C'])
ins25, outs25 = old_style(dats['GW5A-25A'])

doc = dict(
    task='P1.T17',
    device='GW5AST-138C',
    ide_version=fse_parser.detect_ide_version(G),
    gowinhome=G,
    generated=datetime.date.today().isoformat(),
    datasheet_pll_count=12,
    measured_site_count=len(records),
    sites=records,
    dat=dict(
        named_tables_populated_rows=named_tables(dats['GW5AST-138C']),
        old_style_inputs_present=len(ins138), old_style_inputs_total=len(chipdb._plla_inputs),
        old_style_outputs_present=len(outs138), old_style_outputs_total=len(chipdb._plla_outputs),
        old_style_inputs_missing=[n for _, n in chipdb._plla_inputs if n not in ins138],
        old_style_outputs_missing=[n for _, n in chipdb._plla_outputs if n not in outs138]),
    fse=dict(pseudo_ttyps=d138['pseudo'], has_drpfuse=d138['has_drpfuse']),
    reference_25a=dict(
        pseudo_ttyps=d25['pseudo'], has_drpfuse=d25['has_drpfuse'],
        named_tables_populated_rows=named_tables(dats['GW5A-25A']),
        old_style_inputs_present=len(ins25), old_style_outputs_present=len(outs25),
        slot_table_rows=len(d25['t35'][1024]),
        slot_table_attr_ids=len({x[0] for x in d25['t35'][1024]}),
        chipdb_slots=[[27,0,6,'PllLB'],[27,91,2,'PllRB'],[0,0,5,'PllLT'],
                      [0,91,3,'PllRT'],[0,45,4,'old_style'],[36,45,8,'old_style']]),
    attrids_py_pll_attrids=len(attrids.pll_attrids))

(OUT / 'sites-138c.json').write_text(json.dumps(doc, indent=2) + '\n')

# ---- attrids TSV ------------------------------------------------------
lines = ['device\tsite_idx\tside\trow\tcol\tttyp\ttable_id\ttable_rows\tdistinct_attr_ids\tattr_id_min\tattr_id_max']
for rec in records:
    for (r, c, tt, n) in rec['tiles']:
        tab = d138['t35'][tt]
        ids = {x[0] for x in tab}
        lines.append(f"GW5AST-138C\t{rec['pll_idx']}\t{rec['side']}\t{r}\t{c}\t{tt}\t35\t{n}\t{len(ids)}\t{min(ids)}\t{max(ids)}")
tab = d25['t35'][1024]
ids = {x[0] for x in tab}
lines.append(f"GW5A-25A\t-\tslot\t-\t-\t1024\t35\t{len(tab)}\t{len(ids)}\t{min(ids)}\t{max(ids)}")
(OUT / 'attrids-138c.tsv').write_text('\n'.join(lines) + '\n')

print('sites', len(records))
for rec in records:
    print(rec['pll_idx'], rec['side'], (rec['row'], rec['col']), rec['tiles'], rec['attr_id_count'], rec['table_rows'])
print('attrid tsv rows', len(lines) - 1)
print('138C old_style ins/outs', len(ins138), len(outs138))
