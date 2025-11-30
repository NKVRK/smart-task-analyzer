const state = {
  lastResult: null
};

function notify(message) {
  const n = document.getElementById('notification');
  n.textContent = message;
  n.className = 'notification show';
  setTimeout(() => {
    n.className = 'notification';
  }, 3000);
}

function parseJSON(text) {
  try {
    const data = JSON.parse(text);
    if (!Array.isArray(data)) {
      throw new Error('JSON must be an array of tasks');
    }
    return { success: true, data };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function clearError(id) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = '';
    el.classList.remove('show');
  }
}

function showError(id, message) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = message;
    el.classList.add('show');
  }
}

function disableButtons(disabled) {
  ['addTaskBtn', 'analyzeBtn', 'suggestBtn'].forEach(id => {
    document.getElementById(id).disabled = disabled;
  });
}

function updateMeta(meta) {
  const box = document.getElementById('metaArea');
  const pre = document.getElementById('metaContent');
  if (!box || !pre) return;

  if (!meta || Object.keys(meta).length === 0) {
    box.style.display = 'none';
    pre.textContent = '';
    return;
  }

  box.style.display = 'block';
  pre.textContent = JSON.stringify(meta, null, 2);
}

function renderTasks(tasks, isSuggestion = false) {
  const area = document.getElementById('resultsArea');
  
  if (!tasks || tasks.length === 0) {
    area.innerHTML = '<div class="empty-state">No tasks to display</div>';
    return;
  }

  let html = '';
  tasks.forEach((task, index) => {
    const warningsHtml = task.warnings && task.warnings.length
      ? `<ul class="task-warnings">${task.warnings.map(w => `<li>${escapeHtml(w)}</li>`).join('')}</ul>`
      : '';

    html += `
      <div class="task-card">
        <div class="task-header">
          <div class="task-title">${escapeHtml(task.title)}</div>
          <span class="badge ${task.tier.toLowerCase()}">${task.tier}</span>
        </div>
        <div class="task-details">
          Score: <strong>${task.score}</strong> • 
          Importance: ${task.importance} • 
          Effort: ${task.estimated_hours}h • 
          Due: ${task.due_date || 'Not set'}
        </div>
        ${task.explanation ? `<div class="task-explanation">${escapeHtml(task.explanation)}</div>` : ''}
        ${warningsHtml}
        ${task.score_breakdown ? `
          <button class="breakdown-toggle" onclick="toggleBreakdown(${index})">
            View score breakdown
          </button>
          <div id="breakdown-${index}" class="breakdown-content">
            ${escapeHtml(JSON.stringify(task.score_breakdown, null, 2))}
          </div>
        ` : ''}
      </div>
    `;
  });

  area.innerHTML = html;
}

function renderSuggestions(tasks) {
  const area = document.getElementById('suggestionsArea');
  
  if (!tasks || tasks.length === 0) {
    area.innerHTML = '';
    return;
  }

  let html = '<div class="suggestions-box"><div class="suggestions-title">Top 3 Suggestions for Today</div>';
  
  tasks.forEach((task, index) => {
    html += `
      <div class="task-card" style="margin-bottom: ${index < tasks.length - 1 ? '10px' : '0'}">
        <div class="task-header">
          <div class="task-title">${escapeHtml(task.title)}</div>
          <span class="badge ${task.tier.toLowerCase()}">${task.tier}</span>
        </div>
        <div class="task-details">
          Score: <strong>${task.score}</strong> • Due: ${task.due_date || 'Not set'}
        </div>
        ${task.explanation ? `<div class="task-explanation">${escapeHtml(task.explanation)}</div>` : ''}
      </div>
    `;
  });

  html += '</div>';
  area.innerHTML = html;
}

