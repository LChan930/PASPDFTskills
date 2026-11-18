#!/usr/bin/env python3
"""Offline, bounded native PASP FDF evidence audit; standard library only.

This is a compatibility snapshot, not the PASP input parser. Duplicate values
remain ambiguous; no first/last-wins rule is invented. No calculation is run.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import sys

MAX_BYTES = 16 * 1024 * 1024
MAX_LINES = 500000
MAX_FILES = 256
ENERGY = {'ha': 1., 'hartree': 1., 'ev': 1 / 27.211386245988,
          'ry': .5, 'rydberg': .5, 'mev': 1 / 27211.386245988}
TRUE, FALSE = {'t', 'true', '.true.'}, {'f', 'false', '.false.'}

def number(text: str) -> float:
    value = float(text.replace('D', 'E').replace('d', 'e'))
    if not math.isfinite(value):
        raise ValueError('nonfinite number')
    return value

def integer(text: str) -> int:
    if not re.fullmatch(r'[+-]?\d+', text):
        raise ValueError('integer literal required')
    return int(text)

def tokens(line: str) -> list[str]:
    # Comments are stripped only outside quotes, preserving filenames with spaces/#.
    lex = shlex.shlex(line, posix=True)
    lex.whitespace_split = True
    lex.commenters = '#!'
    lex.escape = ''  # FDF paths are not shell commands; retain Windows separators.
    return list(lex)

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def upf_filename(line: str) -> str:
    """Decode one bounded Fortran character item, retaining its quote evidence."""
    text = line.strip()
    if not text:
        raise ValueError('Provide one UPF filename per species.')
    if text[0] in {'"', "'"}:
        quote, result, i = text[0], [], 1
        while i < len(text):
            if text[i] == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    result.append(quote); i += 2; continue
                tail = text[i + 1:].strip()
                if tail and not tail.startswith(('#', '!')):
                    raise ValueError('Provide one quoted UPF filename per species, without trailing items.')
                if not result:
                    raise ValueError('UPF filename must not be empty.')
                return ''.join(result)
            result.append(text[i]); i += 1
        raise ValueError('Unclosed UPF filename quote.')
    text = re.split(r'[#!]', text, maxsplit=1)[0].strip()
    if not text or re.search(r"[\s/,;*='\"]", text):
        raise ValueError('Quote the complete UPF path with single or double quotes; unquoted directory separators, spaces and commas are unsafe.')
    return text

def registry() -> tuple[dict, list]:
    """Use packaged public parameter tables, never production-source discovery."""
    result, sources = {}, []
    base = Path(__file__).resolve().parent.parent / 'reference' / 'params'
    for path in sorted(base.glob('input-parameters-*.md')):
        sources.append({'path': str(path), 'sha256': digest(path)})
        for line in path.read_text(encoding='utf-8').splitlines():
            cells = line.split('|')
            if len(cells) < 5:
                continue
            match = re.fullmatch(r'\s*`([^`]+)`\s*', cells[1])
            if match:
                result[match[1].lower()] = {'name': match[1], 'type': cells[2].strip(),
                                           'documented_default': cells[3].strip(),
                                           'source': str(path)}
    if not result:
        raise OSError('packaged parameter tables absent or unrecognized')
    return result, sources

class Audit:
    def __init__(self, main: Path, ranks: int | None, ibz: int | None):
        self.main, self.cwd = main.resolve(), main.resolve().parent
        self.ranks, self.ibz = ranks, ibz
        self.tags, self.spec_sources = registry()
        self.findings, self.files, self.includes = [], {}, []
        self.scalars, self.blocks = defaultdict(list), defaultdict(list)
        self.expanded, self.block = [], None
        self.raw_lines = {}
        self.defaults, self.effective = {}, {}

    def finding(self, severity, code, message, anchors=None):
        self.findings.append({'severity': severity, 'code': code, 'message': message,
                              'anchors': anchors or []})

    def dependency(self, path, kind):
        path = path.resolve()
        if path.is_file():
            self.files[str(path)] = {'path': str(path), 'kind': kind,
                                     'bytes': path.stat().st_size, 'sha256': digest(path)}

    def expand(self, path, stack=()):
        path = path.resolve()
        if path in stack:
            self.finding('ERROR', 'include_cycle', 'Include cycle: ' + ' -> '.join(map(str, (*stack, path))))
            return
        if len(stack) >= 64 or len(self.files) >= MAX_FILES or len(self.expanded) >= MAX_LINES:
            self.finding('ERROR', 'resource_limit', 'Input closure exceeds bounded audit limits.')
            return
        if not path.is_file():
            self.finding('ERROR', 'missing_include', f'Missing included input: {path}')
            return
        if path.stat().st_size > MAX_BYTES:
            self.finding('ERROR', 'resource_limit', f'FDF exceeds {MAX_BYTES} bytes: {path}')
            return
        self.dependency(path, 'fdf')
        try:
            text = path.read_text(encoding='utf-8-sig')
        except (UnicodeError, OSError) as exc:
            self.finding('ERROR', 'input_read', str(exc)); return
        for lineno, line in enumerate(text.splitlines(), 1):
            anchor = {'file': str(path), 'line': lineno}
            self.raw_lines[(str(path), lineno)] = line
            if len(self.expanded) >= MAX_LINES:
                self.finding('ERROR', 'resource_limit', 'Expanded line budget exceeded.', [anchor]); return
            try:
                row = tokens(line)
            except ValueError as exc:
                self.finding('ERROR', 'quoting', str(exc), [anchor]); continue
            if not row:
                continue
            if row[0].lower() == '%include':
                if len(row) != 2:
                    self.finding('ERROR', 'include_syntax', 'Use %include followed by one path; quote paths containing spaces.', [anchor]); continue
                target = Path(row[1])
                if not target.is_absolute():
                    work = self.cwd / target
                    local = path.parent / target
                    if work.exists() and local.exists() and work.resolve() != local.resolve():
                        self.finding('WARN', 'ambiguous_include_base', 'Working-directory target selected; another target exists beside the including file.', [anchor])
                    target = work
                    if not work.exists() and local.exists():
                        target = local
                        self.finding('WARN', 'include_parent_fallback', 'Resolved beside including file; confirm executable working-directory behavior.', [anchor])
                self.includes.append({'anchor': anchor, 'target': str(target.resolve())})
                self.expand(target, (*stack, path))
            else:
                self.expanded.append((row, anchor))

    def parse(self):
        for row, anchor in self.expanded:
            key = row[0].lower()
            if key == '%block':
                if len(row) != 2 or self.block:
                    self.finding('ERROR', 'block_open', 'Malformed or nested %block.', [anchor]); continue
                self.block = {'name': row[1].lower(), 'anchor': anchor, 'rows': []}
            elif key == '%endblock':
                if not self.block:
                    self.finding('ERROR', 'block_close', 'Unmatched %endblock.', [anchor]); continue
                if len(row) != 2 or row[1].lower() != self.block['name']:
                    self.finding('ERROR', 'block_mismatch', 'Opening and closing block names differ.', [self.block['anchor'], anchor])
                self.blocks[self.block['name']].append(self.block); self.block = None
            elif self.block:
                self.block['rows'].append({'tokens': row, 'anchor': anchor,
                                          'raw': self.raw_lines[(anchor['file'], anchor['line'])]})
            elif key.startswith('%'):
                self.finding('WARN', 'unknown_directive', 'Unrecognized FDF directive; release compatibility unknown.', [anchor])
            else:
                self.scalars[key].append({'value': ' '.join(row[1:]), 'tokens': row[1:], 'anchor': anchor})
        if self.block:
            self.finding('ERROR', 'block_unclosed', 'Unclosed block: ' + self.block['name'], [self.block['anchor']])
        for kind, mapping in [('scalar', self.scalars), ('block', self.blocks)]:
            for key, values in mapping.items():
                if len(values) > 1:
                    self.finding('WARN', 'duplicate_definition', f'Duplicate {kind} {key}; effective precedence unresolved.', [v['anchor'] for v in values])
                if key not in self.tags and key not in {'rmax_cut', 'chemicalspecieslabel'}:
                    hint = ' Possible typo: DFT.nk_pool or DFT.nb_pool; choose explicitly.' if key == 'dft.nv_pool' else ''
                    self.finding('WARN', 'unknown_tag', f'Key {key} absent from bounded packaged registry; release compatibility unknown.' + hint, [v['anchor'] for v in values])
        for key, values in self.scalars.items():
            if len(values) != 1 or key not in self.tags:
                continue
            typ = self.tags[key]['type']; t = values[0]['tokens']
            try:
                if not t:
                    raise ValueError('missing value')
                if 'integer' in typ and ('块' not in typ and '每物种' not in typ):
                    if len(t) != 1: raise ValueError('one integer required')
                    integer(t[0])
                elif typ == 'logical':
                    if len(t) != 1 or t[0].lower() not in TRUE | FALSE: raise ValueError('logical T/F literal required')
                elif 'real' in typ:
                    number(t[0])
                    if '带能量单位' in typ and (len(t) != 2 or t[1].lower() not in ENERGY):
                        raise ValueError('recognized explicit energy unit required')
                    if '带' not in typ and len(t) != 1: raise ValueError('bare scalar; unexpected unit/token')
            except ValueError as exc:
                self.finding('ERROR', 'scalar_value', f'{key}: {exc}', [values[0]['anchor']])

    def value(self, key, default=None):
        rows = self.scalars.get(key, [])
        if not rows:
            if default is not None:
                self.defaults[key] = {'value': default, 'basis': self.tags.get(key, {}).get('documented_default', 'packaged semantic rule')}
            return default
        return rows[0]['value'] if len(rows) == 1 else None

    def num(self, key, default=None, isint=False):
        value = self.value(key, default)
        if value is None: return None
        try: return integer(str(value)) if isint else number(str(value))
        except ValueError: return None

    def flag(self, key, default=False):
        val = self.value(key, 'T' if default else 'F')
        if val is None: return None
        return True if val.lower() in TRUE else False if val.lower() in FALSE else None

    def rows(self, key):
        bs = self.blocks.get(key, [])
        return bs[0]['rows'] if len(bs) == 1 else []

    def matrix(self, key, cols, count=None):
        rows = self.rows(key)
        if count is not None and len(rows) != count:
            self.finding('ERROR', 'block_shape', f'{key}: expected {count} rows, observed {len(rows)}.', [b['anchor'] for b in self.blocks.get(key, [])])
        for row in rows:
            try:
                if len(row['tokens']) != cols: raise ValueError(f'expected {cols} numeric fields')
                for t in row['tokens']: number(t)
            except ValueError as exc: self.finding('ERROR', 'block_numeric', f'{key}: {exc}', [row['anchor']])

    def structure(self):
        if self.flag('read_poscar'):
            p = self.cwd/'POSCAR'
            self.dependency(p, 'structure')
            self.finding('UNKNOWN', 'poscar_not_decoded', 'POSCAR exists but its structure is outside this FDF parser coverage.' if p.is_file() else 'READ_POSCAR requires missing POSCAR.')
            return {}, None
        nat = self.num('numberofatoms', 0, True); nsp = self.num('number_of_species', 1, True)
        if nat is None or nat <= 0: self.finding('ERROR', 'atom_count', 'NumberOfAtoms must be positive and unambiguous.')
        if nsp is None or nsp <= 0: self.finding('ERROR', 'species_count', 'number_of_species must be positive and unambiguous.')
        rows = self.rows('atomiccoordinatesandatomicspecies'); species = {}; populations = Counter()
        if nat is not None and len(rows) != nat: self.finding('ERROR', 'coordinate_count', f'{nat} atoms requested but {len(rows)} coordinate rows found.')
        for row in rows:
            t = row['tokens']
            try:
                if len(t) < 5: raise ValueError('x y z species_index symbol required')
                for v in t[:3]: number(v)
                idx = integer(t[3]); symbol = t[4]
                if idx < 1 or (nsp and idx > nsp) or not re.fullmatch('[A-Z][a-z]?', symbol): raise ValueError('invalid species index/symbol')
                if idx in species and species[idx] != symbol: raise ValueError('inconsistent symbols for species index')
                species[idx] = symbol; populations[symbol] += 1
            except ValueError as exc: self.finding('ERROR', 'coordinate_row', str(exc), [row['anchor']])
        if nsp and set(species) != set(range(1,nsp+1)): self.finding('ERROR', 'species_mapping', 'Coordinate species indices do not cover declared species.')
        if self.blocks.get('chemicalspecieslabel'):
            self.finding('WARN', 'chemical_species_compatibility', 'ChemicalSpeciesLabel is not required by this native FDF snapshot; coordinate symbols and pseudo_pot_files define audited mapping.')
        lattice = self.value('latticeconstant')
        try:
            ts = str(lattice).split()
            if len(ts) != 2 or number(ts[0]) <= 0 or ts[1].lower() not in {'ang','angstrom','bohr'}: raise ValueError()
        except ValueError: self.finding('ERROR', 'lattice_constant', 'Positive finite LatticeConstant with Ang/Angstrom/Bohr required by this audit snapshot.')
        if self.blocks.get('latticevectors') and self.blocks.get('latticeparameters'): self.finding('ERROR','lattice_conflict','Both lattice forms provided.')
        if self.blocks.get('latticevectors'): self.matrix('latticevectors',3,3)
        elif self.blocks.get('latticeparameters'): self.matrix('latticeparameters',6,1)
        else: self.finding('UNKNOWN','lattice_default','No lattice block; documented identity default is not evidence of intended cell.')
        for key in ['dft.magmom','md_initial_velocity']:
            if self.blocks.get(key): self.matrix(key,3,nat)
        if self.num('dft.ispin',1,True) in {2,4} and not self.blocks.get('dft.magmom'):
            self.finding('WARN','magmom_default','No MAGMOM block; reference default (0,0,1) per atom does not establish intended order.')
        return dict(populations), species

    def upfs(self, species):
        result=[]; rows=self.rows('pseudo_pot_files')
        nsp=self.num('number_of_species',1,True)
        if len(rows)!=nsp: self.finding('ERROR','upf_count','pseudo_pot_files count must match species count.')
        for i,row in enumerate(rows,1):
            try:
                filename = upf_filename(row['raw'])
            except ValueError as exc:
                self.finding('ERROR','upf_path_quote',str(exc),[row['anchor']]);continue
            path=(self.cwd/filename).resolve()
            if not path.is_file():
                self.finding('ERROR','missing_upf',f'Missing required UPF: {path}',[row['anchor']]);continue
            self.dependency(path,'upf')
            with path.open('r',encoding='utf-8',errors='replace') as f: text=f.read(256*1024)
            header=re.search(r'<PP_HEADER\b([^>]*)>',text,re.I|re.S)
            attrs=dict((k.lower(),v) for k,v in re.findall(r'([\w_]+)\s*=\s*[\"\x27]([^\"\x27]*)[\"\x27]',header.group(1) if header else ''))
            meta={k:attrs.get(k) for k in ['element','z_valence','relativistic','has_so','pseudo_type','functional']}
            meta.update(path=str(path),species_index=i)
            if meta['element'] and species and meta['element'].strip()!=species.get(i): self.finding('ERROR','upf_element',f'UPF element {meta["element"]} mismatches species {species.get(i)}.',[row['anchor']])
            if not meta['element']: self.finding('UNKNOWN','upf_metadata','UPF metadata not recognized; filename is not element/SOC evidence.',[row['anchor']])
            if meta['has_so'] and meta['has_so'].lower() in TRUE and self.num('dft.ispin',1,True)!=4: self.finding('ERROR','soc_spin','FR UPF has_so=T requires ISPIN=4 in this snapshot.',[row['anchor']])
            result.append(meta)
        if self.num('dft.ispin',1,True)==4:
            self.finding('UNKNOWN','soc_not_spin_alone','ISPIN=4 is noncollinear; actual SOC depends on per-species has_so/relativistic metadata and release behavior.')
        return result

    def semantics(self, populations):
        if self.value('model') is None or str(self.value('model')).lower()!='dft': self.finding('ERROR','model','Explicit Model DFT required for this audit route.')
        spin=self.num('dft.ispin',1,True)
        if spin not in {1,2,4}: self.finding('ERROR','spin_enum','ISPIN must be 1,2,4 in the packaged snapshot.')
        # ENCUT_RHO depends on the selected, unit-converted ENCUT; never hardcode 40 Ha.
        enc=self.value('dft.encut','10 Ha'); rho=self.value('dft.encut_rho')
        def energy(s):
            ts=str(s).split()
            if len(ts)!=2 or ts[1].lower() not in ENERGY: raise ValueError()
            v=number(ts[0])*ENERGY[ts[1].lower()]
            if v<=0: raise ValueError()
            return v
        try:
            en=energy(enc); rh=energy(rho) if rho is not None else 4*en
            self.effective['cutoffs_documented']={'encut_ha':en,'encut_rho_ha':rh,'rho_basis':'explicit' if rho is not None else '4 * selected ENCUT','runtime_verified':False}
        except ValueError:self.finding('ERROR','cutoff_value','Cutoffs require positive finite number and supported energy unit; duplicate/ambiguous values remain unresolved.')
        u=self.num('dft.n_manifolds_plus_u',0,True);ut=self.num('dft.plusu_type',1,True);rows=self.rows('dft_plus_u')
        if u is None or u<0 or len(rows)!=u:self.finding('ERROR','hubbard_count','Nonnegative manifold count must equal DFT_plus_U rows.')
        if ut not in {1,2}:self.finding('ERROR','hubbard_type','plusU_type supported values are 1,2.')
        selected=set()
        for row in rows:
            t=row['tokens'];minimum=3 if ut==1 else 4
            try:
                if len(t)<minimum or len(' '.join(t))>200 or not re.fullmatch(r'\d[spdfg]',t[1]) or t[0] not in populations:raise ValueError('unknown species/shell or malformed record')
                if ut==2 and t[1].endswith('g'):raise ValueError('type2 g shell unsupported in snapshot')
                for v in t[2:minimum]:number(v)
                ids=[integer(v) for v in t[minimum:]] or list(range(1,populations[t[0]]+1))
                for idx in ids:
                    if idx<1 or idx>populations[t[0]]:raise ValueError('species-local atom ID out of range')
                    sel=(t[0],t[1],idx)
                    if sel in selected:raise ValueError('overlapping Hubbard selection')
                    selected.add(sel)
            except (ValueError,IndexError) as exc:self.finding('ERROR','hubbard_row',str(exc),[row['anchor']])
        rs=self.flag('dft.rs') or self.flag('dft.bfield');scf=self.flag('dft.scf_only')
        if u and (rs or scf or self.flag('dft.lrram')):self.finding('ERROR','hubbard_route','Packaged snapshot does not support +U with PWRS/SCF_ONLY/RRAM.')
        nk=self.num('dft.nk_pool',1,True);nb=self.num('dft.nb_pool',1,True)
        if nk is None or nb is None or nk<=0 or nb<=0:
            self.finding('ERROR','pool_positive','Pool counts must be positive unambiguous integers.')
        else:
            if self.ranks is None:self.finding('UNKNOWN','ranks_unknown','Rank divisibility not checked: supply --ranks with actual MPI ranks.')
            elif self.ranks%nk or (self.ranks//nk)%nb:self.finding('ERROR','pool_ranks','nk_pool must divide ranks and nb_pool must divide ranks/nk_pool.')
            if self.ibz is None:self.finding('UNKNOWN','ibz_unknown','k-pool divisibility not checked: supply actual generated global k count via --irreducible-kpoints; raw mesh product is not substituted.')
            elif self.ibz%nk or nk>self.ibz:self.finding('ERROR','pool_kpoints','nk_pool must divide actual global k count.')
            if (rs or scf or self.num('dft.lchern',0,True)) and nb!=1:self.finding('ERROR','pool_route','PWRS/SCF_ONLY/Chern require nb_pool=1 in snapshot.')
            if self.num('dft.lchern',0,True) and nk!=1:self.finding('ERROR','chern_pool','Chern requires nk_pool=1 in snapshot.')
            if rs and self.num('dft.algo',4,True)!=4:self.finding('ERROR','rs_algo','Complete PWRS requires ALGO=4 in snapshot.')
            if nb>1 and self.num('dft.algo',4,True)!=4:self.finding('WARN','band_pool_algorithm','Band parallelism with this algorithm needs release evidence.')
        self.effective['documented_overrides']={'rs':{'value':bool(rs),'basis':'Bfield forces RS or requested RS','runtime_verified':False}}
        band=self.flag('dft.lbandstructure')
        chern=self.num('dft.lchern',0,True)!=0
        lnsc=self.flag('dft.lnsc')
        rwave=self.num('dft.rwave',0,True)==1
        needs=band or self.num('dft.rcharg',0,True)==1 or self.flag('dft.lberry.readchg')
        if chern and lnsc and rwave:
            first=self.num('dft.lberry.nint',1,True)
            last=self.num('dft.lberry.nend',None,True)
            requested=self.num('dft.nband',0,True)
            if first is None or last is None or first<1 or last<first or (requested and last>requested):
                self.finding('ERROR','chern_wave_bounds','Wave-only Chern requires explicit LBERRY.NEND and 1 <= LBERRY.NINT <= LBERRY.NEND <= available loaded bands; NINT defaults to 1. Current NBAND, when explicit, must cover the selection.')
            if self.num('dft.algo',4,True)==1:
                self.finding('ERROR','chern_wave_algorithm','ALGO=1 is unsupported for the direct WAVECAR Chern route; use a supported wave-read algorithm.')
            self.finding('UNKNOWN','chern_wave_support','Direct wave Chern needs executable support for explicit band groups. Verify full two-dimensional WAVECAR mesh, k order, basis, loaded bands and normalized states. WAVECAR.restart can supply validated energies; legacy wave files alone cannot certify energy isolation or automatic occupied-group selection. This audit does not decode or authenticate that spectrum.')
        if chern and lnsc and not rwave and not needs:
            self.finding('WARN','chern_density_restart','Chern and LNSC do not automatically read density. For the density-restart workflow set RCHARG=1 with matching CHGCAR and RWAVE=0.')
        if needs:
            names=['CHGCAR']+(['CHGCAR.restart'] if band else [])+(['PLUS_U_NS'] if u else [])
            if not band and (self.cwd/'CHGCAR.restart').is_file(): names.append('CHGCAR.restart')
            for name in names:
                p=self.cwd/name;self.dependency(p,'restart')
                self.finding('UNKNOWN','restart_provenance',f'{name}: '+('exists; input compatibility and same-run upstream SCF acceptance unverified.' if p.is_file() else 'missing required handoff evidence.'))
        if rwave and self.num('dft.algo',4,True)!=1:
            p=self.cwd/'WAVECAR';self.dependency(p,'restart')
            self.finding('UNKNOWN','wave_restart', 'WAVECAR present; compatibility unverified.' if p.is_file() else 'Missing WAVECAR for requested wave restart.')
            meta=self.cwd/'WAVECAR.restart'
            if meta.is_file(): self.dependency(meta,'restart')
            self.finding('UNKNOWN','wave_spectrum', 'WAVECAR.restart present; binding, spectrum and compatibility require executable validation.' if meta.is_file() else 'No WAVECAR.restart; updated explicit-group legacy wave Chern can proceed without energy/gap certification.')
        elif rwave:
            self.finding('WARN','wave_restart_ignored','ALGO=1 does not read WAVECAR in this snapshot; RWAVE does not supply its orbitals.')

    def run(self):
        self.expand(self.main);self.parse()
        if any(f['code']=='duplicate_definition' for f in self.findings):
            # Any duplicate can affect subsequent interpretation. Keep the full
            # requested closure but do not simulate undocumented parser precedence.
            pop,upfs={},[]
            self.finding('UNKNOWN','semantic_checks_skipped','Semantic checks skipped because duplicate definitions leave effective settings unresolved.')
        else:
            pop,species=self.structure();upfs=self.upfs(species)
            self.semantics(pop)
        return {'schema':'pasp-input-audit-v1','input':str(self.main),'working_directory':str(self.cwd),
                'language':'en','registry':{'keys':len(self.tags),'sources':self.spec_sources},
                'requested':{'scalars':dict(self.scalars),'blocks':dict(self.blocks)},
                'documented_defaults':self.defaults,'effective_documented_only':self.effective,
                'runtime_readback':{},'runtime_effective':{},
                'resources':{'ranks_supplied':self.ranks,'actual_global_kpoints_supplied':self.ibz,'raw_mesh_used_as_ibz':False},
                'files':list(self.files.values()),'include_edges':self.includes,'species_populations':pop,'upfs':upfs,
                'findings':self.findings,'summary':dict(Counter(f['severity'] for f in self.findings)),
                'status':'issues_observed' if any(f['severity']=='ERROR' for f in self.findings) else 'bounded_checks_completed',
                'limits':['No PASP execution or executable parser equivalence.','No cutoff/k-mesh/ground-state convergence certification.',
                          'No duplicate effective-precedence inference.','POSCAR, all release enums, lattice geometry validity and restart binary compatibility are not fully decoded.',
                          'Registry presence checks names; semantic coverage is explicitly bounded by input-audit.md.']}

LABELS={
 'en':('PASP offline input audit','Bounded checks completed; findings are evidence, not a physical-validity certificate.','Findings','Runtime read-back/effective settings are unknown.'),
 'zh-Hans':('PASP 离线输入审计','有界检查已完成；检查结果不构成物理有效性证明。','检查结果','运行回读值和实际生效设置未知。'),
 'zh-Hant':('PASP 離線輸入審計','有界檢查已完成；檢查結果不構成物理有效性證明。','檢查結果','執行回讀值和實際生效設定未知。')}
EXPLANATIONS={
 'include_cycle':('包含文件形成循环。','包含檔案形成循環。'),
 'missing_include':('缺少包含文件。','缺少包含檔案。'),
 'include_syntax':('包含路径语法无效；空格路径须加引号。','包含路徑語法無效；空格路徑須加引號。'),
 'include_parent_fallback':('使用包含文件所在目录回退解析；须核对发行行为。','使用包含檔案所在目錄回退解析；須核對發行行為。'),
 'ambiguous_include_base':('包含路径有多个候选；已采用工作目录。','包含路徑有多個候選；已採用工作目錄。'),
 'resource_limit':('超过离线审计资源上限。','超過離線審計資源上限。'),
 'input_read':('输入无法完整读取。','輸入無法完整讀取。'),
 'quoting':('引号语法无效。','引號語法無效。'),
 'block_open':('块起始标记无效或嵌套。','區塊起始標記無效或巢狀。'),
 'block_close':('块结束标记没有对应起始。','區塊結束標記沒有對應起始。'),
 'block_mismatch':('块名称不匹配。','區塊名稱不匹配。'),
 'block_unclosed':('块没有闭合。','區塊沒有閉合。'),
 'unknown_directive':('未知指令；发行兼容性待核对。','未知指令；發行相容性待核對。'),
 'unknown_tag':('参数不在打包注册表中；仅警告，不认定发行不支持。','參數不在打包登錄表中；僅警告，不認定發行不支援。'),
 'duplicate_definition':('重复定义的实际优先级未知；保留全部源位置。','重複定義的實際優先順序未知；保留全部來源位置。'),
 'semantic_checks_skipped':('因重复定义导致生效设置不明，跳过语义检查。','因重複定義導致生效設定不明，跳過語意檢查。'),
 'scalar_value':('标量类型、单位或有限性不符合已知契约。','純量型別、單位或有限性不符合已知契約。'),
 'ranks_unknown':('未提供实际 MPI 进程数；不能检查资源整除。','未提供實際 MPI 程序數；不能檢查資源整除。'),
 'ibz_unknown':('实际全局 k 点数未知；不以原始网格乘积代替。','實際全域 k 點數未知；不以原始網格乘積代替。'),
 'pool_ranks':('并行池不能按实际进程数整除。','平行池不能按實際程序數整除。'),
 'pool_kpoints':('k 池不能整除实际全局 k 点数。','k 池不能整除實際全域 k 點數。'),
 'restart_provenance':('重启文件缺失或缺少匹配的上游来源证明。','重啟檔案缺失或缺少匹配的上游來源證明。'),
 'wave_restart':('波函数重启文件缺失或兼容性未知。','波函數重啟檔案缺失或相容性未知。'),
 'soc_not_spin_alone':('非共线自旋不单独证明 SOC；须核对每物种元数据。','非共線自旋不單獨證明 SOC；須核對每物種中繼資料。'),
 'soc_spin':('全相对论自旋轨道赝势与自旋设置冲突。','全相對論自旋軌道贗勢與自旋設定衝突。'),
 'upf_metadata':('UPF 元数据识别不足；不依赖文件名判断。','UPF 中繼資料辨識不足；不依賴檔名判斷。'),
 'upf_element':('UPF 元素与结构物种顺序不匹配。','UPF 元素與結構物種順序不匹配。'),
 'missing_upf':('缺少必需的赝势文件。','缺少必需的贗勢檔案。'),
 'upf_count':('赝势文件数与物种数不匹配。','贗勢檔案數與物種數不匹配。'),
 'upf_filename':('每个物种须提供一个赝势文件名。','每個物種須提供一個贗勢檔名。'),
 'upf_path_quote':('赝势路径须用完整的单引号或双引号包围；每物种一行，未加引号的目录分隔符、空格和逗号不安全。','贗勢路徑須用完整的單引號或雙引號包圍；每物種一行，未加引號的目錄分隔符、空格和逗號不安全。'),
 'chern_wave_bounds':('纯波函数陈数须显式设置 LBERRY.NEND，并满足 1<=NINT<=NEND<=实际读入带数；NINT 默认1，显式 NBAND 也须覆盖该范围。','純波函數陳數須顯式設定 LBERRY.NEND，並滿足 1<=NINT<=NEND<=實際讀入帶數；NINT 預設1，顯式 NBAND 也須涵蓋該範圍。'),
 'chern_wave_algorithm':('ALGO1 不支持直接读取 WAVECAR 求陈数，须使用支持波函数读取的算法。','ALGO1 不支援直接讀取 WAVECAR 求陳數，須使用支援波函數讀取的演算法。'),
 'chern_wave_support':('须核对可执行文件支持显式带组陈数及实际网格/带数；匹配 WAVECAR.restart 可恢复能谱，离线审计不认证绑定关系、占据或能隙。','須核對執行檔支援顯式帶組陳數及實際網格/帶數；匹配 WAVECAR.restart 可恢復能譜，離線審計不認證綁定關係、佔據或能隙。'),
 'wave_spectrum':('WAVECAR.restart 的绑定和能谱须由可执行文件验证；旧 WAVECAR 缺少伴随文件时，显式带组流程不认证能隙。','WAVECAR.restart 的綁定與能譜須由執行檔驗證；舊 WAVECAR 缺少伴隨檔時，顯式帶組流程不認證能隙。'),
 'chern_density_restart':('Chern 与 LNSC 不自动读密度；密度重启流程应显式设置 RCHARG1，提供匹配 CHGCAR，并使用 RWAVE0。','Chern 與 LNSC 不自動讀密度；密度重啟流程應顯式設定 RCHARG1，提供匹配 CHGCAR，並使用 RWAVE0。'),
 'wave_restart_ignored':('此版本 ALGO1 不读 WAVECAR，RWAVE 不提供其初始轨道。','此版本 ALGO1 不讀 WAVECAR，RWAVE 不提供其初始軌道。'),
 'cutoff_value':('截断能须为带支持单位的正有限值。','截斷能須為帶支援單位的正有限值。'),
 'magmom_default':('未提供磁矩块；默认磁矩不能证明目标磁序。','未提供磁矩區塊；預設磁矩不能證明目標磁序。'),
 'hubbard_row':('Hubbard 行的物种、壳层、数值或局域原子编号无效。','Hubbard 列的物種、殼層、數值或局域原子編號無效。'),
 'hubbard_count':('Hubbard 壳层数与块行数不符。','Hubbard 殼層數與區塊列數不符。'),
 'hubbard_type':('Hubbard 类型超出已知枚举。','Hubbard 型別超出已知列舉。'),
 'hubbard_route':('Hubbard 与当前任务组合超出打包契约。','Hubbard 與目前任務組合超出打包契約。'),
 'model':('本路线要求明确的 Model DFT。','本路線要求明確的 Model DFT。'),
 'spin_enum':('自旋枚举须为 1、2 或 4。','自旋列舉須為 1、2 或 4。'),
 'atom_count':('原子数须为明确的正整数。','原子數須為明確的正整數。'),
 'species_count':('物种数须为明确的正整数。','物種數須為明確的正整數。'),
 'coordinate_count':('坐标行数与原子数不符。','座標列數與原子數不符。'),
 'coordinate_row':('坐标、物种索引或元素符号无效。','座標、物種索引或元素符號無效。'),
 'species_mapping':('坐标物种索引没有覆盖已声明物种。','座標物種索引沒有涵蓋已宣告物種。'),
 'lattice_constant':('晶格常数须为带支持长度单位的正有限值。','晶格常數須為帶支援長度單位的正有限值。'),
 'lattice_conflict':('两种晶格定义互相冲突。','兩種晶格定義互相衝突。'),
 'lattice_default':('缺少显式晶格；默认单位阵不能证明用户意图。','缺少明確晶格；預設單位矩陣不能證明使用者意圖。'),
 'block_shape':('数值块行数不符合已知形状。','數值區塊列數不符合已知形狀。'),
 'block_numeric':('数值块字段数或有限性无效。','數值區塊欄位數或有限性無效。'),
 'pool_positive':('并行池数须为正整数。','平行池數須為正整數。'),
 'pool_route':('此任务要求单能带池。','此任務要求單能帶池。'),
 'chern_pool':('陈数任务要求单 k 池。','陳數任務要求單 k 池。'),
 'rs_algo':('完整 PWRS 要求已知算法 4。','完整 PWRS 要求已知演算法 4。'),
 'band_pool_algorithm':('当前能带池算法组合须有发行依据。','目前能帶池演算法組合須有發行依據。'),
 'poscar_not_decoded':('POSCAR 缺失或不在当前解码覆盖范围。','POSCAR 缺失或不在目前解碼涵蓋範圍。'),
 'chemical_species_compatibility':('本原生格式不要求 ChemicalSpeciesLabel；按坐标和赝势顺序核对。','本原生格式不要求 ChemicalSpeciesLabel；按座標和贗勢順序核對。')}
def render(result,lang):
    title,summary,findings,unknown=LABELS[lang]
    lines=[f'# {title}','',f"Input: `{result['input']}`",'',summary,'',unknown,'',f"Registry keys: {result['registry']['keys']}; status: {result['status']}",'',f'## {findings}','']
    for f in result['findings']:
        anchors='; '.join(f"{a['file']}:{a['line']}" for a in f['anchors'])
        lines.append(f"- **{f['severity']} {f['code']}**: {f['message']}"+(' — '+anchors if anchors else ''))
        if 'evidence_message' in f:
            lines.append('  '+f['evidence_message'])
    lines+=['','Requested settings, dependency hashes, documented defaults and bounded effective rules:','', '```json',json.dumps({k:result[k] for k in ['requested','documented_defaults','effective_documented_only','resources','files']},ensure_ascii=False,indent=2),'```','']
    return '\n'.join(lines)

def positive(s):
    try:v=integer(s)
    except ValueError as exc:raise argparse.ArgumentTypeError(str(exc))
    if v<=0:raise argparse.ArgumentTypeError('positive integer required')
    return v

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path,help='native FDF file or directory containing lattice_model.fdf')
    p.add_argument('--ranks',type=positive,help='actual MPI rank count, never nodes/threads')
    p.add_argument('--irreducible-kpoints',type=positive,help='known actual generated global k count; also use actual path count for band stage')
    p.add_argument('--lang',choices=LABELS,default='en')
    p.add_argument('--format',choices=['markdown','json'],default='markdown')
    p.add_argument('--output',type=Path,help='exclusively create a new report; never overwrite')
    args=p.parse_args()
    mainfile=args.input/'lattice_model.fdf' if args.input.is_dir() else args.input
    try:
        if not mainfile.is_file():raise OSError('Main input is missing or unreadable: '+str(mainfile))
        audit=Audit(mainfile,args.ranks,args.irreducible_kpoints);result=audit.run()
        result['language']=args.lang;result['localized_summary']=LABELS[args.lang][1]
        if args.lang!='en':
            for finding in result['findings']:
                finding['evidence_message']=finding['message']
                finding['message']=EXPLANATIONS.get(finding['code'],('此项需核对原始证据。','此項須核對原始證據。'))[0 if args.lang=='zh-Hans' else 1]
        text=json.dumps(result,ensure_ascii=False,indent=2)+'\n' if args.format=='json' else render(result,args.lang)
        if args.output:
            with args.output.open('x',encoding='utf-8') as f:f.write(text)
        else:sys.stdout.write(text)
    except (OSError,UnicodeError,ValueError) as exc:
        print('audit_inputs: '+str(exc),file=sys.stderr);return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
