const $ = (selector) => document.querySelector(selector);
const state = { meetings: [], selected: null, file: null };
const statusText = { uploaded: 'Готово к обработке', processing: 'Обрабатывается', transcribed: 'Транскрипция готова', analyzed: 'Готово', failed: 'Ошибка' };

async function api(url, options = {}) {
  const response = await fetch(url, { credentials: 'include', ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Что-то пошло не так');
  return data;
}

async function init() {
  try { const user = await api('/api/auth/me'); $('#user').textContent = user.name; $('#sidebar-user').textContent = user.name; $('#avatar').textContent = user.name.charAt(0).toUpperCase(); await loadMeetings(); }
  catch { location.href = '/'; }
  $('#choose').onclick = () => $('#file').click();
  $('#file').onchange = () => selectFile($('#file').files[0]);
  $('#send').onclick = upload;
  $('#refresh').onclick = loadMeetings;
  $('#search').oninput = renderMeetings;
  $('#close-results').onclick = () => { $('#results').hidden = true; state.selected = null; };
  $('#logout').onclick = async () => { await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' }); location.href = '/'; };
  $('#sidebar-logout').onclick = () => $('#logout').click();
  $('#new-meeting').onclick = () => $('#drop').scrollIntoView({ behavior: 'smooth', block: 'center' });
  $('#drop').ondragover = (event) => { event.preventDefault(); $('#drop').classList.add('dragging'); };
  $('#drop').ondragleave = () => $('#drop').classList.remove('dragging');
  $('#drop').ondrop = (event) => { event.preventDefault(); $('#drop').classList.remove('dragging'); selectFile(event.dataTransfer.files[0]); };
  $('#chat-send').onclick = askQuestion;
}

function selectFile(file) {
  if (!file) return;
  const allowed = ['mp3', 'wav', 'm4a', 'mp4', 'webm'];
  const extension = file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(extension)) return setStatus('Поддерживаются MP3, WAV, M4A, MP4 и WebM');
  state.file = file; $('#fileName').textContent = file.name; $('#send').disabled = false; setStatus(`${(file.size / 1024 / 1024).toFixed(1)} MB · готово к обработке`);
}

function setStatus(message) { $('#status').textContent = message; }

async function upload() {
  if (!state.file) return;
  $('#send').disabled = true; setStatus('Загружаем запись...');
  const form = new FormData(); form.append('file', state.file);
  try { const meeting = await api('/api/meetings', { method: 'POST', body: form }); state.file = null; $('#file').value = ''; $('#fileName').textContent = 'Выберите файл'; await loadMeetings(); await processMeeting(meeting.id); }
  catch (error) { setStatus(error.message); $('#send').disabled = false; }
}

async function processMeeting(id) {
  setStatus('Транскрибируем запись...');
  try {
    await api(`/api/meetings/${id}/process`, { method: 'POST' });
    for (let attempt = 0; attempt < 180; attempt += 1) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const meeting = await api(`/api/meetings/${id}`); await loadMeetings(false);
      if (meeting.status === 'failed') throw new Error(meeting.error_message || 'Не удалось обработать запись');
      if (meeting.status === 'transcribed') { setStatus('Создаём протокол...'); const protocol = await api(`/api/meetings/${id}/analyze`, { method: 'POST' }); showResults(protocol, meeting); return; }
    }
    throw new Error('Обработка занимает больше времени. Проверьте встречу позже.');
  } catch (error) { setStatus(error.message); $('#send').disabled = false; await loadMeetings(false); }
}

async function loadMeetings(showLoading = true) {
  if (showLoading) $('#meetings').innerHTML = '<div class="loading-state">Загрузка встреч...</div>';
  try { state.meetings = await api('/api/meetings'); renderHistory(); renderMeetings(); }
  catch (error) { $('#meetings').innerHTML = `<div class="empty-state"><b>Не удалось загрузить встречи</b><span>${error.message}</span></div>`; }
}

function renderHistory() {
  const history = $('#history-list');
  if (!state.meetings.length) { history.innerHTML = '<span class="history-empty">Пока нет встреч</span>'; return; }
  history.innerHTML = state.meetings.slice(0, 12).map(item => `<button class="history-item" data-history="${item.id}"><span class="history-dot">●</span><span>${escapeHtml(item.filename)}</span></button>`).join('');
  document.querySelectorAll('[data-history]').forEach(item => item.onclick = () => openMeeting(Number(item.dataset.history)));
}

function renderMeetings() {
  const query = ($('#search').value || '').toLowerCase();
  const meetings = state.meetings.filter(item => item.filename.toLowerCase().includes(query));
  if (!meetings.length) { $('#meetings').innerHTML = `<div class="empty-state"><span class="empty-icon">◌</span><b>${query ? 'Ничего не найдено' : 'Встреч пока нет'}</b><span>${query ? 'Попробуйте другой запрос' : 'Загрузите первую запись, чтобы увидеть её здесь'}</span></div>`; return; }
  $('#meetings').innerHTML = meetings.map(meeting => `<article class="meeting-card" data-id="${meeting.id}"><div class="meeting-icon">◒</div><div class="meeting-info"><h3>${escapeHtml(meeting.filename)}</h3><span>${meeting.language ? meeting.language.toUpperCase() : '—'} · ${meeting.duration ? formatDuration(meeting.duration) : 'длительность неизвестна'}</span></div><div class="meeting-status ${meeting.status}"><i></i>${statusText[meeting.status] || meeting.status}</div><button class="delete-meeting" data-delete="${meeting.id}" aria-label="Удалить встречу">×</button></article>`).join('');
  document.querySelectorAll('.meeting-card').forEach(card => card.onclick = (event) => { if (!event.target.closest('[data-delete]')) openMeeting(Number(card.dataset.id)); });
  document.querySelectorAll('[data-delete]').forEach(button => button.onclick = (event) => { event.stopPropagation(); removeMeeting(Number(button.dataset.delete)); });
}

async function openMeeting(id) { const meeting = await api(`/api/meetings/${id}`); if (meeting.protocol_json) showResults(meeting.protocol_json, meeting); else if (meeting.status === 'uploaded' || meeting.status === 'failed') processMeeting(id); else setStatus('Встреча ещё обрабатывается...'); }
async function removeMeeting(id) { if (!confirm('Удалить эту встречу?')) return; await api(`/api/meetings/${id}`, { method: 'DELETE' }); $('#results').hidden = true; await loadMeetings(); }
function showResults(protocol, meeting) { state.selected = meeting.id; $('#result-title').textContent = meeting.filename; $('#summary').textContent = protocol.summary || 'Нет summary'; fillList('#decisions', protocol.decisions); fillList('#actions', protocol.action_items, true); fillList('#risks', protocol.risks); ['json', 'csv', 'pdf'].forEach(format => { $(`#${format}-export`).href = `/api/meetings/${meeting.id}/export/${format}`; }); $('#results').hidden = false; $('#results').scrollIntoView({ behavior: 'smooth', block: 'start' }); setStatus('Встреча готова'); }
function fillList(selector, items = [], actions = false) { $(selector).innerHTML = items.length ? items.map(item => `<li>${escapeHtml(typeof item === 'string' ? item : `${item.task || item.text || ''}${actions && item.assignee ? ` — ${item.assignee}` : ''}`)}</li>`).join('') : '<li class="muted-item">Нет данных</li>'; }
async function askQuestion() { if (!state.selected) return; const input = $('#chat-question'); if (!input.value.trim()) return; $('#chat-answer').textContent = 'Думаю...'; try { const result = await api(`/api/meetings/${state.selected}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: input.value.trim() }) }); $('#chat-answer').textContent = result.answer; } catch (error) { $('#chat-answer').textContent = error.message; } }
function formatDuration(seconds) { const minutes = Math.floor(seconds / 60); return `${minutes} мин`; }
function escapeHtml(value) { return String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character])); }
init();
