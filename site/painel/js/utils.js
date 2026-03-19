/* ═══════════════════════════════════════════
   Utils — Dark Mode, Toasts, PDF Export, Notifications
   ═══════════════════════════════════════════ */

// ─── Dark Mode ───
(function initTheme() {
  var saved = localStorage.getItem('painel-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme');
  var next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('painel-theme', next);
  // Atualiza ícone do botão
  var btn = document.getElementById('btn-theme');
  if (btn) btn.textContent = next === 'dark' ? '☀️' : '🌙';
}

// Atualiza ícone ao carregar
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('btn-theme');
  if (btn) {
    var theme = document.documentElement.getAttribute('data-theme');
    btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    btn.addEventListener('click', toggleTheme);
  }
});


// ─── Toast Notifications ───
function ensureToastContainer() {
  var container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

function showToast(message, type) {
  type = type || 'info';
  var container = ensureToastContainer();
  var icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  var toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
  toast.innerHTML = '<span class="toast-icon">' + (icons[type] || 'ℹ️') + '</span><span>' + message + '</span>';
  container.appendChild(toast);
  setTimeout(function () {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 5000);
}


// ─── PDF Export (usando jsPDF) ───
function loadJsPDF(callback) {
  if (window.jspdf) { callback(); return; }
  var s = document.createElement('script');
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.2/jspdf.umd.min.js';
  s.onload = function () {
    var s2 = document.createElement('script');
    s2.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.4/jspdf.plugin.autotable.min.js';
    s2.onload = callback;
    document.head.appendChild(s2);
  };
  document.head.appendChild(s);
}

function exportTableToPDF(tableId, title, filename) {
  loadJsPDF(function () {
    var jsPDF = window.jspdf.jsPDF;
    var doc = new jsPDF('l', 'mm', 'a4');

    // Header
    doc.setFontSize(18);
    doc.setTextColor(26, 26, 46);
    doc.text(title || 'Relatório', 14, 20);

    doc.setFontSize(10);
    doc.setTextColor(136, 146, 164);
    doc.text('Assessoria Acadêmica — Gerado em ' + new Date().toLocaleDateString('pt-BR') + ' às ' + new Date().toLocaleTimeString('pt-BR'), 14, 28);

    // Tabela
    var table = document.querySelector('#' + tableId);
    if (!table) {
      // Tenta pegar do tbody
      table = document.querySelector('#' + tableId)?.closest('table');
    }

    // Se passou o ID do tbody, pega a table pai
    var tableEl = table;
    if (table && table.tagName === 'TBODY') {
      tableEl = table.closest('table');
    }
    if (!tableEl) {
      // Tenta qualquer tabela visível
      tableEl = document.querySelector('.table-wrap table');
    }

    if (tableEl) {
      doc.autoTable({
        html: tableEl,
        startY: 34,
        styles: {
          fontSize: 8,
          cellPadding: 3,
          lineColor: [200, 200, 200],
          lineWidth: 0.1,
        },
        headStyles: {
          fillColor: [26, 26, 46],
          textColor: [240, 192, 48],
          fontStyle: 'bold',
          fontSize: 8,
        },
        alternateRowStyles: {
          fillColor: [248, 249, 252],
        },
        // Remove a última coluna (Ações)
        columnStyles: {},
        didParseCell: function (data) {
          // Se a coluna header é "Ações", esconde
          if (data.column.index === data.table.columns.length - 1) {
            var headerText = '';
            try {
              headerText = data.table.columns[data.column.index].raw?.textContent || '';
            } catch (e) {}
            if (headerText.includes('Aç') || headerText.includes('Acoes')) {
              data.cell.styles.cellWidth = 0;
              data.cell.text = [];
            }
          }
        },
      });
    }

    // Footer
    var pageCount = doc.internal.getNumberOfPages();
    for (var i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text('Página ' + i + ' de ' + pageCount, doc.internal.pageSize.getWidth() - 30, doc.internal.pageSize.getHeight() - 10);
    }

    doc.save((filename || 'relatorio') + '.pdf');
    showToast('PDF exportado com sucesso!', 'success');
  });
}


// ─── CSV Export ───
function exportTableToCSV(tableId, filename) {
  var table = document.querySelector('#' + tableId);
  if (!table) table = document.querySelector('.table-wrap table');
  if (!table) { showToast('Nenhuma tabela encontrada', 'error'); return; }

  var rows = table.querySelectorAll('tr');
  var csv = [];

  rows.forEach(function (row) {
    var cols = row.querySelectorAll('th, td');
    var rowData = [];
    cols.forEach(function (col, idx) {
      // Ignora última coluna (Ações)
      if (idx === cols.length - 1 && col.classList.contains('actions')) return;
      var text = col.textContent.trim().replace(/"/g, '""');
      rowData.push('"' + text + '"');
    });
    csv.push(rowData.join(','));
  });

  var blob = new Blob(['\ufeff' + csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
  var link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = (filename || 'relatorio') + '.csv';
  link.click();
  showToast('CSV exportado com sucesso!', 'success');
}


// ─── Global Search ───
function initGlobalSearch() {
  var searchBox = document.getElementById('global-search');
  var resultsBox = document.getElementById('global-search-results');
  if (!searchBox || !resultsBox) return;

  var debounce;
  var _searchSelectedIdx = -1;

  searchBox.addEventListener('input', function () {
    clearTimeout(debounce);
    _searchSelectedIdx = -1;
    var q = searchBox.value.trim();
    if (q.length < 2) { resultsBox.style.display = 'none'; return; }
    debounce = setTimeout(function () { doGlobalSearch(q, resultsBox); }, 300);
  });

  searchBox.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { resultsBox.style.display = 'none'; searchBox.blur(); _searchSelectedIdx = -1; return; }

    var items = resultsBox.querySelectorAll('.search-result-item');
    if (!items.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      _searchSelectedIdx = Math.min(_searchSelectedIdx + 1, items.length - 1);
      items.forEach(function (it, i) { it.classList.toggle('search-result-active', i === _searchSelectedIdx); });
      items[_searchSelectedIdx].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      _searchSelectedIdx = Math.max(_searchSelectedIdx - 1, 0);
      items.forEach(function (it, i) { it.classList.toggle('search-result-active', i === _searchSelectedIdx); });
      items[_searchSelectedIdx].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (_searchSelectedIdx >= 0 && items[_searchSelectedIdx]) {
        window.location.href = items[_searchSelectedIdx].getAttribute('href');
      } else if (items[0]) {
        window.location.href = items[0].getAttribute('href');
      }
    }
  });

  document.addEventListener('click', function (e) {
    if (!searchBox.contains(e.target) && !resultsBox.contains(e.target)) {
      resultsBox.style.display = 'none';
      _searchSelectedIdx = -1;
    }
  });
}

async function doGlobalSearch(q, resultsBox) {
  if (!window.sb) return;
  var results = [];

  try {
    // Run all searches in parallel
    var searches = [
      sb.from('alunos').select('id, nome, ra, curso').or('nome.ilike.%' + q + '%,ra.ilike.%' + q + '%,curso.ilike.%' + q + '%').limit(5),
      sb.from('atividades').select('id, descricao, tipo, status, alunos(nome)').or('descricao.ilike.%' + q + '%,tipo.ilike.%' + q + '%').limit(5),
      sb.from('modulos').select('id, nome, codigo').or('nome.ilike.%' + q + '%,codigo.ilike.%' + q + '%').limit(3)
    ];

    var responses = await Promise.all(searches);

    // Alunos
    (responses[0].data || []).forEach(function (a) {
      results.push({ type: 'Aluno', name: a.nome, detail: a.ra + ' — ' + (a.curso || ''), url: 'alunos.html' });
    });

    // Atividades
    (responses[1].data || []).forEach(function (a) {
      var alunoNome = a.alunos ? a.alunos.nome : '';
      var statusMap = { pendente: 'Pendente', em_andamento: 'Em Andamento', entregue: 'Entregue', revisao: 'Revisao' };
      results.push({ type: 'Atividade', name: a.descricao || a.tipo, detail: alunoNome + ' — ' + (statusMap[a.status] || a.status), url: 'atividades.html' });
    });

    // Modulos
    (responses[2].data || []).forEach(function (m) {
      results.push({ type: 'Modulo', name: m.nome, detail: m.codigo || '', url: 'modulos.html' });
    });
  } catch (e) {
    console.warn('[search]', e.message);
  }

  if (!results.length) {
    resultsBox.innerHTML = '<div class="search-empty">Nenhum resultado para "' + escapeHtml(q) + '"</div>';
  } else {
    resultsBox.innerHTML = results.map(function (r) {
      return '<a href="' + escapeHtml(r.url) + '" class="search-result-item">' +
        '<span class="search-result-type">' + escapeHtml(r.type) + '</span>' +
        '<span class="search-result-name">' + escapeHtml(r.name) + '</span>' +
        '<span class="search-result-detail">' + escapeHtml(r.detail) + '</span>' +
        '</a>';
    }).join('');
  }
  resultsBox.style.display = 'block';
}

document.addEventListener('DOMContentLoaded', initGlobalSearch);


// ─── Notificações (badge + painel dropdown) ───
var _notifData = [];
var _notifAlunosCache = {};

async function checkNotifications() {
  if (!window.sb) return;
  var userRole = window._cachedRole || null;

  // Assessoria: show only solicitation status notifications
  if (userRole === 'assessoria') {
    try {
      var userId = null;
      var userRes = await sb.auth.getUser();
      if (userRes.data && userRes.data.user) userId = userRes.data.user.id;
      if (!userId) { _notifData = []; return; }

      var notifications = [];
      // Solicitações recentemente atualizadas (últimos 7 dias)
      var weekAgo = new Date(); weekAgo.setDate(weekAgo.getDate() - 7);
      var { data: updated } = await sb.from('solicitacoes')
        .select('aluno_nome, status, updated_at')
        .eq('assessor_id', userId)
        .gte('updated_at', weekAgo.toISOString())
        .neq('status', 'aguardando')
        .order('updated_at', { ascending: false })
        .limit(10);

      var statusIcons = { desenvolvendo: '🔵', finalizado: '✅', finalizado_cobrar: '💰' };
      var statusTexts = { desenvolvendo: 'Em desenvolvimento', finalizado: 'Finalizado', finalizado_cobrar: 'Finalizado - cobrar' };
      (updated || []).forEach(function(s) {
        notifications.push({
          icon: statusIcons[s.status] || '📋',
          text: s.aluno_nome + ' — ' + (statusTexts[s.status] || s.status),
          sub: timeAgo(new Date(s.updated_at)),
          link: 'acompanhar.html',
          priority: s.status === 'finalizado_cobrar' ? 1 : 2
        });
      });

      _notifData = notifications;
      var badge = document.getElementById('notif-badge');
      if (badge) {
        if (notifications.length > 0) {
          badge.textContent = notifications.length > 99 ? '99+' : notifications.length;
          badge.style.display = 'flex';
        } else {
          badge.style.display = 'none';
        }
      }
    } catch(e) { _notifData = []; }
    return;
  }

  // Extensao: skip heavy notifications
  if (userRole === 'extensao') {
    _notifData = [];
    return;
  }

  try {
    // Load alunos cache
    if (Object.keys(_notifAlunosCache).length === 0) {
      var { data: alunos } = await sb.from('alunos').select('id, nome');
      if (alunos) {
        for (var i = 0; i < alunos.length; i++) {
          _notifAlunosCache[alunos[i].id] = alunos[i].nome;
        }
      }
    }

    var notifications = [];
    var now = new Date();
    var in3days = new Date(now);
    in3days.setDate(in3days.getDate() + 3);
    var in7days = new Date(now);
    in7days.setDate(in7days.getDate() + 7);

    // 1. Atividades Studeo vencendo nos próximos 3 dias (URGENTE)
    try {
      var { data: urgentes } = await sb.from('studeo_sync')
        .select('aluno_id, atividade, data_final, disciplina')
        .eq('respondida', false)
        .gte('data_final', now.toISOString())
        .lte('data_final', in3days.toISOString())
        .order('data_final', { ascending: true })
        .limit(10);
      (urgentes || []).forEach(function (u) {
        var deadline = new Date(u.data_final);
        var diffH = Math.ceil((deadline - now) / (1000*60*60));
        var tempo = diffH <= 24 ? 'Vence hoje!' : 'Vence em ' + Math.ceil(diffH/24) + 'd';
        notifications.push({
          icon: '🔴', text: (_notifAlunosCache[u.aluno_id] || 'Aluno') + ' — ' + (u.atividade || u.disciplina),
          sub: tempo, link: 'rastreio.html', priority: 1
        });
      });
    } catch(e) {}

    // 2. Atividades pendentes (tabela atividades)
    try {
      var { data: pendentes, count: pendCount } = await sb.from('atividades')
        .select('*', { count: 'exact' })
        .eq('status', 'pendente')
        .order('created_at', { ascending: false })
        .limit(5);
      if (pendCount > 0) {
        notifications.push({
          icon: '📋', text: pendCount + ' atividade' + (pendCount > 1 ? 's' : '') + ' pendente' + (pendCount > 1 ? 's' : ''),
          sub: 'Aguardando revisão', link: 'atividades.html', priority: 2
        });
      }
    } catch(e) {}

    // 3. Eventos da agenda nos próximos 7 dias
    try {
      var todayStr = now.toISOString().split('T')[0];
      var weekStr = in7days.toISOString().split('T')[0];
      var { data: eventos } = await sb.from('eventos_agenda')
        .select('titulo, data')
        .gte('data', todayStr)
        .lte('data', weekStr)
        .order('data', { ascending: true })
        .limit(5);
      (eventos || []).forEach(function (ev) {
        var evDate = new Date(ev.data + 'T00:00:00');
        var diffDays = Math.ceil((evDate - now) / (1000*60*60*24));
        var quando = diffDays <= 0 ? 'Hoje' : diffDays === 1 ? 'Amanhã' : 'Em ' + diffDays + ' dias';
        notifications.push({
          icon: '📅', text: ev.titulo, sub: quando, link: 'agenda.html', priority: 3
        });
      });
    } catch(e) {}

    // 4. Alunos sem sync (nunca sincronizados)
    try {
      var { data: allAlunos } = await sb.from('alunos').select('id').not('studeo_senha', 'is', null).neq('studeo_senha', '');
      var { data: synced } = await sb.from('studeo_sync').select('aluno_id');
      var syncedIds = {};
      (synced || []).forEach(function(s) { syncedIds[s.aluno_id] = true; });
      var naoSync = (allAlunos || []).filter(function(a) { return !syncedIds[a.id]; }).length;
      if (naoSync > 0) {
        notifications.push({
          icon: '🔄', text: naoSync + ' aluno' + (naoSync > 1 ? 's' : '') + ' nunca sincronizado' + (naoSync > 1 ? 's' : ''),
          sub: 'Clique para sincronizar', link: 'rastreio.html', priority: 4
        });
      }
    } catch(e) {}

    // Ordenar por prioridade
    notifications.sort(function(a, b) { return a.priority - b.priority; });
    _notifData = notifications;

    // Badge
    var badge = document.getElementById('notif-badge');
    var urgentCount = notifications.filter(function(n) { return n.priority <= 2; }).length;
    if (badge) {
      if (urgentCount > 0) {
        badge.textContent = urgentCount > 99 ? '99+' : urgentCount;
        badge.style.display = 'flex';
      } else {
        badge.style.display = 'none';
      }
    }
  } catch (e) {
    console.warn('[notif] Erro ao verificar:', e.message);
  }
}

function initNotifications() {
  var btn = document.getElementById('btn-notificacoes');
  if (!btn) return;

  // Create dropdown panel on body (avoid sidebar overflow clipping)
  var panel = document.createElement('div');
  panel.className = 'notif-panel';
  panel.id = 'notif-panel';
  panel.innerHTML = '<div class="notif-panel-header">Notificações</div><div class="notif-panel-body" id="notif-panel-body"></div>';
  document.body.appendChild(panel);

  function positionPanel() {
    var rect = btn.getBoundingClientRect();
    var panelHeight = panel.offsetHeight || 300;
    // Position above the button, aligned to left of sidebar
    var top = rect.top - panelHeight - 8;
    if (top < 8) top = 8; // don't go above viewport
    panel.style.left = rect.left + 'px';
    panel.style.top = top + 'px';
  }

  btn.addEventListener('click', function (e) {
    e.preventDefault();
    e.stopPropagation();
    var isOpen = panel.classList.contains('open');
    if (isOpen) {
      panel.classList.remove('open');
      return;
    }
    renderNotifPanel();
    panel.classList.add('open');
    positionPanel();
  });

  // Close on click outside
  document.addEventListener('click', function (e) {
    if (!panel.contains(e.target) && e.target !== btn && !btn.contains(e.target)) {
      panel.classList.remove('open');
    }
  });

  // Load notifications
  checkNotifications();
}

function renderNotifPanel() {
  var body = document.getElementById('notif-panel-body');
  if (!body) return;

  if (!_notifData.length) {
    body.innerHTML = '<div class="notif-empty">Tudo em dia! 🎉</div>';
    return;
  }

  var html = '';
  for (var i = 0; i < _notifData.length; i++) {
    var item = _notifData[i];
    var urgentClass = item.priority <= 1 ? ' notif-urgent' : '';

    html += '<a href="' + (item.link || '#') + '" class="notif-item' + urgentClass + '">';
    html += '<div class="notif-item-icon">' + item.icon + '</div>';
    html += '<div class="notif-item-content">';
    html += '<div class="notif-item-text">' + escapeHtml(item.text) + '</div>';
    html += '<div class="notif-item-time">' + escapeHtml(item.sub) + '</div>';
    html += '</div>';
    html += '</a>';
  }

  body.innerHTML = html;
}

function timeAgo(date) {
  var now = new Date();
  var diff = Math.floor((now - date) / 1000);
  if (diff < 60) return 'agora';
  if (diff < 3600) return Math.floor(diff / 60) + 'min atrás';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h atrás';
  if (diff < 604800) return Math.floor(diff / 86400) + 'd atrás';
  return date.toLocaleDateString('pt-BR');
}

document.addEventListener('DOMContentLoaded', initNotifications);


// ─── Supabase Realtime (notificações) ───
function subscribeToChanges(table, onInsert, onUpdate) {
  if (!window.sb) return;
  try {
    sb.channel('realtime-' + table)
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: table }, function (payload) {
        if (onInsert) onInsert(payload.new);
        showToast('Novo registro em ' + table, 'info');
      })
      .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: table }, function (payload) {
        if (onUpdate) onUpdate(payload.new);
      })
      .subscribe();
  } catch (e) {
    console.warn('[realtime] Não foi possível assinar:', e.message);
  }
}


