#!/usr/bin/env python3
"""Validate FEATURES.txt, TASKS.txt, and TESTS.txt YAML manifests.

Checks performed:
- Unique IDs for features, tasks, tests
- Each feature.tasks item exists in TASKS.txt
- Each task.tests item exists in TESTS.txt
- Each test.covers entry references an existing feature and AC id

Usage: python3 scripts/validate_project_manifests.py
Requires: PyYAML (`pip install pyyaml`) or will instruct how to install.
"""
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    print("PyYAML is required. Install with: pip install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]

def load_yaml(path: Path):
    if not path.exists():
        return {}
    text = path.read_text()
    try:
        return yaml.safe_load(text) or {}
    except Exception as e:
        print(f"Failed to parse {path}: {e}")
        sys.exit(2)

def get_tests_for_ac(tests, feature_id, ac_id):
    """Get all test IDs that cover a specific acceptance criterion.
    
    Args:
        tests: List of test dictionaries from TESTS.txt
        feature_id: Feature ID (e.g., 'feature1')
        ac_id: Acceptance criterion ID (e.g., 'AC1')
    
    Returns:
        List of test IDs that cover the specified feature/AC combination
    """
    return [
        test['id'] for test in tests
        if 'covers' in test
        for cover in test.get('covers', [])
        if cover.get('feature') == feature_id and cover.get('ac') == ac_id
    ]


def build_test_to_tasks_map(tasks):
    """Build mapping from test ID -> list of task IDs that own the test."""
    test_to_tasks = {}
    for task in tasks:
        task_id = task.get('id')
        if not task_id:
            continue
        for test_id in task.get('tests', []) or []:
            test_to_tasks.setdefault(test_id, []).append(task_id)
    return test_to_tasks


def get_epics_for_test(test_id, tasks_by_id, test_to_tasks):
    """Return sorted epic IDs for a given test by looking up associated task(s)."""
    epics = set()
    for task_id in test_to_tasks.get(test_id, []):
        task = tasks_by_id.get(task_id) or {}
        for epic_id in task.get('epic', []) or []:
            epics.add(epic_id)
    return sorted(epics)

def main():
    epics = load_yaml(ROOT / 'EPICS.txt').get('epics', [])
    features = load_yaml(ROOT / 'FEATURES.txt').get('features', [])
    tasks = load_yaml(ROOT / 'TASKS.txt').get('tasks', [])
    tests = load_yaml(ROOT / 'TESTS.txt').get('tests', [])

    epics_by_id = {e['id']: e for e in epics if 'id' in e}
    features_by_id = {f['id']: f for f in features if 'id' in f}
    tasks_by_id = {t['id']: t for t in tasks if 'id' in t}
    tests_by_id = {tt['id']: tt for tt in tests if 'id' in tt}
    test_to_tasks = build_test_to_tasks_map(tasks)

    errors = []

    # Unique ID checks
    if len(epics_by_id) != len(epics):
        errors.append('Duplicate epic IDs found')
    if len(features_by_id) != len(features):
        errors.append('Duplicate feature IDs found')
    if len(tasks_by_id) != len(tasks):
        errors.append('Duplicate task IDs found')
    if len(tests_by_id) != len(tests):
        errors.append('Duplicate test IDs found')

    # Feature -> tasks
    for fid, f in features_by_id.items():
        for tid in f.get('tasks', []) or []:
            if tid not in tasks_by_id:
                errors.append(f'Feature {fid} references unknown task {tid}')
        # build AC map
        ac_ids = {ac['id'] for ac in f.get('acceptance_criteria', []) or [] if 'id' in ac}
        # tests_map references
        for ac, tlist in (f.get('tests_map') or {}).items():
            if ac not in ac_ids:
                errors.append(f'Feature {fid} tests_map references unknown AC {ac}')
            for tid in tlist:
                if tid not in tests_by_id:
                    errors.append(f'Feature {fid} tests_map references unknown test {tid} for AC {ac}')

    # Task -> tests
    for tid, t in tasks_by_id.items():
        task_epics = t.get('epic')
        if not isinstance(task_epics, list) or not task_epics:
            errors.append(f'Task {tid} must define epic as a non-empty list (e.g. epic: [E2])')
        else:
            for epic_id in task_epics:
                if epic_id not in epics_by_id:
                    errors.append(f'Task {tid} references unknown epic {epic_id}')

        for testid in t.get('tests', []) or []:
            if testid not in tests_by_id:
                errors.append(f'Task {tid} references unknown test {testid}')

    # Every test must be owned by at least one task
    for test_id in tests_by_id:
        if not test_to_tasks.get(test_id):
            errors.append(f'Test {test_id} is not associated with any task via TASKS.txt tests list')

    # Test covers -> feature:AC
    for testid, tt in tests_by_id.items():
        for cover in tt.get('covers', []) or []:
            feat = cover.get('feature')
            ac = cover.get('ac')
            if feat not in features_by_id:
                errors.append(f'Test {testid} covers unknown feature {feat}')
            else:
                # verify AC exists in feature
                ac_list = {a['id'] for a in features_by_id[feat].get('acceptance_criteria', []) or [] if 'id' in a}
                if ac not in ac_list:
                    errors.append(f'Test {testid} covers unknown AC {ac} for feature {feat}')

    if errors:
        print('\nValidation failed:')
        for e in errors:
            print('- ' + e)
        sys.exit(1)

    print('Validation passed: manifests are consistent')

if __name__ == '__main__':
    main()
