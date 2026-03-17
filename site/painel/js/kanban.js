/* ═══════════════════════════════════════════
   Kanban — Drag & Drop Board for Atividades
   ═══════════════════════════════════════════ */

var _kanbanData = [];
var _kanbanAlunosList = [];
var _kanbanCurrentEditId = null;
var _draggedCard = null;

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'assessor']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Load filter options
  await loadAssessoresFilter();
  await loadAlunosSelect();

  // Load kanban data
  await loadKanbanData();

  // Init drag & drop
  initDragDrop();

  // Filter listeners
  document.getElementById('filter-assessor').addEventListener('change', filterKanban);
  document.getElementById('filter-tipo').addEventListener('change', filterKanban);
  document.getElementById('filter-aluno').addEventListener('input', filterKanban);

  // Form submit
  document.getElementById('form-atividade').addEventListener('submit', saveAtividade);
});


// ─── Load Data ───

async function loadKanbanData() {
  var { data, error } = await sb
    .from('atividades')
    .select('*, alunos(nome, ra)')
    .order('created_at', { ascending: false });

  if (error) {
    console.error('[kanban] Erro ao carregar:', error);
    showToast('Erro ao carregar atividades', 'error');
    return;
  }

  _kanbanData = data || [];
  renderKanban(_kanbanData);
}

async function loadAlunosSelect() {
  var { data } = await sb.from('alunos').select('id, nome, ra').order('nome');
  _kanbanAlunosList = data || [];

  var select = document.getElementById('ativ-aluno-id');
  if (!select) return;
  select.innerHTML = '<option value="">Selecione o aluno</option>';
  _kanbanAlunosList.forEach(function (a) {
    select.innerHTML += '<option value="' + a.id + '">' + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')</option>';
  });
}

async function loadAssessoresFilter() {
  var { data } = await sb.from('assessores').select('id, role');
  if (!data || !data.length) return;

  // Get user metadata for names
  var select = document.getElementById('filter-assessor');
  if (!select) return;

  // For now, assessor filter will filter by the user who created the activity
  // We keep the dropdown but it filters on client side if assessor_id is available
  // This is a best-effort approach since atividades may not have assessor_id
}


// ─── Render Kanban ───

function renderKanban(atividades) {
  var statuses = ['pendente', 'em_andamento', 'entregue', 'revisao'];
  var grouped = {};

  statuses.forEach(function (s) {
    grouped[s] = [];
  });

  atividades.forEach(function (a) {
    var status = a.status || 'pendente';
    if (!grouped[status]) grouped[status] = [];
    grouped[status].push(a);
  });

  statuses.forEach(function (s) {
    var container = document.getElementById('cards-' + s);
    var countEl = document.getElementById('count-' + s);

    if (countEl) countEl.textContent = grouped[s].length;

    if (!container) return;

    if (!grouped[s].length) {
      container.innerHTML = '<div class="kanban-empty">Nenhuma atividade</div>';
      return;
    }

    container.innerHTML = grouped[s].map(function (a) {
      var aluno = a.alunos || {};
      var desc = a.descricao || '';
      var truncDesc = desc.length > 80 ? desc.substring(0, 80) + '...' : desc;
      var dateStr = a.created_at ? new Date(a.created_at).toLocaleDateString('pt-BR') : '';
      var tipoBadgeClass = 'kanban-badge-' + (a.tipo || 'atividade');
      var tipoLabel = formatTipo(a.tipo);

      return '<div class="kanban-card" draggable="true" data-id="' + a.id + '" data-status="' + (a.status || 'pendente') + '">' +
        '<div class="kanban-card-header">' +
          '<span class="kanban-card-aluno" title="' + escapeHtml(aluno.nome || '') + '">' + escapeHtml(aluno.nome || 'Sem aluno') + '</span>' +
          '<span class="kanban-badge ' + tipoBadgeClass + '">' + tipoLabel + '</span>' +
        '</div>' +
        '<div class="kanban-card-desc">' + escapeHtml(truncDesc || 'Sem descri\u00e7\u00e3o') + '</div>' +
        '<div class="kanban-card-footer">' +
          '<span class="kanban-card-date">' + dateStr + '</span>' +
          '<button class="kanban-card-edit" onclick="editAtividade(\'' + a.id + '\')" title="Editar">\u270F\uFE0F</button>' +
        '</div>' +
      '</div>';
    }).join('');
  });

  // Re-init drag events on new cards
  initCardDragEvents();
}


// ─── Drag & Drop ───