// ─── Keyboard Shortcuts ───
document.addEventListener('keydown', function (e) {
  // Ignore if typing in input/textarea/select
  var tag = (e.target.tagName || '').toLowerCase();
  if (tag === 'input' || tag === 'textarea' || tag === 'select') {
    if (e.key === 'Escape') {
      e.target.blur();
      // Close any open modal
      var openModal = document.querySelector('.modal-overlay.open');
      if (openModal) openModal.classList.remove('open');
    }
    return;
  }

  // "/" → Focus global search
  if (e.key === '/') {
    e.preventDefault();
    var search = document.getElementById('global-search');
    if (search) search.focus();
  }

  // "n" → Open new item modal (context-dependent)
  if (e.key === 'n' || e.key === 'N') {
    var btn = document.getElementById('btn-novo-aluno') ||
              document.getElementById('btn-nova-atividade') ||
              document.getElementById('btn-novo-pagamento') ||
              document.getElementById('btn-novo-modulo');
    if (btn) { e.preventDefault(); btn.click(); }
  }

  // "Escape" → Close modal
  if (e.key === 'Escape') {
    var openModal = document.querySelector('.modal-overlay.open');
    if (openModal) openModal.classList.remove('open');
    var searchResults = document.getElementById('global-search-results');
    if (searchResults) searchResults.style.display = 'none';
  }

  // "d" → Go to Dashboard
  if (e.key === 'd') { window.location.href = 'app.html'; }

  // "?" → Show shortcuts help
  if (e.key === '?') {
    e.preventDefault();
    showShortcutsHelp();
  }
});

