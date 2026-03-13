/* ═══════════════════════════════════════════
   Rastreio Studeo — Sincronização
   ═══════════════════════════════════════════ */

var syncInProgress = false;
var currentTab = 'todas';

document.addEventListener('DOMContentLoaded', async function () {
  var user = await requireAuth();
  if (!user) return;

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Carregar mensalistas no select
  await loadMensalistas();

  // Carregar dados sincronizados
  await loadSyncData();

  // Eventos
  document.getElementById('btn-sync').addEventListener('click', handleSync);
  document.getElementById('btn-sync-all').addEventListener('click', handleSyncAll);
  document.getElementById('filter-aluno-rastreio').addEventListener('change', loadSyncData);
  document.getElementById('filter-status-rastreio').addEventListener('change', loadSyncData);

  // Tab listeners
  document.querySelectorAll('.tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.tab-btn').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      currentTab = btn.getAttribute('data-tab');
      renderSyncData(window._syncData || []);
    });
  });
});

async function loadMensalistas() {
  var { data, error } = await sb.from('alunos')
    .select('id, ra, nome, studeo_senha')
    .eq('tipo', 'mensalista')
    .order('nome');

  if (error) { console.error(error); return; }
  window._mensalistas = data || [];

  var select = document.getElementById('filter-aluno-rastreio');
  var syncSelect = document.getElementById('sync-aluno-select');

  // Populate filter select
  select.innerHTML = '<option value="">Todos os mensalistas</option>';
  (data || []).forEach(function (a) {
    select.innerHTML += '<option value="' + a.id + '">' + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')</option>';
  });

  // Populate sync select
  if (syncSelect) {
    syncSelect.innerHTML = '<option value="">Selecione um aluno</option>';
    (data || []).forEach(function (a) {
      var hasSenha = a.studeo_senha ? '' : ' [sem senha]';
      syncSelect.innerHTML += '<option value="' + a.id + '"' + (!a.studeo_senha ? ' disabled' : '') + '>'
        + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')' + hasSenha + '</option>';
    });
  }

  // Update counter
  document.getElementById('count-mensalistas').textContent = (data || []).length;
}

async function loadSyncData() {
  var alunoId = document.getElementById('filter-aluno-rastreio').value;
  var statusFilter = document.getElementById('filter-status-rastreio').value;

  var query = sb.from('studeo_sync')
    .select('*, alunos(nome, ra)')
    .order('synced_at', { ascending: false });

  if (alunoId) query = query.eq('aluno_id', alunoId);
  if (statusFilter === 'pendente') query = query.eq('respondida', false);
  if (statusFilter === 'respondida') query = query.eq('respondida', true);

  var { data, error } = await query;
  if (error) { console.error(error); return; }

  window._syncData = data || [];
  renderSyncData(data || []);
  updateCounters(data || []);
}

function updateCounters(data) {
  var total = data.length;
  var pendentes = data.filter(function (d) { return !d.respondida; }).length;
  var respondidas = data.filter(function (d) { return d.respondida; }).length;

  document.getElementById('count-atividades-sync').textContent = total;
  document.getElementById('count-pendentes-sync').textContent = pendentes;
  document.getElementById('count-respondidas-sync').textContent = respondidas;
}

