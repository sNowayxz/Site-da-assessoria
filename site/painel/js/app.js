/* ═══════════════════════════════════════════
   Dashboard — Lógica principal v2
   Suporta: admin/dono (full) + assessoria (mini)
   ═══════════════════════════════════════════ */

var _dashRole = null;
var _dashUserId = null;

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'dono', 'assessor', 'visualizador', 'assessoria']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  _dashRole = role;
  _dashUserId = user.id;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  if (role === 'visualizador') {
    document.querySelectorAll('.btn-gold, .btn-export, .kanban-card[draggable]').forEach(function(el) { el.style.display = 'none'; });
  }

  if (role === 'assessoria') {
    await loadAssessoriaDashboard(user.id);
  } else {
    await loadDashboard();
  }
});

// ═══════════════════════════════════════════
// ASSESSORIA MINI-DASHBOARD
// ═══════════════════════════════════════════
async function loadAssessoriaDashboard(userId) {
  var mainContent = document.querySelector('.main-content');
  var topbar = mainContent.querySelector('.topbar');

  // Remove everything after topbar
  var allChildren = Array.from(mainContent.children);
  allChildren.forEach(function(child) {
    if (child !== topbar) child.remove();
  });

  var h1 = topbar.querySelector('h1');
  if (h1) h1.textContent = 'Meu Painel';

  var container = document.createElement('div');
  container.style.padding = '0 24px 24px';
  container.innerHTML = '<div id="assessoria-dash"></div>';
  mainContent.appendChild(container);

  var dashEl = document.getElementById('assessoria-dash');

  try {
    var { data: solics, error } = await sb.from('solicitacoes')
      .select('*')
      .eq('assessor_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw error;
    var items = solics || [];

    var total = items.length;
    var aguardando = items.filter(function(s) { return s.status === 'aguardando'; }).length;
    var desenvolvendo = items.filter(function(s) { return s.status === 'desenvolvendo'; }).length;
    var finalizado = items.filter(function(s) { return s.status === 'finalizado' || s.status === 'finalizado_cobrar'; }).length;
    var totalHoras = items.reduce(function(sum, s) { return sum + (s.horas || 0); }, 0);
    var totalValor = items.reduce(function(sum, s) { return sum + (s.valor_pago || 0); }, 0);

    var html = '';

    // Stats
    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin-bottom:24px;">';
    html += statCard(total, 'Solicitações', 'var(--gold)');
    html += statCard(aguardando, 'Aguardando', '#f59e0b');
    html += statCard(desenvolvendo, 'Desenvolvendo', '#3b82f6');
    html += statCard(finalizado, 'Finalizados', '#22c55e');
    html += statCard(totalHoras + 'h', 'Total Horas', 'var(--gray-600)');
    html += statCard('R$ ' + totalValor.toFixed(0), 'Valor Total', 'var(--gold)');
    html += '</div>';

    // Quick actions
    html += '<div style="display:flex;gap:10px;margin-bottom:24px;flex-wrap:wrap;">';
    html += '<a href="solicitar.html" style="padding:10px 20px;background:var(--gold);color:var(--dark);border-radius:8px;font-weight:700;font-size:0.88rem;text-decoration:none;transition:filter 0.2s;">➕ Nova Solicitação</a>';
    html += '<a href="acompanhar.html" style="padding:10px 20px;background:var(--gray-100);color:var(--gray-700);border-radius:8px;font-weight:600;font-size:0.88rem;text-decoration:none;">📊 Acompanhar</a>';
    html += '<a href="chat.html" style="padding:10px 20px;background:var(--gray-100);color:var(--gray-700);border-radius:8px;font-weight:600;font-size:0.88rem;text-decoration:none;">💬 Chat</a>';
    html += '</div>';

    // Recent solicitations table
    html += '<div style="background:var(--white);border-radius:12px;box-shadow:var(--shadow);overflow:hidden;">';
    html += '<div style="padding:16px 20px;border-bottom:1px solid var(--gray-100);font-weight:700;font-size:0.95rem;color:var(--gray-800);">Minhas Solicitações Recentes</div>';

    if (!items.length) {
      html += '<div style="padding:40px 20px;text-align:center;color:var(--gray-400);">Nenhuma solicitação ainda. <a href="solicitar.html" style="color:var(--gold);font-weight:600;">Criar primeira</a></div>';
    } else {
      html += '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.85rem;">';
      html += '<thead><tr style="background:var(--gray-50);">';
      html += '<th style="padding:10px 14px;text-align:left;font-size:0.75rem;font-weight:700;color:var(--gray-500);text-transform:uppercase;">Status</th>';
      html += '<th style="padding:10px 14px;text-align:left;font-size:0.75rem;font-weight:700;color:var(--gray-500);text-transform:uppercase;">Aluno</th>';
      html += '<th style="padding:10px 14px;text-align:center;font-size:0.75rem;font-weight:700;color:var(--gray-500);text-transform:uppercase;">Horas</th>';
      html += '<th style="padding:10px 14px;text-align:center;font-size:0.75rem;font-weight:700;color:var(--gray-500);text-transform:uppercase;">Evolução</th>';
      html += '<th style="padding:10px 14px;text-align:right;font-size:0.75rem;font-weight:700;color:var(--gray-500);text-transform:uppercase;">Data</th>';
      html += '</tr></thead><tbody>';

      var STATUS_MAP = { aguardando: 'Aguardando', desenvolvendo: 'Desenvolvendo', finalizado: 'Finalizado', finalizado_cobrar: 'A Cobrar' };
      var STATUS_COLORS = { aguardando: '#f59e0b', desenvolvendo: '#3b82f6', finalizado: '#22c55e', finalizado_cobrar: '#7c3aed' };

      items.slice(0, 10).forEach(function(s) {
        var st = s.status || 'aguardando';
        var color = STATUS_COLORS[st] || '#6b7280';
        var horas = s.horas || 0;
        var validadas = s.horas_validadas || 0;
        var pct = horas > 0 ? Math.min(100, Math.round((validadas / horas) * 100)) : 0;
        var dt = new Date(s.created_at).toLocaleDateString('pt-BR');

        html += '<tr style="border-bottom:1px solid var(--gray-100);">';
        html += '<td style="padding:10px 14px;"><span style="display:inline-block;padding:3px 10px;border-radius:12px;font-size:0.72rem;font-weight:700;background:' + color + '20;color:' + color + ';">' + (STATUS_MAP[st] || st) + '</span></td>';
        html += '<td style="padding:10px 14px;font-weight:600;">' + escapeHtml(s.aluno_nome) + '</td>';
        html += '<td style="padding:10px 14px;text-align:center;">' + validadas + '/' + horas + 'h</td>';
        html += '<td style="padding:10px 14px;text-align:center;"><div style="width:80px;height:16px;background:var(--gray-100);border-radius:8px;overflow:hidden;display:inline-block;position:relative;"><div style="height:100%;border-radius:8px;background:linear-gradient(90deg,var(--gold),#f59e0b);width:' + pct + '%;transition:width 0.3s;"></div><span style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:0.68rem;font-weight:700;">' + (pct > 0 ? pct + '%' : '') + '</span></div></td>';
        html += '<td style="padding:10px 14px;text-align:right;font-size:0.78rem;color:var(--gray-400);">' + dt + '</td>';
        html += '</tr>';
      });

      html += '</tbody></table></div>';
    }
    html += '</div>';

    dashEl.innerHTML = html;
  } catch (e) {
    console.error('[assessoria-dash]', e);
    dashEl.innerHTML = '<div style="padding:40px;text-align:center;color:var(--gray-400);">Erro ao carregar dados.</div>';
  }
}

function statCard(value, label, color) {
  return '<div style="background:var(--white);border-radius:12px;padding:16px 20px;box-shadow:var(--shadow);text-align:center;">'
    + '<div style="font-size:1.6rem;font-weight:800;color:' + color + ';">' + value + '</div>'
    + '<div style="font-size:0.72rem;color:var(--gray-500);font-weight:600;text-transform:uppercase;letter-spacing:0.03em;">' + label + '</div>'
    + '</div>';
}

// ═══════════════════════════════════════════
// ADMIN/DONO FULL DASHBOARD
// ═══════════════════════════════════════════
async function loadDashboard() {
  try {
    var counters = await Promise.all([
      sb.from('alunos').select('*', { count: 'exact', head: true }),
      sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'pendente'),
      sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'em_andamento'),
      sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'entregue')
    ]);
    var totalAlunos = counters[0].count;
    var pendentes = counters[1].count;
    var emAndamento = counters[2].count;
    var entregues = counters[3].count;

    var el1 = document.getElementById('count-alunos');
    var el2 = document.getElementById('count-pendentes');
    var el3 = document.getElementById('count-andamento');
    var el4 = document.getElementById('count-entregues');
    if (el1) el1.textContent = totalAlunos || 0;
    if (el2) el2.textContent = pendentes || 0;
    if (el3) el3.textContent = emAndamento || 0;
    if (el4) el4.textContent = entregues || 0;

    try {
      var finResults = await Promise.all([
        sb.from('pagamentos').select('valor').eq('status', 'pago'),
        sb.from('pagamentos').select('valor').eq('status', 'pendente')
      ]);
      var pagos = finResults[0].data;
      var pendPag = finResults[1].data;
      var totalRecebido = (pagos || []).reduce(function (sum, p) { return sum + (parseFloat(p.valor) || 0); }, 0);
      var totalPendenteFin = (pendPag || []).reduce(function (sum, p) { return sum + (parseFloat(p.valor) || 0); }, 0);
      var elRec = document.getElementById('dash-receita');
      var elPen = document.getElementById('dash-pendente-fin');
      if (elRec) elRec.textContent = 'R$ ' + totalRecebido.toFixed(2);
      if (elPen) elPen.textContent = 'R$ ' + totalPendenteFin.toFixed(2);
    } catch (e) {}

    var { data: ultimas } = await sb
      .from('atividades')
      .select('*, alunos(nome, ra)')
      .order('created_at', { ascending: false })
      .limit(10);

    renderRecentActivities(ultimas || []);
    renderStatusChart(pendentes || 0, emAndamento || 0, entregues || 0);
    await renderReceitaChart();
  } catch (e) {
    console.error('Erro ao carregar dashboard:', e);
  }
}

