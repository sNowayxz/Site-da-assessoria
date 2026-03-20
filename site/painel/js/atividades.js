/* ═══════════════════════════════════════════
   Atividades — CRUD + Rastreio
   ═══════════════════════════════════════════ */

var currentEditAtivId = null;
var _atividades = [];
var _alunosList = [];

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'dono', 'assessor']);
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
    resetDescricaoFields();
    openModal('modal-atividade');
  });

  document.getElementById('form-atividade').addEventListener('submit', handleSaveAtividade);

  // Filtros
  document.getElementById('filter-status').addEventListener('change', filterAtividades);
  document.getElementById('filter-tipo').addEventListener('change', filterAtividades);
  document.getElementById('filter-aluno').addEventListener('input', debounce(filterAtividades, 300));
  var dtInicio = document.getElementById('filter-data-inicio');
  var dtFim = document.getElementById('filter-data-fim');
  if (dtInicio) dtInicio.addEventListener('change', filterAtividades);
  if (dtFim) dtFim.addEventListener('change', filterAtividades);
});

/* ── Multi-disciplina helpers ───────── */

function resetDescricaoFields() {
  var container = document.getElementById('descricao-fields');
  container.innerHTML =
    '<div class="descricao-row" style="display:flex;gap:6px;margin-bottom:6px;">' +
      '<input type="text" class="descricao-input" placeholder="Ex: MAPA - Gestão de Pessoas" style="flex:1">' +
    '</div>';
  updateDescricaoCounter();
  toggleAddBtn();
  toggleRemoveBtns();
}

function addDescricaoField() {
  var container = document.getElementById('descricao-fields');
  var rows = container.querySelectorAll('.descricao-row');
  if (rows.length >= 7) {
    showToast('Máximo de 7 disciplinas', 'warning');
    return;
  }

  var div = document.createElement('div');
  div.className = 'descricao-row';
  div.style.cssText = 'display:flex;gap:6px;margin-bottom:6px;';
  div.innerHTML =
    '<input type="text" class="descricao-input" placeholder="Ex: MAPA - Gestão de Pessoas" style="flex:1">' +
    '<button type="button" class="btn-remove-desc" onclick="removeDescricaoField(this)" style="background:none;border:1px solid rgba(239,68,68,.2);color:#ef4444;width:32px;height:38px;border-radius:6px;cursor:pointer;font-size:1.1rem;flex-shrink:0;display:flex;align-items:center;justify-content:center;">&times;</button>';
  container.appendChild(div);

  updateDescricaoCounter();
  toggleAddBtn();
  toggleRemoveBtns();
  div.querySelector('input').focus();
}

function removeDescricaoField(btn) {
  var container = document.getElementById('descricao-fields');
  var rows = container.querySelectorAll('.descricao-row');
  if (rows.length <= 1) return;
  btn.closest('.descricao-row').remove();
  updateDescricaoCounter();
  toggleAddBtn();
  toggleRemoveBtns();
}

function updateDescricaoCounter() {
  var count = document.querySelectorAll('#descricao-fields .descricao-row').length;
  var el = document.getElementById('descricao-counter');
  if (el) el.textContent = count + '/7';
}

function toggleAddBtn() {
  var count = document.querySelectorAll('#descricao-fields .descricao-row').length;
  var btn = document.getElementById('btn-add-disciplina');
  if (btn) {
    btn.style.display = count >= 7 ? 'none' : 'block';
  }
}

function toggleRemoveBtns() {
  var rows = document.querySelectorAll('#descricao-fields .descricao-row');
  // Show remove buttons only when there's more than 1 row
  for (var i = 0; i < rows.length; i++) {
    var removeBtn = rows[i].querySelector('.btn-remove-desc');
    if (rows.length === 1) {
      // First row never has remove button when it's the only one
      if (removeBtn) removeBtn.style.display = 'none';
    } else {
      // Add remove button to first row if it doesn't have one
      if (i === 0 && !removeBtn) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-remove-desc';
        btn.onclick = function() { removeDescricaoField(this); };
        btn.style.cssText = 'background:none;border:1px solid rgba(239,68,68,.2);color:#ef4444;width:32px;height:38px;border-radius:6px;cursor:pointer;font-size:1.1rem;flex-shrink:0;display:flex;align-items:center;justify-content:center;';
        btn.innerHTML = '&times;';
        rows[i].appendChild(btn);
      }
      if (removeBtn) removeBtn.style.display = 'flex';
    }
  }
}

function getDescricaoValues() {
  var inputs = document.querySelectorAll('#descricao-fields .descricao-input');
  var values = [];
  for (var i = 0; i < inputs.length; i++) {
    var v = inputs[i].value.trim();
    if (v) values.push(v);
  }
  return values;
}

/* ── Data ───────────────────────────── */

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

var _ativCurrentPage = 1;
function goToPageAtiv(p) { _ativCurrentPage = p; filterAtividades(); }

