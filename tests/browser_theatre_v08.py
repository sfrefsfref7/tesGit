"""Functional UI E2E with the real FastAPI app mounted in-memory, no open PC ports.
Browser network routing is only a transport shim; gameplay uses real app endpoints.
"""
import json, mimetypes, os
from pathlib import Path
from urllib.parse import urlparse
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright, expect
import app as game_server

ROOT=Path(__file__).resolve().parents[1]
PROOF=ROOT/'evidence-v08'
PROOF.mkdir(exist_ok=True)
URL=os.environ.get('NMD_BASE','https://nightmarket-test.invalid').rstrip('/')
client=TestClient(game_server.app)


def intercept(route):
    req=route.request
    path=urlparse(req.url).path
    try:
        if path.startswith('/static/'):
            file=ROOT/path.lstrip('/')
            if not file.is_file() or not file.resolve().is_relative_to(ROOT.resolve()):
                route.fulfill(status=404,body='not found');return
            content_type=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            route.fulfill(status=200,body=file.read_bytes(),content_type=content_type);return
        if path=='/expedition':
            route.fulfill(status=200,body=(ROOT/'static/expedition.html').read_bytes(),content_type='text/html');return
        if path=='/':
            route.fulfill(status=200,body=(ROOT/'static/index.html').read_bytes(),content_type='text/html');return
        if path.startswith('/api/') or path=='/health':
            if req.method=='POST':
                reply=client.post(path,content=req.post_data or '',headers={'content-type':'application/json'})
            else:reply=client.get(path)
            route.fulfill(status=reply.status_code,body=reply.content,content_type=reply.headers.get('content-type','application/json'));return
        route.fulfill(status=404,body='not found')
    except Exception as exc:
        route.fulfill(status=500,body=str(exc))
        raise


def run():
    report={'build':'v0.8.0','transport':'CI-local FastAPI + Chromium visual functional test (not public internet)' if os.environ.get('NMD_BASE') else 'in-memory FastAPI + Chromium visual functional test (not public internet)', 'checks':{}, 'javascript_errors':[], 'failed_requests':[]}
    with sync_playwright() as p:
        options={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
        if os.path.exists('/usr/bin/chromium'):options['executable_path']='/usr/bin/chromium'
        browser=p.chromium.launch(**options)
        for width,height,kind in [(1440,900,'desktop'),(390,844,'mobile')]:
            context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1, is_mobile=(kind=='mobile'), has_touch=(kind=='mobile'), ignore_https_errors=True)
            page=context.new_page()
            if not os.environ.get('NMD_BASE'):page.route('**/*',intercept)
            page.on('pageerror',lambda e:report['javascript_errors'].append(str(e)))
            page.on('requestfailed',lambda r:report['failed_requests'].append(str(r.url)))
            page.goto(URL+'/expedition',wait_until='networkidle')
            expect(page.locator('#opening')).to_be_visible()
            page.screenshot(path=str(PROOF/f'{kind}-hero-select.png'),full_page=True)
            page.locator('#gameMenuToggle').click()
            expect(page.locator('#gameMenuPanel')).to_be_visible()
            page.locator('#gameMenuClose').click();expect(page.locator('#gameMenuPanel')).to_be_hidden()
            page.locator('#playerName').fill(f'Art QA {kind}')
            page.locator('#startBtn').click()
            expect(page.locator('#game')).to_be_visible(timeout=10000)
            expect(page.locator('#encounterTitle')).to_contain_text('opening advantage')
            assert page.locator('#victoryMarkers i').count()==10
            assert page.locator('.run-tabs button').count()==5
            page.screenshot(path=str(PROOF/f'{kind}-starter.png'),full_page=True)
            page.locator('#encounterContent .offer').first.click()
            expect(page.locator('#encounterTitle')).to_have_text('Choose your path')
            page.screenshot(path=str(PROOF/f'{kind}-route.png'),full_page=True)
            page.locator('.run-tabs [data-scene="boardPanel"]').click()
            expect(page.locator('.run-tabs [data-scene="boardPanel"]')).to_have_class('active')
            page.locator('#gameMenuToggle').click()
            expect(page.locator('#gameMenuPanel')).to_be_visible()
            page.locator('#gameMenuPanel [data-scene="collectionPanel"]').click()
            expect(page.locator('#gameMenuPanel')).to_be_hidden()
            expect(page.locator('.run-tabs [data-scene="collectionPanel"]')).to_have_class('active')
            page.locator('#codexSearch').fill('blade')
            expect(page.locator('#codexCount')).to_contain_text('matching entries')
            page.screenshot(path=str(PROOF/f'{kind}-codex.png'),full_page=True)
            page.reload(wait_until='networkidle')
            expect(page.locator('#game')).to_be_visible(timeout=10000)
            report['checks'][kind]={'menu_operational':True,'real_server_run_started':True,'10_victory_marks':True,'board_navigation':True,'codex_filter':True,'resume_on_reload':True,'document_overflow':page.evaluate('document.documentElement.scrollWidth > innerWidth + 2')}
            context.close()
        assert not report['javascript_errors'],report['javascript_errors']
        assert not report['failed_requests'],report['failed_requests']
        assert all(not v['document_overflow'] for v in report['checks'].values())
        browser.close()
    (PROOF/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':run()