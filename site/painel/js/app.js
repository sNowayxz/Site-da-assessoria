/* ═══════════════════════════════════════════
   Dashboard — Lógica principal
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async function () {
  var user = await requireAuth();
  if (!user) return;

  // User info
  document.getElementById('user-name').textContent = getUserName(user);

  // Logout
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

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
  var ctx = document.getElementById('chart-status');
  if (!ctx) return;
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  new Chart(ctx, {
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
  var ctx = document.getElementById('chart-receita');
  if (!ctx) return;
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';

  try {
    var { data: pagamentos } = await sb.from('pagamentos').select('valor, status, dt_pagamento, created_at');
    var pagos = (pagamentos || []).filter(function(p) { return p.status === 'pago'; });

    // Agrupar por mês
    var meses = {};
    var now = new Date();
    for (var i = 5; i >= 0; i--) {
      var d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      var key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      meses[key] = 0;
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

    var labels = Object.keys(meses).map(function(k) {
      var parts = k.split('-');
      var monthNames = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
      return monthNames[parseInt(parts[1]) - 1] + '/' + parts[0].slice(2);
    });
    var values = Object.values(meses);

    new Chart(ctx, {
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
    // Tabela pagamentos pode não existir
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
