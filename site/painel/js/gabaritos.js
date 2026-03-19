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

  // Responder Atividades
  await loadAlunosResp();
  document.getElementById('btn-buscar-pendentes').addEventListener('click', buscarPendentes);
  document.getElementById('btn-preencher-selecionadas').addEventListener('click', preencherSelecionadas);
  document.getElementById('check-all-pendentes').addEventListener('change', function () {
    var checks = document.querySelectorAll('.check-pendente');
    for (var i = 0; i < checks.length; i++) checks[i].checked = this.checked;
    toggleBtnPreencher();
  });
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
  showConfirm('Tem certeza que deseja excluir este gabarito?', async function() {
    var gab = _gabaritos.find(function(g) { return g.id === id; });
    var { error } = await sb.from('gabaritos').delete().eq('id', id);
    if (error) { showToast('Erro: ' + error.message, 'error'); return; }
    logAudit('delete_gabarito', 'gabaritos', id, {});
    await loadGabaritos();
    if (gab) {
      showUndoToast('Gabarito excluído', async function() {
        await sb.from('gabaritos').insert(gab);
        showToast('Gabarito restaurado!', 'success');
        await loadGabaritos();
      });
    }
  }, { title: 'Excluir Gabarito', confirmText: 'Excluir', type: 'danger' });
}


/* ═══════════════════════════════════════════
   Responder Atividades — Modelitos
   ═══════════════════════════════════════════ */

var PROXY_URL = 'https://site-da-assessoria.vercel.app/api/preencher-atividade';
var _pendentes = [];

async function loadAlunosResp() {
  var { data } = await sb.from('alunos').select('id, nome, ra').order('nome');
  var select = document.getElementById('resp-aluno');
  select.innerHTML = '<option value="">Selecione o aluno</option>';
  (data || []).forEach(function (a) {
    select.innerHTML += '<option value="' + escapeHtml(a.ra) + '">' + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')</option>';
  });
}

async function buscarPendentes() {
  var ra = document.getElementById('resp-aluno').value;
  if (!ra) { showToast('Selecione um aluno', 'error'); return; }

  var btn = document.getElementById('btn-buscar-pendentes');
  var info = document.getElementById('pendentes-info');
  btn.disabled = true; btn.textContent = 'Buscando...';
  info.textContent = 'Consultando Modelitos...';

  try {
    var resp = await fetch(PROXY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'verificar', ra: ra }),
    });
    var data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Erro desconhecido');

    _pendentes = data.pendentes || [];
    info.textContent = _pendentes.length + ' atividade(s) pendente(s) encontrada(s)';
    renderPendentes(_pendentes);
  } catch (err) {
    info.textContent = 'Erro: ' + err.message;
    showToast('Erro ao buscar pendentes: ' + err.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Buscar Pendentes';
  }
}

function renderPendentes(pendentes) {
  var container = document.getElementById('pendentes-table');
  if (!pendentes.length) {
    container.innerHTML = '<div class="resp-empty-state">' +
      '<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.4"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>' +
      '<p>Nenhuma atividade pendente</p></div>';
    return;
  }

  container.innerHTML = pendentes.map(function (p, i) {
    return '<div class="resp-pendente-item">' +
      '<input type="checkbox" class="check-pendente" data-idx="' + i + '" onchange="toggleBtnPreencher()">' +
      '<div class="resp-pendente-info">' +
        '<span class="resp-pendente-id">#' + escapeHtml(p.idQuestionario || '') + '</span>' +
        '<div class="resp-pendente-desc">' + escapeHtml(p.descricao || '—') + '</div>' +
        '<div class="resp-pendente-short">' + escapeHtml(p.shortname || '') + '</div>' +
      '</div>' +
      '<button class="resp-pendente-play" onclick="preencherUma(' + i + ')" title="Preencher">' +
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>' +
      '</button>' +
    '</div>';
  }).join('');
}

function toggleBtnPreencher() {
  var checked = document.querySelectorAll('.check-pendente:checked');
  document.getElementById('btn-preencher-selecionadas').disabled = checked.length === 0;
}

async function preencherUma(idx) {
  var p = _pendentes[idx];
  if (!p) return;
  showConfirm('Preencher atividade ' + p.idQuestionario + '?', async function() { await _doPreencherUma(p); }, { title: 'Preencher Atividade', confirmText: 'Preencher', type: 'info' });
  return;
}
async function _doPreencherUma(p) {

  var status = document.getElementById('preencher-status');
  status.textContent = 'Preenchendo ' + p.idQuestionario + '...';

  try {
    var resp = await fetch(PROXY_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'preencher', idQuestionario: p.idQuestionario, finalizar: true }),
    });
    var data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Erro');

    showToast('Atividade ' + p.idQuestionario + ' preenchida!', 'success');
    status.textContent = 'Concluído: ' + p.idQuestionario;
    logAudit('preencher_atividade', 'gabaritos', p.idQuestionario, { shortname: p.shortname });
  } catch (err) {
    showToast('Erro: ' + err.message, 'error');
    status.textContent = 'Erro: ' + err.message;
  }
}

async function preencherSelecionadas() {
  var checks = document.querySelectorAll('.check-pendente:checked');
  if (!checks.length) return;
  var _checks = checks;
  showConfirm('Preencher ' + checks.length + ' atividade(s) selecionada(s)?', async function() { await _doPreencherSelecionadas(_checks); }, { title: 'Preencher em Lote', confirmText: 'Preencher', type: 'info' });
}
async function _doPreencherSelecionadas(checks) {
  var btn = document.getElementById('btn-preencher-selecionadas');
  var status = document.getElementById('preencher-status');
  btn.disabled = true;

  var total = checks.length;
  var ok = 0;
  var erros = 0;

  for (var i = 0; i < checks.length; i++) {
    var idx = parseInt(checks[i].getAttribute('data-idx'));
    var p = _pendentes[idx];
    if (!p) continue;

    status.textContent = 'Preenchendo ' + (i + 1) + '/' + total + ': ' + p.idQuestionario + '...';

    try {
      var resp = await fetch(PROXY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'preencher', idQuestionario: p.idQuestionario, finalizar: true }),
      });
      var data = await resp.json();
      if (!data.ok) throw new Error(data.error);
      ok++;
      logAudit('preencher_atividade', 'gabaritos', p.idQuestionario, { shortname: p.shortname });
    } catch (err) {
      erros++;
      console.error('Erro em ' + p.idQuestionario + ':', err.message);
    }
  }

  status.textContent = 'Resultado: ' + ok + ' preenchida(s), ' + erros + ' erro(s)';
  showToast(ok + ' atividade(s) preenchida(s)' + (erros ? ', ' + erros + ' erro(s)' : ''), ok ? 'success' : 'error');
  btn.disabled = false;
}