function showShortcutsHelp() {
  // Check if modal already exists
  var existing = document.getElementById('modal-shortcuts');
  if (existing) { existing.classList.add('open'); return; }

  var overlay = document.createElement('div');
  overlay.className = 'modal-overlay open';
  overlay.id = 'modal-shortcuts';
  overlay.innerHTML = '<div class="modal" style="max-width:400px;">' +
    '<div class="modal-header"><h3>Atalhos de Teclado</h3><button class="modal-close" onclick="document.getElementById(\'modal-shortcuts\').classList.remove(\'open\')">&times;</button></div>' +
    '<div class="modal-body">' +
    '<div style="display:flex;flex-direction:column;gap:12px;">' +
    shortcutRow('/', 'Buscar') +
    shortcutRow('N', 'Novo item') +
    shortcutRow('Esc', 'Fechar modal') +
    shortcutRow('D', 'Ir ao Dashboard') +
    shortcutRow('?', 'Mostrar atalhos') +
    '</div></div></div>';
  overlay.addEventListener('click', function (e) { if (e.target === overlay) overlay.classList.remove('open'); });
  document.body.appendChild(overlay);
}

function shortcutRow(key, desc) {
  return '<div style="display:flex;align-items:center;justify-content:space-between;">' +
    '<span style="font-size:0.9rem;color:var(--gray-600);">' + desc + '</span>' +
    '<kbd style="background:var(--gray-100);padding:4px 10px;border-radius:6px;font-family:monospace;font-size:0.85rem;font-weight:600;color:var(--gray-800);border:1px solid var(--gray-200);">' + key + '</kbd>' +
    '</div>';
}


