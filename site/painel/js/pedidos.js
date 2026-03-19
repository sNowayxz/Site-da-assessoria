/* ═══════════════════════════════════════════
   Pedidos de Extensão — Admin CRUD
   ═══════════════════════════════════════════ */

var STATUS_LABELS = {
  aguardando_pagamento: 'Aguardando Pgto',
  pago: 'Pago',
  em_andamento: 'Em Andamento',
  concluido: 'Concluído',
  cancelado: 'Cancelado'
};

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  await loadPedidos();

  document.getElementById('filter-busca').addEventListener('input', filterPedidos);
  document.getElementById('filter-status').addEventListener('change', filterPedidos);
});

async function loadPedidos() {
  var { data, error } = await sb
    .from('pedidos_extensao')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) { console.error(error); return; }
  window._pedidos = data || [];
  updateStats(window._pedidos);
  renderPedidos(window._pedidos);
}

function updateStats(pedidos) {
  var total = pedidos.length;
  var aguardando = 0, pagos = 0, andamento = 0;

  pedidos.forEach(function (p) {
    if (p.status === 'aguardando_pagamento') aguardando++;
    else if (p.status === 'pago') pagos++;
    else if (p.status === 'em_andamento') andamento++;
  });

  document.getElementById('count-total').textContent = total;
  document.getElementById('count-aguardando').textContent = aguardando;
  document.getElementById('count-pagos').textContent = pagos;
  document.getElementById('count-andamento').textContent = andamento;
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
      '<td>' + formatDate(p.created_at) + '</td>' +
      '<td class="actions"><button class="btn-icon" onclick="viewPedido(\'' + p.id + '\')" title="Ver detalhes">👁️</button></td>' +
      '</tr>';
  }).join('');
}

function filterPedidos() {
  var busca = document.getElementById('filter-busca').value.toLowerCase();
  var status = document.getElementById('filter-status').value;
  var filtered = (window._pedidos || []).filter(function (p) {
    var matchBusca = !busca ||
      (p.nome_cliente || '').toLowerCase().includes(busca) ||
      (p.email || '').toLowerCase().includes(busca) ||
      (p.curso || '').toLowerCase().includes(busca) ||
      (p.tema || '').toLowerCase().includes(busca) ||
      (p.ra || '').toLowerCase().includes(busca);
    var matchStatus = !status || p.status === status;
    return matchBusca && matchStatus;
  });
  renderPedidos(filtered);
}

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
    '<div class="detail-item"><label>Carga Hor&aacute;ria</label><p>' + pedido.carga_horaria + 'h</p></div>' +
    '<div class="detail-item"><label>Valor</label><p class="valor-text">R$ ' + (pedido.valor ? Number(pedido.valor).toFixed(2).replace('.', ',') : '—') + '</p></div>' +
    '<div class="detail-item"><label>Status</label><p><span class="badge badge-' + pedido.status + '">' + statusLabel + '</span></p></div>' +
    '<div class="detail-item"><label>Prazo</label><p>' + (pedido.prazo ? formatDate(pedido.prazo) : '—') + '</p></div>' +
    '<div class="detail-item"><label>Criado em</label><p>' + formatDate(pedido.created_at) + '</p></div>' +
    '<div class="detail-item detail-full"><label>Tema</label><p>' + escapeHtml(pedido.tema) + '</p></div>' +
    (pedido.observacoes ? '<div class="detail-item detail-full"><label>Observa&ccedil;&otilde;es</label><p>' + escapeHtml(pedido.observacoes) + '</p></div>' : '') +
    (pedido.payment_id ? '<div class="detail-item"><label>Payment ID</label><p style="font-size:0.82rem;color:var(--gray-400);">' + escapeHtml(pedido.payment_id) + '</p></div>' : '') +
    '</div>';

  // Action buttons based on current status
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
    html += '<button class="btn-status-action to-concluido" onclick="updatePedidoStatus(\'' + pedido.id + '\',\'concluido\')">Marcar Conclu&iacute;do</button>';
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

function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    var d = new Date(dateStr);
    return d.toLocaleDateString('pt-BR');
  } catch (e) { return dateStr; }
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
