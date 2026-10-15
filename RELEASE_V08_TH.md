# Night Market Duel v0.8 — UI Theatre Pass

งานรอบนี้พัฒนาทับโครงโปรเจกต์ v0.7.0 เดิมบนสาขาใหม่ **ไม่เปลี่ยน combat engine / currency / inventory API / WebSocket rooms**

## อ้างอิง The Bazaar อย่างไร
ศึกษาภาพบน Steam, SteamDB, PC Gamer, คู่มือ Screens HUD และแพตช์ UI ในเว็บ playthebazaar.com รวมทั้ง UI ปัจจุบันในเกมเรา ก่อนจัดสัดส่วนจอใหม่ หลักการที่นำมาปรับใช้เป็นแนว genre:

- HUD: Day / Hour / Gold / XP / Income / Prestige / Wins อยู่บนแถบเดียว แสดงชัยชนะ 10 เครื่องหมาย
- ตลาดและ Encounter: พื้นที่แสดงตัวเลือกหลักอยู่ตรงกลางฉาก ไม่ใช่ sidebar เว็บ
- Rug: บอร์ดไอเทม 10 ช่องทอดแนวนอนเต็มจอ, เลือก Small/Medium/Large, Stash อยู่ใต้บอร์ด
- Navigation: แถบเดินทาง Board, Skills, Codex, Chronicle, กลับหน้าหลัก และเมนูที่เปิดจริง
- Combat/modal: ฉากและกรอบรายละเอียดเน้นไอเทม แต่ผลยังเป็น server-authoritative
- Responsive: Desktop/Tablet/Mobile, 390×844, safe-area, แตะเมนูและเลื่อนบอร์ดได้

ภาพตัวละครและฉากในโปรเจกต์เป็นงานต้นฉบับจากก่อนหน้านี้ ไม่ได้นำงานของ Tempo Games มาใช้โดยตรง UI ได้แรงบันดาลใจจาก genre แต่ไม่ได้เป็นการคัดลอกภาพหรือโลโก้ The Bazaar.

## Testing
1. `PYTHONPATH=. pytest -q`
2. `node --check static/expedition.js` และ `node --check static/bazaar-theatre-v08.js`
3. `.github/workflows/staging-v08.yml`: Chromium desktop (1440×900) และ mobile (390×844), login, start, route, tabs, menu, Codex, persistence, screenshots

## ยังคงไม่ได้ทำ
- มอนสเตอร์และสกิลระดับเนื้อหาจริงทั้งหมด 1,000+ รายการ
- ghost async PvP, rank, cosmetics และบัญชีถาวร
- การติดตั้งโมเดล 3D ที่มี rig/physics
- การเทสความหน่วงจริงจาก iPhone/Android ที่ใช้งานเครือข่าย 4G/5G