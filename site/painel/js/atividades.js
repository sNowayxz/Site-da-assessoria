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

  // Realtime: atualiza tabela automaticamente ao inserir/atualizar/deletar
  subscribeAtividadesRealtime();

  // Nova atividade
  document.getElementById('btn-nova-atividade').addEventListener('click', function () {
    currentEditAtivId = null;
    document.getElementById('modal-title-ativ').textContent = 'Nova Atividade';
    document.getElementById('form-atividade').reset();
    resetDescricaoFields();
    clearFileUI();
    openModal('modal-atividade');
  });

  document.getElementById('form-atividade').addEventListener('submit', handleSaveAtividade);

  // Filtros
  document.getElementById('filter-status').addEventListener('change', filterAtividades);
  document.getElementById('filter-tipo').addEventListener('change', filterAtividades);
  document.getElementById('filter-aluno').addEventListener('input', debounce(filterAtividades, 300));
  document.getElementById('filter-descricao').addEventListener('input', debounce(filterAtividades, 300));
  var dtInicio = document.getElementById('filter-data-inicio');
  var dtFim = document.getElementById('filter-data-fim');
  if (dtInicio) dtInicio.addEventListener('change', filterAtividades);
  if (dtFim) dtFim.addEventListener('change', filterAtividades);
});

/* ── Multi-disciplina helpers ───────── */

function buildDiscRow(descVal, valorVal, showRemove) {
  var div = document.createElement('div');
  div.className = 'disc-row';
  var nameInput = document.createElement('input');
  nameInput.type = 'text';
  nameInput.className = 'disc-name descricao-input';
  nameInput.placeholder = 'Ex: MAPA - Gest\u00e3o de Pessoas';
  nameInput.value = descVal || '';

  var valorWrap = document.createElement('div');
  valorWrap.className = 'disc-valor-wrap';
  var btnMinus = document.createElement('button');
  btnMinus.type = 'button';
  btnMinus.textContent = '\u2212';
  btnMinus.onclick = function() { stepValor(valInput, -1); };
  var valInput = document.createElement('input');
  valInput.type = 'number';
  valInput.className = 'disc-valor valor-input';
  valInput.placeholder = 'R$ 0';
  valInput.step = '1';
  valInput.min = '0';
  valInput.value = valorVal || '';
  var btnPlus = document.createElement('button');
  btnPlus.type = 'button';
  btnPlus.textContent = '+';
  btnPlus.onclick = function() { stepValor(valInput, 1); };
  valorWrap.appendChild(btnMinus);
  valorWrap.appendChild(valInput);
  valorWrap.appendChild(btnPlus);

  div.appendChild(nameInput);
  div.appendChild(valorWrap);

  if (showRemove) {
    var removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'disc-remove';
    removeBtn.innerHTML = '&times;';
    removeBtn.onclick = function() { removeDescricaoField(removeBtn); };
    div.appendChild(removeBtn);
  }

  return div;
}

function stepValor(input, delta) {
  var cur = parseFloat(input.value) || 0;
  var next = cur + delta;
  if (next < 0) next = 0;
  input.value = next;
}

function resetDescricaoFields() {
  var container = document.getElementById('descricao-fields');
  container.innerHTML = '';
  container.appendChild(buildDiscRow('', '', false));
  updateDescricaoCounter();
  toggleAddBtn();
}

function addDescricaoField() {
  var container = document.getElementById('descricao-fields');
  var rows = container.querySelectorAll('.disc-row');
  if (rows.length >= 7) {
    showToast('M\u00e1ximo de 7 disciplinas', 'warning');
    return;
  }

  // Ensure first row has remove button when adding second row
  if (rows.length === 1 && !rows[0].querySelector('.disc-remove')) {
    var rb = document.createElement('button');
    rb.type = 'button';
    rb.className = 'disc-remove';
    rb.innerHTML = '&times;';
    rb.onclick = function() { removeDescricaoField(rb); };
    rows[0].appendChild(rb);
  }

  var div = buildDiscRow('', '', true);
  container.appendChild(div);
  updateDescricaoCounter();
  toggleAddBtn();
  div.querySelector('.disc-name').focus();
}

