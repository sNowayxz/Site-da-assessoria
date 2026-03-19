/* ═══════════════════════════════════════════
   Rastreio Studeo — Sincronização
   ═══════════════════════════════════════════ */

var SYNC_API_URL = 'https://site-da-assessoria.vercel.app/api/sync-studeo';
var PREENCHER_API_URL = 'https://site-da-assessoria.vercel.app/api/preencher-atividade';
var syncInProgress = false;

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
  document.getElementById('btn-sync-all').addEventListener('click', handleSyncAll);
  document.getElementById('btn-sync-new').addEventListener('click', handleSyncNew);

  // Grupo chips
  document.querySelectorAll('.grupo-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      document.querySelectorAll('.grupo-chip').forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      updateSyncGroupButton();
      loadSyncData();
    });
  });
  updateSyncGroupButton();

  // Prazo chips
  document.querySelectorAll('.prazo-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      document.querySelectorAll('.prazo-chip').forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      loadSyncData();
    });
  });

});

function getActiveGrupo() {
  var chip = document.querySelector('.grupo-chip.active');
  return chip ? chip.getAttribute('data-grupo') : '';
}

function getActiveGrupoLabel() {
  var grupo = getActiveGrupo();
  if (grupo === 'mensalista') return 'Mensalistas';
  if (grupo === 'recorrente') return 'Recorrentes';
  if (grupo === 'extensao') return 'Extensão';
  return 'Todos';
}

function updateSyncGroupButton() {
  var btn = document.getElementById('btn-sync-all');
  if (btn) btn.textContent = '⚡ Sync ' + getActiveGrupoLabel();
  var btnNew = document.getElementById('btn-sync-new');
  if (btnNew) btnNew.textContent = '🆕 Novos ' + getActiveGrupoLabel();
}

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
  var el;
  el = document.getElementById('count-all'); if (el) el.textContent = (data || []).length;
  el = document.getElementById('count-men'); if (el) el.textContent = counts.mensalista || 0;
  el = document.getElementById('count-rec'); if (el) el.textContent = counts.recorrente || 0;
  el = document.getElementById('count-ext'); if (el) el.textContent = counts.extensao || 0;


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

  var grupoFilter = getActiveGrupo();

  // Prazo chip ativo
  var activeChip = document.querySelector('.prazo-chip.active');
  var dias = activeChip ? parseInt(activeChip.getAttribute('data-dias')) : 60;

  // Build alunos cache with tipo
  if (!window._alunosCache) {
    var { data: alunos } = await sb.from('alunos').select('id, nome, ra, tipo, studeo_senha');
    window._alunosCache = {};
    (alunos || []).forEach(function (a) { window._alunosCache[a.id] = a; });
  }

  // Só pendentes (não respondidas), com prazo no futuro, ordenadas por data_final
  var now = new Date();
  now.setHours(0, 0, 0, 0);

  var query = sb.from('studeo_sync')
    .select('*')
    .eq('respondida', false)
    .gte('data_final', now.toISOString())
    .order('data_final', { ascending: true });

  // Limite de prazo se não for "Todos"
  if (dias > 0) {
    var limite = new Date(now);
    limite.setDate(limite.getDate() + dias);
    query = query.lte('data_final', limite.toISOString());
  }

  // Filtrar por grupo
  if (grupoFilter) {
    var grupoIds = Object.keys(window._alunosCache).filter(function (id) {
      return window._alunosCache[id].tipo === grupoFilter;
    });
    if (grupoIds.length > 0) query = query.in('aluno_id', grupoIds);
  }

  var { data, error } = await query;
  if (error) { console.error(error); return; }

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
      + '<span class="aluno-ra">👤 <span class="copy-value" data-copy="' + escapeHtml(aluno.ra) + '" title="Clique para copiar RA">' + escapeHtml(aluno.ra) + '</span></span>'
      + (aluno.senha ? '<span class="aluno-senha">🔑 <span class="copy-value" data-copy="' + escapeHtml(aluno.senha) + '" title="Clique para copiar senha">' + escapeHtml(aluno.senha) + '</span></span>' : '')
      + '</div>'
      + '</div>'
      + '<div style="display:flex;align-items:center;gap:8px;">'
      + '<span class="badge badge-pendente">' + totalPendentes + ' pendência' + (totalPendentes !== 1 ? 's' : '') + '</span>'
      + '<button class="btn btn-sync" style="font-size:0.78rem;padding:6px 12px;" onclick="buscarEPreencherAluno(\x27' + escapeHtml(aluno.ra) + '\x27, this)" title="Preencher via Modelitos">&#9654; Preencher</button>'
      + '</div>'
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

  // Click-to-copy nos valores de RA e senha
  container.querySelectorAll('.copy-value').forEach(function (el) {
    el.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var text = el.getAttribute('data-copy');
      navigator.clipboard.writeText(text).then(function () {
        el.classList.add('copied');
        setTimeout(function () { el.classList.remove('copied'); }, 1500);
      }).catch(function () {
        // Fallback: select text
        var range = document.createRange();
        range.selectNodeContents(el);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      });
    });
  });

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

