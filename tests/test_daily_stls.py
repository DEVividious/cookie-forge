"""Daily STL files are canonical, never additional copies of build-local models."""
import datetime
import json
from pathlib import Path
import unittest

from helpers import project, run_json

class DailyBuilds(unittest.TestCase):
    def test_batch_has_one_stl_per_project_in_shared_day(self):
        root = Path(project('star.png', 'donut.png'))
        run_json('build', 'star.png', 'donut.png', '--size', '60', '--no-3d', cwd=root)
        day = root/'cookie-forge-output/exports'/datetime.date.today().isoformat()
        self.assertEqual(sorted(p.name for p in day.iterdir()), ['donut-60mm-v1.stl', 'star-60mm-v1.stl'])
        self.assertEqual(len(list(root.rglob('*.stl'))), 2)
        self.assertFalse(list(root.glob('cookie-forge-output/projects/*/builds/*/*.stl')))

    def test_reuse_retains_original_day_and_overwrite_moves_single_stl(self):
        root = Path(project('star.png'))
        run_json('build', 'star.png', '--size', '60', '--no-3d', cwd=root)
        directory = root/'cookie-forge-output/projects/star/builds/60mm-v1'
        path = directory/'project.json'
        m = json.loads(path.read_text())
        stl = next(f for f in m['files'] if f['role']=='stl')
        original = (directory/stl['path']).resolve()
        older = root/'cookie-forge-output/exports/2000-01-01'/original.name
        older.parent.mkdir(parents=True)
        original.rename(older)
        stl['path'] = '../../../../exports/2000-01-01/'+original.name
        path.write_text(json.dumps(m))
        result = run_json('build', '--from', str(directory), cwd=root)['cutters'][0]
        self.assertEqual(result['decision'], 'identical')
        self.assertFalse(original.exists())
        self.assertTrue(older.exists())
        run_json('build', '--from', str(directory), '--overwrite', cwd=root)
        self.assertFalse(older.exists())
        self.assertTrue(original.exists())
        self.assertEqual(len(list(root.rglob('*.stl'))), 1)


    def test_deleted_stl_keeps_project_history(self):
        root = Path(project('star.png'))
        run_json('build', 'star.png', '--size', '60', '--no-3d', cwd=root)
        directory = root/'cookie-forge-output/projects/star/builds/60mm-v1'
        path = directory/'project.json'
        saved = path.read_bytes()
        m = json.loads(saved)
        stl = next(f for f in m['files'] if f['role']=='stl')
        (directory/stl['path']).unlink()
        result = run_json('build', '--from', str(directory), '--dry-run', cwd=root)['cutters'][0]
        self.assertEqual(result['decision'], 'new_version')
        self.assertTrue(result['dir'].endswith('/60mm-v2/'))
        self.assertEqual(path.read_bytes(), saved)
        self.assertFalse(list(root.rglob('*.stl')))



if __name__ == '__main__':
    unittest.main()
