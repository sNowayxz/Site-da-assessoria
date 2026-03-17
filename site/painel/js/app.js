/* ═══════════════════════════════════════════
   Dashboard — Lógica principal
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'assessor', 'visualizador']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  // User info
  document.getElementById('user-name').textContent = getUserName(user);

  // Logout
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Hide action buttons for visualizador
  if (role === 'visualizador') {
    document.querySelectorAll('.btn-gold, .btn-export, .kanban-card[draggable]').forEach(function(el) { el.style.display = 'none'; });
  }

  // Load dashboard data
  await loadDashboard();
});

async function loadDashboard() {
  try {
    // Contadores de atividades
    var { count: totalAlunos } = await sb.from('alunos').select('*', { count: 'exact', head: true });
    var { count: pendentes } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'pendente');
    var { count: emAndamento } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'em_andamento');
    var { count: entregues } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'entregue');

    document.getElementById('count-alunos').textContent = totalAlunos || 0;
    document.getElementById('count-pendentes').textContent = pendentes || 0;
    document.getElementById('count-andamento').textContent = emAndamento || 0;
    document.getElementById('count-entregues').textContent = entregues || 0;

    // Receita financeira (se tabela existir)
    try {
      var { data: pagos } = await sb.from('pagamentos').select('valor').eq('status', 'pago');
      var { data: pendPag } = await sb.from('pagamentos').select('valor').eq('status', 'pendente');

      var totalRecebido = (pagos || []).reduce(function (sum, p) { return sum + (parseFloat(p.valor) || 0); }, 0);
      var totalPendenteFin = (pendPag || []).reduce(function (sum, p) { return sum + (parseFloat(p.valor) || 0); }, 0);

      var elRec = document.getElementById('dash-receita');
      var elPen = document.getElementById('dash-pendente-fin');
      if (elRec) elRec.textContent = 'R$ ' + totalRecebido.toFixed(2);
      if (elPen) elPen.textContent = 'R$ ' + totalPendenteFin.toFixed(2);
    } catch (e) {
      // Tabela pagamentos pode não existir ainda
    }

    // Últimas atividades
    var { data: ultimas } = await sb
      .from('atividades')
      .select('*, alunos(nome, ra)')
      .order('created_at', { ascending: false })
      .limit(10);

    renderRecentActivities(ultimas || []);

    // Charts
    renderStatusChart(pendentes || 0, emAndamento || 0, entregues || 0);
    await renderReceitaChart();
  } catch (e) {
    console.error('Erro ao carregar dashboard:', e);
  }
}

function renderRecentActivities(atividades) {
  var tbody = document.getElementById('recent-activities');
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

  var container = canvas.parentElement;
  var emptyMsg = document.getElementById('chart-status-empty');

  // Se tudo zero, mostra mensagem vazia
  if (!pendentes && !andamento && !entregues) {
    canvas.style.display = 'none';
    if (emptyMsg) emptyMsg.style.display = 'block';
    return;
  }

  // Tem dados — garante canvas visível
  canvas.style.display = 'block';
  if (emptyMsg) emptyMsg.style.display = 'none';

  if (typeof Chart === 'undefined') return;

  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  chartStatusInstance = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Pendentes', 'Em Andamento', 'Entregues'],
      datasets: [{
        data: [pendentes, andamento, entregues],
        backgroundColor: ['#f59e0b', '#3b82f6', '#22c55e'],
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: isDark ? '#8b949e' : '#4a5568', padding: 16, usePointStyle: true, pointStyleWidth: 10 }
        }
      },
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
    if (error) { console.warn('Erro pagamentos chart:', error.message); return; }

    var pagos = (pagamentos || []).filter(function(p) { return p.status === 'pago'; });

    // Se não tem nenhum pagamento pago, mostra estado vazio
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

    // Agrupar por mês (últimos 6 meses)
    var meses = {};
    var keys = [];
    var now = new Date();
    for (var i = 5; i >= 0; i--) {
      var d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      var key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      meses[key] = 0;
      keys.push(key);
    }

    pagos.forEach(function(p) {
      var dt = p.dt_pagamento || p.created_at;
      if (!dt) return;
      var d = new Date(dt);
      var key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      if (meses.hasOwnProperty(key)) {
        meses[key] += Number(p.valor) || 0;
      }
    });

    var monthNames = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
    var labels = keys.map(function(k) {
      var parts = k.split('-');
      return monthNames[parseInt(parts[1]) - 1] + '/' + parts[0].slice(2);
    });
    var values = keys.map(function(k) { return meses[k]; });

    chartReceitaInstance = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Receita (R$)',
          data: values,
          backgroundColor: 'rgba(240,192,48,0.7)',
          borderColor: '#f0c030',
          borderWidth: 1,
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: isDark ? '#21262d' : '#eef1f6' },
            ticks: { color: isDark ? '#8b949e' : '#8892a4', callback: function(v) { return 'R$ ' + v; } }
          },
          x: {
            grid: { display: false },
            ticks: { color: isDark ? '#8b949e' : '#8892a4' }
          }
        }
      }
    });
  } catch (e) {
    console.warn('Erro ao renderizar chart receita:', e);
  }
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
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ═══════════════════════════════════════════
// PERIOD SELECTOR
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

  // Notification badge
  checkNotifications();

  // Dynamic favicon
  updateFaviconBadge();
});

async function refreshCharts() {
  // Destroy existing charts
  if (chartStatusInstance) { chartStatusInstance.destroy(); chartStatusInstance = null; }
  if (chartReceitaInstance) { chartReceitaInstance.destroy(); chartReceitaInstance = null; }

  var dateFilter = '';
  if (currentPeriod > 0) {
    var since = new Date();
    since.setDate(since.getDate() - currentPeriod);
    dateFilter = '&created_at=gte.' + since.toISOString();
  }

  try {
    var { count: pendentes } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'pendente');
    var { count: emAndamento } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'em_andamento');
    var { count: entregues } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'entregue');

    renderStatusChart(pendentes || 0, emAndamento || 0, entregues || 0);
    await renderReceitaChart();
  } catch (e) {
    console.warn('Erro ao atualizar charts:', e);
  }
}

async function checkNotifications() {
  try {
    var { count } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'pendente');
    var badge = document.getElementById('notif-badge');
    if (badge && count > 0) {
      badge.textContent = count;
      badge.style.display = 'flex';
    }
  } catch (e) { /* silent */ }
}