function setSyncButtonsLoading(loading) {
  ['btn-sync-all', 'btn-sync-new'].forEach(function (id) {
    var btn = document.getElementById(id);
    if (btn) {
      if (loading) btn.classList.add('btn-loading');
      else btn.classList.remove('btn-loading');
      btn.disabled = loading;
    }
  });
}

async function handleSyncAll() {
  if (syncInProgress) { showToast('Sincronização em andamento, aguarde...', 'warning'); return; }

  var grupo = getActiveGrupo();
  var all = (window._todosAlunos || []).filter(function (a) { return a.studeo_senha; });
  var alunosList = grupo ? all.filter(function (a) { return a.tipo === grupo; }) : all;
  var grupoLabel = grupo ? (' ' + grupo) : '';

  if (!alunosList.length) {
    showToast('Nenhum aluno com senha do Studeo' + grupoLabel, 'warning');
    return;
  }

  await syncBatch(alunosList, 'Sync' + grupoLabel);
}

async function handleSyncNew() {
  if (syncInProgress) { showToast('Sincronização em andamento, aguarde...', 'warning'); return; }

  var grupo = getActiveGrupo();
  var all = (window._todosAlunos || []).filter(function (a) { return a.studeo_senha; });
  if (grupo) all = all.filter(function (a) { return a.tipo === grupo; });

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

      // Só salvar atividades com prazo aberto (dataFinal no futuro)
      if (ativ.dataFinal) {
        var df = new Date(ativ.dataFinal);
        if (df < new Date()) continue; // prazo já passou, ignorar
      }

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

/* ═══════════════════════════════════════════
   Preencher Atividades — Modelitos (Modal)
   Usa dados já rastreados do studeo_sync
   ═══════════════════════════════════════════ */

var _preencherAtividades = [];
var _preencherRA = '';

function buscarEPreencherAluno(ra, btn) {
  if (!ra) return;

  // Pegar atividades do rastreio já carregado (window._syncData)
  var syncData = window._syncData || [];
  var atividades = syncData.filter(function (item) {
    return item.alunos && item.alunos.ra === ra && !item.respondida;
  });

  if (!atividades.length) {
    showSyncStatus('Nenhuma atividade pendente no rastreio para RA ' + ra, 'warning');
    return;
  }

  _preencherAtividades = atividades;
  _preencherRA = ra;
  abrirModalPreencher(ra, atividades);
}

function abrirModalPreencher(ra, atividades) {
  var nome = atividades[0] && atividades[0].alunos ? atividades[0].alunos.nome : ra;
  document.getElementById('modal-preencher-title').textContent = 'Preencher \u2014 ' + nome + ' (' + ra + ')';
  document.getElementById('modal-preencher-info').textContent = atividades.length + ' atividade(s) pendente(s) do rastreio';
  document.getElementById('modal-preencher-status').textContent = '';

  var html = '';

  atividades.forEach(function (a, i) {
    var prazo = a.data_final ? formatDate(a.data_final) : '';
    var tipo = a.tipo_atividade || 'AV';
    html += '<div class="preencher-item">'
      + '<input type="checkbox" class="check-modal-item" data-idx="' + i + '" checked>'
      + '<div class="preencher-item-info">'
      + '<div class="preencher-item-title">' + escapeHtml(a.atividade) + '</div>'
      + '<div class="preencher-item-meta">'
      + '<span class="badge badge-' + (tipo === 'MAPA' ? 'mapa' : 'av') + '">' + tipo + '</span>'
      + '<span>' + escapeHtml(a.disciplina) + '</span>'
      + '<span>\u2022</span>'
      + '<span>' + escapeHtml(a.cd_shortname) + '</span>'
      + (prazo ? '<span>\u2022 Prazo: ' + prazo + '</span>' : '')
      + '</div>'
      + '</div>'
      + '</div>';
  });

  document.getElementById('modal-preencher-list').innerHTML = html;

  // Sync check-all-modal-top
  var checkAllTop = document.getElementById('check-all-modal-top');
  if (checkAllTop) checkAllTop.checked = true;

  var btnConfirmar = document.getElementById('btn-confirmar-preencher');
  btnConfirmar.disabled = false;
  btnConfirmar.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Preencher Selecionadas';
  btnConfirmar.onclick = executarPreenchimento;

  openModal('modal-preencher');
}

function toggleAllModal(checked) {
  var items = document.querySelectorAll('.check-modal-item');
  for (var i = 0; i < items.length; i++) items[i].checked = checked;
}

async function executarPreenchimento() {
  var checks = document.querySelectorAll('.check-modal-item:checked');
  if (!checks.length) { showSyncStatus('Selecione ao menos uma atividade', 'warning'); return; }

  var finalizar = document.getElementById('check-finalizar').checked;
  var btn = document.getElementById('btn-confirmar-preencher');
  var status = document.getElementById('modal-preencher-status');
  btn.disabled = true;

  // Buscar senha do aluno no cache
  var alunoCache = window._alunosCache || {};
  var alunoData = null;
  for (var key in alunoCache) {
    if (alunoCache[key].ra === _preencherRA) { alunoData = alunoCache[key]; break; }
  }
  if (!alunoData || !alunoData.studeo_senha) {
    status.textContent = 'Aluno sem senha do Studeo cadastrada';
    btn.disabled = false;
    btn.textContent = 'Preencher Selecionadas';
    return;
  }

  // Buscar pendentes do Modelitos para obter os idQuestionario + shortname
  status.textContent = '\u23f3 Consultando Modelitos...';
  btn.textContent = '\u23f3 Consultando...';

  var pendentesModelitos = [];
  try {
    var resp = await fetch(PREENCHER_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'verificar', ra: _preencherRA }),
    });
    var data = await resp.json();
    if (!data.ok) throw new Error(data.error || 'Erro');
    pendentesModelitos = data.pendentes || [];
  } catch (err) {
    status.textContent = 'Erro ao consultar Modelitos: ' + err.message;
    btn.disabled = false;
    btn.textContent = 'Preencher Selecionadas';
    return;
  }

  if (!pendentesModelitos.length) {
    status.textContent = 'Nenhuma atividade encontrada no Modelitos para este RA';
    btn.disabled = false;
    btn.textContent = 'Preencher Selecionadas';
    return;
  }

  var total = checks.length;
  var ok = 0, erros = 0, ignorados = 0;

  for (var i = 0; i < checks.length; i++) {
    var idx = parseInt(checks[i].getAttribute('data-idx'));
    var a = _preencherAtividades[idx];
    if (!a) continue;

    status.textContent = '\u23f3 ' + (i + 1) + '/' + total + ': ' + a.atividade + '...';
    btn.textContent = '\u23f3 ' + (i + 1) + '/' + total;

    // Match por shortname
    var match = pendentesModelitos.filter(function (p) {
      return p.shortname && a.cd_shortname && p.shortname.includes(a.cd_shortname);
    });

    if (!match.length) {
      ignorados++;
      checks[i].parentElement.style.borderColor = '#f59e0b';
      checks[i].parentElement.style.opacity = '0.6';
      continue;
    }

    // Preencher cada match — API agora monta o idQuestionario completo com JWT
    for (var j = 0; j < match.length; j++) {
      try {
        var r = await fetch(PREENCHER_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'preencher',
            idQuestionario: match[j].idQuestionario,
            shortname: match[j].shortname,
            ra: _preencherRA,
            senha: alunoData.studeo_senha,
            finalizar: finalizar,
          }),
        });
        var d = await r.json();
        if (!d.ok) throw new Error(d.error);
        ok++;
      } catch (e) {
        erros++;
        console.error('Erro preenchendo ' + match[j].idQuestionario + ':', e.message);
      }
    }

    checks[i].parentElement.style.opacity = '0.5';
    checks[i].parentElement.style.borderColor = '#22c55e';
  }

  var msg = ok + ' preenchida(s)';
  if (erros) msg += ', ' + erros + ' erro(s)';
  if (ignorados) msg += ', ' + ignorados + ' sem match no Modelitos';
  msg += finalizar ? ' (finalizadas)' : ' (sem finalizar)';

  status.textContent = msg;
  btn.textContent = 'Fechar';
  btn.disabled = false;
  btn.onclick = function () { closeModal('modal-preencher'); };
  showSyncStatus('RA ' + _preencherRA + ': ' + msg, ok ? 'success' : 'error');
}

