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
    // Contadores
    var { count: totalAlunos } = await sb.from('alunos').select('*', { count: 'exact', head: true });
    var { count: pendentes } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'pendente');
    var { count: emAndamento } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'em_andamento');
    var { count: entregues } = await sb.from('atividades').select('*', { count: 'exact', head: true }).eq('status', 'entregue');

    document.getElementById('count-alunos').textContent = totalAlunos || 0;
    document.getElementById('count-pendentes').textContent = pendentes || 0;
    document.getElementById('count-andamento').textContent = emAndamento || 0;
    document.getElementById('count-entregues').textContent = entregues || 0;

    // Últimas atividades
    var { data: ultimas } = await supabase
      .from('atividades')
      .select('*, alunos(nome, ra)')
      .order('created_at', { ascending: false })
      .limit(10);

    renderRecentActivities(ultimas || []);
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