// ─── Collapsible Sidebar Categories ───
document.addEventListener('DOMContentLoaded', function () {
  var labels = document.querySelectorAll('.sidebar-nav-label[data-category]');
  if (!labels.length) return;

  var stored = [];
  try { stored = JSON.parse(localStorage.getItem('sidebar-collapsed') || '[]'); } catch (e) {}

  // Find which category contains the active link — auto-expand it
  var activeLink = document.querySelector('.sidebar-category-links .sidebar-link.active');
  var activeCategory = null;
  if (activeLink) {
    var wrapper = activeLink.closest('.sidebar-category-links');
    if (wrapper && wrapper.previousElementSibling) {
      activeCategory = wrapper.previousElementSibling.getAttribute('data-category');
    }
  }
  if (activeCategory) {
    stored = stored.filter(function (c) { return c !== activeCategory; });
  }

  // Helper: set expanded max-height based on actual content
  function expandSection(el) {
    el.classList.remove('collapsed');
    el.style.maxHeight = el.scrollHeight + 'px';
    el.style.pointerEvents = '';
  }

  function collapseSection(el) {
    // Force current height first so transition works
    el.style.maxHeight = el.scrollHeight + 'px';
    // Force reflow
    el.offsetHeight; // eslint-disable-line no-unused-expressions
    el.classList.add('collapsed');
    el.style.maxHeight = '0px';
  }

  labels.forEach(function (label) {
    var cat = label.getAttribute('data-category');
    var alwaysOpen = label.getAttribute('data-always-open') === 'true';
    var linksDiv = label.nextElementSibling;

    if (alwaysOpen || !linksDiv || !linksDiv.classList.contains('sidebar-category-links')) return;

    // Apply initial state (no transition on first load)
    if (stored.indexOf(cat) !== -1) {
      label.classList.add('collapsed');
      linksDiv.classList.add('collapsed');
      linksDiv.style.maxHeight = '0px';
    } else {
      linksDiv.style.maxHeight = linksDiv.scrollHeight + 'px';
    }

    // After initial setup, listen for transitionend to clean up
    linksDiv.addEventListener('transitionend', function (e) {
      if (e.propertyName === 'max-height' && !linksDiv.classList.contains('collapsed')) {
        // After expanding, set to 'none' so content can grow dynamically
        linksDiv.style.maxHeight = 'none';
      }
    });

    // Toggle on click
    label.addEventListener('click', function () {
      var isCurrentlyCollapsed = label.classList.contains('collapsed');

      if (isCurrentlyCollapsed) {
        // Expand
        label.classList.remove('collapsed');
        expandSection(linksDiv);
      } else {
        // Collapse
        label.classList.add('collapsed');
        collapseSection(linksDiv);
      }

      // Persist state
      var current = [];
      try { current = JSON.parse(localStorage.getItem('sidebar-collapsed') || '[]'); } catch (e) {}
      if (!isCurrentlyCollapsed) {
        // Was open, now collapsing
        if (current.indexOf(cat) === -1) current.push(cat);
      } else {
        // Was collapsed, now expanding
        current = current.filter(function (c) { return c !== cat; });
      }
      localStorage.setItem('sidebar-collapsed', JSON.stringify(current));
    });
  });
});


