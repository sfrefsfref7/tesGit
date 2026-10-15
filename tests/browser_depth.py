"""Two actual browser profiles exercising 0.3's *new* shopping/forge/pact UI.
Run against localhost for staging; rerun against HTTPS for live acceptance.
"""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE=os.environ.get('NMD_PUBLIC_BASE','http://127.0.0.1:3955').rstrip('/')
ART=Path(__file__).resolve().parents[1]/'evidence'
ART.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        contexts=[await browser.new_context(viewport={'width':w,'height':h},device_scale_factor=2,is_mobile=True,has_touch=True)
                  for w,h in ((390,844),(360,780))]
        a,b=[await ctx.new_page() for ctx in contexts]
        errors=[];reqfails=[]
        for i,page in enumerate((a,b)):
            page.on('pageerror',lambda error,i=i:errors.append(f'player{i} {error}'))
            page.on('requestfailed',lambda req,i=i:reqfails.append(f'player{i} {req.url}: {req.failure}'))
            await page.goto(BASE,wait_until='domcontentloaded',timeout=90000)
            await page.locator('#connection.connected').wait_for(timeout=45000)
            await page.locator('.hero-pick').first.wait_for()
            assert await page.locator('.hero-pick').count()==4
        await a.locator('#playerName').fill('Forge A')
        await a.locator('#createBtn').click()
        await a.locator('#gameScreen').wait_for(state='visible',timeout=20000)
        code=(await a.locator('#roomCode').inner_text()).strip()
        await b.locator('#playerName').fill('Forge B')
        await b.locator('#roomInput').fill(code)
        await b.locator('#joinBtn').click()
        await b.locator('#gameScreen').wait_for(state='visible',timeout=20000)
        await a.locator('#nameB').get_by_text('Forge B').wait_for(timeout=20000)
        # Both have independently generated selectable market pacts.
        for page,choice in ((a,0),(b,1)):
            assert await page.locator('.boon-card').count()==3
            await page.locator('.boon-card').nth(choice).click()
            await page.locator('.boon-card.chosen').wait_for(timeout=12000)
            assert await page.locator('.boon-owned').count()==1
            await page.locator('[data-shop="0"]').click()
            await page.locator('#itemModal').wait_for(state='visible')
            await page.locator('#modalAction').click()
            await page.locator('.board-slot.filled').first.wait_for(timeout=12000)
            assert await page.locator('.item-card:not(.empty)').count()==4
        # Test forge through actual touch-sized button and server ACK.
        first=a.locator('.board-slot.filled').first
        await first.click();await first.click()
        await a.locator('#modalForge').wait_for(state='visible')
        assert await a.locator('#modalForge').is_enabled()
        await a.locator('#modalForge').click()
        await a.locator('.board-slot.forged').first.wait_for(timeout=12000)
        assert '+1' in (await a.locator('.board-slot.forged').first.inner_text())
        for i,page in enumerate((a,b)):
            assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth+2'),f'horizontal overflow player {i}'
        await a.screenshot(path=str(ART/'v03-forged-iphone.png'),full_page=True)
        await b.screenshot(path=str(ART/'v03-market-android.png'),full_page=True)
        for page in (a,b):await page.locator('#readyBtn').click()
        for page in (a,b):await page.locator('#phaseLabel').get_by_text('BATTLE').wait_for(timeout=20000)
        await a.screenshot(path=str(ART/'v03-battle-iphone.png'),full_page=True)
        assert not errors,errors
        assert not reqfails,reqfails
        report={'base':BASE,'separate_browser_contexts':2,'room_code':code,'boon_picked_each_player':True,
                'item_bought_each_player':True,'forge_plus_one':True,'cross_player_battle':True,
                'no_horizontal_overflow':True,'js_errors':errors,'request_failures':reqfails,
                'physical_mobile_devices_tested':False}
        (ART/'browser-depth.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
        await browser.close()

if __name__=='__main__':asyncio.run(main())