function renderSyncData(data) {
  var container = document.getElementById('sync-results');
  if (!data.length) {
    container.innerHTML = '<div class="empty-state" style="padding:48px;text-align:center;">Nenhuma atividade sincronizada. Clique em "Sincronizar" para buscar dados do Studeo.</div>';
    return;
  }

  // Agrupar por disciplina
  var grouped = {};
  data.forEach(function (item) {
    var key = item.cd_shortname;
    if (!grouped[key]) {
      grouped[key] = {
        disciplina: item.disciplina,
        cd_shortname: item.cd_shortname,
        ano: item.ano,
        modulo: item.modulo,
        aluno: item.alunos ? item.alunos.nome : 'N/A',
        ra: item.alunos ? item.alunos.ra : '',
        items: []
      };
    }
    grouped[key].items.push(item);
  });

  // Filtrar por aba ativa/passada
  var groups = Object.values(grouped);
  if (currentTab === 'ativas') groups = groups.filter(isActiveDisc);
  if (currentTab === 'passadas') groups = groups.filter(function (g) { return !isActiveDisc(g); });

  if (!groups.length) {
    container.innerHTML = '<div class="empty-state" style="padding:48px;text-align:center;">Nenhuma disciplina ' + (currentTab === 'ativas' ? 'ativa' : currentTab === 'passadas' ? 'passada' : '') + ' encontrada.</div>';
    return;
  }

  var html = '';
  groups.forEach(function (group) {
    var pendentes = group.items.filter(function (i) { return !i.respondida; }).length;
    var total = group.items.length;

    html += '<div class="disc-card">'
      + '<div class="disc-header">'
      + '<div class="disc-info">'
      + '<h3>' + escapeHtml(group.disciplina) + '</h3>'
      + '<span class="disc-meta">' + escapeHtml(group.cd_shortname)
      + (group.ano ? ' | ' + group.ano + '/' + group.modulo : '') + '</span>'
      + '<span class="disc-meta">Aluno: ' + escapeHtml(group.aluno) + ' (' + escapeHtml(group.ra) + ')</span>'
      + '</div>'
      + '<div class="disc-badges">'
      + '<span class="badge badge-pendente">' + pendentes + ' pendente' + (pendentes !== 1 ? 's' : '') + '</span>'
      + '<span class="badge badge-entregue">' + (total - pendentes) + ' respondida' + ((total - pendentes) !== 1 ? 's' : '') + '</span>'
      + '</div>'
      + '</div>'
      + '<div class="disc-activities">';

    group.items.forEach(function (item) {
      var statusClass = item.respondida ? 'respondida' : 'pendente';
      var statusLabel = item.respondida ? 'Respondida' : 'Pendente';
      var tipoClass = item.tipo_atividade === 'MAPA' ? 'badge-mapa' : 'badge-av';
      var dataInfo = '';
      if (item.data_inicial) {
        dataInfo = formatDate(item.data_inicial);
        if (item.data_final) dataInfo += ' ~ ' + formatDate(item.data_final);
      }

      html += '<div class="ativ-row ativ-' + statusClass + '">'
        + '<div class="ativ-info">'
        + '<span class="badge ' + tipoClass + '">' + escapeHtml(item.tipo_atividade || 'AV') + '</span>'
        + '<span class="ativ-nome">' + escapeHtml(item.atividade) + '</span>'
        + '</div>'
        + '<div class="ativ-extra">'
        + (dataInfo ? '<span class="ativ-data">' + dataInfo + '</span>' : '')
        + '<span class="badge badge-' + statusClass + '">' + statusLabel + '</span>'
        + '</div>'
        + '</div>';
    });

    html += '</div></div>';
  });

  container.innerHTML = html;
}

async function handleSync() {
  var selectEl = document.getElementById('sync-aluno-select');
  var alunoId = selectEl.value;
  if (!alunoId) { alert('Selecione um aluno para sincronizar.'); return; }
  if (syncInProgress) { alert('Sincronização em andamento, aguarde...'); return; }

  var aluno = (window._mensalistas || []).find(function (a) { return a.id === alunoId; });
  if (!aluno) { alert('Aluno não encontrado.'); return; }
  if (!aluno.studeo_senha) { alert('Este aluno não tem senha do Studeo cadastrada. Edite o aluno na página de Alunos e adicione a senha.'); return; }

  syncInProgress = true;
  showSyncStatus('Sincronizando ' + aluno.nome + '...', 'loading');

  try {
    var resp = await fetch('/api/sync-studeo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'sync', ra: aluno.ra, senha: aluno.studeo_senha }),
    });

    var result = await resp.json();
    if (!resp.ok || !result.ok) throw new Error(result.error || 'Erro na sincronização');

    // Salvar resultados no Supabase
    var count = await saveResults(alunoId, result.resultado);
    showSyncStatus('Sincronizado! ' + count + ' atividades encontradas para ' + aluno.nome, 'success');
    await loadSyncData();

  } catch (err) {
    showSyncStatus('Erro: ' + err.message, 'error');
  } finally {
    syncInProgress = false;
  }
}