// ─── Role-Based Sidebar Permissions ───

var PAGE_ACCESS = {
  admin: ['app', 'agenda', 'chat', 'alunos', 'importar', 'atividades', 'modulos', 'extensoes', 'kanban', 'financeiro', 'pedidos', 'relatorios', 'rastreio', 'audit', 'perfil', 'solicitar', 'acompanhar', 'depoimentos'],
  dono: ['app', 'agenda', 'chat', 'alunos', 'importar', 'atividades', 'modulos', 'extensoes', 'kanban', 'financeiro', 'pedidos', 'relatorios', 'rastreio', 'audit', 'perfil', 'solicitar', 'acompanhar', 'depoimentos'],
  extensao: ['chat', 'extensoes', 'solicitar', 'acompanhar', 'perfil'],
  assessoria: ['app', 'chat', 'solicitar', 'acompanhar', 'perfil'],
  assessor: ['app', 'agenda', 'chat', 'alunos', 'atividades', 'extensoes', 'kanban', 'perfil'],
  visualizador: ['app', 'agenda', 'perfil']
};

function setupSidebarPermissions(role) {
  if (!role) return;
  var allowed = PAGE_ACCESS[role] || [];

  // Hide sidebar links that aren't allowed
  document.querySelectorAll('.sidebar-link[href]').forEach(function (link) {
    var href = link.getAttribute('href');
    if (!href || href === '#') return;
    var page = href.replace('.html', '');
    if (allowed.indexOf(page) === -1) {
      link.classList.add('role-hidden');
    }
  });

  // Also hide sub-links containers if all children are hidden
  document.querySelectorAll('.sidebar-sub').forEach(function (sub) {
    var visibleLinks = sub.querySelectorAll('.sidebar-link:not(.role-hidden)');
    if (!visibleLinks.length) {
      sub.classList.add('role-hidden');
    }
  });

  // Hide empty categories (label + links div)
  document.querySelectorAll('.sidebar-category-links').forEach(function (cat) {
    var visibleLinks = cat.querySelectorAll('.sidebar-link:not(.role-hidden)');
    if (!visibleLinks.length) {
      cat.classList.add('role-hidden');
      var label = cat.previousElementSibling;
      if (label && label.classList.contains('sidebar-nav-label')) {
        label.classList.add('role-hidden');
      }
    }
  });

  // For limited roles: hide ALL category labels for a clean flat sidebar
  if (role === 'assessoria' || role === 'extensao') {
    document.querySelectorAll('.sidebar-nav-label').forEach(function (label) {
      label.classList.add('role-hidden');
    });
  }

  // Update role label in sidebar (use custom label if available)
  var roleEl = document.querySelector('.sidebar-user-role');
  if (roleEl) {
    var customLabel = typeof getUserLabel === 'function' ? getUserLabel() : null;
    roleEl.textContent = customLabel || (typeof getRoleLabel === 'function' ? getRoleLabel(role) : role);
  }

  // Hide delete buttons for assessoria/extensao (only admin/dono can delete)
  if (role !== 'admin' && role !== 'dono') {
    document.querySelectorAll('.btn-danger, .btn-icon.btn-danger').forEach(function (btn) {
      btn.classList.add('role-hidden');
    });
  }

  // Hide action buttons for visualizador
  if (role === 'visualizador') {
    document.querySelectorAll('.btn-gold, .btn-novo, [id^="btn-novo"], [id^="btn-nova"]').forEach(function (btn) {
      btn.classList.add('role-hidden');
    });
  }

  // Carregar avatar do usuário na sidebar
  loadSidebarAvatar();

  // Personalização para assessorias: mostra logo deles na sidebar
  if (role === 'assessoria') {
    document.documentElement.setAttribute('data-brand', 'assessoria');
    loadBrandLogo();
  }

  // Mostrar layout e esconder loader
  var layout = document.querySelector('.layout');
  if (layout) layout.classList.add('ready');
  var loader = document.getElementById('page-loader');
  if (loader) loader.classList.add('hide');
}