function initDragDrop() {
  var columns = document.querySelectorAll('.kanban-cards');

  columns.forEach(function (col) {
    col.addEventListener('dragover', function (e) {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      var column = col.closest('.kanban-column');
      if (column) column.classList.add('drag-over');
    });

    col.addEventListener('dragleave', function (e) {
      // Only remove if actually leaving the column
      var column = col.closest('.kanban-column');
      if (column && !column.contains(e.relatedTarget)) {
        column.classList.remove('drag-over');
      }
    });

    col.addEventListener('drop', function (e) {
      e.preventDefault();
      var column = col.closest('.kanban-column');
      if (column) column.classList.remove('drag-over');

      var cardId = e.dataTransfer.getData('text/plain');
      var newStatus = col.closest('.kanban-column').getAttribute('data-status');

      if (!cardId || !newStatus) return;

      // Find the activity
      var ativ = _kanbanData.find(function (a) { return a.id === cardId; });
      if (!ativ || ativ.status === newStatus) return;

      // Update in DB
      updateCardStatus(cardId, newStatus);
    });
  });
}

function initCardDragEvents() {
  var cards = document.querySelectorAll('.kanban-card[draggable="true"]');

  cards.forEach(function (card) {
    card.addEventListener('dragstart', function (e) {
      _draggedCard = card;
      card.classList.add('dragging');
      e.dataTransfer.setData('text/plain', card.getAttribute('data-id'));
      e.dataTransfer.effectAllowed = 'move';
    });

    card.addEventListener('dragend', function () {
      card.classList.remove('dragging');
      _draggedCard = null;
      // Clean up all drag-over states
      document.querySelectorAll('.kanban-column.drag-over').forEach(function (col) {
        col.classList.remove('drag-over');
      });
    });
  });
}

async function updateCardStatus(id, newStatus) {
  var { error } = await sb
    .from('atividades')
    .update({ status: newStatus })
    .eq('id', id);

  if (error) {
    console.error('[kanban] Erro ao atualizar status:', error);
    showToast('Erro ao mover atividade', 'error');
    return;
  }

  // Update local data
  var ativ = _kanbanData.find(function (a) { return a.id === id; });
  if (ativ) ativ.status = newStatus;

  // Re-render with current filter
  filterKanban();
  showToast('Status atualizado!', 'success');
}


// ─── Filter ───

function filterKanban() {
  var assessor = document.getElementById('filter-assessor').value;
  var tipo = document.getElementById('filter-tipo').value;
  var aluno = document.getElementById('filter-aluno').value.toLowerCase().trim();

  var filtered = _kanbanData.filter(function (a) {
    var alunoData = a.alunos || {};
    var matchTipo = !tipo || a.tipo === tipo;
    var matchAluno = !aluno ||
      (alunoData.nome || '').toLowerCase().indexOf(aluno) !== -1 ||
      (alunoData.ra || '').toLowerCase().indexOf(aluno) !== -1;
    var matchAssessor = !assessor || a.assessor_id === assessor;

    return matchTipo && matchAluno && matchAssessor;
  });

  renderKanban(filtered);
}


// ─── Edit Modal ───

function editAtividade(id) {
  var ativ = _kanbanData.find(function (a) { return a.id === id; });
  if (!ativ) return;

  _kanbanCurrentEditId = id;
  document.getElementById('modal-title-ativ').textContent = 'Editar Atividade';
  var form = document.getElementById('form-atividade');
  form.aluno_id.value = ativ.aluno_id || '';
  form.tipo.value = ativ.tipo || 'atividade';
  form.descricao.value = ativ.descricao || '';
  form.status.value = ativ.status || 'pendente';
  form.valor.value = ativ.valor || 0;
  form.observacoes.value = ativ.observacoes || '';
  openModal('modal-atividade');
}

async function saveAtividade(e) {
  e.preventDefault();
  var form = e.target;
  var data = {
    aluno_id: form.aluno_id.value,
    tipo: form.tipo.value,
    descricao: form.descricao.value.trim(),
    status: form.status.value,
    valor: parseFloat(form.valor.value) || 0,
    observacoes: form.observacoes.value.trim()
  };

  if (!data.aluno_id) {
    showToast('Selecione um aluno', 'warning');
    return;
  }

  try {
    if (_kanbanCurrentEditId) {
      var { error } = await sb.from('atividades').update(data).eq('id', _kanbanCurrentEditId);
      if (error) throw error;
      showToast('Atividade atualizada!', 'success');
    } else {
      var { error } = await sb.from('atividades').insert(data);
      if (error) throw error;
      showToast('Atividade criada!', 'success');
    }
    closeModal('modal-atividade');
    _kanbanCurrentEditId = null;
    await loadKanbanData();
  } catch (err) {
    showToast('Erro: ' + err.message, 'error');
  }
}


// ─── Helpers ───

function formatTipo(t) {
  var map = { atividade: 'Atividade', mapa: 'Mapa', tcc: 'TCC', relatorio: 'Relat\u00f3rio', extensao: 'Extens\u00e3o', pacote: 'Pacote' };
  return map[t] || t || 'Atividade';
}

function formatStatus(s) {
  var map = { pendente: 'Pendente', em_andamento: 'Em Andamento', entregue: 'Entregue', revisao: 'Revis\u00e3o' };
  return map[s] || s;
}

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
