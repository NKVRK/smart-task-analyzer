# Smart Task Analyzer

A full-stack Django + Vanilla JS application for **explainable task prioritization**. 
---

## ⭐ Overview

Smart Task Analyzer evaluates tasks using weighted scoring models that consider:

- **Importance**
- **Urgency**
- **Effort**
- **Dependencies**
- **Strategy-based weight adjustments**

It produces:

- A **ranked list of tasks**
- **Explanations** for each task
- **Score breakdown**
- **Warnings & cycles detection**
- **Meta information**
- **Top 3 suggestions** (for today)

Frontend provides a clean, accessible UI with:

- Single-task form  
- JSON bulk input  
- Strategy selector  
- Result cards with explanations, warnings, and breakdown  
- Meta panel  
- Keyboard shortcut (**Ctrl+Enter** → Analyze)

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

### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply migrations

```bash
python manage.py migrate
```

### 4. Run the application

```bash
python manage.py runserver
```

Open in browser:

**http://127.0.0.1:8000/**

---

## 🧠 Algorithm Explanation

The Smart Task Analyzer uses a transparent and interpretable scoring approach that assigns each task a numeric score from 0–100. The score is based on four components: **importance**, **urgency**, **effort**, and **dependencies**. Strategy presets modify the weights to emphasize different priorities, such as deadlines, high impact, or quick wins.

### 1. Importance
Importance is a user-defined value between 1 and 10. It is normalized to 0–1 using:

```
importance_score = importance / 10
```

Higher importance directly increases the final score. Strategies like `high_impact` place higher weight on this component.

---

### 2. Urgency
Urgency is derived from the number of days remaining until the due date. Tasks past their due date receive maximum urgency.

```
if no due date → urgency = 0.2
if overdue → urgency = 1.0
else urgency = 1 - (days_left / 30), clipped to 0..1
```

Strategies such as `deadline_driven` heavily weight this factor.

---

### 3. Effort
Effort reduces the score for tasks requiring more time. Lower effort means easier wins:

```
effort_score = 1 / (1 + estimated_hours)
```

`fastest_wins` strategy increases this weight, surfacing tasks that can be completed quickly.

---

### 4. Dependencies
Dependencies penalize tasks that rely on other tasks. Each dependency adds a small penalty to the final score.

```
dependency_penalty = 0.1 × number_of_dependencies
```

The system detects cycles using a DFS graph traversal. Detected cycles are reported in `meta.cycles`, and related tasks get warnings.

---

### 5. Weighted Score

Weights vary per strategy:

| Component   | smart_balance | deadline_driven | high_impact | fastest_wins |
|-------------|---------------|-----------------|-------------|--------------|
| Importance  | 0.35          | 0.25            | 0.60        | 0.20         |
| Urgency     | 0.35          | 0.60            | 0.20        | 0.20         |
| Effort      | 0.20          | 0.10            | 0.10        | 0.50         |
| Dependencies| 0.10          | 0.05            | 0.10        | 0.10         |

Final score:

```
score = 100 * (importance * w1 + urgency * w2 + effort * w3 - dep_penalty * w4)
```

---

### 6. Tier Classification

- **High Priority** — score ≥ 70  
- **Medium Priority** — 40–69  
- **Low Priority** — < 40  

---

### 7. Explainability

Each analyzed task returns:

- A human-readable explanation  
- A full `score_breakdown`  
- Any warnings  
- All cycles in `meta`  

This ensures the system is never a “black box.”

---

## 🔗 API Endpoints

### **POST /api/tasks/analyze/**

Analyzes and ranks tasks.

**Request:**

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

Returns top 3 tasks for today.

---

## 🧪 Running Tests

```bash
python manage.py test
```

Covers:
- Urgency logic  
- Overdue tasks  
- Dependency penalties  
- Cycle detection  
- Strategy impact  

---

## 🎨 Frontend Usage

- Use **Single Task Form** OR **Bulk JSON Input**
- Select a strategy
- Click **Analyze**
- Click **Get Top 3 Suggestions**
- Expand **Score Breakdown**
- Meta panel shows:
  - cycles  
  - strategy used  
  - warnings  

Keyboard Shortcuts:
- **Ctrl + Enter** → Analyze

---