// ─── Brand Logo para Assessorias ───
function loadBrandLogo() {
  if (!window.sb) return;
  sb.auth.getUser().then(function(res) {
    if (!res.data || !res.data.user) return;
    var userId = res.data.user.id;
    sb.from('assessores').select('avatar_url, label').eq('id', userId).single().then(function(r) {
      if (!r.data) return;
      // Trocar logo na sidebar pelo logo da assessoria
      if (r.data.avatar_url) {
        var logoEl = document.querySelector('.sidebar-logo img');
        if (logoEl) {
          logoEl.src = r.data.avatar_url;
          logoEl.style.borderRadius = '50%';
          logoEl.style.objectFit = 'cover';
        }
      }
      // Trocar texto da sidebar pelo nome da assessoria
      if (r.data.label) {
        var brandText = document.querySelector('.sidebar-brand-text');
        if (brandText) {
          var shortName = r.data.label.replace('Assessoria ', '');
          brandText.innerHTML = shortName + '<br><small>Painel Assessoria</small>';
        }
      }
    }).catch(function() {});
  }).catch(function() {});
}

// ─── Sidebar Avatar (global) ───
function loadSidebarAvatar() {
  if (!window.sb) return;

  function applyAvatar(url) {
    var el = document.getElementById('user-avatar');
    if (!el) return;
    el.innerHTML = '<img src="' + url + '" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">';
  }

  // Busca user primeiro para cache por userId
  sb.auth.getUser().then(function(res) {
    if (!res.data || !res.data.user) return;
    var userId = res.data.user.id;
    var cacheKey = 'avatar-' + userId;

    // Limpa cache de outros users (troca de conta)
    for (var i = sessionStorage.length - 1; i >= 0; i--) {
      var k = sessionStorage.key(i);
      if (k && k.startsWith('avatar-') && k !== cacheKey) sessionStorage.removeItem(k);
    }
    // Remove cache antigo sem userId
    sessionStorage.removeItem('sidebar-avatar-url');

    function tryApply() {
      var cached = sessionStorage.getItem(cacheKey);
      if (cached) { applyAvatar(cached); return true; }
      return false;
    }

    if (tryApply()) {
      setTimeout(tryApply, 300);
      setTimeout(tryApply, 800);
      return;
    }

    // Busca do banco
    sb.from('assessores').select('avatar_url').eq('id', userId).single().then(function(r) {
      if (r.data && r.data.avatar_url) {
        sessionStorage.setItem(cacheKey, r.data.avatar_url);
        applyAvatar(r.data.avatar_url);
        setTimeout(function() { applyAvatar(r.data.avatar_url); }, 500);
        setTimeout(function() { applyAvatar(r.data.avatar_url); }, 1000);
      }
    }).catch(function() {});
  }).catch(function() {});
}