window.toggleBreakdown = function(index) {
  const el = document.getElementById(`breakdown-${index}`);
  if (el) {
    el.classList.toggle('show');
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const jsonInput = document.getElementById('jsonInput');
  const addTaskBtn = document.getElementById('addTaskBtn');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const suggestBtn = document.getElementById('suggestBtn');
  const strategy = document.getElementById('strategy');

  // Add task to JSON
  addTaskBtn.addEventListener('click', () => {
    clearError('titleError');
    clearError('importanceError');
    clearError('hoursError');
    clearError('jsonError');

    const title = document.getElementById('taskTitle').value.trim();
    const date = document.getElementById('taskDate').value;
    const importance = parseInt(document.getElementById('taskImportance').value);
    const hours = parseFloat(document.getElementById('taskHours').value);
    const deps = document.getElementById('taskDeps').value.trim();

    let hasError = false;

    if (!title) {
      showError('titleError', 'Title is required');
      hasError = true;
    }

    if (isNaN(importance) || importance < 1 || importance > 10) {
      showError('importanceError', 'Importance must be between 1 and 10');
      hasError = true;
    }

    if (isNaN(hours) || hours < 0) {
      showError('hoursError', 'Hours must be 0 or greater');
      hasError = true;
    }

    if (hasError) {
      notify('Please fix form errors');
      return;
    }

    let tasks = [];
    const existing = parseJSON(jsonInput.value || '[]');
    if (existing.success) {
      tasks = existing.data;
    }

    const newTask = {
      id: 't' + Date.now(),
      title: title,
      due_date: date || null,
      importance: importance,
      estimated_hours: hours,
      dependencies: deps ? deps.split(',').map(s => s.trim()).filter(Boolean) : []
    };

    tasks.push(newTask);
    jsonInput.value = JSON.stringify(tasks, null, 2);
    
    document.getElementById('taskTitle').value = '';
    document.getElementById('taskDate').value = '';
    document.getElementById('taskImportance').value = '';
    document.getElementById('taskHours').value = '';
    document.getElementById('taskDeps').value = '';

    notify('Task added to JSON input');
  });

  // Analyze tasks
  analyzeBtn.addEventListener('click', async () => {
    clearError('jsonError');

    const parsed = parseJSON(jsonInput.value || '[]');
    if (!parsed.success) {
      showError('jsonError', parsed.error);
      notify('Invalid JSON');
      return;
    }

    if (parsed.data.length === 0) {
      showError('jsonError', 'Please add at least one task');
      notify('No tasks to analyze');
      return;
    }

    disableButtons(true);
    notify('Analyzing tasks...');

    try {
      const response = await fetch('/api/tasks/analyze/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: parsed.data,
          strategy: strategy.value
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Server error');
      }

      const result = await response.json();
      state.lastResult = result;
      
      renderTasks(result.analyzed_tasks || []);
      document.getElementById('suggestionsArea').innerHTML = '';
      updateMeta(result.meta || {});
      
      notify('Analysis complete');
    } catch (error) {
      notify('Error: ' + error.message);
      console.error('Analysis error:', error);
      updateMeta(null);
    } finally {
      disableButtons(false);
    }
  });

  // Get top 3 suggestions
  suggestBtn.addEventListener('click', async () => {
    disableButtons(true);
    notify('Getting suggestions...');

    try {
      const response = await fetch(`/api/tasks/suggest/?strategy=${encodeURIComponent(strategy.value)}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Server error');
      }

      const result = await response.json();
      state.lastResult = result;
      
      const suggestions = result.suggested_tasks || result.analyzed_tasks?.slice(0, 3) || [];
      renderSuggestions(suggestions);
      
      if (result.analyzed_tasks) {
        renderTasks(result.analyzed_tasks);
      }
      updateMeta(result.meta || {});
      
      notify('Suggestions loaded');
    } catch (error) {
      notify('Error: ' + error.message);
      console.error('Suggestion error:', error);
      updateMeta(null);
    } finally {
      disableButtons(false);
    }
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      analyzeBtn.click();
    }
  });
});