async function handleSyncAll() {
  if (syncInProgress) { alert('Sincronização em andamento, aguarde...'); return; }

  var mensalistas = (window._mensalistas || []).filter(function (a) { return a.studeo_senha; });
  if (!mensalistas.length) {
    alert('Nenhum mensalista com senha do Studeo cadastrada.');
    return;
  }

  syncInProgress = true;
  var total = mensalistas.length;
  var erros = 0;
  var totalAtiv = 0;

  for (var i = 0; i < mensalistas.length; i++) {
    var aluno = mensalistas[i];
    showSyncStatus('Sincronizando ' + (i + 1) + '/' + total + ': ' + aluno.nome + '...', 'loading');

    try {
      var resp = await fetch('/api/sync-studeo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'sync', ra: aluno.ra, senha: aluno.studeo_senha }),
      });

      var result = await resp.json();
      if (!resp.ok || !result.ok) throw new Error(result.error || 'Erro');

      var count = await saveResults(aluno.id, result.resultado);
      totalAtiv += count;
    } catch (err) {
      erros++;
      console.error('Erro sync ' + aluno.nome + ':', err);
    }
  }

  showSyncStatus(
    'Concluído! ' + totalAtiv + ' atividades de ' + (total - erros) + '/' + total + ' alunos.'
    + (erros ? ' (' + erros + ' erro' + (erros > 1 ? 's' : '') + ')' : ''),
    erros ? 'warning' : 'success'
  );

  await loadSyncData();
  syncInProgress = false;
}

async function saveResults(alunoId, resultado) {
  var count = 0;

  for (var i = 0; i < resultado.length; i++) {
    var disc = resultado[i];
    var allActivities = (disc.atividades || []).concat(disc.mapa || []);

    for (var j = 0; j < allActivities.length; j++) {
      var ativ = allActivities[j];
      if (!ativ.descricao) continue;

      var record = {
        aluno_id: alunoId,
        disciplina: disc.disciplina,
        cd_shortname: disc.cd_shortname,
        ano: disc.ano ? String(disc.ano) : null,
        modulo: disc.modulo ? String(disc.modulo) : null,
        atividade: ativ.descricao,
        tipo_atividade: ativ.tipo || 'AV',
        data_inicial: ativ.dataInicial || null,
        data_final: ativ.dataFinal || null,
        respondida: ativ.respondida || false,
        synced_at: new Date().toISOString(),
      };

      // Upsert (insert ou update se já existe)
      var { error } = await sb.from('studeo_sync').upsert(record, {
        onConflict: 'aluno_id,cd_shortname,atividade',
      });

      if (error) console.error('Upsert error:', error);
      else count++;
    }
  }

  return count;
}

function showSyncStatus(msg, type) {
  var el = document.getElementById('sync-status');
  el.textContent = msg;
  el.className = 'sync-status sync-' + type;
  el.style.display = 'block';

  if (type === 'success' || type === 'warning') {
    setTimeout(function () { el.style.display = 'none'; }, 8000);
  }
}

function isActiveDisc(group) {
  var now = new Date();
  return group.items.some(function (item) {
    if (!item.data_final) return true;
    return new Date(item.data_final) >= now;
  });
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    var d = new Date(dateStr);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch (e) {
    return dateStr;
  }
}

// Modal helpers
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
