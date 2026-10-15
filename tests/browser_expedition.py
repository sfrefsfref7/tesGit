"""Real Chromium mobile-width UI exercise; no fake game objects and no manual network state edits."""
from __future__ import annotations
import json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE=os.getenv('NMD_BASE','http://127.0.0.1:3956').rstrip('/')
EVIDENCE=Path('evidence'); EVIDENCE.mkdir(exist_ok=True)

def run():
    errors=[]; fails=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,**({'executable_path': os.environ['CHROMIUM']} if os.getenv('CHROMIUM') else {}),args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
        page.on('pageerror',lambda exc:errors.append(str(exc)))
        page.on('requestfailed',lambda req:fails.append(f'{req.url}: {req.failure}'))
        page.goto(BASE+'/expedition',wait_until='networkidle',timeout=25000)
        assert page.locator('#opening').is_visible()
        page.locator('#playerName').fill('Night Explorer')
        page.locator('#startBtn').click()
        page.locator('#game').wait_for(state='visible',timeout=10000)
        assert page.locator('.board-item').count()==1
        assert page.locator('.board-cell').count()==9
        assert page.locator('#journeyGold').inner_text().strip()=='◈ 14'
        page.screenshot(path=str(EVIDENCE/'v05-expedition-route-mobile.png'),full_page=True)
        # First hour guarantees a merchant is offered.
        merchant=page.locator('#encounterContent .offer').filter(has_text='Armorer').or_(page.locator('#encounterContent .offer').filter(has_text='Caravan')).or_(page.locator('#encounterContent .offer').filter(has_text='Apothecary'))
        assert merchant.count()>=1
        merchant.first.click()
        assert page.locator('#encounterTitle').inner_text()!='Choose your path'
        assert page.locator('#encounterContent .offer').count()>=4
        # Choose an affordable artifact by displayed offer price.
        bought=False
        for item in page.locator('#encounterContent .offer').all():
            if item.is_enabled():
                item.click();bought=True;break
        assert bought
        assert page.locator('.stash-item').count()==1
        page.locator('.stash-item').first.click()
        assert page.locator('#itemModal').is_visible()
        page.get_by_role('button',name='EQUIP TO BOARD').click()
        assert not page.locator('#itemModal').is_visible()
        page.locator('.board-cell.open').nth(0).click()
        assert page.locator('.board-item').count()==2
        assert page.locator('.stash-item').count()==0
        page.screenshot(path=str(EVIDENCE/'v05-expedition-market-mobile.png'),full_page=True)
        # Visit remaining encounters until forced monster hunt on hour three.
        page.get_by_role('button',name='CONTINUE JOURNEY').click()
        for _ in range(8):
            hour=page.locator('#journeyDay').inner_text()
            if '03/06' in hour:break
            if page.locator('#encounterTitle').inner_text()=='Choose your path':
                page.locator('#encounterContent .offer').first.click()
            phase=page.locator('#encounterTitle').inner_text()
            if page.get_by_role('button',name='CONTINUE JOURNEY').count():
                page.get_by_role('button',name='CONTINUE JOURNEY').first.click()
            elif page.get_by_role('button',name='SKIP ENCOUNTER').count():
                page.get_by_role('button',name='SKIP ENCOUNTER').click()
            elif page.get_by_role('button',name='ENGAGE IN COMBAT').count():
                page.get_by_role('button',name='ENGAGE IN COMBAT').click()
                page.locator('#battleModal').wait_for(state='visible');page.locator('#battleSkip').click()
            else:break
        assert '03/06' in page.locator('#journeyDay').inner_text()
        assert page.locator('#encounterContent .offer').count()==3
        page.locator('#encounterContent .offer').first.click()
        page.get_by_role('button',name='ENGAGE IN COMBAT').click()
        page.locator('#battleModal').wait_for(state='visible')
        assert page.locator('#battleTitle').inner_text()
        page.screenshot(path=str(EVIDENCE/'v05-expedition-battle-mobile.png'),full_page=True)
        page.locator('#battleSkip').click()
        assert page.locator('#battleModal').is_hidden()
        page.reload(wait_until='networkidle')
        page.locator('#game').wait_for(state='visible')
        assert page.locator('#myName').inner_text()=='Night Explorer'
        overflow=page.evaluate('document.documentElement.scrollWidth>window.innerWidth+2')
        assert not overflow, 'Horizontal viewport overflow'
        assert not errors,errors
        assert not fails,fails
        result={'base':BASE,'mobile_viewport':'390x844','create_new_run':True,'merchant_purchase':True,'stash_to_board':True,'hour3_forced_monster':True,'battle_animation_opened':True,'reload_restored_session':True,'horizontal_overflow':overflow,'javascript_errors':errors,'failed_requests':fails,'physical_ios_android_tested':False}
        (EVIDENCE/'v05-browser-expedition.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        browser.close();print(json.dumps(result,indent=2));return result

if __name__=='__main__':run()