function renderAtividades(atividades) {
  var tbody = document.getElementById('atividades-table');
  if (!atividades.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhuma atividade registrada</td></tr>';
    renderPagination('pagination-container', 0, 1, 'goToPageAtiv');
    return;
  }

  var paginated = paginateArray(atividades, _ativCurrentPage);
  renderPagination('pagination-container', atividades.length, _ativCurrentPage, 'goToPageAtiv');

  tbody.innerHTML = paginated.map(function (a) {
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

/* ── Save (batch + auto-pagamento) ──── */

async function handleSaveAtividade(e) {
  e.preventDefault();
  var form = e.target;
  var submitBtn = form.querySelector('button[type="submit"]');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Salvando...'; }

  var baseData = {
    aluno_id: form.aluno_id.value,
    tipo: form.tipo.value,
    status: form.status.value,
    valor: parseFloat(form.valor.value) || 0,
    observacoes: form.observacoes.value.trim()
  };

  if (!baseData.aluno_id) {
    showToast('Selecione um aluno', 'warning');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Salvar'; }
    return;
  }

  try {
    if (currentEditAtivId) {
      // Edição: campo único de descrição (primeiro input)
      var descInputs = document.querySelectorAll('#descricao-fields .descricao-input');
      baseData.descricao = descInputs.length > 0 ? descInputs[0].value.trim() : '';
      var { error } = await sb.from('atividades').update(baseData).eq('id', currentEditAtivId);
      if (error) throw error;
      logAudit('update_atividade', 'atividades', currentEditAtivId, { tipo: baseData.tipo, descricao: baseData.descricao });
      showToast('Atividade atualizada!', 'success');
    } else {
      // Criação: múltiplas disciplinas
      var descricoes = getDescricaoValues();
      if (descricoes.length === 0) descricoes = [''];

      var records = [];
      for (var i = 0; i < descricoes.length; i++) {
        records.push({
          aluno_id: baseData.aluno_id,
          tipo: baseData.tipo,
          status: baseData.status,
          valor: baseData.valor,
          descricao: descricoes[i],
          observacoes: baseData.observacoes
        });
      }

      var { data: inserted, error } = await sb.from('atividades').insert(records).select();
      if (error) throw error;

      logAudit('create_atividade', 'atividades', 'batch_' + records.length, {
        tipo: baseData.tipo,
        descricoes: descricoes.join(', '),
        count: records.length
      });

      // Auto-criar pagamentos para atividades com valor > 0
      if (baseData.valor > 0) {
        var pagamentos = [];
        for (var j = 0; j < records.length; j++) {
          pagamentos.push({
            aluno_id: baseData.aluno_id,
            valor: baseData.valor,
            tipo: (baseData.tipo === 'pacote') ? 'pacote' : 'avulso',
            status: 'pendente',
            referencia: records[j].descricao || formatTipo(baseData.tipo),
            observacoes: 'Gerado automaticamente via atividade'
          });
        }
        var pagResult = await sb.from('pagamentos').insert(pagamentos);
        if (pagResult.error) {
          console.error('Erro ao criar pagamentos:', pagResult.error);
          showToast('Atividade(s) criada(s), mas erro ao gerar pagamento(s)', 'warning');
        } else {
          showToast(records.length + ' atividade(s) criada(s) + pagamento(s) pendente(s) no Financeiro!', 'success');
        }
      } else {
        showToast(records.length + ' atividade(s) criada(s)!', 'success');
      }
    }

    closeModal('modal-atividade');
    await loadAtividades();
  } catch (err) {
    showToast('Erro: ' + err.message, 'error');
  } finally {
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Salvar'; }
  }
}

/* ── Edit ───────────────────────────── */

async function editAtividade(id) {
  var ativ = _atividades.find(function (a) { return a.id === id; });
  if (!ativ) return;

  currentEditAtivId = id;
  document.getElementById('modal-title-ativ').textContent = 'Editar Atividade';
  var form = document.getElementById('form-atividade');
  form.aluno_id.value = ativ.aluno_id;
  form.tipo.value = ativ.tipo;
  form.status.value = ativ.status;
  form.valor.value = ativ.valor || 0;
  form.observacoes.value = ativ.observacoes || '';

  // Reset to single description field for edit
  var container = document.getElementById('descricao-fields');
  container.innerHTML =
    '<div class="descricao-row" style="display:flex;gap:6px;margin-bottom:6px;">' +
      '<input type="text" class="descricao-input" placeholder="Ex: MAPA - Gestão de Pessoas" style="flex:1" value="' + escapeHtml(ativ.descricao || '') + '">' +
    '</div>';

  // Hide add button and counter in edit mode
  var addBtn = document.getElementById('btn-add-disciplina');
  var counter = document.getElementById('descricao-counter');
  if (addBtn) addBtn.style.display = 'none';
  if (counter) counter.textContent = '';

  openModal('modal-atividade');
}

/* ── Delete ─────────────────────────── */

async function deleteAtividade(id) {
  showConfirm('Tem certeza que deseja excluir esta atividade?', async function() {
    var ativ = _atividades.find(function(a) { return a.id === id; });
    var { error } = await sb.from('atividades').delete().eq('id', id);
    if (error) { showToast('Erro: ' + error.message, 'error'); return; }
    logAudit('delete_atividade', 'atividades', id, {});
    await loadAtividades();
    if (ativ) {
      showUndoToast('Atividade excluída', async function() {
        await sb.from('atividades').insert(ativ);
        showToast('Atividade restaurada!', 'success');
        await loadAtividades();
      });
    }
  }, { title: 'Excluir Atividade', confirmText: 'Excluir', type: 'danger' });
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
  if (error) { showToast('Erro: ' + error.message, 'error'); return; }
  logAudit('status_change', 'atividades', id, { from: currentStatus, to: next });
  await loadAtividades();
}
