/* ═══════════════════════════════════════════
   Rastreio Studeo — Sincronização
   ═══════════════════════════════════════════ */

var SYNC_API_URL = 'https://site-da-assessoria.vercel.app/api/sync-studeo';
var syncInProgress = false;
var currentTab = 'todas';

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Carregar mensalistas no select
  await loadMensalistas();

  // Carregar dados sincronizados
  await loadSyncData();

  // Eventos
  document.getElementById('btn-sync').addEventListener('click', handleSync);
  document.getElementById('btn-sync-all').addEventListener('click', handleSyncAll);
  document.getElementById('btn-sync-new').addEventListener('click', handleSyncNew);
  document.getElementById('filter-aluno-rastreio').addEventListener('change', loadSyncData);
  document.getElementById('filter-dias').addEventListener('change', loadSyncData);
  document.getElementById('filter-grupo-rastreio').addEventListener('change', function () { loadAlunos(); loadSyncData(); });
  document.getElementById('sync-grupo-select').addEventListener('change', loadAlunos);

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
    .select('id, ra, nome, studeo_senha, tipo')
    .order('nome');

  if (error) { console.error(error); return; }
  window._todosAlunos = data || [];

  // Contadores por grupo
  var counts = { mensalista: 0, recorrente: 0, extensao: 0 };
  (data || []).forEach(function (a) { counts[a.tipo] = (counts[a.tipo] || 0) + 1; });
  document.getElementById('count-mensalistas').textContent = (data || []).length;

  loadAlunos();
}

function loadAlunos() {
  var grupoSync = (document.getElementById('sync-grupo-select') || {}).value || '';
  var grupoFilter = (document.getElementById('filter-grupo-rastreio') || {}).value || '';
  var all = window._todosAlunos || [];

  // Filtrar por grupo para o sync select
  var syncFiltered = grupoSync ? all.filter(function (a) { return a.tipo === grupoSync; }) : all;
  var syncSelect = document.getElementById('sync-aluno-select');
  if (syncSelect) {
    syncSelect.innerHTML = '<option value="">Selecione um aluno</option>';
    syncFiltered.forEach(function (a) {
      var hasSenha = a.studeo_senha ? '' : ' [sem senha]';
      var grupoTag = ' [' + (a.tipo === 'extensao' ? 'EXT' : a.tipo === 'recorrente' ? 'REC' : 'MEN') + ']';
      syncSelect.innerHTML += '<option value="' + a.id + '"' + (!a.studeo_senha ? ' disabled' : '') + '>'
        + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')' + grupoTag + hasSenha + '</option>';
    });
  }

  // Filtrar por grupo para o filtro de visualização
  var filterFiltered = grupoFilter ? all.filter(function (a) { return a.tipo === grupoFilter; }) : all;
  var select = document.getElementById('filter-aluno-rastreio');
  if (select) {
    select.innerHTML = '<option value="">Todos os alunos</option>';
    filterFiltered.forEach(function (a) {
      select.innerHTML += '<option value="' + a.id + '">' + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')</option>';
    });
  }
}

async function loadSyncData() {
  // Skeleton loading
  var container = document.getElementById('sync-results');
  if (container && !container.querySelector('.aluno-card')) {
    container.innerHTML = '<div style="padding:20px;display:flex;flex-direction:column;gap:16px;">'
      + '<div class="skeleton" style="height:60px;width:100%;"></div>'
      + '<div class="skeleton" style="height:44px;width:90%;"></div>'
      + '<div class="skeleton" style="height:44px;width:85%;"></div>'
      + '</div>';
  }

  var filterAluno = document.getElementById('filter-aluno-rastreio');
  var alunoId = filterAluno ? filterAluno.value : '';
  var grupoFilter = (document.getElementById('filter-grupo-rastreio') || {}).value || '';
  var diasInput = document.getElementById('filter-dias');
  var dias = diasInput ? parseInt(diasInput.value) || 10 : 10;

  // Build alunos cache with tipo
  if (!window._alunosCache) {
    var { data: alunos } = await sb.from('alunos').select('id, nome, ra, tipo, studeo_senha');
    window._alunosCache = {};
    (alunos || []).forEach(function (a) { window._alunosCache[a.id] = a; });
  }

  // Só pendentes, ordenadas por data_final
  var query = sb.from('studeo_sync')
    .select('*')
    .eq('respondida', false)
    .order('data_final', { ascending: true });

  if (alunoId) query = query.eq('aluno_id', alunoId);

  // Filtrar por grupo: pegar IDs dos alunos do grupo selecionado
  if (grupoFilter && !alunoId) {
    var grupoIds = Object.keys(window._alunosCache).filter(function (id) {
      return window._alunosCache[id].tipo === grupoFilter;
    });
    if (grupoIds.length > 0) query = query.in('aluno_id', grupoIds);
  }

  var { data, error } = await query;
  if (error) { console.error(error); return; }

  // Filtrar: só atividades com prazo dentro dos próximos X dias
  var now = new Date();
  now.setHours(0, 0, 0, 0);
  var limite = new Date(now);
  limite.setDate(limite.getDate() + dias);

  data = (data || []).filter(function (item) {
    if (!item.data_final) return false; // sem prazo = não mostrar
    var df = new Date(item.data_final);
    return df >= now && df <= limite;
  });

  // Attach aluno info from cache
  (data || []).forEach(function (item) {
    var aluno = window._alunosCache[item.aluno_id];
    item.alunos = aluno ? { nome: aluno.nome, ra: aluno.ra, studeo_senha: aluno.studeo_senha } : null;
  });

  window._syncData = data || [];
  renderSyncData(data || []);
  updateCounters(data || []);
}

