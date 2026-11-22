#!/usr/bin/env python3
"""Validate declared task-pack structure; never execute project checks or prove approval."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys

if sys.version_info < (3, 9):
    sys.exit('Validator error: Python 3.9 or newer is required')

LIMIT = 2 * 1024 * 1024
ACTIVE = {'ready', 'in_progress', 'done'}
STATES = ACTIVE | {'draft', 'blocked'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def load_json(path):
    require(path.stat().st_size <= LIMIT, 'JSON input exceeds 2 MiB')
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def spec_digest(path):
    """SHA-256 of the spec with BOM and line endings normalized, so a Git CRLF/LF checkout keeps evidence valid."""
    data = path.read_bytes()
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    return hashlib.sha256(data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')).hexdigest()


def heading_slugs(content):
    """GitHub-style heading anchors, including -1/-2 suffixes for repeated headings."""
    slugs, seen = [], {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*\s*$', content, re.M):
        base = re.sub(r'[^\w\- ]', '', heading.lower()).strip().replace(' ', '-')
        count = seen.get(base, 0)
        seen[base] = count + 1
        slugs.append(base if count == 0 else base + '-' + str(count))
    return slugs


def text(value):
    return isinstance(value, str) and bool(value.strip())


def shape(value, required, optional=()):
    require(isinstance(value, dict), 'Expected an object')
    require(set(required) <= set(value) <= set(required) | set(optional),
            'Missing or unknown fields: ' + ', '.join(sorted(set(value) ^ set(required))))


def portable_path(value):
    require(text(value) and '\\' not in value and ':' not in value,
            'Use nonempty portable relative paths')
    # One trailing slash marks a directory (allowed_paths such as "tests/"); "", "/", "//" stay invalid.
    body = value[:-1] if value.endswith('/') else value
    p = PurePosixPath(body)
    require(body and not p.is_absolute() and not PureWindowsPath(body).drive and
            not any(part in ('', '.', '..') for part in body.split('/')),
            'Unsafe relative path: ' + value)
    reserved = {'con', 'prn', 'aux', 'nul'} | {f'{v}{n}' for v in ('com', 'lpt') for n in range(1, 10)}
    require(not any(part.rstrip(' .') != part or part.split('.')[0].lower() in reserved for part in p.parts),
            'Nonportable path: ' + value)
    return p


def pack_file(root, ref):
    require(text(ref), 'Missing file reference')
    base = ref.partition('#')[0]
    relative = portable_path(base)
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        require(not candidate.is_symlink(), 'Symlink in pack reference: ' + ref)
    require(candidate.resolve().is_relative_to(root) and candidate.is_file(),
            'Missing or escaping pack file: ' + ref)
    require(candidate.stat().st_size <= LIMIT, 'Pack file exceeds 2 MiB: ' + ref)
    return candidate


def strings(values, nonempty=True):
    require(isinstance(values, list) and (bool(values) or not nonempty), 'Expected a string list')
    require(all(text(v) for v in values) and len(set(values)) == len(values),
            'String list needs distinct nonempty values')


def identifier(value):
    require(text(value) and re.fullmatch(r'[A-Z][A-Z0-9-]{0,63}', value), 'Invalid stable ID')


def validate(root, selected=None):
    root = root.resolve(strict=True)
    require(root.is_dir(), 'Pack must be a directory')
    data = load_json(pack_file(root, 'manifest.json'))
    shape(data, ('schema_version', 'feature_id', 'spec_file', 'spec_revision', 'approval', 'requirements', 'tasks'))
    require(type(data['schema_version']) is int and data['schema_version'] == 1, 'Unsupported schema_version')
    require(text(data['feature_id']) and text(data['spec_revision']), 'Missing feature or spec revision')
    spec_text = pack_file(root, data['spec_file']).read_text(encoding='utf-8-sig')
    approval = data['approval']
    shape(approval, ('status', 'evidence'))
    require(approval['status'] in ('pending', 'approved') and isinstance(approval['evidence'], str),
            'Invalid approval declaration')
    if approval['status'] == 'approved':
        pack_file(root, approval['evidence'])
    require(isinstance(data['requirements'], list) and 0 < len(data['requirements']) <= 5000,
            'Expected 1-5000 requirements')
    requirements = {}
    for req in data['requirements']:
        shape(req, ('id', 'source', 'status'))
        identifier(req['id'])
        require(req['id'] not in requirements, 'Duplicate requirement ID')
        require(req['status'] in ('proposed', 'approved', 'deferred', 'out_of_scope'), 'Invalid requirement status')
        source = pack_file(root, req['source'])
        fragment = req['source'].partition('#')[2]
        if fragment:
            content = source.read_text(encoding='utf-8-sig')
            slugs = heading_slugs(content)
            explicit = re.findall(r'<a\s+id=[\"\']([^\"\']+)[\"\']\s*>', content)
            require(fragment in slugs or fragment in explicit, 'Missing requirement anchor: ' + req['source'])
        requirements[req['id']] = req
    require(isinstance(data['tasks'], list) and 0 < len(data['tasks']) <= 5000, 'Expected 1-5000 tasks')
    # Pack-level Markdown (CONTRACTS, DECISIONS, INDEX...) must also be filled in before any task is active.
    pack_text = ''.join(p.read_text(encoding='utf-8-sig') for p in sorted(root.glob('*.md'))
                        if p.is_file() and not p.is_symlink() and p.stat().st_size <= LIMIT)
    tasks, files, covered, warnings = {}, set(), set(), []
    for task in data['tasks']:
        shape(task, ('id', 'file', 'requirements', 'depends_on', 'allowed_paths', 'acceptance', 'checks', 'status'),
              ('blocker', 'evidence'))
        identifier(task['id'])
        require(task['id'] not in tasks, 'Duplicate task ID')
        file = pack_file(root, task['file'])
        file_key = file.relative_to(root).as_posix().casefold()
        require(file_key not in files, 'Duplicate task file')
        files.add(file_key)
        body = file.read_text(encoding='utf-8-sig')
        require(not re.search(r'^\s*(?:State|Status)\s*:', body, re.I | re.M),
                'Task state belongs only in manifest, not task text')
        if len(body.split()) > 1200:
            warnings.append(task['id'] + ': task exceeds the initial 1200-word authoring target; inspect boundaries')
        require(task['status'] in STATES, 'Invalid task state')
        for name in ('requirements', 'allowed_paths', 'acceptance'):
            strings(task[name])
        strings(task['depends_on'], nonempty=False)
        require(set(task['requirements']) <= set(requirements), 'Task references an unknown requirement')
        covered.update(task['requirements'])
        for path in task['allowed_paths']:
            portable_path(path)
        require(isinstance(task['checks'], list) and task['checks'], 'Task has no declared checks')
        check_ids = set()
        for check in task['checks']:
            shape(check, ('id', 'instruction'))
            identifier(check['id'])
            require(check['id'] not in check_ids and text(check['instruction']), 'Invalid/duplicate check')
            check_ids.add(check['id'])
        if task['status'] in ACTIVE:
            require(approval['status'] == 'approved', 'Active task lacks declared scope approval')
            require(all(requirements[r]['status'] == 'approved' for r in task['requirements']),
                    'Active task includes unapproved requirements')
            require('REPLACE_' not in body + spec_text + pack_text + json.dumps(task) + data['feature_id'] + data['spec_revision'],
                    'Active task still contains template placeholders')
        if task['status'] == 'blocked':
            require(text(task.get('blocker')), 'Blocked task needs an exact blocker')
        if task['status'] == 'done':
            evidence = load_json(pack_file(root, task.get('evidence')))
            shape(evidence, ('source_revision', 'spec_revision', 'spec_sha256', 'environment', 'checks', 'acceptance_observations'))
            spec_path = pack_file(root, data['spec_file'])
            # Raw-byte hashes from 2.3.x evidence stay valid while the file bytes are unchanged.
            accepted = {spec_digest(spec_path), hashlib.sha256(spec_path.read_bytes()).hexdigest()}
            require(evidence['spec_revision'] == data['spec_revision'] and evidence['spec_sha256'] in accepted,
                    'Completion evidence does not match current specification')
            require(text(evidence['source_revision']) and text(evidence['environment']), 'Missing evidence context')
            strings(evidence['acceptance_observations'])
            require(isinstance(evidence['checks'], list), 'Missing check evidence')
            seen = set()
            for result in evidence['checks']:
                shape(result, ('id', 'result', 'evidence'))
                require(result['id'] in check_ids and result['id'] not in seen, 'Unknown/duplicate evidence check')
                require(result['result'] == 'passed' and text(result['evidence']), 'Done task has incomplete/failed check')
                seen.add(result['id'])
            require(seen == check_ids, 'Done task lacks all required check results')
        tasks[task['id']] = task
    require(all(r['status'] != 'approved' or rid in covered for rid, r in requirements.items()),
            'Approved requirement has no task')
    indegree = {tid: 0 for tid in tasks}
    children = {tid: [] for tid in tasks}
    for tid, task in tasks.items():
        for dep in task['depends_on']:
            require(dep in tasks and dep != tid, 'Unknown or self dependency')
            indegree[tid] += 1
            children[dep].append(tid)
        if task['status'] in ('in_progress', 'done'):
            require(all(tasks[d]['status'] == 'done' for d in task['depends_on']),
                    'Started/completed task has unfinished dependencies')
    ready = [tid for tid, n in indegree.items() if n == 0]
    visited = 0
    while ready:
        tid = ready.pop()
        visited += 1
        for child in children[tid]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    require(visited == len(tasks), 'Dependency cycle')
    eligible = None
    if selected is not None:
        require(selected in tasks, 'Unknown selected task')
        task = tasks[selected]
        eligible = task['status'] in ('ready', 'in_progress') and all(
            tasks[d]['status'] == 'done' for d in task['depends_on'])
    return {'valid': True, 'tasks': len(tasks), 'requirements': len(requirements),
            'selected_task': selected, 'eligible_by_declaration': eligible, 'warnings': warnings,
            'limit': 'Structure only: no commands run; no proof of approval, code correctness, edit containment or security.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pack', type=Path)
    parser.add_argument('--task')
    parser.add_argument('--spec-hash', action='store_true',
                        help='print the spec_sha256 value to record in completion evidence and exit')
    args = parser.parse_args(argv)
    try:
        if args.spec_hash:
            root = args.pack.resolve(strict=True)
            data = load_json(pack_file(root, 'manifest.json'))
            require(isinstance(data, dict) and text(data.get('spec_file')), 'Manifest lacks spec_file')
            print(json.dumps({'spec_file': data['spec_file'], 'spec_revision': data.get('spec_revision'),
                              'spec_sha256': spec_digest(pack_file(root, data['spec_file']))}, indent=2))
            return 0
        report = validate(args.pack, args.task)
        code = 2 if report['eligible_by_declaration'] is False else 0
    except (ValueError, OSError, TypeError, KeyError, RecursionError) as exc:
        report, code = {'valid': False, 'error': str(exc)}, 1
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
