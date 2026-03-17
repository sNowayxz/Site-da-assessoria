/* ═══════════════════════════════════════════
   Atividades — CRUD + Rastreio
   ═══════════════════════════════════════════ */

var currentEditAtivId = null;
var _atividades = [];
var _alunosList = [];

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'assessor']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Hide delete buttons for assessor
  if (role === 'assessor') {
    window._atividadesRole = 'assessor';
  }

  // Carregar alunos para o select
  await loadAlunosSelect();

  // Carregar atividades
  await loadAtividades();

  // Nova atividade
  document.getElementById('btn-nova-atividade').addEventListener('click', function () {
    currentEditAtivId = null;
    document.getElementById('modal-title-ativ').textContent = 'Nova Atividade';
    document.getElementById('form-atividade').reset();
    openModal('modal-atividade');
  });

  document.getElementById('form-atividade').addEventListener('submit', handleSaveAtividade);

  // Filtros
  document.getElementById('filter-status').addEventListener('change', filterAtividades);
  document.getElementById('filter-tipo').addEventListener('change', filterAtividades);
  document.getElementById('filter-aluno').addEventListener('input', filterAtividades);
  var dtInicio = document.getElementById('filter-data-inicio');
  var dtFim = document.getElementById('filter-data-fim');
  if (dtInicio) dtInicio.addEventListener('change', filterAtividades);
  if (dtFim) dtFim.addEventListener('change', filterAtividades);
});

async function loadAlunosSelect() {
  var { data } = await sb.from('alunos').select('id, nome, ra').order('nome');
  _alunosList = data || [];

  var select = document.getElementById('ativ-aluno-id');
  select.innerHTML = '<option value="">Selecione o aluno</option>';
  _alunosList.forEach(function (a) {
    select.innerHTML += '<option value="' + a.id + '">' + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')</option>';
  });
}

async function loadAtividades() {
  var { data, error } = await sb
    .from('atividades')
    .select('*, alunos(nome, ra)')
    .order('created_at', { ascending: false });

  if (error) { console.error(error); return; }
  _atividades = data || [];
  renderAtividades(_atividades);
  updateCounters(_atividades);
}

function updateCounters(atividades) {
  var total = atividades.length;
  var pendentes = atividades.filter(function (a) { return a.status === 'pendente'; }).length;
  var andamento = atividades.filter(function (a) { return a.status === 'em_andamento'; }).length;
  var entregues = atividades.filter(function (a) { return a.status === 'entregue'; }).length;

  var el;
  el = document.getElementById('counter-total'); if (el) el.textContent = total;
  el = document.getElementById('counter-pendentes'); if (el) el.textContent = pendentes;
  el = document.getElementById('counter-andamento'); if (el) el.textContent = andamento;
  el = document.getElementById('counter-entregues'); if (el) el.textContent = entregues;
}

function renderAtividades(atividades) {
  var tbody = document.getElementById('atividades-table');
  if (!atividades.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhuma atividade registrada</td></tr>';
    return;
  }

  tbody.innerHTML = atividades.map(function (a) {
    var aluno = a.alunos || {};
    return '<tr>' +
      '<td><span class="aluno-name">' + escapeHtml(aluno.nome || '—') + '</span><br><small class="text-muted">' + escapeHtml(aluno.ra || '') + '</small></td>' +
      '<td><span class="badge badge-tipo">' + formatTipo(a.tipo) + '</span></td>' +
      '<td class="desc-cell">' + escapeHtml(a.descricao || '—') + '</td>' +
      '<td><span class="badge badge-' + a.status + '">' + formatStatus(a.status) + '</span></td>' +
      '<td>R$ ' + (Number(a.valor) || 0).toFixed(2) + '</td>' +
      '<td>' + formatDate(a.created_at) + '</td>' +
      '<td>' + formatDate(a.updated_at) + '</td>' +
      '<td class="actions">' +
        '<button class="btn-icon btn-status" onclick="cycleStatus(\'' + a.id + '\', \'' + a.status + '\')" title="Avançar Status">⏭️</button>' +
        '<button class="btn-icon" onclick="editAtividade(\'' + a.id + '\')" title="Editar">✏️</button>' +
        (window._atividadesRole !== 'assessor' ? '<button class="btn-icon btn-danger" onclick="deleteAtividade(\'' + a.id + '\')" title="Excluir">🗑️</button>' : '') +
      '</td>' +
      '</tr>';
  }).join('');
}

