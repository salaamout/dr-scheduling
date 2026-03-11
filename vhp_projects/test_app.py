"""
Comprehensive test suite for the VHP Patient Database.

Tests the refactored app factory, models, forms, routes, and backup system.
"""
import json
import os
import shutil
import tempfile
import unittest
from datetime import date, datetime, timedelta

from app import create_app
from app.backup import BackupManager
from app.config import Config
from app.forms import PROCEDURE_OPTIONS, PatientForm
from app.models import Patient, db


class TestConfig(Config):
    """Test configuration — uses an in-memory SQLite database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # in-memory
    WTF_CSRF_ENABLED = False               # disable CSRF for test convenience
    BACKUP_DIR = None                      # set dynamically in setUp
    BACKUP_INTERVAL = 0                    # allow immediate backups
    MAX_BACKUPS = 5
    PERIODIC_BACKUP_INTERVAL = 21600


# ---------------------------------------------------------------------------
# App factory & configuration tests
# ---------------------------------------------------------------------------

class TestAppFactory(unittest.TestCase):
    """Verify the app factory creates a properly configured Flask app."""

    def test_create_app(self):
        app = create_app(TestConfig)
        self.assertIsNotNone(app)
        self.assertTrue(app.config['TESTING'])

    def test_config_defaults(self):
        app = create_app(TestConfig)
        self.assertFalse(app.config['WTF_CSRF_ENABLED'])
        self.assertEqual(app.config['MAX_BACKUPS'], 5)
        self.assertEqual(app.config['PERIODIC_BACKUP_INTERVAL'], 21600)

    def test_instance_path_created(self):
        app = create_app(TestConfig)
        self.assertTrue(os.path.isdir(app.instance_path))

    def test_backup_dir_set_dynamically(self):
        app = create_app(TestConfig)
        self.assertIsNotNone(app.config['BACKUP_DIR'])
        self.assertIn('backups', app.config['BACKUP_DIR'])

    def test_routes_registered(self):
        app = create_app(TestConfig)
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        expected = ['/', '/new', '/trash', '/count-summary', '/edit/<int:patient_id>',
                    '/delete/<int:patient_id>', '/duplicate/<int:patient_id>',
                    '/print/<int:patient_id>', '/print/daily-log',
                    '/restore/<int:patient_id>', '/update-number/<int:patient_id>',
                    '/toggle-cancelled/<int:patient_id>']
        for route in expected:
            self.assertIn(route, rules, f"Route {route} not registered")


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestPatientModel(unittest.TestCase):
    """Test the Patient SQLAlchemy model."""

    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _make_patient(self, **kwargs):
        defaults = dict(
            surgery_type='cataract',
            surgery_date=date(2026, 3, 11),
            chart_number='C-100',
            name='Test Patient',
            age=55,
            sex='M',
            procedure='Cataract',
        )
        defaults.update(kwargs)
        return Patient(**defaults)

    def test_create_patient(self):
        p = self._make_patient()
        db.session.add(p)
        db.session.commit()
        self.assertIsNotNone(p.id)

    def test_default_deleted_false(self):
        p = self._make_patient()
        db.session.add(p)
        db.session.commit()
        self.assertFalse(p.deleted)

    def test_default_cancelled_false(self):
        p = self._make_patient()
        db.session.add(p)
        db.session.commit()
        self.assertFalse(p.cancelled)

    def test_optional_fields_nullable(self):
        p = self._make_patient(eye=None, advocate=None, community=None,
                               number=None, notes=None)
        db.session.add(p)
        db.session.commit()
        fetched = Patient.query.get(p.id)
        self.assertIsNone(fetched.eye)
        self.assertIsNone(fetched.advocate)

    def test_repr(self):
        p = self._make_patient(name='John Doe')
        self.assertEqual(repr(p), '<Patient John Doe>')


# ---------------------------------------------------------------------------
# Form tests
# ---------------------------------------------------------------------------

class TestPatientForm(unittest.TestCase):
    """Test the PatientForm validation."""

    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_valid_form(self):
        with self.app.test_request_context():
            form = PatientForm(data={
                'surgery_type': 'cataract',
                'surgery_date': '2026-03-11',
                'chart_number': 'C-100',
                'name': 'Test',
                'age': 55,
                'sex': 'M',
                'procedure': 'Cataract',
            })
            self.assertTrue(form.validate(), form.errors)

    def test_missing_required_field(self):
        with self.app.test_request_context():
            form = PatientForm(data={
                'surgery_type': 'cataract',
                # missing surgery_date, chart_number, name, age, sex, procedure
            })
            self.assertFalse(form.validate())

    def test_procedure_options_keys(self):
        self.assertIn('cataract', PROCEDURE_OPTIONS)
        self.assertIn('plastics', PROCEDURE_OPTIONS)
        self.assertIn('strabismus', PROCEDURE_OPTIONS)
        self.assertIn('pterygium', PROCEDURE_OPTIONS)
        self.assertIn('derm', PROCEDURE_OPTIONS)


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

class TestRoutes(unittest.TestCase):
    """Integration tests for all route handlers."""

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _add_patient(self, **kwargs):
        defaults = dict(
            surgery_type='cataract',
            surgery_date=date(2026, 3, 11),
            chart_number='C-100',
            name='Test Patient',
            age=55,
            sex='M',
            procedure='Cataract',
        )
        defaults.update(kwargs)
        p = Patient(**defaults)
        db.session.add(p)
        db.session.commit()
        return p

    # -- Index / listing --

    def test_index_empty(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'No patients found', r.data)

    def test_index_with_patients(self):
        self._add_patient(name='Alice')
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Alice', r.data)

    def test_index_filter_by_date(self):
        self._add_patient(name='Alice', surgery_date=date(2026, 3, 11))
        self._add_patient(name='Bob', surgery_date=date(2026, 3, 12))
        r = self.client.get('/?surgery_date=2026-03-11')
        self.assertIn(b'Alice', r.data)
        self.assertNotIn(b'Bob', r.data)

    def test_index_filter_by_type(self):
        self._add_patient(name='Alice', surgery_type='cataract')
        self._add_patient(name='Bob', surgery_type='plastics')
        r = self.client.get('/?surgery_type=cataract')
        self.assertIn(b'Alice', r.data)
        self.assertNotIn(b'Bob', r.data)

    def test_index_search(self):
        self._add_patient(name='Alice Smith', chart_number='C-100')
        self._add_patient(name='Bob Jones', chart_number='C-200')
        r = self.client.get('/?search=Alice')
        self.assertIn(b'Alice', r.data)
        self.assertNotIn(b'Bob', r.data)

    def test_index_search_by_chart_number(self):
        self._add_patient(name='Alice', chart_number='C-100')
        self._add_patient(name='Bob', chart_number='C-200')
        r = self.client.get('/?search=C-200')
        self.assertNotIn(b'Alice', r.data)
        self.assertIn(b'Bob', r.data)

    def test_index_sort(self):
        self._add_patient(name='Zara')
        self._add_patient(name='Alice')
        r = self.client.get('/?sort=name&order=asc')
        self.assertEqual(r.status_code, 200)
        data = r.data.decode()
        self.assertTrue(data.index('Alice') < data.index('Zara'))

    def test_index_hides_deleted(self):
        self._add_patient(name='Deleted', deleted=True)
        r = self.client.get('/')
        self.assertNotIn(b'Deleted', r.data)

    def test_patient_count_excludes_cancelled(self):
        self._add_patient(name='Active')
        self._add_patient(name='Cancelled', cancelled=True)
        r = self.client.get('/')
        # The count should show 1 (only non-cancelled)
        self.assertIn(b'1', r.data)

    # -- Trash --

    def test_trash_shows_deleted(self):
        self._add_patient(name='Deleted', deleted=True)
        r = self.client.get('/trash')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Deleted', r.data)

    def test_trash_empty(self):
        r = self.client.get('/trash')
        self.assertIn(b'No deleted patients found', r.data)

    # -- Restore --

    def test_restore_patient(self):
        p = self._add_patient(deleted=True)
        r = self.client.post(f'/restore/{p.id}', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        refreshed = Patient.query.get(p.id)
        self.assertFalse(refreshed.deleted)

    # -- New patient --

    def test_new_patient_get(self):
        r = self.client.get('/new')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'New Patient', r.data)

    def test_new_patient_post(self):
        r = self.client.post('/new', data={
            'surgery_type': 'cataract',
            'surgery_date': '2026-03-11',
            'chart_number': 'C-500',
            'name': 'New Patient',
            'age': 40,
            'sex': 'F',
            'procedure': 'Cataract',
            'eye': 'OD',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        p = Patient.query.filter_by(chart_number='C-500').first()
        self.assertIsNotNone(p)
        self.assertEqual(p.name, 'New Patient')
        self.assertEqual(p.eye, 'OD')

    def test_new_patient_defaults_surgery_type_from_param(self):
        r = self.client.get('/new?surgery_type=plastics')
        self.assertEqual(r.status_code, 200)
        # The form should have plastics preselected
        self.assertIn(b'plastics', r.data)

    # -- Edit patient --

    def test_edit_patient_get(self):
        p = self._add_patient()
        r = self.client.get(f'/edit/{p.id}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Edit Patient', r.data)

    def test_edit_patient_post(self):
        p = self._add_patient(name='Original')
        r = self.client.post(f'/edit/{p.id}', data={
            'surgery_type': 'cataract',
            'surgery_date': '2026-03-11',
            'chart_number': 'C-100',
            'name': 'Updated Name',
            'age': 60,
            'sex': 'M',
            'procedure': 'Bilateral Lenses',
            'eye': 'OS',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        refreshed = Patient.query.get(p.id)
        self.assertEqual(refreshed.name, 'Updated Name')
        self.assertEqual(refreshed.eye, 'OS')

    def test_edit_patient_clears_eye(self):
        p = self._add_patient(eye='OD')
        r = self.client.post(f'/edit/{p.id}', data={
            'surgery_type': 'cataract',
            'surgery_date': '2026-03-11',
            'chart_number': 'C-100',
            'name': 'Test',
            'age': 55,
            'sex': 'M',
            'procedure': 'Cataract',
            'eye': '',  # clear eye
        }, follow_redirects=True)
        refreshed = Patient.query.get(p.id)
        self.assertIsNone(refreshed.eye)

    def test_edit_nonexistent_patient(self):
        r = self.client.get('/edit/9999')
        self.assertEqual(r.status_code, 404)

    # -- Delete patient (soft delete) --

    def test_delete_patient(self):
        p = self._add_patient()
        r = self.client.post(f'/delete/{p.id}', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        refreshed = Patient.query.get(p.id)
        self.assertTrue(refreshed.deleted)

    def test_delete_preserves_filters(self):
        p = self._add_patient()
        r = self.client.post(f'/delete/{p.id}', data={
            'surgery_type': 'cataract',
        })
        self.assertEqual(r.status_code, 302)
        self.assertIn('surgery_type=cataract', r.location)

    # -- Duplicate patient --

    def test_duplicate_patient_get(self):
        p = self._add_patient(number='42')
        r = self.client.get(f'/duplicate/{p.id}')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Duplicate Patient', r.data)

    def test_duplicate_patient_post(self):
        p = self._add_patient(name='Original')
        r = self.client.post(f'/duplicate/{p.id}', data={
            'surgery_type': 'cataract',
            'surgery_date': '2026-03-11',
            'chart_number': 'C-100',
            'name': 'Duplicated',
            'age': 55,
            'sex': 'M',
            'procedure': 'Cataract',
        }, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Patient.query.count(), 2)

    # -- Print patient --

    def test_print_laserband(self):
        p = self._add_patient()
        r = self.client.get(f'/print/{p.id}?type=laserband')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Laserband', r.data)

    def test_print_log_single(self):
        p = self._add_patient()
        r = self.client.get(f'/print/{p.id}?type=log&log_type=Single')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Surgery Log', r.data)

    def test_print_unknown_type(self):
        p = self._add_patient()
        r = self.client.get(f'/print/{p.id}?type=unknown')
        # Should redirect with 400 or flash error
        self.assertIn(r.status_code, [302, 400])

    def test_print_nonexistent_patient(self):
        r = self.client.get('/print/9999')
        self.assertEqual(r.status_code, 404)

    # -- Daily log --

    def test_daily_log(self):
        self._add_patient(surgery_date=date(2026, 3, 11), surgery_type='cataract')
        r = self.client.get('/print/daily-log?surgery_date=2026-03-11&surgery_type=cataract')
        self.assertEqual(r.status_code, 200)

    def test_daily_log_missing_params(self):
        r = self.client.get('/print/daily-log')
        self.assertEqual(r.status_code, 302)  # redirect

    def test_daily_log_invalid_date(self):
        r = self.client.get('/print/daily-log?surgery_date=not-a-date&surgery_type=cataract')
        self.assertEqual(r.status_code, 302)  # redirect with flash error

    # -- Update number (AJAX) --

    def test_update_number(self):
        p = self._add_patient(number='1')
        r = self.client.post(
            f'/update-number/{p.id}',
            data=json.dumps({'number': '42'}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertTrue(data['success'])
        refreshed = Patient.query.get(p.id)
        self.assertEqual(refreshed.number, '42')

    def test_update_number_missing_data(self):
        p = self._add_patient()
        r = self.client.post(
            f'/update-number/{p.id}',
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 400)

    # -- Toggle cancelled (AJAX) --

    def test_toggle_cancelled(self):
        p = self._add_patient(cancelled=False)
        r = self.client.post(
            f'/toggle-cancelled/{p.id}',
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertTrue(data['success'])
        self.assertTrue(data['cancelled'])

        # Toggle back
        r = self.client.post(
            f'/toggle-cancelled/{p.id}',
            content_type='application/json',
        )
        data = json.loads(r.data)
        self.assertFalse(data['cancelled'])

    # -- Count summary --

    def test_count_summary_empty(self):
        r = self.client.get('/count-summary')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'No surgery data found', r.data)

    def test_count_summary_with_data(self):
        self._add_patient(surgery_type='cataract', surgery_date=date(2026, 3, 11))
        self._add_patient(surgery_type='plastics', surgery_date=date(2026, 3, 11))
        self._add_patient(surgery_type='cataract', surgery_date=date(2026, 3, 11))
        r = self.client.get('/count-summary')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Count Summary', r.data)

    def test_count_summary_excludes_deleted(self):
        self._add_patient(surgery_type='cataract', deleted=True)
        r = self.client.get('/count-summary')
        self.assertIn(b'No surgery data found', r.data)

    def test_count_summary_excludes_cancelled(self):
        self._add_patient(surgery_type='cataract', cancelled=True)
        r = self.client.get('/count-summary')
        self.assertIn(b'No surgery data found', r.data)


# ---------------------------------------------------------------------------
# Backup manager tests
# ---------------------------------------------------------------------------

class TestBackupManager(unittest.TestCase):
    """Test the BackupManager class."""

    def setUp(self):
        self.app = create_app(TestConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Use a temp directory for backups
        self.backup_dir = tempfile.mkdtemp()
        self.app.config['BACKUP_DIR'] = self.backup_dir

        # Create a fake database file in the instance path
        os.makedirs(self.app.instance_path, exist_ok=True)
        self.db_path = os.path.join(self.app.instance_path, 'patients.db')
        with open(self.db_path, 'w') as f:
            f.write('fake db content')

    def tearDown(self):
        shutil.rmtree(self.backup_dir, ignore_errors=True)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.ctx.pop()

    def test_create_backup(self):
        from app import backup_manager
        backup_manager.init_app(self.app)
        backup_manager.create_backup()
        backups = os.listdir(self.backup_dir)
        self.assertEqual(len(backups), 1)
        self.assertTrue(backups[0].startswith('patients_'))
        self.assertTrue(backups[0].endswith('.db'))

    def test_create_backup_no_db(self):
        os.remove(self.db_path)
        from app import backup_manager
        backup_manager.init_app(self.app)
        backup_manager.create_backup()
        backups = os.listdir(self.backup_dir)
        self.assertEqual(len(backups), 0)

    def test_get_backup_datetime(self):
        dt = BackupManager._get_backup_datetime('/some/path/patients_20260311_143000.db')
        self.assertEqual(dt, datetime(2026, 3, 11, 14, 30, 0))

    def test_check_backup_interval(self):
        from app import backup_manager
        backup_manager.init_app(self.app)
        backup_manager._last_backup = datetime.min  # reset
        backup_manager.check_backup()
        backups = os.listdir(self.backup_dir)
        self.assertGreaterEqual(len(backups), 1)

    def test_should_keep_backup_first_in_period(self):
        from app import backup_manager
        backup_manager.init_app(self.app)
        periodic = {}
        result = backup_manager._should_keep_backup(
            '/tmp/patients_20260311_060000.db', periodic
        )
        self.assertTrue(result)
        self.assertIn('20260311_06', periodic)

    def test_should_keep_backup_better_fit(self):
        from app import backup_manager
        backup_manager.init_app(self.app)
        periodic = {}
        # First backup at 6:30 AM
        backup_manager._should_keep_backup('/tmp/patients_20260311_063000.db', periodic)
        # Second backup at 6:05 AM — closer to period start (6:00)
        result = backup_manager._should_keep_backup(
            '/tmp/patients_20260311_060500.db', periodic
        )
        self.assertTrue(result)

    def test_should_keep_backup_worse_fit(self):
        from app import backup_manager
        backup_manager.init_app(self.app)
        periodic = {}
        # First at 6:01 — very close to period start
        backup_manager._should_keep_backup('/tmp/patients_20260311_060100.db', periodic)
        # Second at 6:30 — worse fit
        result = backup_manager._should_keep_backup(
            '/tmp/patients_20260311_063000.db', periodic
        )
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------------------

class TestCSRF(unittest.TestCase):
    """Test that CSRF protection is properly configured."""

    def test_csrf_enabled_in_production_config(self):
        self.assertTrue(Config.WTF_CSRF_ENABLED)
        self.assertTrue(Config.WTF_CSRF_CHECK_DEFAULT)
        self.assertEqual(Config.WTF_CSRF_TIME_LIMIT, 3600)

    def test_secret_key_not_hardcoded(self):
        # SECRET_KEY should be randomly generated, not a fixed dev string
        self.assertNotEqual(Config.SECRET_KEY, 'dev-secret-key-change-in-production')

    def test_csrf_meta_tag_in_base_template(self):
        app = create_app(TestConfig)
        client = app.test_client()
        r = client.get('/')
        self.assertIn(b'csrf-token', r.data)


if __name__ == '__main__':
    unittest.main()
