"""
Test script to verify all changes since the last git commit.
Uses Flask test client — no running server needed.
"""
import os
import sys
import zipfile
import io
import re

# Ensure we can import from the project
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import init_db

init_db()

errors = []
passed = []

def check(condition, pass_msg, fail_msg):
    if condition:
        passed.append(pass_msg)
    else:
        errors.append(fail_msg)

client = app.test_client()
app.config['TESTING'] = True

# ---- 1. Dashboard ----
r = client.get('/')
text = r.data.decode()
check(r.status_code == 200, 'Dashboard loads (200)', f'Dashboard FAILED ({r.status_code})')
check('Laser (eyes)' in text, 'Dashboard: Laser eyes count displayed', 'Dashboard: Missing Laser (eyes) label')
check('YAG:' in text, 'Dashboard: YAG count displayed', 'Dashboard: Missing YAG count')
check('SLT:' in text, 'Dashboard: SLT count displayed', 'Dashboard: Missing SLT count')
check('Procedures:' in text, 'Dashboard: Derm procedures count displayed', 'Dashboard: Missing Derm procedures count')
check('Export All Logs (ZIP)' in text, 'Dashboard: Export ZIP link present', 'Dashboard: Missing Export ZIP link')
check('/export/all/zip' in text, 'Dashboard: ZIP export URL correct', 'Dashboard: ZIP export URL missing')

# ---- 2. Log category pages ----
categories = ['Priority Patients', 'Dermatology', 'Laser', 'Guzman Referrals', 'Darlene Prosthetics']
for cat in categories:
    r = client.get(f'/log/{cat}')
    check(r.status_code == 200, f'Log view [{cat}] loads (200)', f'Log view [{cat}] FAILED ({r.status_code})')

# ---- 3. Dermatology: # Procedures column + fields ----
r = client.get('/log/Dermatology')
text = r.data.decode()
check('# Procedures' in text, 'Derm log: # Procedures column present', 'Derm log: Missing # Procedures column')
check('procedure_count' in text, 'Derm log: procedure_count field in modal', 'Derm log: procedure_count missing in modal')

# ---- 4. Dropdowns in log views ----
r = client.get('/log/Laser')
text = r.data.decode()
check('<select' in text and 'procedure_type' in text, 'Laser: procedure_type select present', 'Laser: procedure_type select missing')

r = client.get('/log/Guzman Referrals')
text = r.data.decode()
check('<select' in text and 'name="problem"' in text, 'Guzman: problem select present', 'Guzman: problem select missing')
check('name="appointment_timeframe"' in text, 'Guzman: appointment_timeframe select present', 'Guzman: appointment_timeframe missing')

r = client.get('/log/Priority Patients')
text = r.data.decode()
check('name="surgery_type"' in text and '<select' in text, 'Priority: surgery_type select present', 'Priority: surgery_type select missing')

# ---- 5. CSV exports ----
for cat in categories:
    r = client.get(f'/export/{cat}/csv')
    check(r.status_code == 200, f'CSV export [{cat}] (200)', f'CSV export [{cat}] FAILED ({r.status_code})')

r = client.get('/export/Dermatology/csv')
text = r.data.decode()
check('# Procedures' in text, 'Derm CSV: # Procedures header', 'Derm CSV: Missing # Procedures header')
check('Follow-up Date' not in text, 'Derm CSV: No Follow-up Date column (removed)', 'Derm CSV: Follow-up Date column still present')

r = client.get('/export/Darlene Prosthetics/csv')
text = r.data.decode()
check('Notes' in text, 'Darlene CSV: Notes header present', 'Darlene CSV: Missing Notes header')

r = client.get('/export/Priority Patients/csv')
text = r.data.decode()
check('Follow-up' not in text, 'Priority CSV: Follow-up removed', 'Priority CSV: Follow-up still present')

# ---- 6. ZIP export ----
r = client.get('/export/all/zip')
check(r.status_code == 200, 'ZIP export (200)', f'ZIP export FAILED ({r.status_code})')
check('application/zip' in r.content_type, 'ZIP: correct Content-Type', f'ZIP: wrong Content-Type ({r.content_type})')
check(len(r.data) > 0, f'ZIP: non-empty ({len(r.data)} bytes)', 'ZIP: empty content')
try:
    zf = zipfile.ZipFile(io.BytesIO(r.data))
    names = zf.namelist()
    check(len(names) == 5, f'ZIP: contains {len(names)} files (correct)', f'ZIP: expected 5 files, got {len(names)}: {names}')
    expected_files = [
        'priority_patients_log.csv', 'dermatology_log.csv', 'laser_log.csv',
        'guzman_referrals_log.csv', 'darlene_prosthetics_log.csv'
    ]
    for ef in expected_files:
        check(ef in names, f'ZIP: {ef} present', f'ZIP: {ef} missing')
    zf.close()
except Exception as e:
    errors.append(f'ZIP: could not read zip: {e}')

