"""Scenario s9: training material folder 'cnc-onboarding' (create mode, materials)."""
import random

from fixture import w, wb, minimal_pdf

ROOT = "s9-cnc-onboarding"


def _opaque(seed: int, size: int, magic: bytes) -> bytes:
    rnd = random.Random(seed)
    return magic + bytes(rnd.getrandbits(8) for _ in range(size - len(magic)))


def build(base):
    r = base / ROOT
    w(r / "00-welcome.md", '''\
# Welcome to the VMC cell

This pack prepares new operators to run the VMC-3 vertical machining centers
in Cell B.

- Day 1: safety basics and lockout/tagout.
- Day 2: machine overview and the daily start-up checklist.
- Day 3: your first part, run with a trainer beside you.

You may operate a machine without supervision only after you pass the safety
quiz with at least 80% and your trainer signs your training card.

Questions? Ask the training coordinator (phone extension 214) or your shift lead.
''')
    wb(r / "01-safety-basics.pdf", minimal_pdf([
        "Safety basics - VMC cell (rev C, 2024-08-12)",
        "",
        "Personal protective equipment (required in Cell B):",
        "- Safety glasses with side shields at all times.",
        "- Hearing protection when the enclosure door is open.",
        "- Safety shoes. No gloves near a rotating spindle.",
        "- Tie back long hair; no loose sleeves or jewelry.",
        "",
        "Emergency stops: red mushroom buttons on the pendant and beside the door.",
        "Chips: clear them with a brush or chip hook, never by hand.",
        "Before any maintenance or jam clearing: follow 03-lockout-tagout.md.",
    ]))
    wb(r / "02-machine-overview.pptx", _opaque(2, 48_213, b"PK\x03\x04"))
    w(r / "03-lockout-tagout.md", '''\
# Lockout/tagout (LOTO) for VMC-3

Follow every step before you reach inside the machine for maintenance,
tool-change jams, or coolant work.

1. Tell the shift lead and any operators nearby.
2. Press Feed Hold, then stop the spindle.
3. Switch the main disconnect (back panel) to OFF.
4. Fit your personal lock and tag to the disconnect. One lock per person.
5. Bleed the air supply at the regulator until the gauge reads 0.
6. Try to start the machine to confirm it is isolated (try-out).
7. Do the work.
8. Remove tools and guards back in place, then remove your own lock only.
''')
    wb(r / "04-daily-startup-checklist.xlsx", _opaque(4, 21_877, b"PK\x03\x04"))
    w(r / "05-first-part/instructions.md", '''\
# First part: Bracket A

Run this exercise on Day 3 with your trainer.

1. Read the drawing `drawing-bracket-A.pdf`.
2. Load program `O1001.nc` and check the tool list against the setup sheet in the program header.
3. Set work offset G54 on the vise's fixed jaw corner.
4. Run the first part in single-block mode with rapid override at 25%.
5. Measure the part and record results on the inspection sheet with your trainer.
''')
    wb(r / "05-first-part/drawing-bracket-A.pdf", minimal_pdf([
        "BRACKET A - drawing BA-001 rev B",
        "Material: 6061-T6 aluminum, 100 x 60 x 12 mm stock",
        "General tolerance: +/- 0.05 mm unless noted",
        "Holes: 2 x 6.6 mm through, 40 mm apart",
    ]))
    w(r / "05-first-part/O1001.nc", '''\
%
O1001 (BRACKET A - TRAINING)
(SETUP: VISE, G54 = FIXED JAW CORNER, Z0 = TOP OF STOCK)
(T1 = 10 MM 3-FLUTE END MILL, T2 = 6.6 MM DRILL)
G21 G17 G40 G49 G80 G90
T1 M06
G54 S8000 M03
G00 X-6. Y-6.
G43 H01 Z25. M08
G01 Z-3. F300
G01 X106. F900
G01 Y66.
G01 X-6.
G01 Y-6.
G00 Z25. M09
T2 M06
G54 S3500 M03
G43 H02 Z25. M08
G81 X30. Y30. Z-14. R2. F250
X70.
G80 G00 Z25. M09
M30
%
''')
    w(r / "quiz/quiz-safety.md", '''\
# Safety quiz (10 questions, pass mark 80%)

1. Which PPE must you wear at all times in Cell B?
2. When is hearing protection required?
3. Why are gloves banned near a rotating spindle?
4. Where are the emergency stop buttons?
5. How do you remove chips from the work area?
6. Who must you tell before starting lockout/tagout?
7. What do you switch off first: the main disconnect or the spindle?
8. How many locks does each person fit to the disconnect?
9. How do you confirm the machine is isolated?
10. Who may remove your lock?
''')
    w(r / "quiz/answers.md", '''\
# Safety quiz - answer key

TRAINERS ONLY. Do not share with trainees before the quiz.

1. Safety glasses with side shields.
2. Whenever the enclosure door is open.
3. A glove can catch and pull the hand in.
4. On the pendant and beside the door.
5. With a brush or chip hook.
6. The shift lead and nearby operators.
7. The spindle (after Feed Hold), then the main disconnect.
8. One personal lock per person.
9. Try to start the machine (try-out).
10. Only you.
''')
    w(r / "CHANGELOG.txt", '''\
2024-08-12  v2  Added 03-lockout-tagout.md. Checklist updated to rev C. Safety basics rev C.
2024-02-01  v1  First version of the onboarding pack.
''')