function filterAtividades() {
  var status = document.getElementById('filter-status').value;
  var tipo = document.getElementById('filter-tipo').value;
  var aluno = document.getElementById('filter-aluno').value.toLowerCase();
  var dtInicio = document.getElementById('filter-data-inicio') ? document.getElementById('filter-data-inicio').value : '';
  var dtFim = document.getElementById('filter-data-fim') ? document.getElementById('filter-data-fim').value : '';

  var filtered = _atividades.filter(function (a) {
    var alunoData = a.alunos || {};
    var matchStatus = !status || a.status === status;
    var matchTipo = !tipo || a.tipo === tipo;
    var matchAluno = !aluno || (alunoData.nome || '').toLowerCase().includes(aluno) || (alunoData.ra || '').toLowerCase().includes(aluno);
    var matchDate = true;
    if (dtInicio) {
      var created = (a.created_at || '').slice(0, 10);
      matchDate = matchDate && created >= dtInicio;
    }
    if (dtFim) {
      var created = (a.created_at || '').slice(0, 10);
      matchDate = matchDate && created <= dtFim;
    }
    return matchStatus && matchTipo && matchAluno && matchDate;
  });
  renderAtividades(filtered);
  updateCounters(filtered);
}

async function handleSaveAtividade(e) {
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

  if (!data.aluno_id) { alert('Selecione um aluno'); return; }

  try {
    if (currentEditAtivId) {
      var { error } = await sb.from('atividades').update(data).eq('id', currentEditAtivId);
      if (error) throw error;
    } else {
      var { error } = await sb.from('atividades').insert(data);
      if (error) throw error;
    }
    logAudit(currentEditAtivId ? 'update_atividade' : 'create_atividade', 'atividades', currentEditAtivId || 'new', { tipo: data.tipo, descricao: data.descricao });
    closeModal('modal-atividade');
    await loadAtividades();
  } catch (err) {
    alert('Erro: ' + err.message);
  }
}

async function editAtividade(id) {
  var ativ = _atividades.find(function (a) { return a.id === id; });
  if (!ativ) return;

  currentEditAtivId = id;
  document.getElementById('modal-title-ativ').textContent = 'Editar Atividade';
  var form = document.getElementById('form-atividade');
  form.aluno_id.value = ativ.aluno_id;
  form.tipo.value = ativ.tipo;
  form.descricao.value = ativ.descricao || '';
  form.status.value = ativ.status;
  form.valor.value = ativ.valor || 0;
  form.observacoes.value = ativ.observacoes || '';
  openModal('modal-atividade');
}

async function deleteAtividade(id) {
  if (!confirm('Tem certeza que deseja excluir esta atividade?')) return;
  var { error } = await sb.from('atividades').delete().eq('id', id);
  if (error) { alert('Erro: ' + error.message); return; }
  logAudit('delete_atividade', 'atividades', id, {});
  await loadAtividades();
}

// Avança o status no fluxo: pendente → em_andamento → entregue
async function cycleStatus(id, currentStatus) {
  var nextMap = {
    pendente: 'em_andamento',
    em_andamento: 'entregue',
    entregue: 'revisao',
    revisao: 'pendente'
  };
  var next = nextMap[currentStatus] || 'pendente';
  var { error } = await sb.from('atividades').update({ status: next }).eq('id', id);
  if (error) { alert('Erro: ' + error.message); return; }
  logAudit('status_change', 'atividades', id, { from: currentStatus, to: next });
  await loadAtividades();
}

function formatTipo(t) {
  var map = { atividade: 'Atividade', mapa: 'Mapa', tcc: 'TCC', relatorio: 'Relatório', extensao: 'Extensão', pacote: 'Pacote' };
  return map[t] || t;
}

function formatStatus(s) {
  var map = { pendente: 'Pendente', em_andamento: 'Em Andamento', entregue: 'Entregue', revisao: 'Revisão' };
  return map[s] || s;
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('pt-BR');
}

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Modal helpers
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