# ---- 7. PDF exports ----
for cat in categories:
    r = client.get(f'/export/{cat}/pdf')
    check(r.status_code == 200, f'PDF export [{cat}] (200)', f'PDF export [{cat}] FAILED ({r.status_code})')
    check(r.content_type == 'application/pdf', f'PDF [{cat}]: correct Content-Type', f'PDF [{cat}]: wrong Content-Type ({r.content_type})')

# ---- 8. Search and Backups ----
r = client.get('/search?q=test')
check(r.status_code == 200, 'Search page (200)', f'Search page FAILED ({r.status_code})')

r = client.get('/backups')
check(r.status_code == 200, 'Backups page (200)', f'Backups page FAILED ({r.status_code})')

# ---- 9. CRUD: Add patient + log entries with new fields ----

# Add test patient
r = client.post('/patient/add', data={
    'full_name': 'ZZZ Test Patient',
    'chart_id': 'ZZZ-TEST-99999',
    'date_of_birth': '1990-01-01',
    'notes': 'Auto-test patient',
    'redirect_to': '/',
}, follow_redirects=False)
check(r.status_code in (302, 200), 'Add patient works', f'Add patient FAILED ({r.status_code})')

# Find test patient
r = client.get('/search?q=ZZZ-TEST-99999')
text = r.data.decode()
check('ZZZ Test Patient' in text, 'Test patient found in search', 'Test patient NOT found in search')

# Extract patient id
match = re.search(r'/patient/(\d+)', text)
patient_id = int(match.group(1)) if match else 1

# Add Derm log entry with procedure_count=3
r = client.post('/log-entry/add', data={
    'patient_id': patient_id,
    'log_category': 'Dermatology',
    'notes': 'Test derm entry',
    'advocate': 'TestAdvocate',
    'community': 'TestCommunity',
    'procedure': 'Injection',
    'procedure_count': 3,
    'derm_date': '2026-03-13',
    'redirect_to': '/log/Dermatology',
}, follow_redirects=False)
check(r.status_code in (302, 200), 'Add derm log entry with procedure_count=3', f'Add derm entry FAILED ({r.status_code})')

# Verify derm page shows the entry
r = client.get('/log/Dermatology')
text = r.data.decode()
check('ZZZ Test Patient' in text, 'Derm log: test patient entry visible', 'Derm log: test patient entry NOT visible')

# Add Laser log entry with YAG + OU
r = client.post('/log-entry/add', data={
    'patient_id': patient_id,
    'log_category': 'Laser',
    'procedure_type': 'YAG',
    'eye': 'OU',
    'laser_date': '2026-03-13',
    'redirect_to': '/log/Laser',
}, follow_redirects=False)
check(r.status_code in (302, 200), 'Add laser log entry (YAG, OU)', f'Add laser entry FAILED ({r.status_code})')

# Verify dashboard counts updated
r = client.get('/')
text = r.data.decode()
check(r.status_code == 200, 'Dashboard loads after CRUD operations', f'Dashboard FAILED after CRUD ({r.status_code})')

# ---- 10. Edit log entry ----
r = client.get('/log/Dermatology')
text = r.data.decode()
entry_match = re.search(r'/log-entry/(\d+)/edit', text)
if entry_match:
    entry_id = entry_match.group(1)
    r = client.get(f'/log-entry/{entry_id}/edit')
    text = r.data.decode()
    check(r.status_code == 200, f'Edit log entry page loads ({entry_id})', f'Edit log entry page FAILED ({r.status_code})')
    check('procedure_count' in text, 'Edit page: procedure_count field present', 'Edit page: procedure_count field missing')
    
    # Test actual edit with procedure_count
    r = client.post(f'/log-entry/{entry_id}/edit', data={
        'notes': 'Updated test note',
        'procedure': 'Biopsy',
        'procedure_count': 5,
        'advocate': 'UpdatedAdvocate',
        'community': 'UpdatedCommunity',
        'derm_date': '2026-03-14',
    }, follow_redirects=False)
    check(r.status_code in (302, 200), 'Edit log entry with procedure_count works', f'Edit log entry FAILED ({r.status_code})')
else:
    errors.append('No log entry found to test edit')

# ---- 11. Cleanup: delete test data ----
r = client.post(f'/patient/{patient_id}/delete', follow_redirects=False)
check(r.status_code in (302, 200), 'Cleanup: test patient deleted', f'Cleanup FAILED ({r.status_code})')

# ---- SUMMARY ----
print()
print('=' * 60)
print(f'  RESULTS: {len(passed)} passed, {len(errors)} failed')
print('=' * 60)
for p in passed:
    print(f'  ✅ {p}')
if errors:
    print()
    print(f'  FAILURES ({len(errors)}):')
    print('-' * 60)
    for e in errors:
        print(f'  ❌ {e}')
    print()
    sys.exit(1)
else:
    print()
    print('  🎉 ALL TESTS PASSED!')
    print()
