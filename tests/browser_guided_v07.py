"""Run UI acceptance on real browser profiles against local staged HTTP server."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
BASE=os.environ.get('NMD_BASE','http://127.0.0.1:3958').rstrip('/')
E=Path('evidence');E.mkdir(exist_ok=True)
def run():
    errors=[];failures=[]
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'],**({'executable_path':os.environ['CHROMIUM']} if os.getenv('CHROMIUM') else {}))
        ctx=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        page=ctx.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('requestfailed',lambda r:failures.append(str(r.url)))
        page.goto(BASE+'/expedition',wait_until='networkidle',timeout=30000)
        expect(page.locator('#opening')).to_be_visible()
        page.locator('#playerName').fill('Guided Adventurer')
        page.locator('#startBtn').click()
        expect(page.locator('#game')).to_be_visible(timeout=15000)
        expect(page.locator('#encounterTitle')).to_contain_text('opening advantage',timeout=10000)
        assert page.locator('#encounterContent .offer').count()==3
        page.screenshot(path=str(E/'v07-starting-boon.png'),full_page=True)
        page.locator('#encounterContent .offer').filter(has_text='Guild Patronage').click()
        expect(page.locator('#journeyGold')).to_have_text('◈ 24',timeout=8000)
        expect(page.locator('#journeyIncome')).to_have_text('◈ 7/day',timeout=8000)
        expect(page.locator('#encounterTitle')).to_have_text('Choose your path')
        page.screenshot(path=str(E/'v07-route.png'),full_page=True)
        # Inspect merchant offers after a real server-side encounter choice.
        candidates=page.locator('#encounterContent .offer').filter(has_text='Armorer').or_(page.locator('#encounterContent .offer').filter(has_text='Caravan')).or_(page.locator('#encounterContent .offer').filter(has_text='Apothecary')).or_(page.locator('#encounterContent .offer').filter(has_text='Artisan'))
        assert candidates.count()>0
        candidates.first.click()
        expect(page.locator('#encounterTitle')).not_to_have_text('Choose your path',timeout=8000)
        assert page.locator('#encounterContent .offer').count()>=4
        page.screenshot(path=str(E/'v07-specialized-market.png'),full_page=True)
        page.locator('#mobileDock button[data-target="collectionPanel"]').click()
        page.locator('#codexSearch').fill('blade')
        expect(page.locator('#codexCount')).to_contain_text('matching entries')
        assert page.locator('#codexResults .codex-entry').count()>0
        page.screenshot(path=str(E/'v07-codex.png'),full_page=True)
        page.reload(wait_until='networkidle')
        expect(page.locator('#journeyIncome')).to_have_text('◈ 7/day',timeout=10000)
        assert not page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 2')
        assert not errors,errors
        assert not failures,failures
        # Separate desktop profile - Duel remains available.
        desktop=b.new_context(viewport={'width':1366,'height':768})
        duel=desktop.new_page();duel.goto(BASE+'/',wait_until='networkidle');expect(duel.locator('#heroPicks')).to_be_visible()
        report={'build':'0.7.0','guided_start':True,'starter_three_offers':True,'income_applied_server_side':True,
                'specialized_shop':True,'codex_filter':True,'refresh_persists':True,
                'classic_multiplayer_lobby':True,'js_errors':errors,'request_failures':failures,'physical_devices_tested':False}
        (E/'v07-browser-report.json').write_text(json.dumps(report,indent=2))
        b.close();print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()