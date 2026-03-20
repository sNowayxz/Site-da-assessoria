/* ═══════════════════════════════════════════
   Pedidos — Extensões + Atividades (unificado)
   ═══════════════════════════════════════════ */

var currentPedidoTab = 'extensoes';
var _pedidosAtiv = [];

var STATUS_LABELS = {
  aguardando_pagamento: 'Aguardando Pgto',
  pago: 'Pago',
  em_andamento: 'Em Andamento',
  concluido: 'Concluído',
  cancelado: 'Cancelado'
};

var ATIV_STATUS_LABELS = {
  pendente: 'Pendente',
  em_andamento: 'Em Andamento',
  entregue: 'Entregue',
  revisao: 'Revisão'
};

var TIPO_LABELS = {
  atividade: 'Atividade',
  mapa: 'Mapa',
  tcc: 'TCC',
  relatorio: 'Relatório',
  extensao: 'Extensão',
  pacote: 'Pacote'
};

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'dono', 'assessor']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Load both tabs
  await loadPedidos();
  await loadAtividadesPedidos();

  // Extensões filters
  document.getElementById('filter-busca').addEventListener('input', filterPedidos);
  document.getElementById('filter-status').addEventListener('change', filterPedidos);
  document.getElementById('filter-tema').addEventListener('input', filterPedidos);

  // Atividades filters
  document.getElementById('filter-aluno-ativ').addEventListener('input', filterAtividadesPedidos);
  document.getElementById('filter-status-ativ').addEventListener('change', filterAtividadesPedidos);
  document.getElementById('filter-tipo-ativ').addEventListener('change', filterAtividadesPedidos);
  document.getElementById('filter-descricao-ativ').addEventListener('input', filterAtividadesPedidos);
});

/* ── Tab Switching ──────────────────── */

function switchPedidoTab(tab) {
  currentPedidoTab = tab;

  var tabs = document.querySelectorAll('.ped-tab');
  for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove('active');
  document.getElementById('ped-tab-' + tab).classList.add('active');

  var contents = document.querySelectorAll('.ped-tab-content');
  for (var j = 0; j < contents.length; j++) contents[j].classList.remove('active');
  document.getElementById('tab-' + tab).classList.add('active');

  updateStatsForTab();
}

/* ── Stats ──────────────────────────── */

function updateStatsForTab() {
  var container = document.getElementById('ped-stats');

  if (currentPedidoTab === 'extensoes') {
    var pedidos = window._pedidos || [];
    var total = pedidos.length;
    var aguardando = 0, pagos = 0, andamento = 0;
    pedidos.forEach(function (p) {
      if (p.status === 'aguardando_pagamento') aguardando++;
      else if (p.status === 'pago') pagos++;
      else if (p.status === 'em_andamento') andamento++;
    });
    container.innerHTML =
      '<div class="stat-card"><div class="stat-icon blue">📦</div><div class="stat-info"><h3>' + total + '</h3><p>Total de Pedidos</p></div></div>' +
      '<div class="stat-card"><div class="stat-icon orange">⏳</div><div class="stat-info"><h3>' + aguardando + '</h3><p>Aguardando Pgto</p></div></div>' +
      '<div class="stat-card"><div class="stat-icon green">💳</div><div class="stat-info"><h3>' + pagos + '</h3><p>Pagos</p></div></div>' +
      '<div class="stat-card"><div class="stat-icon purple">🔄</div><div class="stat-info"><h3>' + andamento + '</h3><p>Em Andamento</p></div></div>';
  } else {
    var atividades = _pedidosAtiv;
    var aTotal = atividades.length;
    var pendentes = 0, aAndamento = 0, entregues = 0, revisao = 0;
    atividades.forEach(function (a) {
      if (a.status === 'pendente') pendentes++;
      else if (a.status === 'em_andamento') aAndamento++;
      else if (a.status === 'entregue') entregues++;
      else if (a.status === 'revisao') revisao++;
    });
    container.innerHTML =
      '<div class="stat-card"><div class="stat-icon blue">📋</div><div class="stat-info"><h3>' + aTotal + '</h3><p>Total</p></div></div>' +
      '<div class="stat-card"><div class="stat-icon orange">⏳</div><div class="stat-info"><h3>' + pendentes + '</h3><p>Pendentes</p></div></div>' +
      '<div class="stat-card"><div class="stat-icon purple">🔄</div><div class="stat-info"><h3>' + aAndamento + '</h3><p>Em Andamento</p></div></div>' +
      '<div class="stat-card"><div class="stat-icon green">✅</div><div class="stat-info"><h3>' + entregues + '</h3><p>Entregues</p></div></div>';
  }
}

/* ── Extensões ─────────────────────── */

async function loadPedidos() {
  var { data, error } = await sb
    .from('pedidos_extensao')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) { console.error(error); return; }
  window._pedidos = data || [];
  renderPedidos(window._pedidos);
  if (currentPedidoTab === 'extensoes') updateStatsForTab();
}