// ─── Pagination ───
var ITEMS_PER_PAGE = 20;

function paginateArray(arr, page) {
  var start = (page - 1) * ITEMS_PER_PAGE;
  return arr.slice(start, start + ITEMS_PER_PAGE);
}

function renderPagination(containerId, totalItems, currentPage, onPageChange) {
  var container = document.getElementById(containerId);
  if (!container) return;

  var totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
  if (totalPages <= 1) { container.innerHTML = ''; return; }

  var html = '<div class="pagination">';
  html += '<button class="page-btn" ' + (currentPage <= 1 ? 'disabled' : '') + ' onclick="' + onPageChange + '(' + (currentPage - 1) + ')">‹</button>';

  for (var i = 1; i <= totalPages; i++) {
    if (totalPages > 7 && i > 3 && i < totalPages - 2 && Math.abs(i - currentPage) > 1) {
      if (i === 4 || i === totalPages - 3) html += '<span class="page-dots">...</span>';
      continue;
    }
    html += '<button class="page-btn' + (i === currentPage ? ' active' : '') + '" onclick="' + onPageChange + '(' + i + ')">' + i + '</button>';
  }

  html += '<button class="page-btn" ' + (currentPage >= totalPages ? 'disabled' : '') + ' onclick="' + onPageChange + '(' + (currentPage + 1) + ')">›</button>';
  html += '<span class="page-info">' + totalItems + ' registros</span>';
  html += '</div>';
  container.innerHTML = html;
}


// ─── Audit Log Helper ───
function logAudit(action, tableName, recordId, details) {
  try {
    var user = window._cachedUser || null;
    var entry = {
      action: action,
      table_name: tableName,
      record_id: recordId || null,
      details: details || {}
    };
    if (user) {
      entry.user_id = user.id;
      entry.user_email = user.email || '';
    }
    // Fire-and-forget: don't await, don't block
    sb.from('audit_log').insert(entry).then(function () {}).catch(function (e) {
      console.warn('[audit] Erro ao registrar:', e.message);
    });
  } catch (e) {
    console.warn('[audit] logAudit error:', e.message);
  }
}