function renderRecentActivities(atividades) {
  var tbody = document.getElementById('recent-activities');
  if (!tbody) return;
  if (!atividades.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nenhuma atividade registrada</td></tr>';
    return;
  }
  tbody.innerHTML = atividades.map(function (a) {
    var aluno = a.alunos || {};
    return '<tr>' +
      '<td>' + escapeHtml(aluno.nome || '—') + '</td>' +
      '<td><span class="badge badge-tipo">' + escapeHtml(a.tipo) + '</span></td>' +
      '<td>' + escapeHtml(a.descricao || '—') + '</td>' +
      '<td><span class="badge badge-' + a.status + '">' + formatStatus(a.status) + '</span></td>' +
      '<td>' + formatDate(a.created_at) + '</td>' +
      '</tr>';
  }).join('');
}

function renderStatusChart(pendentes, andamento, entregues) {
  var canvas = document.getElementById('chart-status');
  if (!canvas) return;
  var emptyMsg = document.getElementById('chart-status-empty');
  if (!pendentes && !andamento && !entregues) {
    canvas.style.display = 'none';
    if (emptyMsg) emptyMsg.style.display = 'block';
    return;
  }
  canvas.style.display = 'block';
  if (emptyMsg) emptyMsg.style.display = 'none';
  if (typeof Chart === 'undefined') return;
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  if (chartStatusInstance) { chartStatusInstance.destroy(); chartStatusInstance = null; }
  chartStatusInstance = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Pendentes', 'Em Andamento', 'Entregues'],
      datasets: [{ data: [pendentes, andamento, entregues], backgroundColor: ['#f59e0b', '#3b82f6', '#22c55e'], borderWidth: 0, hoverOffset: 8 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { color: isDark ? '#8b949e' : '#4a5568', padding: 16, usePointStyle: true, pointStyleWidth: 10 } } },
      cutout: '65%'
    }
  });
}

