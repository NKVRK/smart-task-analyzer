# TESTS.md — Smart Task Analyzer Manual Test Suite

This document contains **all manual test cases** exactly as previously generated.
Each includes Purpose, Strategy, JSON Input, Expected Behavior.

---

# How to Run Tests
1. `python manage.py runserver`
2. Open `http://127.0.0.1:8000/`
3. Paste JSON → Select Strategy → Analyze.

---

# Scenario 1 — Basic Sanity Check
**Strategy:** smart_balance

**JSON:**
```json
[{"id":"t1","title":"Fix login bug","due_date":"2025-12-01","importance":9,"estimated_hours":3,"dependencies":[]},
{"id":"t2","title":"Write user documentation","due_date":"2025-12-20","importance":7,"estimated_hours":6,"dependencies":[]},
{"id":"t3","title":"Refactor reporting module","due_date":"2026-01-15","importance":6,"estimated_hours":10,"dependencies":[]},
{"id":"t4","title":"Set up monitoring alerts","due_date":"2025-12-05","importance":8,"estimated_hours":2,"dependencies":[]}]
```
**Expected:** t1 & t4 rank highest; no warnings; meta shows strategy.

---

# Scenario 2 — Urgency Extremes
**Strategy:** deadline_driven

**JSON:**
```json
[{"id":"t1","title":"Renew SSL certificate","due_date":"2025-11-15","importance":7,"estimated_hours":1,"dependencies":[]},
{"id":"t2","title":"Plan next quarter roadmap","due_date":"2026-03-01","importance":8,"estimated_hours":5,"dependencies":[]},
{"id":"t3","title":"Prepare incident postmortem","due_date":"2025-11-29","importance":9,"estimated_hours":3,"dependencies":[]},
{"id":"t4","title":"Upgrade CI pipeline","due_date":null,"importance":6,"estimated_hours":4,"dependencies":[]}]
```
**Expected:** Past-due tasks rise; explanations show due status.

---

# Scenario 3 — Dependencies & Cycle
**Strategy:** smart_balance

**JSON:**
```json
[{"id":"t1","title":"Design database schema","due_date":"2025-12-10","importance":8,"estimated_hours":5,"dependencies":[]},
{"id":"t2","title":"Implement API endpoints","due_date":"2025-12-12","importance":8,"estimated_hours":6,"dependencies":["t1"]},
{"id":"t3","title":"Create frontend UI","due_date":"2025-12-15","importance":7,"estimated_hours":7,"dependencies":["t2"]},
{"id":"t4","title":"Write integration tests","due_date":"2025-12-20","importance":7,"estimated_hours":4,"dependencies":["t2","t3"]},
{"id":"t5","title":"Cyclic task A","due_date":"2025-12-05","importance":6,"estimated_hours":2,"dependencies":["t6"]},
{"id":"t6","title":"Cyclic task B","due_date":"2025-12-06","importance":6,"estimated_hours":2,"dependencies":["t5"]}]
```
**Expected:** Chain ranking t1→t2→t3→t4; cycle t5↔t6 visible in warnings & meta.

---

# Scenario 4 — Missing/Invalid Data
**Strategy:** smart_balance

**JSON:**
```json
[{"id":"t1","title":"Task missing fields","due_date":null,"estimated_hours":3,"dependencies":[]},
{"id":"t2","title":"Negative hours","due_date":"2025-12-03","importance":999,"estimated_hours":-5,"dependencies":[]},
{"id":"t3","title":"Non-numeric importance","due_date":"2025-12-10","importance":"high","estimated_hours":4,"dependencies":[]},
{"id":"t4","title":"Unknown deps","due_date":"2025-12-08","importance":5,"estimated_hours":2,"dependencies":["t999","t1000"]}]
```
**Expected:** Warnings shown; backend normalizes or adjusts fields.

---

# Scenario 5 — Large Dataset
**Strategy:** smart_balance (then high_impact)

**JSON:**
```json
[{"id":"t1","title":"Bugfix: profile","due_date":"2025-12-01","importance":8,"estimated_hours":3,"dependencies":[]},
{"id":"t2","title":"Passwordless login","due_date":"2025-12-20","importance":9,"estimated_hours":10,"dependencies":[]},
{"id":"t3","title":"Improve logging","due_date":"2025-12-05","importance":6,"estimated_hours":2,"dependencies":[]},
{"id":"t4","title":"CSV bug","due_date":"2025-11-28","importance":7,"estimated_hours":1,"dependencies":[]},
{"id":"t5","title":"Refactor auth","due_date":"2026-01-10","importance":7,"estimated_hours":12,"dependencies":[]},
{"id":"t6","title":"Dark mode","due_date":"2026-02-01","importance":5,"estimated_hours":8,"dependencies":[]},
{"id":"t7","title":"Cleanup flags","due_date":"2025-12-02","importance":4,"estimated_hours":1,"dependencies":[]},
{"id":"t8","title":"Error alerts","due_date":"2025-12-07","importance":8,"estimated_hours":3,"dependencies":[]},
{"id":"t9","title":"DB indexes","due_date":"2025-12-15","importance":8,"estimated_hours":6,"dependencies":[]},
{"id":"t10","title":"Onboarding docs","due_date":"2025-12-18","importance":6,"estimated_hours":4,"dependencies":[]}]
```

**Expected:** t1,t4 high; future heavy tasks low; high_impact boosts importance.

---

# Scenario 6 — Strategy Comparison
**Run with:** smart_balance, deadline_driven, high_impact, fastest_wins

**JSON:**
```json
[{"id":"t1","title":"Short urgent bug","due_date":"2025-12-01","importance":7,"estimated_hours":1,"dependencies":[]},
{"id":"t2","title":"Huge refactor","due_date":"2026-03-01","importance":10,"estimated_hours":40,"dependencies":[]},
{"id":"t3","title":"Medium feature","due_date":"2025-12-20","importance":7,"estimated_hours":8,"dependencies":[]},
{"id":"t4","title":"Tiny polish","due_date":"2026-01-15","importance":3,"estimated_hours":0.5,"dependencies":[]}]
```
**Expected:**
- smart_balance → balanced ranking
- deadline_driven → t1 first
- high_impact → t2 rises dramatically
- fastest_wins → t4 rises