function renderPedidos(pedidos) {
  var tbody = document.getElementById('pedidos-table');
  if (!pedidos.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Nenhum pedido encontrado</td></tr>';
    return;
  }

  tbody.innerHTML = pedidos.map(function (p) {
    return '<tr>' +
      '<td><span class="aluno-name">' + escapeHtml(p.nome_cliente) + '</span><br><span class="text-muted">' + escapeHtml(p.email) + '</span></td>' +
      '<td>' + escapeHtml(p.curso) + '</td>' +
      '<td>' + p.carga_horaria + 'h</td>' +
      '<td class="valor-text">R$ ' + (p.valor ? Number(p.valor).toFixed(2).replace('.', ',') : '—') + '</td>' +
      '<td><span class="badge badge-' + p.status + '">' + (STATUS_LABELS[p.status] || p.status) + '</span></td>' +
      '<td>' + formatDatePed(p.created_at) + '</td>' +
      '<td class="actions"><button class="btn-icon" onclick="viewPedido(\'' + p.id + '\')" title="Ver detalhes">👁️</button></td>' +
      '</tr>';
  }).join('');
}

function filterPedidos() {
  var busca = document.getElementById('filter-busca').value.toLowerCase();
  var status = document.getElementById('filter-status').value;
  var tema = document.getElementById('filter-tema').value.toLowerCase();

  var filtered = (window._pedidos || []).filter(function (p) {
    var matchBusca = !busca ||
      (p.nome_cliente || '').toLowerCase().includes(busca) ||
      (p.email || '').toLowerCase().includes(busca) ||
      (p.curso || '').toLowerCase().includes(busca) ||
      (p.ra || '').toLowerCase().includes(busca);
    var matchStatus = !status || p.status === status;
    var matchTema = !tema || (p.tema || '').toLowerCase().includes(tema);
    return matchBusca && matchStatus && matchTema;
  });
  renderPedidos(filtered);
}

/* ── Atividades ────────────────────── */

async function loadAtividadesPedidos() {
  var { data, error } = await sb
    .from('atividades')
    .select('*, alunos(nome, ra)')
    .order('created_at', { ascending: false });

  if (error) { console.error(error); return; }
  _pedidosAtiv = data || [];
  renderAtividadesPedidos(_pedidosAtiv);
  if (currentPedidoTab === 'atividades') updateStatsForTab();
}

function renderAtividadesPedidos(atividades) {
  var tbody = document.getElementById('atividades-ped-table');
  if (!atividades.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Nenhuma atividade encontrada</td></tr>';
    return;
  }

  tbody.innerHTML = atividades.map(function (a) {
    var aluno = a.alunos || {};
    return '<tr>' +
      '<td><span class="aluno-name">' + escapeHtml(aluno.nome || '—') + '</span><br><small class="text-muted">' + escapeHtml(aluno.ra || '') + '</small></td>' +
      '<td><span class="badge badge-tipo">' + (TIPO_LABELS[a.tipo] || a.tipo) + '</span></td>' +
      '<td class="desc-cell">' + escapeHtml(a.descricao || '—') + '</td>' +
      '<td class="valor-text">R$ ' + (Number(a.valor) || 0).toFixed(2).replace('.', ',') + '</td>' +
      '<td><span class="badge badge-' + a.status + '">' + (ATIV_STATUS_LABELS[a.status] || a.status) + '</span></td>' +
      '<td>' + formatDatePed(a.created_at) + '</td>' +
      '<td class="actions"><button class="btn-icon btn-status" onclick="cycleAtivStatus(\'' + a.id + '\',\'' + a.status + '\')" title="Avançar Status">⏭️</button></td>' +
      '</tr>';
  }).join('');
}

function filterAtividadesPedidos() {
  var aluno = document.getElementById('filter-aluno-ativ').value.toLowerCase();
  var status = document.getElementById('filter-status-ativ').value;
  var tipo = document.getElementById('filter-tipo-ativ').value;
  var descricao = document.getElementById('filter-descricao-ativ').value.toLowerCase();

  var filtered = _pedidosAtiv.filter(function (a) {
    var alunoData = a.alunos || {};
    var matchAluno = !aluno || (alunoData.nome || '').toLowerCase().includes(aluno) || (alunoData.ra || '').toLowerCase().includes(aluno);
    var matchStatus = !status || a.status === status;
    var matchTipo = !tipo || a.tipo === tipo;
    var matchDesc = !descricao || (a.descricao || '').toLowerCase().includes(descricao);
    return matchAluno && matchStatus && matchTipo && matchDesc;
  });
  renderAtividadesPedidos(filtered);
}

async function cycleAtivStatus(id, currentStatus) {
  var nextMap = {
    pendente: 'em_andamento',
    em_andamento: 'entregue',
    entregue: 'revisao',
    revisao: 'pendente'
  };
  var next = nextMap[currentStatus] || 'pendente';
  var { error } = await sb.from('atividades').update({ status: next }).eq('id', id);
  if (error) { showToast('Erro: ' + error.message, 'error'); return; }
  await loadAtividadesPedidos();
  if (currentPedidoTab === 'atividades') updateStatsForTab();
  showToast('Status atualizado!', 'success');
}