function removeDescricaoField(btn) {
  var container = document.getElementById('descricao-fields');
  var rows = container.querySelectorAll('.disc-row');
  if (rows.length <= 1) return;
  btn.closest('.disc-row').remove();
  // If only 1 row left, remove its remove button
  var remaining = container.querySelectorAll('.disc-row');
  if (remaining.length === 1) {
    var rb = remaining[0].querySelector('.disc-remove');
    if (rb) rb.remove();
  }
  updateDescricaoCounter();
  toggleAddBtn();
}

function updateDescricaoCounter() {
  var count = document.querySelectorAll('#descricao-fields .disc-row').length;
  var el = document.getElementById('descricao-counter');
  if (el) el.textContent = count + '/7';
}

function toggleAddBtn() {
  var count = document.querySelectorAll('#descricao-fields .disc-row').length;
  var btn = document.getElementById('btn-add-disciplina');
  if (btn) {
    btn.style.display = count >= 7 ? 'none' : 'flex';
  }
}

function getDisciplinaValues() {
  var rows = document.querySelectorAll('#descricao-fields .disc-row');
  var values = [];
  for (var i = 0; i < rows.length; i++) {
    var descInput = rows[i].querySelector('.descricao-input');
    var valorInput = rows[i].querySelector('.valor-input');
    var desc = descInput ? descInput.value.trim() : '';
    var valor = valorInput ? (parseFloat(valorInput.value) || 0) : 0;
    if (desc) values.push({ descricao: desc, valor: valor });
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
  var descricao = document.getElementById('filter-descricao').value.toLowerCase();
  var dtInicio = document.getElementById('filter-data-inicio') ? document.getElementById('filter-data-inicio').value : '';
  var dtFim = document.getElementById('filter-data-fim') ? document.getElementById('filter-data-fim').value : '';

  var filtered = _atividades.filter(function (a) {
    var alunoData = a.alunos || {};
    var matchStatus = !status || a.status === status;
    var matchTipo = !tipo || a.tipo === tipo;
    var matchAluno = !aluno || (alunoData.nome || '').toLowerCase().includes(aluno) || (alunoData.ra || '').toLowerCase().includes(aluno);
    var matchDescricao = !descricao || (a.descricao || '').toLowerCase().includes(descricao);
    var matchDate = true;
    if (dtInicio) {
      var created = (a.created_at || '').slice(0, 10);
      matchDate = matchDate && created >= dtInicio;
    }
    if (dtFim) {
      var created = (a.created_at || '').slice(0, 10);
      matchDate = matchDate && created <= dtFim;
    }
    return matchStatus && matchTipo && matchAluno && matchDescricao && matchDate;
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
    observacoes: form.observacoes.value.trim()
  };

  if (!baseData.aluno_id) {
    showToast('Selecione um aluno', 'warning');
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Salvar'; }
    return;
  }

  try {
    if (currentEditAtivId) {
      // Edição: campo único de descrição + valor
      var rows = document.querySelectorAll('#descricao-fields .disc-row');
      var descInput = rows.length > 0 ? rows[0].querySelector('.descricao-input') : null;
      var valorInput = rows.length > 0 ? rows[0].querySelector('.valor-input') : null;
      baseData.descricao = descInput ? descInput.value.trim() : '';
      baseData.valor = valorInput ? (parseFloat(valorInput.value) || 0) : 0;
      var { error } = await sb.from('atividades').update(baseData).eq('id', currentEditAtivId);
      if (error) throw error;
      if (_pendingFiles.length > 0) await uploadFiles(currentEditAtivId);
      logAudit('update_atividade', 'atividades', currentEditAtivId, { tipo: baseData.tipo, descricao: baseData.descricao });
      showToast('Atividade atualizada!', 'success');
    } else {
      // Criação: múltiplas disciplinas com valores individuais
      var disciplinas = getDisciplinaValues();
      if (disciplinas.length === 0) disciplinas = [{ descricao: '', valor: 0 }];

      var records = [];
      for (var i = 0; i < disciplinas.length; i++) {
        records.push({
          aluno_id: baseData.aluno_id,
          tipo: baseData.tipo,
          status: baseData.status,
          valor: disciplinas[i].valor,
          descricao: disciplinas[i].descricao,
          observacoes: baseData.observacoes
        });
      }

      var { data: inserted, error } = await sb.from('atividades').insert(records).select();
      if (error) throw error;

      // Upload arquivos para a primeira atividade criada
      if (_pendingFiles.length > 0 && inserted && inserted.length > 0) {
        await uploadFiles(inserted[0].id);
      }

      logAudit('create_atividade', 'atividades', 'batch_' + records.length, {
        tipo: baseData.tipo,
        disciplinas: disciplinas.map(function(d) { return d.descricao + ' (R$' + d.valor + ')'; }).join(', '),
        count: records.length
      });

      // Auto-criar pagamentos para atividades com valor > 0
      var pagamentos = [];
      for (var j = 0; j < records.length; j++) {
        if (records[j].valor > 0) {
          pagamentos.push({
            aluno_id: baseData.aluno_id,
            valor: records[j].valor,
            tipo: (baseData.tipo === 'pacote') ? 'pacote' : 'avulso',
            status: 'pendente',
            referencia: records[j].descricao || formatTipo(baseData.tipo),
            observacoes: 'Gerado automaticamente via atividade'
          });
        }
      }
      if (pagamentos.length > 0) {
        var pagResult = await sb.from('pagamentos').insert(pagamentos);
        if (pagResult.error) {
          console.error('Erro ao criar pagamentos:', pagResult.error);
          showToast('Atividade(s) criada(s), mas erro ao gerar pagamento(s)', 'warning');
        } else {
          showToast(records.length + ' atividade(s) criada(s) + ' + pagamentos.length + ' pagamento(s) pendente(s) no Financeiro!', 'success');
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
  form.observacoes.value = ativ.observacoes || '';

  // Reset to single description + valor field for edit
  var container = document.getElementById('descricao-fields');
  container.innerHTML = '';
  container.appendChild(buildDiscRow(ativ.descricao || '', ativ.valor || 0, false));

  // Hide add button and counter in edit mode
  var addBtn = document.getElementById('btn-add-disciplina');
  var counter = document.getElementById('descricao-counter');
  if (addBtn) addBtn.style.display = 'none';
  if (counter) counter.textContent = '';

  // Load existing files and clear pending
  clearFileUI();
  loadExistingFiles(id);

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

/* ── File Upload ────────────────────── */

var _pendingFiles = [];

function handleFileSelect(input) {
  var files = Array.prototype.slice.call(input.files);
  for (var i = 0; i < files.length; i++) {
    if (files[i].size > 10 * 1024 * 1024) {
      showToast('Arquivo "' + files[i].name + '" excede 10MB', 'warning');
      continue;
    }
    _pendingFiles.push(files[i]);
  }
  input.value = '';
  renderPendingFiles();
}

function renderPendingFiles() {
  var container = document.getElementById('file-list');
  if (!container) return;
  container.innerHTML = '';
  for (var i = 0; i < _pendingFiles.length; i++) {
    var f = _pendingFiles[i];
    var div = document.createElement('div');
    div.className = 'file-item';
    var sizeKB = (f.size / 1024).toFixed(0);
    var sizeLabel = sizeKB > 1024 ? (f.size / 1024 / 1024).toFixed(1) + ' MB' : sizeKB + ' KB';
    div.innerHTML = '<span class="file-name">' + escapeHtml(f.name) + '</span>' +
      '<span class="file-size">' + sizeLabel + '</span>' +
      '<button type="button" class="file-remove" data-idx="' + i + '" title="Remover">&times;</button>';
    container.appendChild(div);
  }
  container.querySelectorAll('.file-remove').forEach(function(btn) {
    btn.addEventListener('click', function() {
      _pendingFiles.splice(parseInt(this.getAttribute('data-idx')), 1);
      renderPendingFiles();
    });
  });
}

async function uploadFiles(atividadeId) {
  var uploaded = [];
  for (var i = 0; i < _pendingFiles.length; i++) {
    var file = _pendingFiles[i];
    var ext = file.name.split('.').pop();
    var path = 'atividades/' + atividadeId + '/' + Date.now() + '_' + i + '.' + ext;
    var { data, error } = await sb.storage.from('arquivos').upload(path, file, { upsert: true });
    if (error) {
      console.error('Upload error:', error);
      showToast('Erro ao enviar "' + file.name + '"', 'error');
      continue;
    }
    var { data: urlData } = sb.storage.from('arquivos').getPublicUrl(path);
    uploaded.push({
      atividade_id: atividadeId,
      nome: file.name,
      tamanho: file.size,
      tipo: file.type || 'application/octet-stream',
      url: urlData.publicUrl,
      path: path
    });
  }
  if (uploaded.length > 0) {
    var { error } = await sb.from('atividade_arquivos').insert(uploaded);
    if (error) console.error('Erro ao salvar metadados:', error);
  }
  _pendingFiles = [];
  return uploaded;
}

async function loadExistingFiles(atividadeId) {
  var container = document.getElementById('existing-files');
  if (!container) return;
  container.innerHTML = '';
  var { data, error } = await sb.from('atividade_arquivos').select('*').eq('atividade_id', atividadeId);
  if (error || !data || data.length === 0) return;
  for (var i = 0; i < data.length; i++) {
    var f = data[i];
    var div = document.createElement('div');
    div.className = 'file-item';
    var sizeKB = (f.tamanho / 1024).toFixed(0);
    var sizeLabel = sizeKB > 1024 ? (f.tamanho / 1024 / 1024).toFixed(1) + ' MB' : sizeKB + ' KB';
    div.innerHTML = '<span class="file-name">' + escapeHtml(f.nome) + '</span>' +
      '<span class="file-size">' + sizeLabel + '</span>' +
      '<a href="' + escapeHtml(f.url) + '" target="_blank" rel="noopener">Abrir</a>' +
      '<button type="button" class="file-remove" data-file-id="' + f.id + '" data-path="' + escapeHtml(f.path) + '" title="Remover">&times;</button>';
    container.appendChild(div);
  }
  container.querySelectorAll('.file-remove').forEach(function(btn) {
    btn.addEventListener('click', async function() {
      var fileId = this.getAttribute('data-file-id');
      var filePath = this.getAttribute('data-path');
      await sb.storage.from('arquivos').remove([filePath]);
      await sb.from('atividade_arquivos').delete().eq('id', fileId);
      this.closest('.file-item').remove();
      showToast('Arquivo removido', 'success');
    });
  });
}

function clearFileUI() {
  _pendingFiles = [];
  var fl = document.getElementById('file-list');
  var ef = document.getElementById('existing-files');
  if (fl) fl.innerHTML = '';
  if (ef) ef.innerHTML = '';
}

/* ── Realtime ──────────────────────────── */

var _atividadesRealtimeSub = null;

function subscribeAtividadesRealtime() {
  if (_atividadesRealtimeSub) sb.removeChannel(_atividadesRealtimeSub);
  _atividadesRealtimeSub = sb.channel('atividades-realtime')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'atividades' }, function () {
      loadAtividades();
    })
    .subscribe();
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