async function renderReceitaChart() {
  var canvas = document.getElementById('chart-receita');
  if (!canvas) return;
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  try {
    var { data: pagamentos, error } = await sb.from('pagamentos').select('valor, status, dt_pagamento, created_at');
    if (error) return;
    var pagos = (pagamentos || []).filter(function(p) { return p.status === 'pago'; });
    if (!pagos.length) {
      canvas.style.display = 'none';
      var emptyEl = document.getElementById('chart-receita-empty');
      if (emptyEl) emptyEl.style.display = 'block';
      return;
    }
    canvas.style.display = 'block';
    var emptyEl2 = document.getElementById('chart-receita-empty');
    if (emptyEl2) emptyEl2.style.display = 'none';
    if (typeof Chart === 'undefined') return;

    var meses = {}; var keys = []; var now = new Date();
    for (var i = 5; i >= 0; i--) {
      var d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      var key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      meses[key] = 0; keys.push(key);
    }
    pagos.forEach(function(p) {
      var dt = p.dt_pagamento || p.created_at; if (!dt) return;
      var d2 = new Date(dt);
      var k = d2.getFullYear() + '-' + String(d2.getMonth() + 1).padStart(2, '0');
      if (meses.hasOwnProperty(k)) meses[k] += Number(p.valor) || 0;
    });
    var monthNames = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
    var labels = keys.map(function(k) { var p = k.split('-'); return monthNames[parseInt(p[1]) - 1] + '/' + p[0].slice(2); });
    var values = keys.map(function(k) { return meses[k]; });
    if (chartReceitaInstance) { chartReceitaInstance.destroy(); chartReceitaInstance = null; }
    chartReceitaInstance = new Chart(canvas, {
      type: 'bar',
      data: { labels: labels, datasets: [{ label: 'Receita (R$)', data: values, backgroundColor: 'rgba(240,192,48,0.7)', borderColor: '#f0c030', borderWidth: 1, borderRadius: 6, borderSkipped: false }] },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: isDark ? '#21262d' : '#eef1f6' }, ticks: { color: isDark ? '#8b949e' : '#8892a4', callback: function(v) { return 'R$ ' + v; } } },
          x: { grid: { display: false }, ticks: { color: isDark ? '#8b949e' : '#8892a4' } }
        }
      }
    });
  } catch (e) { console.warn('Erro chart receita:', e); }
}

