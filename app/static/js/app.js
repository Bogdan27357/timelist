// ==================== API Helpers ====================
const API = {
    async get(url) {
        const res = await fetch(url);
        return res.json();
    },
    async post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async put(url, data) {
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },
    async del(url) {
        const res = await fetch(url, { method: 'DELETE' });
        return res.json();
    },
};

// ==================== Navigation ====================
let employeesCache = [];

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        const section = item.dataset.section;
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(section).classList.add('active');
        loadSection(section);
    });
});

function loadSection(section) {
    switch (section) {
        case 'dashboard': loadDashboard(); break;
        case 'employees': loadEmployees(); break;
        case 'timesheet': loadTimesheet(); break;
        case 'absences': loadAbsences(); break;
        case 'calls': loadCalls(); break;
        case 'calendar': loadCalendar(); break;
    }
}

// ==================== Modals ====================
function showModal(id) {
    document.getElementById(id).classList.add('active');
}
function hideModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Close modals on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
        if (e.target === overlay) overlay.classList.remove('active');
    });
});

// ==================== Dashboard ====================
async function loadDashboard() {
    const stats = await API.get('/api/dashboard/stats');
    document.getElementById('statEmployees').textContent = stats.total_employees;
    document.getElementById('statActive').textContent = stats.active_today;
    document.getElementById('statVacation').textContent = stats.on_vacation;
    document.getElementById('statSick').textContent = stats.on_sick_leave;
    document.getElementById('statCalls').textContent = stats.total_calls_this_month;
    document.getElementById('statAnalyzed').textContent = stats.analyzed_calls;
    document.getElementById('statAvgHours').textContent = stats.avg_hours_today;
}

// ==================== Employees ====================
async function loadEmployees() {
    const data = await API.get('/api/employees/');
    employeesCache = data;
    const tbody = document.getElementById('employeesTable');
    tbody.innerHTML = data.map(e => `
        <tr>
            <td>${esc(e.full_name)}</td>
            <td>${esc(e.position)}</td>
            <td>${esc(e.department)}</td>
            <td>${esc(e.email)}</td>
            <td>${esc(e.phone)}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteEmployee(${e.id})">&#10005;</button>
            </td>
        </tr>
    `).join('');
    populateEmployeeSelects(data);
}

function populateEmployeeSelects(employees) {
    const selects = ['tsEmployee', 'absEmployee'];
    selects.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = employees.map(e => `<option value="${e.id}">${esc(e.full_name)}</option>`).join('');
    });
    const filter = document.getElementById('tsFilterEmployee');
    if (filter) {
        filter.innerHTML = '<option value="">Все</option>' +
            employees.map(e => `<option value="${e.id}">${esc(e.full_name)}</option>`).join('');
    }
}

async function saveEmployee() {
    await API.post('/api/employees/', {
        full_name: document.getElementById('empName').value,
        position: document.getElementById('empPosition').value,
        department: document.getElementById('empDepartment').value,
        email: document.getElementById('empEmail').value,
        phone: document.getElementById('empPhone').value,
        hire_date: document.getElementById('empHireDate').value || null,
    });
    hideModal('employeeModal');
    loadEmployees();
}

async function deleteEmployee(id) {
    if (!confirm('Деактивировать сотрудника?')) return;
    await API.del(`/api/employees/${id}`);
    loadEmployees();
}

