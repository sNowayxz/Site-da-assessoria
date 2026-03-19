/* ═══════════════════════════════════════════
   Gabaritos — CRUD
   ═══════════════════════════════════════════ */

var currentEditGabId = null;
var _gabaritos = [];

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'dono']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  await loadGabaritos();

  // Novo gabarito
  document.getElementById('btn-novo-gabarito').addEventListener('click', function () {
    currentEditGabId = null;
    document.getElementById('modal-title-gab').textContent = 'Novo Gabarito';
    document.getElementById('form-gabarito').reset();
    openModal('modal-gabarito');
  });

  document.getElementById('form-gabarito').addEventListener('submit', handleSaveGabarito);

  // Filtros
  document.getElementById('filter-status').addEventListener('change', filterGabaritos);
  document.getElementById('filter-tipo').addEventListener('change', filterGabaritos);
  document.getElementById('filter-busca').addEventListener('input', debounce(filterGabaritos, 300));
});

async function loadGabaritos() {
  var { data, error } = await sb
    .from('gabaritos')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) { console.error(error); return; }
  _gabaritos = data || [];
  renderGabaritos(_gabaritos);
  updateCounters(_gabaritos);
}

function updateCounters(gabaritos) {
  var total = gabaritos.length;
  var pendentes = gabaritos.filter(function (g) { return g.status === 'pendente'; }).length;
  var prontos = gabaritos.filter(function (g) { return g.status === 'pronto'; }).length;
  var enviados = gabaritos.filter(function (g) { return g.status === 'enviado'; }).length;

  var el;
  el = document.getElementById('counter-total'); if (el) el.textContent = total;
  el = document.getElementById('counter-pendentes'); if (el) el.textContent = pendentes;
  el = document.getElementById('counter-prontos'); if (el) el.textContent = prontos;
  el = document.getElementById('counter-enviados'); if (el) el.textContent = enviados;
}

function renderGabaritos(gabaritos) {
  var tbody = document.getElementById('gabaritos-table');
  if (!gabaritos.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Nenhum gabarito registrado</td></tr>';
    return;
  }

  tbody.innerHTML = gabaritos.map(function (g) {
    var gabPreview = (g.gabarito || '').substring(0, 40);
    if ((g.gabarito || '').length > 40) gabPreview += '...';

    return '<tr>' +
      '<td><span class="aluno-name">' + escapeHtml(g.disciplina || '—') + '</span>' +
        (g.shortname ? '<br><small class="text-muted">' + escapeHtml(g.shortname) + '</small>' : '') +
      '</td>' +
      '<td class="desc-cell">' + escapeHtml(g.atividade || '—') + '</td>' +
      '<td><span class="badge badge-tipo">' + formatTipoGab(g.tipo) + '</span></td>' +
      '<td class="desc-cell"><code>' + escapeHtml(gabPreview || '(vazio)') + '</code></td>' +
      '<td><span class="badge badge-' + g.status + '">' + formatStatusGab(g.status) + '</span></td>' +
      '<td>' + formatDate(g.updated_at) + '</td>' +
      '<td class="actions">' +
        '<button class="btn-icon" onclick="editGabarito(\'' + g.id + '\')" title="Editar">&#9999;&#65039;</button>' +
        '<button class="btn-icon btn-danger" onclick="deleteGabarito(\'' + g.id + '\')" title="Excluir">&#128465;&#65039;</button>' +
      '</td>' +
      '</tr>';
  }).join('');
}

function formatTipoGab(tipo) {
  var map = { questionario: 'Question\u00e1rio', discursiva: 'Discursiva' };
  return map[tipo] || tipo || '—';
}

function formatStatusGab(status) {
  var map = { pendente: 'Pendente', pronto: 'Pronto', enviado: 'Enviado', erro: 'Erro' };
  return map[status] || status || '—';
}

function filterGabaritos() {
  var status = document.getElementById('filter-status').value;
  var tipo = document.getElementById('filter-tipo').value;
  var busca = document.getElementById('filter-busca').value.toLowerCase();

  var filtered = _gabaritos.filter(function (g) {
    var matchStatus = !status || g.status === status;
    var matchTipo = !tipo || g.tipo === tipo;
    var matchBusca = !busca ||
      (g.disciplina || '').toLowerCase().includes(busca) ||
      (g.atividade || '').toLowerCase().includes(busca) ||
      (g.shortname || '').toLowerCase().includes(busca);
    return matchStatus && matchTipo && matchBusca;
  });
  renderGabaritos(filtered);
  updateCounters(filtered);
}

async function handleSaveGabarito(e) {
  e.preventDefault();
  var form = e.target;
  var submitBtn = form.querySelector('button[type="submit"]');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Salvando...'; }

  var data = {
    disciplina: form.disciplina.value.trim(),
    shortname: form.shortname.value.trim(),
    atividade: form.atividade.value.trim(),
    id_questionario: form.id_questionario.value.trim(),
    tipo: form.tipo.value,
    enunciado: form.enunciado.value.trim(),
    gabarito: form.gabarito.value.trim(),
    status: form.status.value
  };

  if (!data.disciplina) { showToast('Informe a disciplina', 'error'); return; }
  if (!data.atividade) { showToast('Informe a atividade', 'error'); return; }

  // Auto-set status to pronto if gabarito was filled
  if (data.gabarito && data.status === 'pendente') {
    data.status = 'pronto';
  }

  try {
    if (currentEditGabId) {
      var { error } = await sb.from('gabaritos').update(data).eq('id', currentEditGabId);
      if (error) throw error;
    } else {
      var { error } = await sb.from('gabaritos').insert(data);
      if (error) throw error;
    }
    logAudit(currentEditGabId ? 'update_gabarito' : 'create_gabarito', 'gabaritos', currentEditGabId || 'new', { disciplina: data.disciplina, atividade: data.atividade });
    showToast(currentEditGabId ? 'Gabarito atualizado!' : 'Gabarito criado!', 'success');
    closeModal('modal-gabarito');
    await loadGabaritos();
  } catch (err) {
    showToast('Erro: ' + err.message, 'error');
  } finally {
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Salvar'; }
  }
}

function editGabarito(id) {
  var gab = _gabaritos.find(function (g) { return g.id === id; });
  if (!gab) return;

  currentEditGabId = id;
  document.getElementById('modal-title-gab').textContent = 'Editar Gabarito';
  var form = document.getElementById('form-gabarito');
  form.disciplina.value = gab.disciplina || '';
  form.shortname.value = gab.shortname || '';
  form.atividade.value = gab.atividade || '';
  form.id_questionario.value = gab.id_questionario || '';
  form.tipo.value = gab.tipo || 'questionario';
  form.enunciado.value = gab.enunciado || '';
  form.gabarito.value = gab.gabarito || '';
  form.status.value = gab.status || 'pendente';
  openModal('modal-gabarito');
}

async function deleteGabarito(id) {
  if (!confirm('Tem certeza que deseja excluir este gabarito?')) return;
  var { error } = await sb.from('gabaritos').delete().eq('id', id);
  if (error) { alert('Erro: ' + error.message); return; }
  logAudit('delete_gabarito', 'gabaritos', id, {});
  showToast('Gabarito exclu\u00eddo!', 'success');
  await loadGabaritos();
}
