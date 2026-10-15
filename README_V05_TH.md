# Night Market Duel v0.5.0 — Extended Expedition (prototype)

ระบบนี้เป็นเกม *original* ที่ได้รับแรงบันดาลใจจากโครงสร้าง auto-battler/merchant roguelike ซึ่งศึกษาผ่าน BazaarDB แพตช์ 19.2 (13 ต.ค. 2026) ไม่ใช่เกม The Bazaar ของ Tempo และไม่ใช้ไอเทม ภาพ โลโก้ สกิล หรือเนื้อหาที่นำมาคัดลอกโดยตรง

## โหมด

- `/` — Duel 1v1 ถ่ายทอดสดผ่าน HTTPS/WSS: ห้องส่วนตัว 2 คน ไอเทม 40 ชนิด 6 ช่อง Best of 3 ยังเหมือนเดิม
- `/expedition` — Solo roguelike: บอร์ดปลดล็อกจาก 4 ถึง 10 ช่อง, Small/Medium/Large ขนาด 1/2/3, Stash 10 ช่อง, ไอเทม 88, สกิล 32, มอนสเตอร์ 36, Event themes 28, 6 encounters ต่อวัน, ชั่วโมงที่ 3 บังคับเจอมอนสเตอร์, ชั่วโมงที่ 6 สู้ Ghost Rival, 10 crests หรือ prestige หมด, ระบบเรียนสกิล/อัปเกรด/รวมไอเทม/enchantment, เรื่องเล่า, combat events ที่จำลองฝั่งเซิร์ฟเวอร์

## ติดตั้งสำหรับรันในเครื่องทดสอบ

```bash
pip install -r requirements.txt pytest httpx
python -m pytest -q
python -m uvicorn app:app --host 127.0.0.1 --port 3000
```

## ข้อจำกัด

Expedition ยังเป็น PvE เดี่ยว แยกจาก 1v1 Duel; ห้องเดิมยังไม่สามารถเชื่อม Economy/10-slot item pool แบบ Expedition และไม่เท่ากับระบบ BazaarDB ทั้งหมด; ไม่มีบัญชีถาวร/เซฟถาวร รีสตาร์ตโฮสต์แล้วการเดินทางที่เก็บใน RAM หาย; Free instance อาจพัก/รีสตาร์ตและมี cold start; TestClient และ Chromium ไม่เท่ากับมือถือจริง; เอฟเฟกต์และงานภาพใช้ 2D/SVG สร้างใหม่ ไม่ใช่โมเดล 3D ของ The Bazaar; ไม่สามารถรับรองปราศจากบั๊กได้

## ใครทำอะไร

ChatGPT เป็นผู้เขียน/แก้โค้ดระบบ Expedition ใน sandbox โค้ด Duel เดิมเป็นโปรเจกต์ที่ผู้ใช้เคยให้ ChatGPT พัฒนาก่อนหน้านี้ ไม่ใช้ Gemini Hub, Smoodty, PC ผู้ใช้; ถ้าปล่อยขึ้น GitHub/Render จะใช้เครื่องมือเชื่อมของ ChatGPT เป็นตัวดีพลอยและทดสอบ