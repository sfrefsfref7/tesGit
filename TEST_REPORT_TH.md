# รายงานการทดสอบ Night Market Duel v0.2.0

**วันที่:** 15 ตุลาคม 2569

**ขอบเขต:** ทดสอบภายใน ChatGPT container เท่านั้น ไม่ได้ทดสอบภายนอกผ่าน 4G/5G และไม่ได้เปิด public host

## หลักฐานที่ผ่าน

- `python -m pytest -q`: **32 passed**
- `node --check static/app.js`: **ผ่านการตรวจไวยากรณ์**
- HTTP GET (`TestClient`): หน้าเว็บ, CSS, JS, ภาพ SVG, `/health` ตอบ 200; ไฟล์ Python ต้นฉบับภายในระบบไม่สามารถเปิดด้วย HTTP GET
- Simulation fuzz: 100 seeds โดยสลับ Hero และไอเทม, ตรวจ HP, poison, burn และขนาดคิวเอฟเฟกต์
- เปิด FastAPI/Uvicorn บน loopback จริง และเชื่อมด้วย WebSocket **สอง connection แยกกัน**: สร้างห้อง, เข้าห้อง, ซื้อไอเทม, กด Ready, ได้รับ snapshot การต่อสู้, เชื่อมต่อใหม่ด้วย session token เดิม
- ห้องเต็มปฏิเสธผู้เล่นที่สาม, token ไม่ถูกต้องปฏิเสธ, action ID ซื้อของซ้ำไม่หักทองซ้ำ
- ปรับปรุง rematch ให้ต้องได้ความยินยอมทั้งสองคน และ rematch กับบอทได้
- ป้องกัน JSON ที่เสียหายทำให้ socket หลุด, จำกัด bufferedAmount client, เพิ่ม heartbeat watchdog บนหน้าจอที่กำลังใช้งาน

## ผลเครือข่ายล่าสุดภายในเครื่องเดียวกัน

รายละเอียดค่าที่วัดจริงอยู่ที่ `evidence/network-internal.json` (ค่าสมรรถนะเป็นเพียง baseline loopback ไม่อ้างว่าเป็น latency ภายนอก)

- RTT p50 **0.79 ms**, p95 **2.54 ms**, jitter stddev **5.56 ms** (30 samples)
- Snapshot interval p50 **201.21 ms**, p95 **205.33 ms**
- Snapshot age p50 **0.95 ms**, p95 **2.50 ms** (loopback, นาฬิกาเครื่องเดียวกัน)
- Server update tick p50 **0.022 ms**, p95 **0.036 ms**
- ข้อมูล snapshot เฉลี่ย **9,980.76 bytes/s/client** (ประเมินจาก JSON ที่รับ, ไม่รวม overhead โปรโตคอล)
- ผล reconnect สู่ slot เดิม **ผ่าน**

## สิ่งที่ยังไม่ผ่านการยืนยัน

- Public HTTPS/WSS: **ยังไม่ทดสอบ เพราะยังไม่ได้เชื่อมโฮสต์ภายนอก**
- เครือข่ายจริง 4G/5G กับ Wi-Fi คนละวง: **ยังไม่ทดสอบ**
- FPS / layout ของ iPhone และ Android จริง: **ยังไม่ได้วัด** (headless Chromium ถูกปฏิเสธการเข้าถึง localhost ด้วย `ERR_BLOCKED_BY_ADMINISTRATOR`)
- ผลขณะ Render Free spin-down, server restart, หรือ latency 100–300ms: **ยังไม่ได้วัด**
- Browser interaction แบบกดจริง: **ยังไม่ได้ยืนยันผ่านอัตโนมัติ**; API/snapshot เชื่อมต่อได้และผ่าน 32 unit/integration tests

**ไม่ควรอ้างว่าเกมไม่มีบั๊ก หรือว่าเล่นข้ามอินเทอร์เน็ตได้ก่อนมีหลักฐานดีพลอยและทดสอบจริง**