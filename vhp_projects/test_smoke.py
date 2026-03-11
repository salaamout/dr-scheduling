"""Quick smoke test for the updated app."""
from app import create_app
from app.models import Patient

app = create_app()

with app.test_client() as client:
    r = client.get('/')
    print(f'GET /: {r.status_code}')
    assert r.status_code == 200

    r = client.get('/count-summary')
    print(f'GET /count-summary: {r.status_code}')
    assert r.status_code == 200

    r = client.get('/trash')
    print(f'GET /trash: {r.status_code}')
    assert r.status_code == 200

    r = client.get('/new')
    print(f'GET /new: {r.status_code}')
    assert r.status_code == 200

    r = client.get('/?search=test&surgery_date=2026-01-01')
    print(f'GET /?search=test: {r.status_code}')
    assert r.status_code == 200

with app.app_context():
    patients = Patient.query.limit(3).all()
    for p in patients:
        print(f'  Patient: name={repr(p.name)}, eye={repr(p.eye)}, cancelled={repr(p.cancelled)}')

print('All tests passed!')
