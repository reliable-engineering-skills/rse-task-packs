import copy
import hashlib
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/validate_task_pack.py'
spec = importlib.util.spec_from_file_location('task_pack', SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class TaskPackTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'tasks').mkdir()
        (self.root / 'SPEC.md').write_text('# FR-001\nReject negative quantities.\n', encoding='utf-8')
        (self.root / 'DECISIONS.md').write_text('Fixture: user requested negative-quantity rejection.\n', encoding='utf-8')
        (self.root / 'tasks/T001.md').write_text('Reject negative quantities and run its focused check.\n', encoding='utf-8')
        self.data = {
            'schema_version': 1, 'feature_id': 'quantity-validation', 'spec_file': 'SPEC.md',
            'spec_revision': 'fixture-v1', 'approval': {'status': 'approved', 'evidence': 'DECISIONS.md'},
            'requirements': [{'id': 'FR-001', 'source': 'SPEC.md#fr-001', 'status': 'approved'}],
            'tasks': [{'id': 'T001', 'file': 'tasks/T001.md', 'requirements': ['FR-001'], 'depends_on': [],
                       'allowed_paths': ['src/quantity.py', 'tests/test_quantity.py'],
                       'acceptance': ['Negative quantity fails without writing an order'],
                       'checks': [{'id': 'CHK-001', 'instruction': 'Run focused quantity validation cases'}],
                       'status': 'ready'}]}

    def write(self):
        (self.root / 'manifest.json').write_text(json.dumps(self.data), encoding='utf-8')

    def check(self, selected=None):
        self.write()
        return validator.validate(self.root, selected)

    def second_task(self):
        second = copy.deepcopy(self.data['tasks'][0])
        second.update(id='T002', file='tasks/T002.md')
        (self.root / 'tasks/T002.md').write_text('A second fixture task.\n', encoding='utf-8')
        self.data['tasks'].append(second)
        return second

    def complete(self, task=None):
        task = task or self.data['tasks'][0]
        (self.root / 'evidence').mkdir(exist_ok=True)
        task.update(status='done', evidence='evidence/' + task['id'] + '.json')
        evidence = {'source_revision': 'fixture-result-v2', 'spec_revision': self.data['spec_revision'],
                    'spec_sha256': validator.spec_digest(self.root / 'SPEC.md'), 'environment': 'isolated unit fixture',
                    'checks': [{'id': 'CHK-001', 'result': 'passed', 'evidence': 'Fixture result, not a real project run'}],
                    'acceptance_observations': ['Fixture: invalid input produced no order write']}
        (self.root / task['evidence']).write_text(json.dumps(evidence), encoding='utf-8')

    def test_ready_task_is_eligible_without_executing_checks(self):
        self.assertTrue(self.check('T001')['eligible_by_declaration'])
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),
                         ['DECISIONS.md', 'SPEC.md', 'manifest.json', 'tasks'])

    def test_proposed_requirement_cannot_be_executed(self):
        self.data['requirements'][0]['status'] = 'proposed'
        with self.assertRaisesRegex(ValueError, 'unapproved'):
            self.check()

    def test_pending_scope_cannot_be_executed(self):
        self.data['approval'] = {'status': 'pending', 'evidence': ''}
        with self.assertRaisesRegex(ValueError, 'scope approval'):
            self.check()

    def test_draft_is_structurally_valid_but_not_eligible(self):
        self.data['tasks'][0]['status'] = 'draft'
        self.data['approval'] = {'status': 'pending', 'evidence': ''}
        self.assertFalse(self.check('T001')['eligible_by_declaration'])

    def test_unknown_requirement_is_rejected(self):
        self.data['tasks'][0]['requirements'] = ['FR-999']
        with self.assertRaisesRegex(ValueError, 'unknown requirement'):
            self.check()

    def test_orphan_approved_requirement_is_rejected(self):
        self.data['requirements'].append({'id': 'FR-002', 'source': 'SPEC.md', 'status': 'approved'})
        with self.assertRaisesRegex(ValueError, 'no task'):
            self.check()

    def test_dependency_cycle_is_rejected(self):
        second = self.second_task()
        second['depends_on'] = ['T001']
        self.data['tasks'][0]['depends_on'] = ['T002']
        with self.assertRaisesRegex(ValueError, 'cycle'):
            self.check()

    def test_ready_task_waits_for_dependency_evidence(self):
        second = self.second_task()
        second['depends_on'] = ['T001']
        self.assertFalse(self.check('T002')['eligible_by_declaration'])
        self.complete()
        self.assertTrue(self.check('T002')['eligible_by_declaration'])

    def test_started_task_with_unfinished_dependency_is_rejected(self):
        second = self.second_task()
        second.update(depends_on=['T001'], status='in_progress')
        with self.assertRaisesRegex(ValueError, 'unfinished dependencies'):
            self.check()

    def test_done_task_requires_all_check_evidence(self):
        self.complete()
        path = self.root / 'evidence/T001.json'
        result = json.loads(path.read_text(encoding='utf-8'))
        result['checks'] = []
        path.write_text(json.dumps(result), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'required check'):
            self.check()

    def test_done_task_cannot_hide_failed_check(self):
        self.complete()
        path = self.root / 'evidence/T001.json'
        result = json.loads(path.read_text(encoding='utf-8'))
        result['checks'][0]['result'] = 'failed'
        path.write_text(json.dumps(result), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'incomplete/failed'):
            self.check()

    def test_completed_task_is_valid_but_not_selected_for_reexecution(self):
        self.complete()
        self.assertFalse(self.check('T001')['eligible_by_declaration'])

    def test_path_traversal_and_absolute_paths_are_rejected(self):
        for path in ('../SPEC.md', '/SPEC.md', 'C:/SPEC.md', 'tasks/../SPEC.md', 'tasks\\T001.md'):
            with self.subTest(path=path):
                self.data['tasks'][0]['file'] = path
                with self.assertRaises(ValueError):
                    self.check()

    def test_directory_allowed_paths_may_end_with_one_slash(self):
        self.data['tasks'][0]['allowed_paths'] = ['tests/', 'src/admin/', 'auth.py']
        self.assertTrue(self.check()['valid'])

    def test_unsafe_directory_paths_stay_rejected(self):
        for path in ('/', '//', '../', 'src//', 'src//x', './', '/abs/', 'C:/x/'):
            with self.subTest(path=path):
                self.data['tasks'][0]['allowed_paths'] = [path]
                with self.assertRaises(ValueError):
                    self.check()

    def test_duplicate_ids_are_rejected(self):
        self.second_task()['id'] = 'T001'
        with self.assertRaisesRegex(ValueError, 'Duplicate task ID'):
            self.check()

    def test_duplicate_file_with_different_fragment_is_rejected(self):
        self.second_task()['file'] = 'tasks/T001.md#other'
        with self.assertRaisesRegex(ValueError, 'Duplicate task file'):
            self.check()

    def test_blocked_task_requires_a_reason(self):
        self.data['tasks'][0]['status'] = 'blocked'
        with self.assertRaisesRegex(ValueError, 'blocker'):
            self.check()

    def test_active_task_rejects_unresolved_spec_placeholders(self):
        (self.root / 'SPEC.md').write_text('# FR-001\nREPLACE_WITH_REQUIREMENT', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'placeholders'):
            self.check()

    def test_duplicate_json_keys_are_not_silently_accepted(self):
        self.write()
        path = self.root / 'manifest.json'
        path.write_text(path.read_text(encoding='utf-8').replace('"schema_version": 1',
                        '"schema_version": 1, "schema_version": 1'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            validator.validate(self.root)

    def test_missing_requirement_anchor_rejected(self):
        self.data['requirements'][0]['source'] = 'SPEC.md#missing'
        with self.assertRaisesRegex(ValueError, 'Missing requirement anchor'):
            self.check()

    def test_changed_spec_invalidates_completion(self):
        self.complete()
        (self.root / 'SPEC.md').write_text('# FR-001\nChanged acceptance.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'current specification'):
            self.check()

    def test_changed_spec_revision_invalidates_completion(self):
        self.complete()
        self.data['spec_revision'] = 'fixture-v2'
        with self.assertRaisesRegex(ValueError, 'current specification'):
            self.check()

    def test_task_text_cannot_claim_conflicting_state(self):
        (self.root / 'tasks/T001.md').write_text('State: DRAFT. Do not execute.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'state belongs only'):
            self.check()

    def test_cli_returns_not_ready_for_draft_without_running_commands(self):
        self.data['tasks'][0]['status'] = 'draft'
        self.write()
        output = io.StringIO()
        with redirect_stdout(output):
            code = validator.main([str(self.root), '--task', 'T001'])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(output.getvalue())['eligible_by_declaration'])

    def test_cli_returns_error_for_invalid_scope_and_no_success_record(self):
        self.data['approval']['status'] = 'pending'
        self.write()
        output = io.StringIO()
        with redirect_stdout(output):
            code = validator.main([str(self.root), '--task', 'T001'])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(output.getvalue())['valid'])


    def test_legacy_raw_byte_hash_remains_valid(self):
        self.complete()
        evidence_path = self.root / 'evidence/T001.json'
        evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
        evidence['spec_sha256'] = hashlib.sha256((self.root / 'SPEC.md').read_bytes()).hexdigest()
        evidence_path.write_text(json.dumps(evidence), encoding='utf-8')
        self.assertTrue(self.check()['valid'])

    def test_crlf_checkout_keeps_completion_valid(self):
        self.complete()
        self.check()
        spec_path = self.root / 'SPEC.md'
        lf = spec_path.read_bytes().replace(b'\r\n', b'\n')
        for checkout in (lf, lf.replace(b'\n', b'\r\n')):
            spec_path.write_bytes(checkout)
            self.assertTrue(self.check()['valid'])

    def test_bom_does_not_invalidate_completion(self):
        self.complete()
        spec_path = self.root / 'SPEC.md'
        spec_path.write_bytes(b'\xef\xbb\xbf' + spec_path.read_bytes())
        self.assertTrue(self.check()['valid'])

    def test_spec_hash_cli_prints_the_value_the_validator_expects(self):
        self.write()
        output = io.StringIO()
        with redirect_stdout(output):
            code = validator.main([str(self.root), '--spec-hash'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())['spec_sha256'],
                         validator.spec_digest(self.root / 'SPEC.md'))

    def test_repeated_heading_anchor_uses_numbered_suffix(self):
        (self.root / 'SPEC.md').write_text('# FR-001\nFirst.\n\n# Notes\nA.\n\n# Notes\nB.\n', encoding='utf-8')
        self.data['requirements'][0]['source'] = 'SPEC.md#notes-1'
        self.assertTrue(self.check()['valid'])

    def test_active_task_rejects_placeholders_in_pack_decisions(self):
        (self.root / 'DECISIONS.md').write_text('Approval: REPLACE_WITH_ACTUAL_USER_DECISION\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'placeholders'):
            self.check()

    def test_draft_pack_may_keep_template_placeholders(self):
        (self.root / 'DECISIONS.md').write_text('Approval: REPLACE_WITH_ACTUAL_USER_DECISION\n', encoding='utf-8')
        self.data['tasks'][0]['status'] = 'draft'
        self.data['approval'] = {'status': 'pending', 'evidence': ''}
        self.assertTrue(self.check()['valid'])


if __name__ == '__main__':
    unittest.main()