// ─── Filter Persistence ───
function saveFilterState(pageKey, filters) {
  try {
    localStorage.setItem('filters-' + pageKey, JSON.stringify(filters));
  } catch (e) {}
}

function loadFilterState(pageKey) {
  try {
    var saved = localStorage.getItem('filters-' + pageKey);
    if (saved) return JSON.parse(saved);
  } catch (e) {}
  return null;
}


// ─── Excel Export (via SheetJS) ───
function loadXLSX(callback) {
  if (window.XLSX) { callback(); return; }
  var s = document.createElement('script');
  s.src = 'https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js';
  s.onload = callback;
  s.onerror = function () { showToast('Erro ao carregar biblioteca Excel', 'error'); };
  document.head.appendChild(s);
}

function exportTableToExcel(tableId, filename) {
  loadXLSX(function () {
    var table = document.querySelector('#' + tableId);
    if (!table) table = document.querySelector('.table-wrap table');
    if (!table) { showToast('Nenhuma tabela encontrada', 'error'); return; }
    var wb = XLSX.utils.table_to_book(table, { sheet: 'Dados' });
    XLSX.writeFile(wb, (filename || 'relatorio') + '.xlsx');
    showToast('Excel exportado com sucesso!', 'success');
  });
}

// Export report with charts as images in PDF
function exportReportToPDF(title, filename, chartCanvasIds) {
  loadJsPDF(function () {
    var jsPDF = window.jspdf.jsPDF;
    var doc = new jsPDF('l', 'mm', 'a4');

    // Header
    doc.setFontSize(18);
    doc.setTextColor(26, 26, 46);
    doc.text(title || 'Relatorio', 14, 20);
    doc.setFontSize(10);
    doc.setTextColor(136, 146, 164);
    doc.text('Assessoria Academica — Gerado em ' + new Date().toLocaleDateString('pt-BR') + ' as ' + new Date().toLocaleTimeString('pt-BR'), 14, 28);

    var yPos = 36;

    // Add chart images
    if (chartCanvasIds && chartCanvasIds.length) {
      chartCanvasIds.forEach(function (canvasId) {
        var canvas = document.getElementById(canvasId);
        if (canvas) {
          try {
            var imgData = canvas.toDataURL('image/png');
            var pageW = doc.internal.pageSize.getWidth();
            var imgW = (pageW - 28) / 2;
            var imgH = imgW * 0.6;
            if (yPos + imgH > doc.internal.pageSize.getHeight() - 20) {
              doc.addPage();
              yPos = 20;
            }
            doc.addImage(imgData, 'PNG', 14, yPos, imgW, imgH);
            yPos += imgH + 10;
          } catch (e) {
            console.warn('[pdf] Erro ao adicionar grafico:', e.message);
          }
        }
      });
    }

    // Add tables
    var tables = document.querySelectorAll('.table-wrap table');
    tables.forEach(function (tableEl) {
      if (yPos > doc.internal.pageSize.getHeight() - 40) {
        doc.addPage();
        yPos = 20;
      }
      doc.autoTable({
        html: tableEl,
        startY: yPos,
        styles: { fontSize: 7, cellPadding: 2, lineColor: [200, 200, 200], lineWidth: 0.1 },
        headStyles: { fillColor: [26, 26, 46], textColor: [240, 192, 48], fontStyle: 'bold', fontSize: 7 },
        alternateRowStyles: { fillColor: [248, 249, 252] }
      });
      yPos = doc.lastAutoTable.finalY + 10;
    });

    // Footer
    var pageCount = doc.internal.getNumberOfPages();
    for (var i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text('Pagina ' + i + ' de ' + pageCount, doc.internal.pageSize.getWidth() - 30, doc.internal.pageSize.getHeight() - 10);
    }

    doc.save((filename || 'relatorio') + '.pdf');
    showToast('PDF com graficos exportado!', 'success');
  });
}


// ─── Shared Helpers (centralizados) ───

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function formatTipo(t) {
  var map = { atividade: 'Atividade', mapa: 'Mapa', tcc: 'TCC', relatorio: 'Relatório', extensao: 'Extensão', pacote: 'Pacote', avulso: 'Avulso', mensalidade: 'Mensalidade' };
  return map[t] || t || '';
}

function formatStatus(s) {
  var map = { pendente: 'Pendente', em_andamento: 'Em Andamento', entregue: 'Entregue', revisao: 'Revisão', pago: 'Pago', atrasado: 'Atrasado', cancelado: 'Cancelado' };
  return map[s] || s || '';
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('pt-BR');
}

// Debounce genérico
function debounce(fn, delay) {
  var timer;
  return function () {
    var ctx = this;
    var args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function () { fn.apply(ctx, args); }, delay);
  };
}
