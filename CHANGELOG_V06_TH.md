# v0.6.0 — Premium Market Visual Overhaul

ศึกษาภาพหน้าจอเมนู The Bazaar, BazaarDB, Steam Community, Mobalytics และ Interface In Game เพื่อเรียนรู้การจัดวางภาพ UI เท่านั้น ไม่คัดลอกทรัพยากรเกม ชื่อตัวละคร โลโก้ หรือหน้าจอจากเกม The Bazaar โดยตรง

- Original illustrated market vista (authored with ChatGPT image generation, locally optimized to WebP; not downloaded from The Bazaar).
- New original full-bleed menu, market terrace, stylized gold/bronze panel framing and game HUD.
- Refined touch hero selector, 10-slot battler, card visuals, rarity frames, cooldown markers, offering cards and large skill modal.
- Server-authoritative gameplay API, room management, original duel gameplay retained unchanged.
- Added navigable mobile bottom dock (Market / Board / Skills / Journal), real display settings, reduced FX and compact cards toggles stored locally.
- Added safe authored vector icons for cards and relics, so mobile cards are not empty emoji placeholders.
- Asset cache versioning and dedicated visual tests / responsive screenshots.

จงทดสอบบน staging ก่อนขึ้น production ทุกครั้ง ข้อจำกัด: งานภาพ original, ไม่ใช่ The Bazaar ต้นฉบับ; ชุดไอเทมยังน้อยกว่า BazaarDB; โหมด Expedition ยังคง PvE แยกกับ 1v1 และ free host ยัง cold start ได้ ไม่รับรองว่าปราศจากบั๊กบนมือถือจริง