from pathlib import Path


START_SCRIPT = Path(__file__).resolve().parents[1] / "start-windows.bat"


def test_start_windows_migre_la_base_avant_uvicorn():
    script = START_SCRIPT.read_text(encoding="utf-8")

    pip_command = '"%VENV_PYTHON%" -m pip install -q -r requirements.txt'
    migration_command = '"%VENV_PYTHON%" -m alembic upgrade head'
    server_command = '"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000'

    assert pip_command in script
    assert migration_command in script
    assert server_command in script
    assert script.index(pip_command) < script.index(migration_command) < script.index(server_command)
    assert "\npip install" not in script
    assert "\nuvicorn " not in script
