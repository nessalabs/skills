#!/usr/bin/env python3
"""Exercise the shipped trace helper through real ast-grep on isolated source."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / 'skills/engineering/trace/scripts/expand.py'
FIXTURE = '''def root():
    first()
    second()
    first()

def first():
    leaf()
    root()

def second():
    leaf()

def leaf():
    pass
'''

class TraceBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = os.environ.get('AST_GREP_BIN') or shutil.which('ast-grep')
        if not parser:
            raise RuntimeError('Install ast-grep or set AST_GREP_BIN; parser is required')
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        (cls.root/'fixture.py').write_text(FIXTURE)
        bindir = cls.root/'bin'
        bindir.mkdir()
        (bindir/'ast-grep').symlink_to(Path(parser).resolve())
        cls.env = {**os.environ, 'PATH': str(bindir)+os.pathsep+os.environ.get('PATH','')}
        cls.parser_version = subprocess.check_output([parser,'--version'], text=True).strip()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def trace(self, depth, symbol='root'):
        run = subprocess.run([sys.executable, str(HELPER), symbol, '--root', str(self.root),
                              '--lang','python','--in','fixture.py','--depth',str(depth),'--json'],
                             env=self.env,capture_output=True,text=True,check=True)
        self.assertEqual(run.stderr, '', 'Unexpected parser diagnostics cannot count as an empty trace')
        return json.loads(run.stdout)

    def names(self, depth):
        return [row['symbol'] for row in self.trace(depth) if row.get('def')]

    def test_one_hop_and_call_text_deduplication(self):
        rows=self.trace(1)
        self.assertEqual([row['symbol'] for row in rows], ['root'])
        self.assertEqual([call['callee'] for call in rows[0]['calls']], ['first','second'])

    def test_positive_depth_limits_recursive_expansion(self):
        self.assertEqual(self.names(2), ['root','first','second'])

    def test_depth_first_order_and_shared_leaf_cycle_deduplication(self):
        self.assertEqual(self.names(3), ['root','first','leaf','second'])

    def test_nonpositive_depth_still_inspects_root(self):
        self.assertEqual(self.names(0), ['root'])
        self.assertEqual(self.names(-1), ['root'])

    def test_recursive_candidate_file_can_expand_multiple_same_name_methods(self):
        source = self.root/'fixture.py'
        source.write_text("def root():\n    obj.act()\n\nclass First:\n    def act(self):\n        pass\n\nclass Second:\n    def act(self):\n        pass\n")
        try:
            rows = self.trace(2)
            self.assertEqual([row['symbol'] for row in rows], ['root','act','act'])
            keys = [(row['def']['file'],row['def']['start']) for row in rows]
            self.assertEqual(len(keys),len(set(keys)))
        finally:
            source.write_text(FIXTURE)

    def test_missing_definition_is_reported_as_gap(self):
        rows=self.trace(1,'absent')
        self.assertEqual(rows[0]['defs'], [])
        self.assertIn('no definition found',rows[0]['note'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
