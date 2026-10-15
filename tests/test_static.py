from pathlib import Path
from fastapi.testclient import TestClient
from app import app


def test_frontend_and_assets_available():
    with TestClient(app) as c:
        for path, expected in [('/', 'text/html'),('/static/style.css', 'text/css'),('/static/app.js', 'javascript'),('/static/art/market.svg', 'svg'),('/static/art/vex.svg', 'svg'),('/static/art/nyra.svg', 'svg'),('/static/art/bronn.svg', 'svg'),('/static/art/cael.svg', 'svg')]:
            response=c.get(path)
            assert response.status_code==200, path
            assert expected in response.headers.get('content-type',''), path
            assert len(response.content)>300
        assert c.get('/health').json()['build']=='0.2.0'
        assert c.get('/app.py').status_code==404
        assert c.get('/game.py').status_code==404
        assert c.get('/requirements.txt').status_code==404


def test_frontend_has_all_required_actions_and_no_fixed_lan_link():
    static=Path(__file__).resolve().parents[1]/'static'
    html=(static/'index.html').read_text()
    js=(static/'app.js').read_text()
    css=(static/'style.css').read_text()
    for element_id in ('createBtn','joinBtn','roomInput','playerName','copyBtn','leaveBtn','readyBtn','rematchBtn','shopGrid','boardGrid','itemModal'):
        assert f'id="{element_id}"' in html
    for binding in ("$('#createBtn').onclick", "$('#joinBtn').onclick", "$('#copyBtn').onclick", "$('#leaveBtn').onclick", "$('#readyBtn').onclick", "$('#rematchBtn').onclick"):
        assert binding in js
    assert "location.host" in js and "'wss:'" in js and "socket.bufferedAmount" in js
    assert '[hidden]{display:none!important}' in css
    assert '127.0.0.1' not in js and 'localhost' not in js