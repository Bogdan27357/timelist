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
let meetingsCache = [];

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
        case 'meetings': loadMeetings(); break;
        case 'tasks': loadTasks(); break;
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
    document.getElementById('statMeetings').textContent = stats.total_meetings;
    document.getElementById('statTasks').textContent = stats.total_tasks;
    document.getElementById('statOverdue').textContent = stats.tasks_overdue;
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
    const taskAssignee = document.getElementById('taskAssignee');
    if (taskAssignee) {
        taskAssignee.innerHTML = '<option value="">Не назначен</option>' +
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

// ==================== Meetings (5-step 1C Timelist flow) ====================
const TRANSCRIPTION_STATUS = {
    pending: { label: 'Ожидает', badge: 'badge-neutral' },
    processing: { label: 'Расшифровка...', badge: 'badge-warning' },
    done: { label: 'Готова', badge: 'badge-success' },
    error: { label: 'Ошибка', badge: 'badge-danger' },
};

async function loadMeetings() {
    const data = await API.get('/api/meetings/');
    meetingsCache = data;
    const tbody = document.getElementById('meetingsTable');
    tbody.innerHTML = data.map(m => {
        const ts = TRANSCRIPTION_STATUS[m.transcription_status] || TRANSCRIPTION_STATUS.pending;
        const partNames = (m.participants || []).map(p => p.name || 'Участник').join(', ');
        return `<tr>
            <td>${new Date(m.meeting_date).toLocaleString('ru-RU')}</td>
            <td><a href="#" onclick="openMeetingDetail(${m.id}); return false;"><strong>${esc(m.title)}</strong></a></td>
            <td>${m.duration_minutes} мин</td>
            <td>${esc(partNames) || '—'}</td>
            <td><span class="badge ${ts.badge}">${ts.label}</span></td>
            <td>
                ${m.is_protocol_generated
                    ? (m.is_protocol_transferred
                        ? '<span class="badge badge-success">Перенесён</span>'
                        : '<span class="badge badge-info">Сгенерирован</span>')
                    : '<span class="badge badge-neutral">Нет</span>'}
            </td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="openMeetingDetail(${m.id})">&#9998; Открыть</button>
                <button class="btn btn-danger btn-sm" onclick="deleteMeeting(${m.id})">&#10005;</button>
            </td>
        </tr>`;
    }).join('');
}

async function saveMeeting() {
    await API.post('/api/meetings/', {
        title: document.getElementById('mtTitle').value,
        description: document.getElementById('mtDescription').value,
        meeting_date: document.getElementById('mtDate').value,
        duration_minutes: parseInt(document.getElementById('mtDuration').value) || 60,
        location: document.getElementById('mtLocation').value,
        speaker_count: parseInt(document.getElementById('mtSpeakerCount').value) || 2,
    });
    hideModal('meetingModal');
    loadMeetings();
}

async function deleteMeeting(id) {
    if (!confirm('Удалить мероприятие?')) return;
    await API.del(`/api/meetings/${id}`);
    loadMeetings();
}

async function openMeetingDetail(id) {
    const m = await API.get(`/api/meetings/${id}`);
    document.getElementById('meetingDetailTitle').textContent = m.title;

    const ts = TRANSCRIPTION_STATUS[m.transcription_status] || TRANSCRIPTION_STATUS.pending;
    const partList = (m.participants || []).map(p =>
        `<tr><td>${esc(p.name)}</td><td>${esc(p.role)}</td><td>${esc(p.speaker_label)}</td>
         <td><button class="btn btn-danger btn-sm" onclick="removeParticipant(${m.id},${p.id})">&#10005;</button></td></tr>`
    ).join('');

    const sentimentLabel = m.ai_sentiment === 'positive' ? 'Позитивный'
        : m.ai_sentiment === 'negative' ? 'Негативный' : 'Нейтральный';
    const sentimentBadge = m.ai_sentiment === 'positive' ? 'badge-success'
        : m.ai_sentiment === 'negative' ? 'badge-danger' : 'badge-warning';

    let html = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
        <div><strong>Дата:</strong> ${new Date(m.meeting_date).toLocaleString('ru-RU')}</div>
        <div><strong>Длительность:</strong> ${m.duration_minutes} мин</div>
        <div><strong>Место:</strong> ${esc(m.location) || '—'}</div>
        <div><strong>Спикеров:</strong> ${m.speaker_count}</div>
    </div>
    ${m.description ? `<div class="card" style="margin-bottom:12px;"><strong>Описание:</strong> ${esc(m.description)}</div>` : ''}

    <!-- Participants -->
    <div class="card" style="margin-bottom:12px;">
        <h4>Участники и роли</h4>
        <table><thead><tr><th>Имя</th><th>Роль</th><th>Спикер</th><th></th></tr></thead>
        <tbody>${partList || '<tr><td colspan="4">Нет участников</td></tr>'}</tbody></table>
        <div style="margin-top:8px;display:flex;gap:8px;">
            <input id="addPartName" placeholder="Имя" style="padding:6px;border:1px solid #ddd;border-radius:6px;">
            <select id="addPartRole" style="padding:6px;border:1px solid #ddd;border-radius:6px;">
                <option>Участник</option><option>Председатель</option><option>Секретарь</option><option>Докладчик</option>
            </select>
            <button class="btn btn-primary btn-sm" onclick="addParticipant(${m.id})">+ Добавить</button>
        </div>
    </div>

    <!-- 5-step flow -->
    <div class="card" style="margin-bottom:12px;">
        <h4>5 шагов к протоколу</h4>
        <div style="display:flex;flex-direction:column;gap:10px;margin-top:12px;">

            <!-- Step 1: Upload audio -->
            <div style="display:flex;align-items:center;gap:12px;padding:10px;background:#f8f9fa;border-radius:8px;">
                <span class="badge badge-info" style="min-width:24px;text-align:center;">1</span>
                <div style="flex:1;">
                    <strong>Прикрепить аудиофайл</strong>
                    ${m.audio_file_path ? '<span class="badge badge-success" style="margin-left:8px;">Загружен</span>' : ''}
                </div>
                <div>
                    <input type="file" id="audioFile_${m.id}" accept=".mp3,.wav,.ogg,.m4a,.flac,.webm,.mp4,.wma" style="font-size:0.8rem;">
                    <button class="btn btn-primary btn-sm" onclick="uploadAudio(${m.id})">Загрузить</button>
                </div>
            </div>

            <!-- Step 1b: Or upload transcript -->
            <div style="display:flex;align-items:center;gap:12px;padding:10px;background:#f8f9fa;border-radius:8px;">
                <span class="badge badge-neutral" style="min-width:24px;text-align:center;">1b</span>
                <div style="flex:1;"><strong>Или загрузить текстовый транскрипт</strong></div>
                <div>
                    <input type="file" id="txtFile_${m.id}" accept=".txt" style="font-size:0.8rem;">
                    <button class="btn btn-outline btn-sm" onclick="uploadMeetingTranscript(${m.id})">Загрузить .txt</button>
                </div>
            </div>

            <!-- Step 2: Transcribe -->
            <div style="display:flex;align-items:center;gap:12px;padding:10px;background:#f8f9fa;border-radius:8px;">
                <span class="badge badge-info" style="min-width:24px;text-align:center;">2</span>
                <div style="flex:1;">
                    <strong>Запустить расшифровку (Whisper)</strong>
                    <span class="badge ${ts.badge}" style="margin-left:8px;">${ts.label}</span>
                </div>
                <button class="btn btn-primary btn-sm" id="btnTranscribe_${m.id}"
                    onclick="transcribeMeeting(${m.id}, this)"
                    ${!m.audio_file_path || m.transcription_status === 'done' ? 'disabled' : ''}>
                    Запустить сервис
                </button>
            </div>

            <!-- Step 3: Diarize speakers -->
            <div style="display:flex;align-items:center;gap:12px;padding:10px;background:#f8f9fa;border-radius:8px;">
                <span class="badge badge-info" style="min-width:24px;text-align:center;">3</span>
                <div style="flex:1;"><strong>Определить спикеров (ИИ)</strong></div>
                <button class="btn btn-primary btn-sm" onclick="diarizeMeeting(${m.id}, this)"
                    ${!m.transcript ? 'disabled' : ''}>
                    Диаризация
                </button>
            </div>

            <!-- Step 4: Generate protocol -->
            <div style="display:flex;align-items:center;gap:12px;padding:10px;background:#f8f9fa;border-radius:8px;">
                <span class="badge badge-info" style="min-width:24px;text-align:center;">4</span>
                <div style="flex:1;">
                    <strong>Получить автопротокол (ИИ)</strong>
                    ${m.is_protocol_generated ? '<span class="badge badge-success" style="margin-left:8px;">Готов</span>' : ''}
                </div>
                <button class="btn btn-primary btn-sm" onclick="generateProtocol(${m.id}, this)"
                    ${!m.transcript ? 'disabled' : ''}>
                    Получить автопротокол
                </button>
            </div>

            <!-- Step 5: Transfer & create tasks -->
            <div style="display:flex;align-items:center;gap:12px;padding:10px;background:#f8f9fa;border-radius:8px;">
                <span class="badge badge-info" style="min-width:24px;text-align:center;">5</span>
                <div style="flex:1;">
                    <strong>Перенести протокол и поставить задачи</strong>
                    ${m.is_protocol_transferred ? '<span class="badge badge-success" style="margin-left:8px;">Перенесён</span>' : ''}
                </div>
                <button class="btn btn-success btn-sm" onclick="transferProtocol(${m.id}, this)"
                    ${!m.is_protocol_generated || m.is_protocol_transferred ? 'disabled' : ''}>
                    Перенести протокол
                </button>
            </div>
        </div>
    </div>`;

    // Show stenogram/transcript with speaker colors
    if (m.stenogram || m.transcript) {
        const stenText = m.stenogram || m.transcript;
        html += `<div class="card" style="margin-bottom:12px;">
            <h4>Стенограмма</h4>
            <div class="stenogram-container">${renderStenogram(stenText)}</div>
        </div>`;
    }

    // Show AI protocol as formal document
    if (m.is_protocol_generated) {
        html += `<div class="card" style="margin-bottom:12px;">
            <h4>Автопротокол (ИИ)
                <span class="badge ${sentimentBadge}" style="margin-left:8px;font-size:0.7rem;">${sentimentLabel}</span>
            </h4>
            <div class="analysis-result" style="margin-bottom:16px;">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div class="analysis-section">
                        <strong>Резюме</strong>
                        <p>${esc(m.ai_summary)}</p>
                    </div>
                    <div class="analysis-section">
                        <strong>Ключевые темы</strong>
                        <p>${esc(m.ai_key_topics)}</p>
                    </div>
                </div>
            </div>
            <div class="protocol-document">${renderProtocolDocument(m)}</div>
        </div>`;
    }

    // Show final protocol as formal document
    if (m.is_protocol_transferred && m.final_protocol) {
        html += `<div class="card" style="margin-bottom:12px;border:2px solid var(--success);">
            <h4 style="color:var(--success);">Итоговый протокол мероприятия</h4>
            <div class="protocol-document">${renderProtocolDocument(m)}</div>
        </div>`;
    }

    document.getElementById('meetingDetailContent').innerHTML = html;
    showModal('meetingDetailModal');
}

async function uploadAudio(meetingId) {
    const input = document.getElementById(`audioFile_${meetingId}`);
    if (!input.files.length) return alert('Выберите аудиофайл');
    const formData = new FormData();
    formData.append('file', input.files[0]);
    formData.append('speaker_count', '2');
    const res = await fetch(`/api/meetings/${meetingId}/upload-audio`, { method: 'POST', body: formData });
    const result = await res.json();
    if (res.ok) {
        alert(`Файл загружен (${result.size_mb} МБ)`);
        openMeetingDetail(meetingId);
    } else {
        alert(result.detail || 'Ошибка загрузки');
    }
}

async function uploadMeetingTranscript(meetingId) {
    const input = document.getElementById(`txtFile_${meetingId}`);
    if (!input.files.length) return alert('Выберите текстовый файл');
    const formData = new FormData();
    formData.append('file', input.files[0]);
    await fetch(`/api/meetings/${meetingId}/upload-transcript`, { method: 'POST', body: formData });
    openMeetingDetail(meetingId);
}

async function transcribeMeeting(meetingId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Расшифровка...';
    try {
        const res = await fetch(`/api/meetings/${meetingId}/transcribe`, { method: 'POST' });
        const result = await res.json();
        if (res.ok) {
            alert('Расшифровка завершена!');
        } else {
            alert(result.detail || 'Ошибка расшифровки');
        }
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    openMeetingDetail(meetingId);
}

async function diarizeMeeting(meetingId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Определение спикеров...';
    try {
        await fetch(`/api/meetings/${meetingId}/diarize`, { method: 'POST' });
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    openMeetingDetail(meetingId);
}

async function generateProtocol(meetingId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Генерация протокола...';
    try {
        await fetch(`/api/meetings/${meetingId}/generate-protocol`, { method: 'POST' });
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    openMeetingDetail(meetingId);
}

async function transferProtocol(meetingId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Перенос...';
    try {
        await fetch(`/api/meetings/${meetingId}/transfer-protocol`, { method: 'POST' });
        alert('Протокол перенесён, задачи созданы!');
    } catch (e) {
        alert('Ошибка: ' + e.message);
    }
    openMeetingDetail(meetingId);
    loadTasks();
}

async function addParticipant(meetingId) {
    const name = document.getElementById('addPartName').value;
    if (!name) return alert('Введите имя');
    const role = document.getElementById('addPartRole').value;
    await API.post(`/api/meetings/${meetingId}/participants`, { name, role });
    openMeetingDetail(meetingId);
}

async function removeParticipant(meetingId, participantId) {
    await API.del(`/api/meetings/${meetingId}/participants/${participantId}`);
    openMeetingDetail(meetingId);
}

// ==================== Tasks ====================
const TASK_STATUS_LABELS = { new: 'Новая', in_progress: 'В работе', done: 'Выполнена', cancelled: 'Отменена' };
const TASK_STATUS_BADGES = { new: 'badge-info', in_progress: 'badge-warning', done: 'badge-success', cancelled: 'badge-neutral' };
const PRIORITY_LABELS = { low: 'Низкий', medium: 'Средний', high: 'Высокий', critical: 'Критический' };
const PRIORITY_BADGES = { low: 'badge-neutral', medium: 'badge-info', high: 'badge-warning', critical: 'badge-danger' };

async function loadTasks() {
    let url = '/api/tasks/?';
    const status = document.getElementById('taskFilterStatus')?.value;
    if (status) url += `status=${status}&`;

    const data = await API.get(url);
    const tbody = document.getElementById('tasksTable');
    tbody.innerHTML = data.map(t => {
        const meeting = meetingsCache.find(m => m.id === t.meeting_id);
        const assignee = t.assignee_name || (employeesCache.find(e => e.id === t.assignee_id)?.full_name) || '—';
        const isOverdue = t.due_date && new Date(t.due_date) < new Date() && t.status !== 'done' && t.status !== 'cancelled';
        return `<tr style="${isOverdue ? 'background:#fff5f5;' : ''}">
            <td>${esc(t.title)}</td>
            <td>${meeting ? esc(meeting.title) : (t.meeting_id || '—')}</td>
            <td>${esc(assignee)}</td>
            <td><span class="badge ${PRIORITY_BADGES[t.priority] || 'badge-neutral'}">${PRIORITY_LABELS[t.priority] || t.priority}</span></td>
            <td>${t.due_date || '—'} ${isOverdue ? '<span class="badge badge-danger">Просрочена</span>' : ''}</td>
            <td><span class="badge ${TASK_STATUS_BADGES[t.status] || 'badge-neutral'}">${TASK_STATUS_LABELS[t.status] || t.status}</span></td>
            <td>
                ${t.status === 'new' ? `<button class="btn btn-warning btn-sm" onclick="updateTaskStatus(${t.id},'in_progress')">В работу</button>` : ''}
                ${t.status === 'in_progress' ? `<button class="btn btn-success btn-sm" onclick="updateTaskStatus(${t.id},'done')">&#10003; Готово</button>` : ''}
                <button class="btn btn-danger btn-sm" onclick="deleteTask(${t.id})">&#10005;</button>
            </td>
        </tr>`;
    }).join('');
}

async function saveTask() {
    const assigneeId = document.getElementById('taskAssignee').value;
    const assigneeName = assigneeId ?
        (employeesCache.find(e => e.id === parseInt(assigneeId))?.full_name || '') : '';
    await API.post('/api/tasks/', {
        title: document.getElementById('taskTitle').value,
        description: document.getElementById('taskDescription').value,
        assignee_id: assigneeId ? parseInt(assigneeId) : null,
        assignee_name: assigneeName,
        priority: document.getElementById('taskPriority').value,
        due_date: document.getElementById('taskDueDate').value || null,
    });
    hideModal('taskModal');
    loadTasks();
}

async function updateTaskStatus(id, status) {
    await API.put(`/api/tasks/${id}`, { status });
    loadTasks();
}

async function deleteTask(id) {
    if (!confirm('Удалить задачу?')) return;
    await API.del(`/api/tasks/${id}`);
    loadTasks();
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

    const sentimentLabel = call.ai_sentiment === 'positive' ? 'Позитивный'
        : call.ai_sentiment === 'negative' ? 'Негативный' : 'Нейтральный';
    const sentimentBadge = call.ai_sentiment === 'positive' ? 'badge-success'
        : call.ai_sentiment === 'negative' ? 'badge-danger' : 'badge-warning';

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
                <span class="badge ${sentimentBadge}">${sentimentLabel}</span>
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
    const firstDay = (new Date(calYear, calMonth - 1, 1).getDay() + 6) % 7;

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

// ==================== Stenogram & Protocol Renderers ====================

function renderStenogram(text) {
    if (!text) return '';
    const lines = text.split('\n');
    const speakerColors = {};
    let colorIndex = 0;

    return lines.map(line => {
        const trimmed = line.trim();
        if (!trimmed) return '';

        // Try to detect speaker pattern: "[timecode] Speaker: text" or "Speaker: text"
        let timecode = '';
        let speaker = '';
        let content = trimmed;

        // Extract timecode [HH:MM:SS] or [MM:SS - MM:SS] or [MM:SS]
        const tcMatch = trimmed.match(/^\[([^\]]+)\]\s*(.*)/);
        if (tcMatch) {
            timecode = tcMatch[1];
            content = tcMatch[2];
        }

        // Extract speaker name: "Name:" pattern
        const spMatch = content.match(/^([^:]{1,40}):\s*(.*)/);
        if (spMatch && !spMatch[1].match(/^\d/)) {
            speaker = spMatch[1].trim();
            content = spMatch[2];
        }

        if (speaker) {
            if (!(speaker in speakerColors)) {
                speakerColors[speaker] = colorIndex % 6;
                colorIndex++;
            }
            const cls = `speaker-${speakerColors[speaker]}`;
            return `<div class="stenogram-line ${cls}">`
                + (timecode ? `<span class="timecode">[${esc(timecode)}]</span>` : '')
                + `<span class="speaker-name">${esc(speaker)}:</span>`
                + `<span>${esc(content)}</span></div>`;
        }

        // No speaker detected — plain line
        return `<div class="stenogram-line">`
            + (timecode ? `<span class="timecode">[${esc(timecode)}]</span>` : '')
            + `<span>${esc(content)}</span></div>`;
    }).join('');
}

function renderProtocolDocument(m) {
    const date = new Date(m.meeting_date).toLocaleDateString('ru-RU', {
        year: 'numeric', month: 'long', day: 'numeric'
    });
    const time = new Date(m.meeting_date).toLocaleTimeString('ru-RU', {
        hour: '2-digit', minute: '2-digit'
    });

    const participants = (m.participants || []);
    const chairman = participants.find(p => p.role === 'Председатель');
    const secretary = participants.find(p => p.role === 'Секретарь');

    // Parse decisions from ai_decisions
    const decisionsLines = (m.ai_decisions || '').split('\n').filter(l => l.trim());
    // Parse action items from ai_action_items
    const actionLines = (m.ai_action_items || '').split('\n').filter(l => l.trim());

    let html = `
        <div class="protocol-title">ПРОТОКОЛ</div>
        <div class="protocol-subtitle">${esc(m.title)}</div>

        <dl class="protocol-meta">
            <dt>Дата:</dt><dd>${date}, ${time}</dd>
            ${m.location ? `<dt>Место:</dt><dd>${esc(m.location)}</dd>` : ''}
            <dt>Председатель:</dt><dd>${chairman ? esc(chairman.name) : '—'}</dd>
            <dt>Секретарь:</dt><dd>${secretary ? esc(secretary.name) : '—'}</dd>
        </dl>
    `;

    // Attendees
    if (participants.length) {
        html += `<div class="protocol-section-title">Присутствовали</div>
        <table class="protocol-table">
            <thead><tr><th>N</th><th>ФИО</th><th>Роль</th></tr></thead>
            <tbody>
                ${participants.map((p, i) =>
                    `<tr><td>${i + 1}</td><td>${esc(p.name)}</td><td>${esc(p.role)}</td></tr>`
                ).join('')}
            </tbody>
        </table>`;
    }

    // Summary
    if (m.ai_summary) {
        html += `<div class="protocol-section-title">Краткое содержание</div>
        <p>${esc(m.ai_summary)}</p>`;
    }

    // Key topics as agenda
    if (m.ai_key_topics) {
        const topics = m.ai_key_topics.split(',').map(t => t.trim()).filter(Boolean);
        html += `<div class="protocol-section-title">Повестка дня</div>
        <ol>${topics.map(t => `<li>${esc(t)}</li>`).join('')}</ol>`;
    }

    // Decisions
    if (decisionsLines.length) {
        html += `<div class="protocol-section-title">Решения</div>
        <table class="protocol-table">
            <thead><tr><th style="width:40px;">N</th><th>Решение</th></tr></thead>
            <tbody>
                ${decisionsLines.map((d, i) => {
                    const clean = d.replace(/^\d+\.\s*/, '').replace(/^-\s*/, '');
                    return `<tr><td>${i + 1}</td><td>${esc(clean)}</td></tr>`;
                }).join('')}
            </tbody>
        </table>`;
    }

    // Action items / Tasks
    if (actionLines.length) {
        html += `<div class="protocol-section-title">Задачи на контроле</div>
        <table class="protocol-table">
            <thead><tr><th style="width:40px;">N</th><th>Задача</th><th>Ответственный</th><th>Срок</th></tr></thead>
            <tbody>
                ${actionLines.map((line, i) => {
                    const clean = line.replace(/^-\s*/, '');
                    // Try to extract (assignee) [deadline]
                    let task = clean, assignee = '', deadline = '';
                    const assigneeMatch = clean.match(/\(([^)]+)\)/);
                    if (assigneeMatch) {
                        assignee = assigneeMatch[1];
                        task = clean.replace(assigneeMatch[0], '').trim();
                    }
                    const deadlineMatch = clean.match(/\[([^\]]+)\]/);
                    if (deadlineMatch) {
                        deadline = deadlineMatch[1];
                        task = task.replace(deadlineMatch[0], '').trim();
                    }
                    return `<tr><td>${i + 1}</td><td>${esc(task)}</td><td>${esc(assignee)}</td><td>${esc(deadline)}</td></tr>`;
                }).join('')}
            </tbody>
        </table>`;
    }

    // Signatures
    html += `<div class="protocol-signatures">
        <div>
            <div class="signature-line">Председатель: ${chairman ? esc(chairman.name) : '________________'}</div>
        </div>
        <div>
            <div class="signature-line">Секретарь: ${secretary ? esc(secretary.name) : '________________'}</div>
        </div>
    </div>`;

    return html;
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
