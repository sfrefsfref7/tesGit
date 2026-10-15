# แผนตรวจเทียบ The Bazaar ของจริง (patch 19.2 reference)

แหล่งศึกษาหลัก: https://bazaardb.gg/ ; https://playthebazaar.com/patch-notes ; https://mobalytics.gg/the-bazaar/guides/beginner-guide ; https://mobalytics.gg/the-bazaar/guides/start-of-run-guide

**เป้าหมาย:** สร้างเกม ORIGINAL ที่มีเกมลูป การตัดสินใจ และ UX ใกล้เคียง ไม่ใช้โลโก้ ชื่อ Hero ภาพ การ์ด และสคริปต์อันมีลิขสิทธิ์จากต้นฉบับ

| หน้าระบบต้นแบบ | Night Market v0.7 | ช่องว่างที่ยังมี |
|---|---|---|
| Main menu / lobby | มี (1v1 และ Expedition) | การนำทางและแอนิเมชันยังแตกต่าง |
| Hero selection | 4 Hero original พร้อม Portrait | skill pool แยก Hero ยังเล็ก |
| Start-of-run choices | มี 3 boon: เศรษฐกิจ ของ Enchant และ Skill | สูตรตัวเลขไม่เหมือนต้นฉบับ |
| Encounter choice per hour | มี 3 การ์ดเลือกเส้นทาง, PvE ช่วงชั่วโมง 3, PvP ตอนสิ้นวัน | ระยะวัน/โอกาสสุ่ม/พูลยังลดรูป |
| Merchant specialty | แยก Weapons, Machines, Potions, Relics และ Reroll | ขาด merchant เฉพาะและราคาสุ่มระดับสูง |
| Board, Stash, position | บอร์ด 10, Stash 10, Small/Medium/Large, Move, Combine | บอร์ดไม่ได้ใช้ physics, สถานะบางประเภทไม่ครบ |
| Skill trainer / Enchant | มี 32 skill และ 7 enchantment | Trigger priority, stash passives และระดับสกิลไม่ครบ |
| Monster encounter | ตรวจ Loadout ก่อนสู้; ความยาก Bronze/Silver/Gold และ reward ต่างกัน | ยังไม่ใช้ predefined board เฉพาะมอนสเตอร์ทั้งหมด |
| Level-up screen | เลือกรางวัล 3 แบบใน Guided mode | ไม่ครบสายรางวัลตามแพตช์เกมต้นฉบับ |
| Combat screen | การ์ดสองฝั่ง, HP, status effect, event timeline จาก server | ไม่ใช่ renderer/animation system เทียบเท่าต้นฉบับ |
| Run outcome | 10 wins vs Prestige loss; result modal | ยังขาดสมุดสถิติ/รีเพลย์/เครื่องสำอาง |
| Collection database | ค้นหาและกรองไอเทม 88 และ Skill 32 | ไม่เท่ากับรายการ BazaarDB 1,362/514 |
| Friend 1v1 | WebSocket server authoritative, lobby, room | ไม่ใช่ asynchronous ghost arena และไม่ซิงค์ Expedition inventory เข้า 1v1 |
| Mobile and accessibility | Portrait responsive, safe area, compact cards, reduced FX | ยังต้องทดสอบ iOS/Android จริงและ gesture/เสียง |

### ข้อจำกัดสำคัญ
- ตัวเกม The Bazaar มีระบบ PvP แบบ asynchronous เป็นหลัก ขณะที่ Friend Duel ของเราคือ synchronous 1v1
- คนละ engine ไม่ได้ทำ UI ตรงทุกพิกเซล, ไม่ได้ใช้ Hero หรือการ์ดต้นฉบับ
- การอัปเดต v0.7 แยก guided phase เพื่อไม่ทำลาย save/session ของโหมดเดิม และใช้ server-side validation