// ==================== Timesheet ====================
async function loadTimesheet() {
    let url = '/api/timesheet/?';
    const empId = document.getElementById('tsFilterEmployee')?.value;
    const from = document.getElementById('tsFilterFrom')?.value;
    const to = document.getElementById('tsFilterTo')?.value;
    if (empId) url += `employee_id=${empId}&`;
    if (from) url += `date_from=${from}&`;
    if (to) url += `date_to=${to}&`;

    const data = await API.get(url);
    const tbody = document.getElementById('timesheetTable');
    tbody.innerHTML = data.map(e => {
        const emp = employeesCache.find(em => em.id === e.employee_id);
        return `<tr>
            <td>${e.date}</td>
            <td>${emp ? esc(emp.full_name) : e.employee_id}</td>
            <td>${e.clock_in || '—'}</td>
            <td>${e.clock_out || '—'}</td>
            <td>${e.break_minutes} мин</td>
            <td><strong>${e.total_hours}</strong></td>
            <td>${e.overtime_hours > 0 ? `<span class="badge badge-warning">${e.overtime_hours}</span>` : '—'}</td>
            <td>${esc(e.note)}</td>
            <td><button class="btn btn-danger btn-sm" onclick="deleteTimesheet(${e.id})">&#10005;</button></td>
        </tr>`;
    }).join('');
    if (employeesCache.length === 0) loadEmployees();
}

async function saveTimesheet() {
    await API.post('/api/timesheet/', {
        employee_id: parseInt(document.getElementById('tsEmployee').value),
        date: document.getElementById('tsDate').value,
        clock_in: document.getElementById('tsClockIn').value || null,
        clock_out: document.getElementById('tsClockOut').value || null,
        break_minutes: parseInt(document.getElementById('tsBreak').value) || 0,
        note: document.getElementById('tsNote').value,
    });
    hideModal('timesheetModal');
    loadTimesheet();
}

async function deleteTimesheet(id) {
    if (!confirm('Удалить запись?')) return;
    await API.del(`/api/timesheet/${id}`);
    loadTimesheet();
}

// ==================== Absences ====================
const ABSENCE_LABELS = {
    vacation: 'Отпуск', sick_leave: 'Больничный', business_trip: 'Командировка',
    remote: 'Удалёнка', day_off: 'Отгул', other: 'Другое',
};
const STATUS_LABELS = { pending: 'На рассмотрении', approved: 'Одобрено', rejected: 'Отклонено' };
const STATUS_BADGES = { pending: 'badge-warning', approved: 'badge-success', rejected: 'badge-danger' };

async function loadAbsences() {
    const data = await API.get('/api/absences/');
    const tbody = document.getElementById('absencesTable');
    tbody.innerHTML = data.map(a => {
        const emp = employeesCache.find(e => e.id === a.employee_id);
        return `<tr>
            <td>${emp ? esc(emp.full_name) : a.employee_id}</td>
            <td>${ABSENCE_LABELS[a.absence_type] || a.absence_type}</td>
            <td>${a.start_date}</td>
            <td>${a.end_date}</td>
            <td><span class="badge ${STATUS_BADGES[a.status] || 'badge-neutral'}">${STATUS_LABELS[a.status] || a.status}</span></td>
            <td>${esc(a.reason)}</td>
            <td>
                ${a.status === 'pending' ? `
                    <button class="btn btn-success btn-sm" onclick="updateAbsenceStatus(${a.id},'approved')">&#10003;</button>
                    <button class="btn btn-danger btn-sm" onclick="updateAbsenceStatus(${a.id},'rejected')">&#10005;</button>
                ` : ''}
                <button class="btn btn-danger btn-sm" onclick="deleteAbsence(${a.id})">&#128465;</button>
            </td>
        </tr>`;
    }).join('');
    if (employeesCache.length === 0) loadEmployees();
}

async function saveAbsence() {
    await API.post('/api/absences/', {
        employee_id: parseInt(document.getElementById('absEmployee').value),
        absence_type: document.getElementById('absType').value,
        start_date: document.getElementById('absStart').value,
        end_date: document.getElementById('absEnd').value,
        reason: document.getElementById('absReason').value,
    });
    hideModal('absenceModal');
    loadAbsences();
}

async function updateAbsenceStatus(id, status) {
    await API.put(`/api/absences/${id}`, { status });
    loadAbsences();
}

async function deleteAbsence(id) {
    if (!confirm('Удалить запись?')) return;
    await API.del(`/api/absences/${id}`);
    loadAbsences();
}