// ═══════════════════════════════════════════
// PERIOD SELECTOR (fixed — filters by date)
// ═══════════════════════════════════════════
var currentPeriod = 7;
var chartStatusInstance = null;
var chartReceitaInstance = null;

document.addEventListener('DOMContentLoaded', function () {
  var periodSelector = document.getElementById('period-selector');
  if (periodSelector) {
    periodSelector.addEventListener('click', function (e) {
      var btn = e.target.closest('.period-btn');
      if (!btn) return;
      periodSelector.querySelectorAll('.period-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      currentPeriod = parseInt(btn.getAttribute('data-period'));
      refreshCharts();
    });
  }
  updateFaviconBadge();
});

async function refreshCharts() {
  if (chartStatusInstance) { chartStatusInstance.destroy(); chartStatusInstance = null; }
  if (chartReceitaInstance) { chartReceitaInstance.destroy(); chartReceitaInstance = null; }
  try {
    var q1 = sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'pendente');
    var q2 = sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'em_andamento');
    var q3 = sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'entregue');
    if (currentPeriod > 0) {
      var since = new Date(); since.setDate(since.getDate() - currentPeriod);
      var sinceISO = since.toISOString();
      q1 = q1.gte('created_at', sinceISO);
      q2 = q2.gte('created_at', sinceISO);
      q3 = q3.gte('created_at', sinceISO);
    }
    var results = await Promise.all([q1, q2, q3]);
    renderStatusChart(results[0].count || 0, results[1].count || 0, results[2].count || 0);
    await renderReceitaChart();
  } catch (e) { console.warn('Erro charts:', e); }
}