/* ── PDF Export ─────────────────────── */

function exportPedidoPDF() {
  if (currentPedidoTab === 'extensoes') {
    exportTableToPDF('pedidos-table', 'Pedidos de Extensão - Relatório', 'pedidos-extensoes');
  } else {
    exportTableToPDF('atividades-ped-table', 'Atividades - Relatório', 'pedidos-atividades');
  }
}

/* ── Pedido Detail Modal ───────────── */

function viewPedido(id) {
  var pedido = (window._pedidos || []).find(function (p) { return p.id === id; });
  if (!pedido) return;

  var container = document.getElementById('pedido-detail');
  var statusLabel = STATUS_LABELS[pedido.status] || pedido.status;

  var html = '<div class="detail-grid">' +
    '<div class="detail-item"><label>Cliente</label><p>' + escapeHtml(pedido.nome_cliente) + '</p></div>' +
    '<div class="detail-item"><label>Email</label><p>' + escapeHtml(pedido.email) + '</p></div>' +
    '<div class="detail-item"><label>Telefone</label><p>' + escapeHtml(pedido.telefone || '—') + '</p></div>' +
    '<div class="detail-item"><label>RA</label><p>' + escapeHtml(pedido.ra || '—') + '</p></div>' +
    '<div class="detail-item"><label>Curso</label><p>' + escapeHtml(pedido.curso) + '</p></div>' +
    '<div class="detail-item"><label>Carga Hor\u00e1ria</label><p>' + pedido.carga_horaria + 'h</p></div>' +
    '<div class="detail-item"><label>Valor</label><p class="valor-text">R$ ' + (pedido.valor ? Number(pedido.valor).toFixed(2).replace('.', ',') : '—') + '</p></div>' +
    '<div class="detail-item"><label>Status</label><p><span class="badge badge-' + pedido.status + '">' + statusLabel + '</span></p></div>' +
    '<div class="detail-item"><label>Prazo</label><p>' + (pedido.prazo ? formatDatePed(pedido.prazo) : '—') + '</p></div>' +
    '<div class="detail-item"><label>Criado em</label><p>' + formatDatePed(pedido.created_at) + '</p></div>' +
    '<div class="detail-item detail-full"><label>Tema</label><p>' + escapeHtml(pedido.tema) + '</p></div>' +
    (pedido.observacoes ? '<div class="detail-item detail-full"><label>Observa\u00e7\u00f5es</label><p>' + escapeHtml(pedido.observacoes) + '</p></div>' : '') +
    (pedido.payment_id ? '<div class="detail-item"><label>Payment ID</label><p style="font-size:0.82rem;color:var(--gray-400);">' + escapeHtml(pedido.payment_id) + '</p></div>' : '') +
    '</div>';

  html += '<div class="detail-actions">';
  if (pedido.status === 'aguardando_pagamento') {
    html += '<button class="btn-status-action to-pago" onclick="updatePedidoStatus(\'' + pedido.id + '\',\'pago\')">Marcar como Pago</button>';
    html += '<button class="btn-status-action to-cancelado" onclick="updatePedidoStatus(\'' + pedido.id + '\',\'cancelado\')">Cancelar</button>';
  }
  if (pedido.status === 'pago') {
    html += '<button class="btn-status-action to-andamento" onclick="updatePedidoStatus(\'' + pedido.id + '\',\'em_andamento\')">Iniciar Trabalho</button>';
    html += '<button class="btn-status-action to-cancelado" onclick="updatePedidoStatus(\'' + pedido.id + '\',\'cancelado\')">Cancelar</button>';
  }
  if (pedido.status === 'em_andamento') {
    html += '<button class="btn-status-action to-concluido" onclick="updatePedidoStatus(\'' + pedido.id + '\',\'concluido\')">Marcar Conclu\u00eddo</button>';
  }
  if (pedido.status === 'cancelado') {
    html += '<button class="btn-status-action to-pago" onclick="updatePedidoStatus(\'' + pedido.id + '\',\'aguardando_pagamento\')">Reabrir Pedido</button>';
  }
  html += '</div>';

  container.innerHTML = html;
  openModal('modal-pedido');
}

async function updatePedidoStatus(id, newStatus) {
  showConfirm('Alterar status para "' + (STATUS_LABELS[newStatus] || newStatus) + '"?', async function() {
    var { error } = await sb
      .from('pedidos_extensao')
      .update({ status: newStatus, updated_at: new Date().toISOString() })
      .eq('id', id);

    if (error) {
      showToast('Erro ao atualizar: ' + error.message, 'error');
      return;
    }

    closeModal('modal-pedido');
    await loadPedidos();
  }, { title: 'Alterar Status', confirmText: 'Alterar', type: 'warning' });
}

/* ── Helpers ────────────────────────── */

function formatDatePed(dateStr) {
  if (!dateStr) return '—';
  try {
    var d = new Date(dateStr);
    return d.toLocaleDateString('pt-BR');
  } catch (e) { return dateStr; }
}

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
