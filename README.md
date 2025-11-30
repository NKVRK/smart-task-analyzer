# Smart Task Analyzer

A full‑stack Django + Vanilla JavaScript application for **intelligent, explainable task prioritization**.  
The system evaluates tasks based on urgency, importance, effort, and dependencies, producing a clear, ranked list of what the user should work on first.

---

## ⭐ Overview

The Smart Task Analyzer combines a configurable scoring algorithm with a clean and responsive frontend interface.  
It gives users:

- A fully explainable priority score  
- Strategy‑based prioritization  
- Cycle detection for dependencies  
- Clear reasoning for each score  
- A clean UI with JSON input, single‑task form, and result panels  

The backend exposes two API endpoints, and the frontend consumes them through a simple and intuitive interface.

---

## 📦 Project Structure

```
task-analyzer/
├── backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tasks/
│   ├── scoring.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── models.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── manage.py
├── README.md
└── requirements.txt
```

---

## ⚙️ Setup Instructions

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply database migrations

```bash
python manage.py migrate
```

### 4. Run the development server

```bash
python manage.py runserver
```

Open the application at:

**http://127.0.0.1:8000/**

---

## 🧠 Algorithm Explanation (Human‑Readable)

The Smart Task Analyzer assigns each task a numerical score based on four key components:

### **1. Importance**
A value from 1 to 10.  
It is normalized into a 0–1 scale:

```
importance_score = importance / 10
```

### **2. Urgency**
Based on the due date:

- Tasks due soon receive higher urgency.
- Tasks past due receive a strong boost, capped to avoid extreme scores.
- Tasks with no due date get urgency = 0.

```
If overdue:
    urgency = 1.0 (with capped boost)
Else:
    urgency = 1 - (days_left / 60)
```

The urgency scale smoothly decreases for tasks further into the future, using a 60‑day horizon.

### **3. Effort**
Lower-effort tasks are considered “quick wins.”  
Raw effort is converted into a decreasing function:

```
effort_raw = 1 / (1 + estimated_hours)
```

Then normalized across all tasks so scores remain consistent regardless of range.

### **4. Dependencies (Out‑degree weight)**
A task that other tasks depend on becomes more valuable to complete early.  
The analyzer counts how many tasks depend on each task:

```
dependencies_outdegree[task_id] = number of tasks that list it as a dependency
```

This value is normalized so that heavily blocking tasks rank higher.

---

## 🎯 Strategy-Based Weighting

The system supports multiple scoring strategies.  
Each strategy adjusts the relative importance of urgency, importance, effort, and dependencies.

| Strategy         | Urgency | Importance | Dependencies | Effort |
|------------------|---------|------------|--------------|--------|
| smart_balance    | 0.35    | 0.30       | 0.20         | 0.15   |
| deadline_driven  | 0.60    | 0.20       | 0.10         | 0.10   |
| high_impact      | 0.20    | 0.60       | 0.15         | 0.05   |
| fastest_wins     | 0.15    | 0.15       | 0.10         | 0.60   |

The final score is:

```
score = urgency*w1 + importance*w2 + dependencies*w3 + effort*w4
```

Then tasks are sorted by:

1. Highest score  
2. Highest importance  
3. Lowest effort  

This ensures meaningful and stable ordering even when scores are close.

---

## 🔍 Circular Dependency Detection

The analyzer performs graph‑based cycle detection using depth‑first search.  
If cycles are found, they are included in the `meta` section of the API response.

Example:

```json
{
  "cycle_id": 1,
  "tasks": ["t1", "t2", "t1"],
  "message": "circular dependency detected"
}
```

This helps users understand why certain tasks cannot be completed in a valid order.

---

## 🔗 API Endpoints

### **POST /api/tasks/analyze/**  
Analyzes and returns all tasks sorted by priority.

**Request Example:**

```json
{
  "tasks": [
    {
      "id": "t1",
      "title": "Fix bugs",
      "due_date": "2025-12-01",
      "importance": 8,
      "estimated_hours": 3,
      "dependencies": []
    }
  ],
  "strategy": "smart_balance"
}
```

### **GET /api/tasks/suggest/?strategy=smart_balance**  
Returns the top 3 tasks from the most recent analysis.

---

## 🧪 Running Tests

The project includes unit tests for:

- Past‑due urgency handling  
- Cycle detection  
- Defaulting of missing fields  

Run tests with:

```bash
python manage.py test
```

---

## 🎨 Frontend Usage Guide

- Add tasks using the single‑task form or paste JSON directly.  
- Choose a strategy from the dropdown.  
- Click **Analyze Tasks** or **Get Top 3 Suggestions**.  
- View:
  - Priority tier  
  - Score breakdown  
  - Explanations  
  - Dependency warnings  
  - Meta section with cycles  

Keyboard shortcut:

**Ctrl + Enter → Analyze Tasks**

The interface is responsive and works across screen sizes.

---

## 🧩 Design Decisions

- **Normalization:** Effort and dependency values are normalized to keep scoring consistent regardless of dataset size.
- **60‑day urgency horizon:** Provides a smooth decay curve and avoids punishing tasks with distant deadlines too harshly.
- **Separate strategy presets:** Keeps the algorithm clean and allows users to shift priorities instantly.
- **Cycle detection included in meta:** Avoids mixing warnings with the core score but still surfaces important structural issues.
- **Lightweight frontend:** Pure JavaScript without any framework to keep the solution simple and fast.

---

## ⏱️ Time Breakdown

Approximate time spent:

- Backend algorithm design: **1 hr 30 min**
- Backend API implementation: **25 min**
- Frontend UI + JS logic: **1 hr**
- Testing + cycle detection: **20 min**
- README documentation: **10 min**

---

## 🚀 Future Improvements

- Add visual dependency graph
- Add weekend/holiday‑aware urgency adjustment
- Add Eisenhower Matrix visualization
- Save tasks to database for persistence
- Improve suggestion logic to consider “today’s workload”
- Provide per‑task warnings for cycles directly inside task cards

---

## ✔ Submission Includes

- Django backend
- Frontend HTML/CSS/JS
- Scoring engine with strategies
- API endpoints
- Unit tests
- README with design explanation

---

This completes the Smart Task Analyzer documentation.