// ==================== Calls ====================
async function loadCalls() {
    const data = await API.get('/api/calls/');
    const tbody = document.getElementById('callsTable');
    tbody.innerHTML = data.map(c => `
        <tr>
            <td>${new Date(c.call_date).toLocaleString('ru-RU')}</td>
            <td>${esc(c.title)}</td>
            <td>${c.duration_minutes} мин</td>
            <td>${esc(c.participants)}</td>
            <td>
                ${c.is_analyzed
                    ? '<span class="badge badge-success">Готов</span>'
                    : (c.transcript ? '<span class="badge badge-warning">Ожидает</span>' : '<span class="badge badge-neutral">Нет данных</span>')}
            </td>
            <td>
                ${c.transcript && !c.is_analyzed ? `<button class="btn btn-primary btn-sm" onclick="analyzeCall(${c.id}, this)">&#9881; Анализ</button>` : ''}
                ${c.is_analyzed ? `<button class="btn btn-success btn-sm" onclick="showAnalysis(${c.id})">&#128202; Результат</button>` : ''}
                <button class="btn btn-danger btn-sm" onclick="deleteCall(${c.id})">&#10005;</button>
            </td>
        </tr>
    `).join('');
}

async function saveCall() {
    await API.post('/api/calls/', {
        title: document.getElementById('callTitle').value,
        call_date: document.getElementById('callDate').value,
        duration_minutes: parseInt(document.getElementById('callDuration').value) || 0,
        participants: document.getElementById('callParticipants').value,
        transcript: document.getElementById('callTranscript').value,
    });
    hideModal('callModal');
    loadCalls();
}

async function uploadTranscript() {
    const file = document.getElementById('uploadFile').files[0];
    if (!file) return alert('Выберите файл');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', document.getElementById('uploadTitle').value);
    formData.append('participants', document.getElementById('uploadParticipants').value);
    formData.append('call_date', document.getElementById('uploadDate').value);

    await fetch('/api/calls/upload', { method: 'POST', body: formData });
    hideModal('uploadModal');
    loadCalls();
}

async function analyzeCall(id, btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Анализ...';
    try {
        await fetch(`/api/calls/${id}/analyze`, { method: 'POST' });
        loadCalls();
    } catch (e) {
        alert('Ошибка анализа: ' + e.message);
        btn.disabled = false;
        btn.innerHTML = '&#9881; Анализ';
    }
}

async function showAnalysis(id) {
    const call = await API.get(`/api/calls/${id}`);
    document.getElementById('analysisTitle').textContent = `ИИ-анализ: ${call.title}`;

    const sentimentClass = call.ai_sentiment === 'positive' ? 'sentiment-positive'
        : call.ai_sentiment === 'negative' ? 'sentiment-negative' : 'sentiment-neutral';
    const sentimentLabel = call.ai_sentiment === 'positive' ? 'Позитивный'
        : call.ai_sentiment === 'negative' ? 'Негативный' : 'Нейтральный';

    document.getElementById('analysisContent').innerHTML = `
        <div class="analysis-result">
            <div class="analysis-section">
                <strong>Резюме</strong>
                <p>${esc(call.ai_summary)}</p>
            </div>
            <div class="analysis-section">
                <strong>Ключевые темы</strong>
                <p>${esc(call.ai_key_topics)}</p>
            </div>
            <div class="analysis-section">
                <strong>Принятые решения</strong>
                <pre style="white-space:pre-wrap;font-family:inherit;">${esc(call.ai_decisions)}</pre>
            </div>
            <div class="analysis-section">
                <strong>Задачи и действия</strong>
                <pre style="white-space:pre-wrap;font-family:inherit;">${esc(call.ai_action_items)}</pre>
            </div>
            <div class="analysis-section">
                <strong>Тон встречи</strong>
                <span class="badge ${sentimentClass === 'sentiment-positive' ? 'badge-success' : sentimentClass === 'sentiment-negative' ? 'badge-danger' : 'badge-warning'}">
                    ${sentimentLabel}
                </span>
            </div>
        </div>
    `;
    showModal('analysisModal');
}

async function deleteCall(id) {
    if (!confirm('Удалить созвон?')) return;
    await API.del(`/api/calls/${id}`);
    loadCalls();
}

// ==================== Calendar ====================
let calYear, calMonth;

function initCalendar() {
    const now = new Date();
    calYear = now.getFullYear();
    calMonth = now.getMonth() + 1;
}

function changeMonth(delta) {
    calMonth += delta;
    if (calMonth > 12) { calMonth = 1; calYear++; }
    if (calMonth < 1) { calMonth = 12; calYear--; }
    loadCalendar();
}

const MONTHS_RU = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];

async function loadCalendar() {
    if (!calYear) initCalendar();
    document.getElementById('calendarMonth').textContent = `${MONTHS_RU[calMonth]} ${calYear}`;

    const data = await API.get(`/api/dashboard/calendar?year=${calYear}&month=${calMonth}`);
    const grid = document.getElementById('calendarGrid');

    const daysInMonth = new Date(calYear, calMonth, 0).getDate();
    const firstDay = (new Date(calYear, calMonth - 1, 1).getDay() + 6) % 7; // Monday = 0

    const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

    let html = '<table style="table-layout:fixed;"><thead><tr>';
    DAYS.forEach(d => html += `<th style="text-align:center;">${d}</th>`);
    html += '</tr></thead><tbody><tr>';

    for (let i = 0; i < firstDay; i++) html += '<td></td>';

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${calYear}-${String(calMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayEvents = data.events.filter(e => {
            if (e.type === 'absence') return dateStr >= e.start && dateStr <= e.end;
            if (e.type === 'call') return e.date.startsWith(dateStr);
            return false;
        });

        let cellContent = `<div style="font-weight:600;margin-bottom:4px;">${day}</div>`;
        dayEvents.forEach(e => {
            if (e.type === 'absence') {
                const label = ABSENCE_LABELS[e.absence_type] || e.absence_type;
                cellContent += `<div class="badge badge-info" style="font-size:0.65rem;margin:1px 0;display:block;">${label}: ${esc(e.employee)}</div>`;
            } else if (e.type === 'call') {
                cellContent += `<div class="badge ${e.analyzed ? 'badge-success' : 'badge-warning'}" style="font-size:0.65rem;margin:1px 0;display:block;">${esc(e.title)}</div>`;
            }
        });

        const isWeekend = (firstDay + day - 1) % 7 >= 5;
        html += `<td style="vertical-align:top;padding:6px;min-height:80px;${isWeekend ? 'background:#f9fafb;' : ''}">${cellContent}</td>`;

        if ((firstDay + day) % 7 === 0 && day < daysInMonth) html += '</tr><tr>';
    }

    const remaining = (7 - (firstDay + daysInMonth) % 7) % 7;
    for (let i = 0; i < remaining; i++) html += '<td></td>';
    html += '</tr></tbody></table>';

    grid.innerHTML = html;
}

// ==================== Ollama Status ====================
async function checkOllama() {
    try {
        const status = await API.get('/api/calls/ollama-status');
        const el = document.getElementById('ollamaStatus');
        if (status.status === 'online') {
            el.className = 'ollama-status ollama-online';
            el.innerHTML = `<span>&#9679;</span> <span class="nav-text">Ollama: ${status.current_model} ${status.model_available ? '&#10003;' : '(модель не найдена)'}</span>`;
        } else {
            el.className = 'ollama-status ollama-offline';
            el.innerHTML = '<span>&#9679;</span> <span class="nav-text">Ollama: оффлайн</span>';
        }
    } catch {
        // ignore
    }
}

// ==================== Helpers ====================
function esc(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ==================== Init ====================
loadDashboard();
loadEmployees();
checkOllama();
initCalendar();
