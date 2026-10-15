"""Visual/interaction acceptance for the v0.6 UI; independent browser, not phone hardware."""
from __future__ import annotations
import os,json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
BASE=os.getenv('NMD_BASE','http://127.0.0.1:3957').rstrip('/')
E=Path('evidence'); E.mkdir(exist_ok=True)

def run():
    errs=[]; failed=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage'],**({'executable_path':os.environ['CHROMIUM']} if os.getenv('CHROMIUM') else {}))
        phone=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=1)
        page=phone.new_page();page.on('pageerror',lambda e:errs.append(str(e)));page.on('requestfailed',lambda r:failed.append(str(r.url)))
        page.goto(BASE+'/expedition',wait_until='networkidle')
        expect(page.locator('#opening')).to_be_visible()
        assert page.locator('body').evaluate('(el)=>getComputedStyle(el,":before").backgroundImage.includes("moonlit-exchange")')
        assert page.locator('#heroes .hero-card').count()==4
        page.screenshot(path=str(E/'v06-mobile-opening.png'),full_page=True)
        page.locator('#settingsToggle').click()
        expect(page.locator('#settingsPanel')).to_be_visible()
        page.locator('#compactCards').check()
        assert page.locator('body').evaluate('(el)=>el.classList.contains("compact-cards")')
        page.locator('#lowEffects').check()
        assert page.locator('body').evaluate('(el)=>el.classList.contains("reduce-fx")')
        page.locator('#settingsClose').click()
        page.locator('#playerName').fill('Night Explorer')
        page.locator('#startBtn').click()
        expect(page.locator('#game')).to_be_visible(timeout=15000)
        expect(page.locator('#mobileDock')).to_be_visible()
        assert page.locator('.board-item .vector-art svg').count()>=1
        assert page.locator('#board .board-item').count()==1
        page.screenshot(path=str(E/'v06-mobile-board.png'),full_page=True)
        page.locator('#mobileDock button[data-target="encounterPanel"]').click()
        assert page.locator('#encounterContent .offer').count()==3
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth+2')
        page.screenshot(path=str(E/'v06-mobile-route.png'),full_page=True)
        # Visit a merchant and inspect a newly acquired item.
        encounter=page.locator('#encounterContent .offer').filter(has_text='Armorer').or_(page.locator('#encounterContent .offer').filter(has_text='Caravan')).or_(page.locator('#encounterContent .offer').filter(has_text='Apothecary'))
        encounter.first.click()
        expect(page.locator('#encounterTitle')).not_to_have_text('Choose your path',timeout=12000)
        market=page.locator('#encounterContent .offer:enabled').first
        market.click()
        expect(page.locator('.stash-item')).to_have_count(1,timeout=12000)
        page.locator('.stash-item').first.click()
        expect(page.locator('#itemModal')).to_be_visible()
        assert page.locator('#modalGlyph svg').count()==1
        page.screenshot(path=str(E/'v06-mobile-inspect.png'),full_page=True)
        page.locator('#closeModal').click()
        page.reload(wait_until='networkidle');expect(page.locator('#game')).to_be_visible(timeout=15000)
        assert page.locator('body').evaluate('(el)=>el.classList.contains("compact-cards")')
        assert not errs,errs
        assert not failed,failed
        desk=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
        big=desk.new_page();big.on('pageerror',lambda e:errs.append(str(e)));big.goto(BASE+'/expedition',wait_until='networkidle')
        big.screenshot(path=str(E/'v06-desktop-opening.png'),full_page=True)
        # Ensure live duel is still reachable from the common navigation.
        big.goto(BASE+'/',wait_until='networkidle');expect(big.locator('#heroPicks')).to_be_visible()
        big.screenshot(path=str(E/'v06-desktop-duel.png'),full_page=True)
        result={'build':'0.6.0','profile':'Chromium Playwright mobile 390x844 and desktop 1440x900','opening_art_loaded':True,'hero_picker':4,'settings_persisted':True,'board_cards_with_vector_art':True,'merchant_and_item_inspection':True,'mobile_dock_visible':True,'duel_lobby_not_broken':True,'js_errors':errs,'request_failures':failed,'real_ios_android_tested':False}
        (E/'v06-visual-report.json').write_text(json.dumps(result,indent=2))
        browser.close();print(json.dumps(result,indent=2));return result
if __name__=='__main__':run()