/* ═══════════════════════════════════════════
   Preencher em Massa — Checkboxes por Atividade
   Agrupa por atividade e preenche todos os alunos
   ═══════════════════════════════════════════ */

var _massaAtividades = [];

async function preencherEmMassa() {
  var syncData = window._syncData || [];
  if (!syncData.length) { showSyncStatus('Nenhum dado de rastreio carregado', 'warning'); return; }

  // Agrupar por atividade (cd_shortname + atividade)
  var byAtividade = {};
  syncData.forEach(function (item) {
    if (!item.alunos || !item.alunos.ra || item.respondida) return;
    var key = (item.cd_shortname || '') + '|' + (item.atividade || '');
    if (!byAtividade[key]) {
      byAtividade[key] = {
        atividade: item.atividade,
        disciplina: item.disciplina,
        cd_shortname: item.cd_shortname,
        tipo: item.tipo_atividade || 'AV',
        data_final: item.data_final,
        alunos: []
      };
    }
    // Prazo mais próximo
    if (item.data_final && (!byAtividade[key].data_final || item.data_final < byAtividade[key].data_final)) {
      byAtividade[key].data_final = item.data_final;
    }
    byAtividade[key].alunos.push({
      nome: item.alunos.nome,
      ra: item.alunos.ra,
      aluno_id: item.aluno_id
    });
  });

  var atividades = Object.values(byAtividade);
  if (!atividades.length) { showSyncStatus('Nenhuma atividade pendente para preencher', 'warning'); return; }

  // Ordenar por prazo
  atividades.sort(function (a, b) {
    if (!a.data_final) return 1;
    if (!b.data_final) return -1;
    return a.data_final.localeCompare(b.data_final);
  });

  _massaAtividades = atividades;

  // Contar alunos únicos
  var uniqueRAs = {};
  atividades.forEach(function (a) {
    a.alunos.forEach(function (al) { uniqueRAs[al.ra] = true; });
  });

  document.getElementById('modal-preencher-title').textContent = 'Preencher em Massa';
  document.getElementById('modal-preencher-info').textContent = atividades.length + ' atividade(s) de ' + Object.keys(uniqueRAs).length + ' aluno(s)';
  document.getElementById('modal-preencher-status').textContent = '';

  var html = '';

  atividades.forEach(function (a, i) {
    var prazo = a.data_final ? formatDate(a.data_final) : '';
    var tipo = a.tipo || 'AV';
    var urgente = false;
    if (a.data_final) {
      var hoje = new Date(); hoje.setHours(0,0,0,0);
      var diff = Math.ceil((new Date(a.data_final) - hoje) / 86400000);
      urgente = diff <= 3;
    }
    var alunoNames = a.alunos.map(function (al) { return al.nome; });
    var alunoPreview = alunoNames.length <= 3 ? alunoNames.join(', ') : alunoNames.slice(0, 3).join(', ') + ' +' + (alunoNames.length - 3);

    html += '<div class="preencher-item' + (urgente ? ' urgente' : '') + '">'
      + '<input type="checkbox" class="check-modal-item" data-idx="' + i + '" checked>'
      + '<div class="preencher-item-info">'
      + '<div class="preencher-item-title">' + escapeHtml(a.atividade) + '</div>'
      + '<div class="preencher-item-meta">'
      + '<span class="badge badge-' + (tipo === 'MAPA' ? 'mapa' : 'av') + '">' + tipo + '</span>'
      + '<span>' + escapeHtml(a.disciplina) + '</span>'
      + '<span>\u2022</span>'
      + '<span>' + escapeHtml(a.cd_shortname) + '</span>'
      + (prazo ? '<span>\u2022 Prazo: ' + prazo + '</span>' : '')
      + '</div>'
      + '<div class="preencher-item-alunos">\uD83D\uDC65 ' + a.alunos.length + ' aluno(s): ' + escapeHtml(alunoPreview) + '</div>'
      + '</div>'
      + '</div>';
  });

  document.getElementById('modal-preencher-list').innerHTML = html;

  // Sync check-all-modal-top
  var checkAllTop = document.getElementById('check-all-modal-top');
  if (checkAllTop) checkAllTop.checked = true;

  var btnConfirmar = document.getElementById('btn-confirmar-preencher');
  btnConfirmar.disabled = false;
  btnConfirmar.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Preencher Selecionadas';
  btnConfirmar.onclick = executarMassaPorAtividade;

  openModal('modal-preencher');
}