function updateCounters(data) {
  // Atividades no prazo
  var totalAtiv = data.length;

  // Alunos únicos com pendências no prazo
  var alunosUnicos = {};
  data.forEach(function (d) {
    if (d.aluno_id) alunosUnicos[d.aluno_id] = true;
  });
  var alunosComPendencias = Object.keys(alunosUnicos).length;

  // Alunos já sincronizados (que têm pelo menos 1 registro no studeo_sync)
  var totalAlunos = (window._todosAlunos || []).length;

  document.getElementById('count-atividades-sync').textContent = totalAtiv;
  document.getElementById('count-alunos-prazo').textContent = alunosComPendencias;

  // Contar sincronizados em background
  sb.from('studeo_sync').select('aluno_id').then(function (r) {
    var syncedIds = {};
    (r.data || []).forEach(function (s) { syncedIds[s.aluno_id] = true; });
    var el = document.getElementById('count-respondidas-sync');
    if (el) el.textContent = Object.keys(syncedIds).length + '/' + totalAlunos;
  });
}

function renderSyncData(data) {
  var container = document.getElementById('sync-results');
  if (!data.length) {
    container.innerHTML = '<div class="empty-state" style="padding:48px;text-align:center;">Nenhuma atividade pendente encontrada. Clique em "Sincronizar" para buscar dados do Studeo.</div>';
    return;
  }

  // Agrupar por aluno → disciplina (estilo Modelitos)
  var byAluno = {};
  data.forEach(function (item) {
    var alunoKey = item.aluno_id || 'unknown';
    if (!byAluno[alunoKey]) {
      byAluno[alunoKey] = {
        nome: item.alunos ? item.alunos.nome : 'N/A',
        ra: item.alunos ? item.alunos.ra : '',
        senha: item.alunos ? item.alunos.studeo_senha : '',
        disciplinas: {}
      };
    }
    var discKey = item.cd_shortname;
    if (!byAluno[alunoKey].disciplinas[discKey]) {
      byAluno[alunoKey].disciplinas[discKey] = {
        disciplina: item.disciplina,
        cd_shortname: item.cd_shortname,
        items: []
      };
    }
    byAluno[alunoKey].disciplinas[discKey].items.push(item);
  });

  var html = '';
  var alunos = Object.values(byAluno);

  // Ordenar alunos por nome
  alunos.sort(function (a, b) { return (a.nome || '').localeCompare(b.nome || ''); });

  alunos.forEach(function (aluno) {
    var discs = Object.values(aluno.disciplinas);
    var totalPendentes = 0;
    discs.forEach(function (d) {
      totalPendentes += d.items.filter(function (i) { return !i.respondida; }).length;
    });

    // Ordenar disciplinas pelo prazo mais próximo
    discs.sort(function (a, b) {
      var aMin = getEarliestDeadline(a.items);
      var bMin = getEarliestDeadline(b.items);
      if (!aMin) return 1;
      if (!bMin) return -1;
      return aMin - bMin;
    });

    html += '<div class="aluno-card">'
      + '<div class="aluno-header">'
      + '<div class="aluno-info">'
      + '<h3>' + escapeHtml(aluno.nome) + '</h3>'
      + '<div class="aluno-credentials">'
      + '<span class="aluno-ra" title="RA">👤 ' + escapeHtml(aluno.ra) + '</span>'
      + (aluno.senha ? '<span class="aluno-senha" title="Senha Studeo">🔑 <code>' + escapeHtml(aluno.senha) + '</code></span>' : '')
      + '</div>'
      + '</div>'
      + '<span class="badge badge-pendente">' + totalPendentes + ' pendência' + (totalPendentes !== 1 ? 's' : '') + '</span>'
      + '</div>';

    discs.forEach(function (disc) {
      var pendentes = disc.items.filter(function (i) { return !i.respondida; }).length;
      // Prazo mais próximo desta disciplina
      var deadline = getEarliestDeadline(disc.items);
      var prazoText = '';
      var urgente = false;

      if (deadline) {
        var hoje = new Date();
        hoje.setHours(0, 0, 0, 0);
        var diffDays = Math.ceil((deadline - hoje) / (1000 * 60 * 60 * 24));
        if (diffDays <= 0) {
          prazoText = 'Vence hoje!';
          urgente = true;
        } else if (diffDays <= 3) {
          prazoText = 'Vence em ' + diffDays + ' dia' + (diffDays > 1 ? 's' : '') + '!';
          urgente = true;
        } else if (diffDays <= 7) {
          prazoText = 'Vence em ' + diffDays + ' dias';
        } else {
          prazoText = 'Entrega até: ' + formatDate(deadline);
        }
      }

      html += '<div class="disc-row' + (urgente ? ' disc-urgente' : '') + '">'
        + '<div class="disc-row-info">'
        + '<span class="disc-nome">' + escapeHtml(disc.disciplina) + '</span>'
        + '<span class="disc-pendencias">(' + pendentes + ' pendência' + (pendentes !== 1 ? 's' : '') + ')</span>'
        + '</div>'
        + '<div class="disc-row-prazo">'
        + (prazoText ? '<span class="prazo-text' + (urgente ? ' prazo-urgente' : '') + '">' + prazoText + '</span>' : '')
        + '</div>'
        + '</div>';
    });

    html += '</div>';
  });

  container.innerHTML = html;

  // Animar entrada dos cards
  container.querySelectorAll('.aluno-card').forEach(function (card, i) {
    card.style.opacity = '0';
    card.style.transform = 'translateY(12px)';
    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    setTimeout(function () {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 50 + i * 40);
  });
}

async function handleSync() {
  var selectEl = document.getElementById('sync-aluno-select');
  var alunoId = selectEl.value;
  if (!alunoId) { alert('Selecione um aluno para sincronizar.'); return; }
  if (syncInProgress) { alert('Sincronização em andamento, aguarde...'); return; }

  var aluno = (window._todosAlunos || []).find(function (a) { return a.id === alunoId; });
  if (!aluno) { alert('Aluno não encontrado.'); return; }
  if (!aluno.studeo_senha) { alert('Este aluno não tem senha do Studeo cadastrada. Edite o aluno na página de Alunos e adicione a senha.'); return; }

  syncInProgress = true;
  setSyncButtonsLoading(true);
  showSyncStatus('Sincronizando ' + aluno.nome + '...', 'loading');

  try {
    var resp = await fetch(SYNC_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'sync', ra: aluno.ra, senha: aluno.studeo_senha }),
    });

    var result = await resp.json();
    if (!resp.ok || !result.ok) {
      var errMsg = result.error || 'Erro na sincronização';
      if (errMsg.includes('Credenciais') || errMsg.includes('401') || errMsg.includes('password')) {
        errMsg = 'Credenciais inválidas para ' + aluno.nome + '. Verifique o RA e a senha do Studeo na página de Alunos.';
      }
      throw new Error(errMsg);
    }

    // Salvar resultados no Supabase
    var count = await saveResults(alunoId, result.resultado);
    showSyncStatus('Sincronizado! ' + count + ' atividades encontradas para ' + aluno.nome, 'success');
    await loadSyncData();

  } catch (err) {
    showSyncStatus('Erro: ' + err.message, 'error');
  } finally {
    syncInProgress = false;
    setSyncButtonsLoading(false);
  }
}

