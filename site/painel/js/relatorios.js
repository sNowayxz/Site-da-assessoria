/* ═══════════════════════════════════════════
   Relatórios — Analytics & Reports
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async function () {
  var user = await requireAuth();
  if (!user) return;

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  await loadRelatorios();
});

async function loadRelatorios() {
  try {
    // Fetch all data in parallel
    var [atvRes, pagRes, aluRes, pedRes] = await Promise.all([
      sb.from('atividades').select('*, alunos(nome)'),
      sb.from('pagamentos').select('*'),
      sb.from('alunos').select('*'),
      sb.from('pedidos_extensao').select('*')
    ]);

    var atividades = atvRes.data || [];
    var pagamentos = pagRes.data || [];
    var alunos = aluRes.data || [];
    var pedidos = pedRes.data || [];

    // ─── KPIs ───
    var totalReceita = pagamentos.filter(function(p) { return p.status === 'pago'; })
      .reduce(function(s, p) { return s + (parseFloat(p.valor) || 0); }, 0);
    var totalPendente = pagamentos.filter(function(p) { return p.status === 'pendente'; })
      .reduce(function(s, p) { return s + (parseFloat(p.valor) || 0); }, 0);
    var ticketMedio = pagamentos.length ? totalReceita / pagamentos.filter(function(p) { return p.status === 'pago'; }).length : 0;
    var taxaConversao = pedidos.length ? (pedidos.filter(function(p) { return p.status === 'pago' || p.status === 'concluido'; }).length / pedidos.length * 100) : 0;

    document.getElementById('kpi-receita').textContent = 'R$ ' + totalReceita.toFixed(2);
    document.getElementById('kpi-pendente').textContent = 'R$ ' + totalPendente.toFixed(2);
    document.getElementById('kpi-ticket').textContent = ticketMedio ? 'R$ ' + ticketMedio.toFixed(2) : 'R$ 0.00';
    document.getElementById('kpi-conversao').textContent = taxaConversao.toFixed(1) + '%';
    document.getElementById('kpi-alunos').textContent = alunos.length;
    document.getElementById('kpi-atividades').textContent = atividades.length;

    // ─── Receita por Mês (tabela) ───
    var meses = {};
    pagamentos.filter(function(p) { return p.status === 'pago'; }).forEach(function(p) {
      var dt = p.dt_pagamento || p.created_at;
      if (!dt) return;
      var d = new Date(dt);
      var key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      meses[key] = (meses[key] || 0) + (parseFloat(p.valor) || 0);
    });

    var monthNames = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
    var sortedKeys = Object.keys(meses).sort().reverse().slice(0, 12);

    var receitaHtml = sortedKeys.map(function(k) {
      var parts = k.split('-');
      var label = monthNames[parseInt(parts[1]) - 1] + '/' + parts[0];
      return '<tr><td>' + label + '</td><td style="font-weight:700;">R$ ' + meses[k].toFixed(2) + '</td></tr>';
    }).join('');
    document.getElementById('tabela-receita').innerHTML = receitaHtml || '<tr><td colspan="2" class="empty-state">Sem dados</td></tr>';

    // ─── Top 5 alunos ───
    var alunoCount = {};
    atividades.forEach(function(a) {
      var nome = a.alunos ? a.alunos.nome : 'Desconhecido';
      alunoCount[nome] = (alunoCount[nome] || 0) + 1;
    });
    var topAlunos = Object.entries(alunoCount).sort(function(a, b) { return b[1] - a[1]; }).slice(0, 5);
    var topHtml = topAlunos.map(function(item, i) {
      return '<tr><td>' + (i + 1) + 'º</td><td>' + escapeHtml(item[0]) + '</td><td style="font-weight:700;">' + item[1] + '</td></tr>';
    }).join('');
    document.getElementById('tabela-top-alunos').innerHTML = topHtml || '<tr><td colspan="3" class="empty-state">Sem dados</td></tr>';

    // ─── Chart: Distribuição por tipo ───
    var tipoCount = {};
    atividades.forEach(function(a) {
      tipoCount[a.tipo] = (tipoCount[a.tipo] || 0) + 1;
    });

    if (typeof Chart !== 'undefined' && Object.keys(tipoCount).length) {
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      var colors = ['#f0c030', '#3b82f6', '#22c55e', '#ef4444', '#8b5cf6', '#f59e0b'];
      new Chart(document.getElementById('chart-tipos'), {
        type: 'pie',
        data: {
          labels: Object.keys(tipoCount).map(function(t) { return t.charAt(0).toUpperCase() + t.slice(1); }),
          datasets: [{
            data: Object.values(tipoCount),
            backgroundColor: colors.slice(0, Object.keys(tipoCount).length),
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { color: isDark ? '#8b949e' : '#4a5568', padding: 12, usePointStyle: true } }
          }
        }
      });
    }

    // ─── Chart: Receita mensal (bar) ───
    if (typeof Chart !== 'undefined' && sortedKeys.length) {
      var isDark2 = document.documentElement.getAttribute('data-theme') === 'dark';
      var barKeys = sortedKeys.slice().reverse();
      new Chart(document.getElementById('chart-receita-mensal'), {
        type: 'bar',
        data: {
          labels: barKeys.map(function(k) { var p = k.split('-'); return monthNames[parseInt(p[1])-1] + '/' + p[0].slice(2); }),
          datasets: [{
            label: 'Receita (R$)',
            data: barKeys.map(function(k) { return meses[k]; }),
            backgroundColor: 'rgba(240,192,48,0.7)',
            borderColor: '#f0c030',
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, grid: { color: isDark2 ? '#21262d' : '#eef1f6' }, ticks: { color: isDark2 ? '#8b949e' : '#8892a4', callback: function(v) { return 'R$ ' + v; } } },
            x: { grid: { display: false }, ticks: { color: isDark2 ? '#8b949e' : '#8892a4' } }
          }
        }
      });
    }

  } catch (e) {
    console.error('Erro nos relatórios:', e);
  }
}

function escapeHtml(t) {
  var d = document.createElement('div');
  d.textContent = t || '';
  return d.innerHTML;
}
