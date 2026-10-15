# Build v0.5.0 • 15 October 2026

- แก้ข้อผิดพลาดในโครง v0.4 ที่หน้า Expedition เรียก JS ที่ยังไม่มี
- สร้าง UI Expedition 390px รองรับ hero select, ปุ่มเริ่ม, restore session, merchant offers, การซื้อ, การย้ายจาก Stash ขึ้นบอร์ด, inspect, upgrade, combine, sell, enchant, skill training และ animation ต่อสู้ตาม event timeline
- 88 รายการไอเทมจาก catalog original, 32 Skills, 36 Monsters, 28 Event names; เพิ่ม event rewards จริงตาม phase เช่น Skill/Free Forge/Random Relic/Gamble
- ปรับเส้นทางให้ชั่วโมงที่ 3 มีตัวเลือก Monster 3 แบบ ชั่วโมง 6 เจอ Rival ตามแนวคิด 6 hours/day; บอร์ด 10 ช่องปลดล็อกตามเลเวล
- เพิ่มการทำงานจริงของ 16 สกิลใหม่ลง logic เศรษฐกิจหรือ battle simulation
- ปรับสถานะ Poison DOT และ Burn ให้แสดงผลการรับ damage ตาม event timeline ไม่หักเลือดจากสถานะพิษที่เพิ่งถูกใส่
- ลิงก์จากหน้า 1v1 ไปโหมด Expedition ใหม่
- เพิ่ม regression+fuzz pytest, browser-level E2E เพื่อทดสอบตั้งแต่เริ่มจนต่อสู้และ refresh session

**ข้อจำกัด**: ไม่ใช่ The Bazaar ฉบับสมบูรณ์ ไม่ได้คัดลอกกราฟิกใด ๆ; Expedition ยังเป็นโหมด PvE เดี่ยว, 1v1 ยังใช้กฎเกมเดิม; ลิงก์ production ต้องผ่าน CI ก่อนอัปเดต; ยังไม่ได้ทดสอบ iPhone/Android จริง