function setSyncButtonsLoading(loading) {
  ['btn-sync', 'btn-sync-all', 'btn-sync-new'].forEach(function (id) {
    var btn = document.getElementById(id);
    if (btn) {
      if (loading) btn.classList.add('btn-loading');
      else btn.classList.remove('btn-loading');
      btn.disabled = loading;
    }
  });
}

async function handleSyncAll() {
  if (syncInProgress) { alert('Sincronização em andamento, aguarde...'); return; }

  var grupoSync = (document.getElementById('sync-grupo-select') || {}).value || '';
  var all = (window._todosAlunos || []).filter(function (a) { return a.studeo_senha; });

  // Filtrar por grupo se selecionado
  var alunosList = grupoSync ? all.filter(function (a) { return a.tipo === grupoSync; }) : all;
  var grupoLabel = grupoSync ? (' do grupo ' + grupoSync) : '';

  if (!alunosList.length) {
    alert('Nenhum aluno com senha do Studeo' + grupoLabel + '.');
    return;
  }

  await syncBatch(alunosList, 'Sync' + grupoLabel);
}

async function handleSyncNew() {
  if (syncInProgress) { alert('Sincronização em andamento, aguarde...'); return; }

  var grupoSync = (document.getElementById('sync-grupo-select') || {}).value || '';
  var all = (window._todosAlunos || []).filter(function (a) { return a.studeo_senha; });
  if (grupoSync) all = all.filter(function (a) { return a.tipo === grupoSync; });

  // Buscar quais alunos já têm sync
  var { data: synced } = await sb.from('studeo_sync').select('aluno_id');
  var syncedIds = {};
  (synced || []).forEach(function (s) { syncedIds[s.aluno_id] = true; });

  // Filtrar apenas os que NUNCA foram sincronizados
  var novos = all.filter(function (a) { return !syncedIds[a.id]; });

  if (!novos.length) {
    showSyncStatus('Todos os alunos já foram sincronizados!', 'success');
    return;
  }

  await syncBatch(novos, 'Novos (' + novos.length + ')');
}

