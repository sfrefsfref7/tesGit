"""Actual Chromium interactions in 2 independent mobile-mode browser contexts.
Simulated mobile viewport, NOT verification on a physical Android or iPhone.
"""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE = os.environ.get('NMD_PUBLIC_BASE', 'https://night-market-duel-dome.onrender.com').rstrip('/')
OUT = Path(__file__).resolve().parent.parent / 'evidence'
OUT.mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ca = await browser.new_context(viewport={'width':390,'height':844},device_scale_factor=3,is_mobile=True,has_touch=True)
        cb = await browser.new_context(viewport={'width':412,'height':915},device_scale_factor=2.625,is_mobile=True,has_touch=True)
        a=await ca.new_page();b=await cb.new_page()
        js_errors=[];request_failures=[]
        for page,n in ((a,'iphone-size'),(b,'android-size')):
            page.on('pageerror',lambda err,n=n:js_errors.append(f'{n}: {err}'))
            page.on('requestfailed',lambda req,n=n:request_failures.append(f'{n}: {req.method} {req.url} ({req.failure})'))
            await page.goto(BASE,wait_until='domcontentloaded',timeout=90000)
            await page.locator('#connection.connected').wait_for(timeout=35000)
            assert await page.locator('.hero-pick').count()==4
        await a.locator('#playerName').fill('Browser A')
        await a.locator('#createBtn').click()
        await a.locator('#gameScreen').wait_for(state='visible',timeout=15000)
        room=(await a.locator('#roomCode').inner_text()).strip()
        assert len(room)==5 and room!='-----',room
        await b.locator('#playerName').fill('Browser B')
        await b.locator('#roomInput').fill(room)
        await b.locator('#joinBtn').click()
        await b.locator('#gameScreen').wait_for(state='visible',timeout=15000)
        await a.locator('#nameB').get_by_text('Browser B').wait_for(timeout=15000)
        assert (await b.locator('#nameA').inner_text()).strip()=='Browser A'
        await a.screenshot(path=str(OUT/'iphone-mobile-room.png'),full_page=True)
        await b.screenshot(path=str(OUT/'android-mobile-room.png'),full_page=True)
        for page in [a,b]:
            assert await page.locator('#readyBtn').is_visible()
            await page.locator('#readyBtn').click()
        await a.locator('#phaseLabel').get_by_text('BATTLE').wait_for(timeout=15000)
        await b.locator('#phaseLabel').get_by_text('BATTLE').wait_for(timeout=15000)
        await a.screenshot(path=str(OUT/'iphone-mobile-battle.png'),full_page=True)
        report={'base_url':BASE,'chromium_mobile_contexts':2,'independent_browser_profiles':True,'same_room':room,'both_observed_battle':True,'javascript_errors':js_errors,'network_request_failures':request_failures,'physical_phones_tested':False}
        (OUT/'browser-public.json').write_text(json.dumps(report,indent=2)+'\n')
        assert not js_errors,js_errors
        assert not request_failures,request_failures
        print(json.dumps(report,indent=2))
        await browser.close()

if __name__=='__main__':asyncio.run(main())