function updateFaviconBadge() {
  try {
    var badge = document.getElementById('notif-badge');
    if (!badge) return;
    var count = parseInt(badge.textContent) || 0;
    if (count <= 0) return;

    var favicon = document.querySelector('link[rel="icon"]');
    if (!favicon) return;

    var img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = function () {
      var canvas = document.createElement('canvas');
      canvas.width = 32;
      canvas.height = 32;
      var ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, 32, 32);

      // Draw badge
      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(24, 8, 8, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = 'white';
      ctx.font = 'bold 10px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(count > 9 ? '9+' : String(count), 24, 8);

      favicon.href = canvas.toDataURL('image/png');
    };
    img.src = favicon.href;
  } catch (e) { /* silent */ }
}

// ═══════════════════════════════════════════
// KANBAN BOARD
// ═══════════════════════════════════════════
async function loadKanban() {
  try {
    var { data: atividades } = await sb
      .from('atividades')
      .select('id, tipo, descricao, status, created_at, alunos(nome)')
      .in('status', ['pendente', 'em_andamento', 'entregue'])
      .order('created_at', { ascending: false })
      .limit(30);

    if (!atividades) return;

    var columns = { pendente: [], em_andamento: [], entregue: [] };
    atividades.forEach(function (a) {
      if (columns[a.status]) columns[a.status].push(a);
    });

    ['pendente', 'em_andamento', 'entregue'].forEach(function (status) {
      var container = document.getElementById('kanban-cards-' + status);
      var countEl = document.getElementById('kanban-count-' + status);
      if (!container) return;

      if (countEl) countEl.textContent = columns[status].length;

      container.innerHTML = columns[status].slice(0, 10).map(function (a) {
        var aluno = a.alunos ? a.alunos.nome : '—';
        return '<div class="kanban-card" draggable="true" data-id="' + a.id + '">' +
          '<div class="kanban-card-title">' + escapeHtml(a.descricao || a.tipo) + '</div>' +
          '<div class="kanban-card-meta">' + escapeHtml(aluno) + ' · ' + formatDate(a.created_at) + '</div>' +
          '</div>';
      }).join('');
    });

    initKanbanDragDrop();
  } catch (e) {
    console.warn('Erro kanban:', e);
  }
}

function initKanbanDragDrop() {
  var cards = document.querySelectorAll('.kanban-card');
  var columns = document.querySelectorAll('.kanban-column');

  cards.forEach(function (card) {
    card.addEventListener('dragstart', function (e) {
      e.dataTransfer.setData('text/plain', card.getAttribute('data-id'));
      card.classList.add('dragging');
    });
    card.addEventListener('dragend', function () {
      card.classList.remove('dragging');
      columns.forEach(function (col) { col.classList.remove('drag-over'); });
    });
  });

  columns.forEach(function (column) {
    column.addEventListener('dragover', function (e) {
      e.preventDefault();
      column.classList.add('drag-over');
    });
    column.addEventListener('dragleave', function () {
      column.classList.remove('drag-over');
    });
    column.addEventListener('drop', async function (e) {
      e.preventDefault();
      column.classList.remove('drag-over');
      var id = e.dataTransfer.getData('text/plain');
      var newStatus = column.getAttribute('data-status');

      try {
        await sb.from('atividades').update({ status: newStatus }).eq('id', id);
        showToast('Status atualizado para ' + formatStatus(newStatus), 'success');
        loadKanban();
        loadDashboard();
      } catch (err) {
        showToast('Erro ao atualizar status', 'error');
      }
    });
  });
}

// Call loadKanban after loadDashboard
document.addEventListener('DOMContentLoaded', function () {
  setTimeout(loadKanban, 500);
});