// ═══════════════════════════════════════════
// DYNAMIC FAVICON WITH BADGE
// ═══════════════════════════════════════════
function updateFaviconBadge() {
  setTimeout(function() {
    try {
      var badge = document.getElementById('notif-badge');
      if (!badge) return;
      var count = parseInt(badge.textContent) || 0;
      if (count <= 0) return;
      var link = document.querySelector('link[rel="icon"]');
      if (!link) { link = document.createElement('link'); link.rel = 'icon'; document.head.appendChild(link); }
      var canvas = document.createElement('canvas');
      canvas.width = 32; canvas.height = 32;
      var ctx = canvas.getContext('2d');
      ctx.fillStyle = '#f0c030'; ctx.beginPath(); ctx.arc(16, 16, 14, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#1a1a2e'; ctx.font = 'bold 16px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('A', 16, 17);
      ctx.fillStyle = '#ef4444'; ctx.beginPath(); ctx.arc(26, 6, 7, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'white'; ctx.font = 'bold 9px Arial'; ctx.fillText(count > 9 ? '9+' : String(count), 26, 7);
      link.href = canvas.toDataURL('image/png');
    } catch (e) {}
  }, 3000);
}

// ═══════════════════════════════════════════
// KANBAN BOARD
// ═══════════════════════════════════════════
async function loadKanban() {
  if (_dashRole === 'assessoria') return;
  try {
    var { data: atividades } = await sb
      .from('atividades')
      .select('id, tipo, descricao, status, created_at, alunos(nome)')
      .in('status', ['pendente', 'em_andamento', 'entregue'])
      .order('created_at', { ascending: false })
      .limit(30);
    if (!atividades) return;
    var columns = { pendente: [], em_andamento: [], entregue: [] };
    atividades.forEach(function (a) { if (columns[a.status]) columns[a.status].push(a); });
    ['pendente', 'em_andamento', 'entregue'].forEach(function (status) {
      var container = document.getElementById('kanban-cards-' + status);
      var countEl = document.getElementById('kanban-count-' + status);
      if (!container) return;
      if (countEl) countEl.textContent = columns[status].length;
      container.innerHTML = columns[status].slice(0, 10).map(function (a) {
        var aluno = a.alunos ? a.alunos.nome : '—';
        return '<div class="kanban-card" draggable="true" data-id="' + a.id + '">'
          + '<div class="kanban-card-title">' + escapeHtml(a.descricao || a.tipo) + '</div>'
          + '<div class="kanban-card-meta">' + escapeHtml(aluno) + ' · ' + formatDate(a.created_at) + '</div>'
          + '</div>';
      }).join('');
    });
    initKanbanDragDrop();
  } catch (e) { console.warn('Erro kanban:', e); }
}

function initKanbanDragDrop() {
  document.querySelectorAll('.kanban-card').forEach(function (card) {
    card.addEventListener('dragstart', function (e) {
      e.dataTransfer.setData('text/plain', card.getAttribute('data-id'));
      card.classList.add('dragging');
    });
    card.addEventListener('dragend', function () {
      card.classList.remove('dragging');
      document.querySelectorAll('.kanban-column').forEach(function (col) { col.classList.remove('drag-over'); });
    });
  });
  document.querySelectorAll('.kanban-column').forEach(function (column) {
    column.addEventListener('dragover', function (e) { e.preventDefault(); column.classList.add('drag-over'); });
    column.addEventListener('dragleave', function () { column.classList.remove('drag-over'); });
    column.addEventListener('drop', async function (e) {
      e.preventDefault(); column.classList.remove('drag-over');
      var id = e.dataTransfer.getData('text/plain');
      var newStatus = column.getAttribute('data-status');
      try {
        await sb.from('atividades').update({ status: newStatus }).eq('id', id);
        showToast('Status atualizado para ' + formatStatus(newStatus), 'success');
        loadKanban(); loadDashboard();
      } catch (err) { showToast('Erro ao atualizar status', 'error'); }
    });
  });
}

document.addEventListener('DOMContentLoaded', function () {
  setTimeout(loadKanban, 500);
});