async function syncBatch(alunosList, label) {
  syncInProgress = true;
  setSyncButtonsLoading(true);
  var total = alunosList.length;
  var erros = 0;
  var totalAtiv = 0;

  for (var i = 0; i < alunosList.length; i++) {
    var aluno = alunosList[i];
    showSyncStatus(label + ': ' + (i + 1) + '/' + total + ' — ' + aluno.nome + '...', 'loading');

    try {
      var resp = await fetch(SYNC_API_URL, {
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
    label + ' concluído! ' + totalAtiv + ' atividades de ' + (total - erros) + '/' + total + ' alunos.'
    + (erros ? ' (' + erros + ' erro' + (erros > 1 ? 's' : '') + ')' : ''),
    erros ? 'warning' : 'success'
  );

  await loadSyncData();
  syncInProgress = false;
  setSyncButtonsLoading(false);
}

async function saveResults(alunoId, resultado) {
  var now = new Date().toISOString();
  var seen = {};
  var records = [];

  for (var i = 0; i < resultado.length; i++) {
    var disc = resultado[i];
    // Combina atividades e mapa, deduplicando por descricao
    var allActivities = (disc.atividades || []).concat(disc.mapa || []);

    for (var j = 0; j < allActivities.length; j++) {
      var ativ = allActivities[j];
      if (!ativ.descricao) continue;

      // Deduplicar: mesmo shortname + descricao = mesma atividade
      var key = disc.cd_shortname + '|' + ativ.descricao;
      if (seen[key]) continue;
      seen[key] = true;

      // Determinar tipo: se descricao começa com "MAPA" é MAPA, senão AV
      var tipo = (ativ.descricao || '').toUpperCase().indexOf('MAPA') === 0 ? 'MAPA' : 'AV';

      records.push({
        aluno_id: alunoId,
        disciplina: disc.disciplina,
        cd_shortname: disc.cd_shortname,
        ano: disc.ano ? String(disc.ano) : null,
        modulo: disc.modulo ? String(disc.modulo) : null,
        atividade: ativ.descricao,
        tipo_atividade: tipo,
        data_inicial: ativ.dataInicial || null,
        data_final: ativ.dataFinal || null,
        respondida: ativ.respondida || false,
        synced_at: now,
      });
    }
  }

  if (!records.length) return 0;

  // Limpar registros antigos deste aluno e inserir novos
  var { error: delError } = await sb.from('studeo_sync')
    .delete()
    .eq('aluno_id', alunoId);
  if (delError) console.error('Delete error:', delError);

  // Inserir em chunks de 200
  var count = 0;
  for (var i = 0; i < records.length; i += 200) {
    var chunk = records.slice(i, i + 200);
    var { error } = await sb.from('studeo_sync').insert(chunk);
    if (error) {
      console.error('Insert batch error:', error);
      // Tentar inserir um a um como fallback
      for (var k = 0; k < chunk.length; k++) {
        var { error: errSingle } = await sb.from('studeo_sync').insert([chunk[k]]);
        if (!errSingle) count++;
        else console.error('Insert single error:', errSingle, chunk[k]);
      }
    } else {
      count += chunk.length;
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

function getEarliestDeadline(items) {
  var min = null;
  items.forEach(function (item) {
    if (item.data_final) {
      var d = new Date(item.data_final);
      if (!min || d < min) min = d;
    }
  });
  return min;
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