async function executarMassaPorAtividade() {
  var checks = document.querySelectorAll('.check-modal-item:checked');
  if (!checks.length) { showSyncStatus('Selecione ao menos uma atividade', 'warning'); return; }

  var finalizar = document.getElementById('check-finalizar').checked;
  var btn = document.getElementById('btn-confirmar-preencher');
  var status = document.getElementById('modal-preencher-status');
  btn.disabled = true;

  var btnMassa = document.getElementById('btn-preencher-massa');

  // Coletar atividades selecionadas e RAs únicos
  var selectedAtiv = [];
  var allRAs = {};
  for (var c = 0; c < checks.length; c++) {
    var idx = parseInt(checks[c].getAttribute('data-idx'));
    var ativ = _massaAtividades[idx];
    if (!ativ) continue;
    selectedAtiv.push(ativ);
    ativ.alunos.forEach(function (al) {
      if (!allRAs[al.ra]) allRAs[al.ra] = { nome: al.nome, ra: al.ra };
    });
  }

  var ras = Object.values(allRAs);
  var alunoCache = window._alunosCache || {};
  var totalOk = 0, totalErros = 0, totalIgnorados = 0, alunosOk = 0;

  for (var r = 0; r < ras.length; r++) {
    var ra = ras[r].ra;
    var nome = ras[r].nome;

    // Buscar senha
    var alunoData = null;
    for (var key in alunoCache) {
      if (alunoCache[key].ra === ra) { alunoData = alunoCache[key]; break; }
    }
    if (!alunoData || !alunoData.studeo_senha) {
      var countForRA = selectedAtiv.filter(function (a) {
        return a.alunos.some(function (al) { return al.ra === ra; });
      }).length;
      totalIgnorados += countForRA;
      continue;
    }

    status.textContent = '\u23f3 ' + (r + 1) + '/' + ras.length + ': ' + nome + '...';
    btn.textContent = '\u23f3 ' + (r + 1) + '/' + ras.length;
    if (btnMassa) btnMassa.textContent = '\u23f3 ' + (r + 1) + '/' + ras.length;

    // Verificar pendentes no Modelitos (1x por aluno)
    var pendentesModelitos = [];
    try {
      var resp = await fetch(PREENCHER_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'verificar', ra: ra }),
      });
      var data = await resp.json();
      if (data.ok) pendentesModelitos = data.pendentes || [];
    } catch (e) { /* ignora */ }

    if (!pendentesModelitos.length) {
      var countForRA2 = selectedAtiv.filter(function (a) {
        return a.alunos.some(function (al) { return al.ra === ra; });
      }).length;
      totalIgnorados += countForRA2;
      continue;
    }

    // Para cada atividade selecionada que este aluno tem
    for (var a = 0; a < selectedAtiv.length; a++) {
      var ativ = selectedAtiv[a];
      if (!ativ.alunos.some(function (al) { return al.ra === ra; })) continue;

      var match = pendentesModelitos.filter(function (p) {
        return p.shortname && ativ.cd_shortname && p.shortname.includes(ativ.cd_shortname);
      });
      if (!match.length) { totalIgnorados++; continue; }

      for (var j = 0; j < match.length; j++) {
        try {
          var rr = await fetch(PREENCHER_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action: 'preencher',
              idQuestionario: match[j].idQuestionario,
              shortname: match[j].shortname,
              ra: ra,
              senha: alunoData.studeo_senha,
              finalizar: finalizar,
            }),
          });
          var dd = await rr.json();
          if (!dd.ok) throw new Error(dd.error);
          totalOk++;
        } catch (e) {
          totalErros++;
        }
      }
    }
    alunosOk++;
  }

  // Marcar itens preenchidos no modal
  for (var c2 = 0; c2 < checks.length; c2++) {
    checks[c2].parentElement.style.opacity = '0.5';
    checks[c2].parentElement.style.borderColor = '#22c55e';
  }

  var msg = alunosOk + '/' + ras.length + ' alunos, ' + totalOk + ' preenchida(s)';
  if (totalErros) msg += ', ' + totalErros + ' erro(s)';
  if (totalIgnorados) msg += ', ' + totalIgnorados + ' ignorada(s)';
  msg += finalizar ? ' (finalizadas)' : ' (sem finalizar)';

  status.textContent = msg;
  btn.textContent = 'Fechar';
  btn.disabled = false;
  btn.onclick = function () { closeModal('modal-preencher'); };
  showSyncStatus('Massa: ' + msg, totalOk ? 'success' : 'warning');
  if (btnMassa) { btnMassa.disabled = false; btnMassa.textContent = '\u26a1 Preencher em Massa'; }
}
