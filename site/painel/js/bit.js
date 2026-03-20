/* ══════════════════════════════════════
   Bit — Gestão de Serviços / Contas
   ══════════════════════════════════════ */

var currentTab = 'gestao';
var currentFilter = 'todos';
var gestaoData = [];
var cpData = [];
var crData = [];
var clientesList = [];
var servicosList = [];
var editingId = null;

/* ── Utility ────────────────────────── */

function formatBRL(val) {
  if (val === null || val === undefined) val = 0;
  return 'R$ ' + Number(val).toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  var d = new Date(dateStr);
  if (isNaN(d.getTime())) {
    var parts = dateStr.split('-');
    if (parts.length >= 3) return parts[2].substring(0, 2) + '/' + parts[1] + '/' + parts[0];
    return dateStr;
  }
  var dd = String(d.getDate()).padStart(2, '0');
  var mm = String(d.getMonth() + 1).padStart(2, '0');
  var yyyy = d.getFullYear();
  return dd + '/' + mm + '/' + yyyy;
}

function formatWhatsApp(num) {
  if (!num) return '—';
  var n = String(num).replace(/\D/g, '');
  if (n.length === 13 && n.substring(0, 2) === '55') n = n.substring(2);
  if (n.length === 12 && n.substring(0, 2) === '55') n = n.substring(2);
  if (n.length === 11) return '(' + n.slice(0, 2) + ') ' + n.slice(2, 7) + '-' + n.slice(7);
  if (n.length === 10) return '(' + n.slice(0, 2) + ') ' + n.slice(2, 6) + '-' + n.slice(6);
  return n;
}

function cleanPhone(num) {
  if (!num) return '';
  var n = String(num).replace(/\D/g, '');
  if (n.length >= 12 && n.substring(0, 2) === '55') return n;
  if (n.length === 11 || n.length === 10) return '55' + n;
  return n;
}

function todayStr() {
  var d = new Date();
  var mm = String(d.getMonth() + 1).padStart(2, '0');
  var dd = String(d.getDate()).padStart(2, '0');
  return d.getFullYear() + '-' + mm + '-' + dd;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(function() {
    showToast('Copiado!', 'success');
  });
}

/* ── Summary Cards ─────────────────── */

function updateSummary() {
  var container = document.getElementById('bit-summary');
  var today = todayStr();
  var html = '';

  if (currentTab === 'gestao') {
    var ativos = 0, expirados = 0, totalReceita = 0;
    for (var i = 0; i < gestaoData.length; i++) {
      var g = gestaoData[i];
      var exp = g.data_expiracao && g.data_expiracao < today;
      if (exp) { expirados++; } else { ativos++; }
      totalReceita += Number(g.valor) || 0;
    }
    html =
      '<div class="bit-card"><div class="bit-card-icon blue">&#128203;</div><div class="bit-card-info"><div class="bit-card-label">Total</div><div class="bit-card-value">' + gestaoData.length + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon green">&#9989;</div><div class="bit-card-info"><div class="bit-card-label">Ativos</div><div class="bit-card-value">' + ativos + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon red">&#9888;&#65039;</div><div class="bit-card-info"><div class="bit-card-label">Expirados</div><div class="bit-card-value">' + expirados + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon gold">&#128176;</div><div class="bit-card-info"><div class="bit-card-label">Receita Total</div><div class="bit-card-value">' + formatBRL(totalReceita) + '</div></div></div>';
  } else if (currentTab === 'cp') {
    var abertos = 0, pagos = 0, vencidos = 0, totalAberto = 0;
    for (var j = 0; j < cpData.length; j++) {
      var c = cpData[j];
      if (c.situacao == 1) { pagos++; }
      else if (c.vencimento && c.vencimento < today) { vencidos++; totalAberto += (Number(c.valor) || 0) - (Number(c.valor_pago) || 0); }
      else { abertos++; totalAberto += (Number(c.valor) || 0) - (Number(c.valor_pago) || 0); }
    }
    html =
      '<div class="bit-card"><div class="bit-card-icon blue">&#128203;</div><div class="bit-card-info"><div class="bit-card-label">Total</div><div class="bit-card-value">' + cpData.length + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon gold">&#9203;</div><div class="bit-card-info"><div class="bit-card-label">Abertos</div><div class="bit-card-value">' + abertos + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon red">&#128308;</div><div class="bit-card-info"><div class="bit-card-label">Vencidos</div><div class="bit-card-value">' + vencidos + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon green">&#9989;</div><div class="bit-card-info"><div class="bit-card-label">Pagos</div><div class="bit-card-value">' + pagos + '</div></div></div>';
  } else if (currentTab === 'cr') {
    var crAbertos = 0, recebidos = 0, crVencidos = 0, crTotalAberto = 0;
    for (var k = 0; k < crData.length; k++) {
      var cr = crData[k];
      if (cr.situacao == 1) { recebidos++; }
      else if (cr.vencimento && cr.vencimento < today) { crVencidos++; crTotalAberto += (Number(cr.valor) || 0) - (Number(cr.valor_recebido) || 0); }
      else { crAbertos++; crTotalAberto += (Number(cr.valor) || 0) - (Number(cr.valor_recebido) || 0); }
    }
    html =
      '<div class="bit-card"><div class="bit-card-icon blue">&#128203;</div><div class="bit-card-info"><div class="bit-card-label">Total</div><div class="bit-card-value">' + crData.length + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon gold">&#9203;</div><div class="bit-card-info"><div class="bit-card-label">Abertos</div><div class="bit-card-value">' + crAbertos + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon red">&#128308;</div><div class="bit-card-info"><div class="bit-card-label">Vencidos</div><div class="bit-card-value">' + crVencidos + '</div></div></div>' +
      '<div class="bit-card"><div class="bit-card-icon green">&#9989;</div><div class="bit-card-info"><div class="bit-card-label">Recebidos</div><div class="bit-card-value">' + recebidos + '</div></div></div>';
  }

  container.innerHTML = html;
}

/* ── Tab Switching ──────────────────── */

function switchTab(tab) {
  currentTab = tab;
  currentFilter = 'todos';

  var tabs = document.querySelectorAll('.bit-tab');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].classList.remove('active');
  }
  document.getElementById('tab-btn-' + tab).classList.add('active');

  var contents = document.querySelectorAll('.bit-tab-content');
  for (var j = 0; j < contents.length; j++) {
    contents[j].classList.remove('active');
  }
  document.getElementById('tab-' + tab).classList.add('active');

  var activeContent = document.getElementById('tab-' + tab);
  var filters = activeContent.querySelectorAll('.bit-filter');
  for (var k = 0; k < filters.length; k++) {
    filters[k].classList.remove('active');
    if (filters[k].textContent === 'Todos') filters[k].classList.add('active');
  }

  if (tab === 'gestao') loadGestao();
  else if (tab === 'cp') loadContasPagar();
  else if (tab === 'cr') loadContasReceber();
}

/* ── Data Loading ───────────────────── */

async function loadGestao() {
  try {
    var { data, error } = await sb
      .from('bit_gestao')
      .select('*, bit_clientes(id,nome,whatsapp), bit_servicos(id,descricao)')
      .order('data_expiracao', { ascending: false });
    if (error) throw error;
    gestaoData = data || [];
    renderGestao();
    updateSummary();
  } catch (e) {
    console.error('Erro ao carregar gestao:', e);
    showToast('Erro ao carregar gestao', 'error');
  }
}

async function loadContasPagar() {
  try {
    var { data, error } = await sb
      .from('bit_contas_pagar')
      .select('*')
      .order('vencimento', { ascending: false });
    if (error) throw error;
    cpData = data || [];
    renderContasPagar();
    updateSummary();
  } catch (e) {
    console.error('Erro ao carregar contas a pagar:', e);
    showToast('Erro ao carregar contas a pagar', 'error');
  }
}

async function loadContasReceber() {
  try {
    var { data, error } = await sb
      .from('bit_contas_receber')
      .select('*, bit_clientes(id,nome)')
      .order('vencimento', { ascending: false });
    if (error) throw error;
    crData = data || [];
    renderContasReceber();
    updateSummary();
  } catch (e) {
    console.error('Erro ao carregar contas a receber:', e);
    showToast('Erro ao carregar contas a receber', 'error');
  }
}

async function loadClientes() {
  try {
    var { data, error } = await sb
      .from('bit_clientes')
      .select('id, nome, whatsapp')
      .eq('ativo', true)
      .order('nome');
    if (error) throw error;
    clientesList = data || [];
  } catch (e) {
    console.error('Erro ao carregar clientes:', e);
  }
}

async function loadServicos() {
  try {
    var { data, error } = await sb
      .from('bit_servicos')
      .select('id, descricao, valor')
      .eq('ativo', true)
      .order('descricao');
    if (error) throw error;
    servicosList = data || [];
  } catch (e) {
    console.error('Erro ao carregar servicos:', e);
  }
}

/* ── Rendering ──────────────────────── */

function renderGestao() {
  var tbody = document.getElementById('gestao-table');
  var today = todayStr();
  var search = (document.getElementById('bit-search').value || '').toLowerCase();

  var filtered = gestaoData.filter(function (r) {
    var nome = (r.bit_clientes && r.bit_clientes.nome) ? r.bit_clientes.nome.toLowerCase() : '';
    if (search && nome.indexOf(search) === -1) return false;
    var expired = r.data_expiracao && r.data_expiracao < today;
    if (currentFilter === 'ativos' && expired) return false;
    if (currentFilter === 'expirados' && !expired) return false;
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7"><div class="bit-empty"><div class="bit-empty-icon">&#128203;</div><div class="bit-empty-text">Nenhum registro encontrado</div></div></td></tr>';
    return;
  }

  var html = '';
  for (var i = 0; i < filtered.length; i++) {
    var r = filtered[i];
    var clienteNome = (r.bit_clientes && r.bit_clientes.nome) || '—';
    var whatsapp = (r.bit_clientes && r.bit_clientes.whatsapp) || '';
    var servicoDesc = (r.bit_servicos && r.bit_servicos.descricao) || '—';
    var expired = r.data_expiracao && r.data_expiracao < today;
    var badge = expired
      ? '<span class="badge badge-expirado">Expirado</span>'
      : '<span class="badge badge-ativo">Ativo</span>';

    var wppClean = cleanPhone(whatsapp);
    var wppBtn = wppClean
      ? '<a href="https://wa.me/' + wppClean + '" target="_blank" class="bit-icon-btn wpp" title="WhatsApp">&#128172;</a>'
      : '';

    // Login/senha detail
    var detail = '';
    if (r.login || r.senha) {
      detail = '<div class="bit-detail">';
      if (r.login) detail += '&#128100; <code>' + escapeHtml(r.login) + '</code> <button class="bit-icon-btn copy" style="width:20px;height:20px;font-size:0.65rem;" onclick="copyText(\'' + escapeHtml(r.login).replace(/'/g, "\\'") + '\')" title="Copiar login">&#128203;</button> ';
      if (r.senha) detail += '&#128274; <code>' + escapeHtml(r.senha) + '</code> <button class="bit-icon-btn copy" style="width:20px;height:20px;font-size:0.65rem;" onclick="copyText(\'' + escapeHtml(r.senha).replace(/'/g, "\\'") + '\')" title="Copiar senha">&#128203;</button>';
      detail += '</div>';
    }

    html += '<tr>' +
      '<td><strong>' + escapeHtml(clienteNome) + '</strong>' + detail + '</td>' +
      '<td>' + formatWhatsApp(whatsapp) + ' ' + wppBtn + '</td>' +
      '<td>' + escapeHtml(servicoDesc) + '</td>' +
      '<td class="td-valor">' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.data_expiracao) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td class="td-acoes"><div class="bit-actions">' +
        '<button class="bit-icon-btn edit" onclick="openModal(\'gestao\',' + r.id + ')" title="Editar">&#9998;</button>' +
        '<button class="bit-icon-btn del" onclick="deleteRecord(\'bit_gestao\',' + r.id + ')" title="Excluir">&#128465;</button>' +
      '</div></td>' +
    '</tr>';
  }
  tbody.innerHTML = html;
}

function renderContasPagar() {
  var tbody = document.getElementById('cp-table');
  var today = todayStr();
  var search = (document.getElementById('bit-search-cp').value || '').toLowerCase();

  var filtered = cpData.filter(function (r) {
    if (search && (r.fornecedor || '').toLowerCase().indexOf(search) === -1) return false;
    var pago = r.situacao == 1;
    var vencido = !pago && r.vencimento && r.vencimento < today;
    var aberto = !pago && !vencido;
    if (currentFilter === 'pagos' && !pago) return false;
    if (currentFilter === 'vencidos' && !vencido) return false;
    if (currentFilter === 'abertos' && !aberto) return false;
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8"><div class="bit-empty"><div class="bit-empty-icon">&#128176;</div><div class="bit-empty-text">Nenhum registro encontrado</div></div></td></tr>';
    return;
  }

  var html = '';
  for (var i = 0; i < filtered.length; i++) {
    var r = filtered[i];
    var pago = r.situacao == 1;
    var vencido = !pago && r.vencimento && r.vencimento < today;
    var badge, quitarBtn = '';

    if (pago) {
      badge = '<span class="badge badge-pago">Pago</span>';
    } else if (vencido) {
      badge = '<span class="badge badge-vencido">Vencido</span>';
      quitarBtn = '<button class="bit-icon-btn quitar" onclick="quitarConta(' + r.id + ',\'pagar\')" title="Quitar">&#10004;</button>';
    } else {
      badge = '<span class="badge badge-aberto">Aberto</span>';
      quitarBtn = '<button class="bit-icon-btn quitar" onclick="quitarConta(' + r.id + ',\'pagar\')" title="Quitar">&#10004;</button>';
    }

    var valorAberto = (Number(r.valor) || 0) - (Number(r.valor_pago) || 0);

    html += '<tr>' +
      '<td><strong>' + escapeHtml(r.fornecedor || '—') + '</strong></td>' +
      '<td>' + escapeHtml(r.num_documento || '—') + '</td>' +
      '<td class="td-valor">' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.vencimento) + '</td>' +
      '<td class="td-valor">' + formatBRL(r.valor_pago) + '</td>' +
      '<td class="td-valor">' + formatBRL(valorAberto) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td class="td-acoes"><div class="bit-actions">' +
        quitarBtn +
        '<button class="bit-icon-btn edit" onclick="openModal(\'cp\',' + r.id + ')" title="Editar">&#9998;</button>' +
        '<button class="bit-icon-btn del" onclick="deleteRecord(\'bit_contas_pagar\',' + r.id + ')" title="Excluir">&#128465;</button>' +
      '</div></td>' +
    '</tr>';
  }
  tbody.innerHTML = html;
}

function renderContasReceber() {
  var tbody = document.getElementById('cr-table');
  var today = todayStr();
  var search = (document.getElementById('bit-search-cr').value || '').toLowerCase();

  var filtered = crData.filter(function (r) {
    var nome = (r.bit_clientes && r.bit_clientes.nome) ? r.bit_clientes.nome.toLowerCase() : '';
    if (search && nome.indexOf(search) === -1) return false;
    var recebido = r.situacao == 1;
    var vencido = !recebido && r.vencimento && r.vencimento < today;
    var aberto = !recebido && !vencido;
    if (currentFilter === 'recebidos' && !recebido) return false;
    if (currentFilter === 'vencidos' && !vencido) return false;
    if (currentFilter === 'abertos' && !aberto) return false;
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8"><div class="bit-empty"><div class="bit-empty-icon">&#128176;</div><div class="bit-empty-text">Nenhum registro encontrado</div></div></td></tr>';
    return;
  }

  var html = '';
  for (var i = 0; i < filtered.length; i++) {
    var r = filtered[i];
    var clienteNome = (r.bit_clientes && r.bit_clientes.nome) || '—';
    var recebido = r.situacao == 1;
    var vencido = !recebido && r.vencimento && r.vencimento < today;
    var badge, receberBtn = '';

    if (recebido) {
      badge = '<span class="badge badge-recebido">Recebido</span>';
    } else if (vencido) {
      badge = '<span class="badge badge-vencido">Vencido</span>';
      receberBtn = '<button class="bit-icon-btn quitar" onclick="quitarConta(' + r.id + ',\'receber\')" title="Receber">&#10004;</button>';
    } else {
      badge = '<span class="badge badge-aberto">Aberto</span>';
      receberBtn = '<button class="bit-icon-btn quitar" onclick="quitarConta(' + r.id + ',\'receber\')" title="Receber">&#10004;</button>';
    }

    var valorAberto = (Number(r.valor) || 0) - (Number(r.valor_recebido) || 0);

    html += '<tr>' +
      '<td><strong>' + escapeHtml(clienteNome) + '</strong></td>' +
      '<td>' + escapeHtml(r.num_documento || '—') + '</td>' +
      '<td class="td-valor">' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.vencimento) + '</td>' +
      '<td class="td-valor">' + formatBRL(r.valor_recebido) + '</td>' +
      '<td class="td-valor">' + formatBRL(valorAberto) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td class="td-acoes"><div class="bit-actions">' +
        receberBtn +
        '<button class="bit-icon-btn edit" onclick="openModal(\'cr\',' + r.id + ')" title="Editar">&#9998;</button>' +
        '<button class="bit-icon-btn del" onclick="deleteRecord(\'bit_contas_receber\',' + r.id + ')" title="Excluir">&#128465;</button>' +
      '</div></td>' +
    '</tr>';
  }
  tbody.innerHTML = html;
}

/* ── Filtering & Search ─────────────── */

function setFilter(filter) {
  currentFilter = filter;

  var activeContent = document.getElementById('tab-' + currentTab);
  var filters = activeContent.querySelectorAll('.bit-filter');
  for (var i = 0; i < filters.length; i++) {
    filters[i].classList.remove('active');
    var txt = filters[i].textContent.toLowerCase().replace(/\s/g, '');
    if (txt === filter) filters[i].classList.add('active');
  }

  if (currentTab === 'gestao') renderGestao();
  else if (currentTab === 'cp') renderContasPagar();
  else if (currentTab === 'cr') renderContasReceber();
}

function searchBit() {
  if (currentTab === 'gestao') renderGestao();
  else if (currentTab === 'cp') renderContasPagar();
  else if (currentTab === 'cr') renderContasReceber();
}

/* ── Modal ──────────────────────────── */

function openModal(type, id) {
  editingId = id || null;
  var title = '';
  var bodyHtml = '';

  if (type === 'gestao') {
    title = editingId ? 'Editar Gestao' : 'Nova Gestao';
    var clienteOpts = '<option value="">Selecione o cliente</option>';
    for (var i = 0; i < clientesList.length; i++) {
      clienteOpts += '<option value="' + clientesList[i].id + '">' + escapeHtml(clientesList[i].nome) + '</option>';
    }
    var servicoOpts = '<option value="">Selecione o servico</option>';
    for (var j = 0; j < servicosList.length; j++) {
      servicoOpts += '<option value="' + servicosList[j].id + '">' + escapeHtml(servicosList[j].descricao) + ' (' + formatBRL(servicosList[j].valor) + ')</option>';
    }
    bodyHtml =
      '<label>Cliente</label><select id="m-cliente">' + clienteOpts + '</select>' +
      '<label>Servico</label><select id="m-servico" onchange="preencherValorServico()">' + servicoOpts + '</select>' +
      '<label>Valor (R$)</label><input type="number" id="m-valor" step="0.01" min="0" placeholder="0.00">' +
      '<label>Data de Expiracao</label><input type="date" id="m-expiracao">' +
      '<label>Login</label><input type="text" id="m-login" placeholder="Login de acesso">' +
      '<label>Senha</label><input type="text" id="m-senha" placeholder="Senha de acesso">' +
      '<label>Observacao</label><textarea id="m-obs" placeholder="Observacoes..."></textarea>';
  } else if (type === 'cp') {
    title = editingId ? 'Editar Conta a Pagar' : 'Nova Conta a Pagar';
    bodyHtml =
      '<label>Fornecedor</label><input type="text" id="m-fornecedor" placeholder="Nome do fornecedor">' +
      '<label>N. Documento</label><input type="text" id="m-numdoc" placeholder="N. do documento">' +
      '<label>Valor (R$)</label><input type="number" id="m-valor" step="0.01" min="0" placeholder="0.00">' +
      '<label>Emissao</label><input type="date" id="m-emissao">' +
      '<label>Vencimento</label><input type="date" id="m-vencimento">' +
      '<label>Observacao</label><textarea id="m-obs" placeholder="Observacoes..."></textarea>';
  } else if (type === 'cr') {
    title = editingId ? 'Editar Conta a Receber' : 'Nova Conta a Receber';
    var crClienteOpts = '<option value="">Selecione o cliente</option>';
    for (var k = 0; k < clientesList.length; k++) {
      crClienteOpts += '<option value="' + clientesList[k].id + '">' + escapeHtml(clientesList[k].nome) + '</option>';
    }
    bodyHtml =
      '<label>Cliente</label><select id="m-cliente">' + crClienteOpts + '</select>' +
      '<label>N. Documento</label><input type="text" id="m-numdoc" placeholder="N. do documento">' +
      '<label>Valor (R$)</label><input type="number" id="m-valor" step="0.01" min="0" placeholder="0.00">' +
      '<label>Emissao</label><input type="date" id="m-emissao">' +
      '<label>Vencimento</label><input type="date" id="m-vencimento">' +
      '<label>Observacao</label><textarea id="m-obs" placeholder="Observacoes..."></textarea>';
  }

  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHtml;
  document.getElementById('modal-overlay').classList.add('show');

  if (editingId) {
    fillModalForEdit(type, editingId);
  }
}

function fillModalForEdit(type, id) {
  if (type === 'gestao') {
    var rec = gestaoData.find(function (r) { return r.id === id; });
    if (!rec) return;
    document.getElementById('m-cliente').value = rec.cliente_id || '';
    document.getElementById('m-servico').value = rec.servico_id || '';
    document.getElementById('m-valor').value = rec.valor || '';
    document.getElementById('m-expiracao').value = rec.data_expiracao ? rec.data_expiracao.substring(0, 10) : '';
    document.getElementById('m-login').value = rec.login || '';
    document.getElementById('m-senha').value = rec.senha || '';
    document.getElementById('m-obs').value = rec.observacao || '';
  } else if (type === 'cp') {
    var rec2 = cpData.find(function (r) { return r.id === id; });
    if (!rec2) return;
    document.getElementById('m-fornecedor').value = rec2.fornecedor || '';
    document.getElementById('m-numdoc').value = rec2.num_documento || '';
    document.getElementById('m-valor').value = rec2.valor || '';
    document.getElementById('m-emissao').value = rec2.emissao || '';
    document.getElementById('m-vencimento').value = rec2.vencimento || '';
    document.getElementById('m-obs').value = rec2.observacao || '';
  } else if (type === 'cr') {
    var rec3 = crData.find(function (r) { return r.id === id; });
    if (!rec3) return;
    document.getElementById('m-cliente').value = rec3.cliente_id || '';
    document.getElementById('m-numdoc').value = rec3.num_documento || '';
    document.getElementById('m-valor').value = rec3.valor || '';
    document.getElementById('m-emissao').value = rec3.emissao || '';
    document.getElementById('m-vencimento').value = rec3.vencimento || '';
    document.getElementById('m-obs').value = rec3.observacao || '';
  }
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('show');
  editingId = null;
}

function preencherValorServico() {
  var sel = document.getElementById('m-servico');
  if (!sel) return;
  var sId = Number(sel.value);
  var servico = servicosList.find(function (s) { return s.id === sId; });
  if (servico && servico.valor) {
    document.getElementById('m-valor').value = servico.valor;
  }
}

/* ── Save Record ────────────────────── */

async function saveRecord() {
  try {
    var payload = {};
    var table = '';

    if (currentTab === 'gestao') {
      table = 'bit_gestao';
      payload = {
        cliente_id: Number(document.getElementById('m-cliente').value) || null,
        servico_id: Number(document.getElementById('m-servico').value) || null,
        valor: Number(document.getElementById('m-valor').value) || 0,
        data_expiracao: document.getElementById('m-expiracao').value || null,
        login: document.getElementById('m-login').value || '',
        senha: document.getElementById('m-senha').value || '',
        observacao: document.getElementById('m-obs').value || ''
      };
      if (!payload.cliente_id || !payload.servico_id) {
        showToast('Selecione cliente e servico', 'error');
        return;
      }
    } else if (currentTab === 'cp') {
      table = 'bit_contas_pagar';
      payload = {
        fornecedor: document.getElementById('m-fornecedor').value || '',
        num_documento: document.getElementById('m-numdoc').value || '',
        valor: Number(document.getElementById('m-valor').value) || 0,
        emissao: document.getElementById('m-emissao').value || null,
        vencimento: document.getElementById('m-vencimento').value || null,
        observacao: document.getElementById('m-obs').value || '',
        valor_pago: 0,
        situacao: 0
      };
      if (!payload.fornecedor) {
        showToast('Informe o fornecedor', 'error');
        return;
      }
    } else if (currentTab === 'cr') {
      table = 'bit_contas_receber';
      payload = {
        cliente_id: Number(document.getElementById('m-cliente').value) || null,
        num_documento: document.getElementById('m-numdoc').value || '',
        valor: Number(document.getElementById('m-valor').value) || 0,
        emissao: document.getElementById('m-emissao').value || null,
        vencimento: document.getElementById('m-vencimento').value || null,
        observacao: document.getElementById('m-obs').value || '',
        valor_recebido: 0,
        situacao: 0
      };
      if (!payload.cliente_id) {
        showToast('Selecione o cliente', 'error');
        return;
      }
    }

    var error;
    if (editingId) {
      if (currentTab === 'cp') {
        delete payload.valor_pago;
        delete payload.situacao;
      } else if (currentTab === 'cr') {
        delete payload.valor_recebido;
        delete payload.situacao;
      }
      var res = await sb.from(table).update(payload).eq('id', editingId);
      error = res.error;
    } else {
      var res2 = await sb.from(table).insert(payload);
      error = res2.error;
    }

    if (error) throw error;

    showToast(editingId ? 'Registro atualizado!' : 'Registro criado!', 'success');
    closeModal();

    if (currentTab === 'gestao') loadGestao();
    else if (currentTab === 'cp') loadContasPagar();
    else if (currentTab === 'cr') loadContasReceber();
  } catch (e) {
    console.error('Erro ao salvar:', e);
    showToast('Erro ao salvar registro', 'error');
  }
}

/* ── Delete Record ──────────────────── */

async function deleteRecord(table, id) {
  if (!confirm('Deseja realmente excluir este registro?')) return;

  try {
    var { error } = await sb.from(table).delete().eq('id', id);
    if (error) throw error;

    showToast('Registro excluido!', 'success');

    if (currentTab === 'gestao') loadGestao();
    else if (currentTab === 'cp') loadContasPagar();
    else if (currentTab === 'cr') loadContasReceber();
  } catch (e) {
    console.error('Erro ao excluir:', e);
    showToast('Erro ao excluir registro', 'error');
  }
}

/* ── Quitar / Receber ───────────────── */

async function quitarConta(id, tipo) {
  var label = tipo === 'pagar' ? 'quitar esta conta' : 'confirmar recebimento';
  if (!confirm('Deseja ' + label + '?')) return;

  try {
    var table, payload;

    if (tipo === 'pagar') {
      table = 'bit_contas_pagar';
      var rec = cpData.find(function (r) { return r.id === id; });
      payload = {
        situacao: 1,
        valor_pago: rec ? rec.valor : 0,
        quitacao: todayStr()
      };
    } else {
      table = 'bit_contas_receber';
      var rec2 = crData.find(function (r) { return r.id === id; });
      payload = {
        situacao: 1,
        valor_recebido: rec2 ? rec2.valor : 0,
        quitacao: todayStr()
      };
    }

    var { error } = await sb.from(table).update(payload).eq('id', id);
    if (error) throw error;

    showToast(tipo === 'pagar' ? 'Conta quitada!' : 'Recebimento confirmado!', 'success');

    if (tipo === 'pagar') loadContasPagar();
    else loadContasReceber();
  } catch (e) {
    console.error('Erro ao quitar:', e);
    showToast('Erro ao processar', 'error');
  }
}

/* ── Init ───────────────────────────── */

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'dono']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  var name = getUserName(user);
  document.getElementById('user-avatar').textContent = name.charAt(0).toUpperCase();
  document.getElementById('user-name').textContent = name;

  await Promise.all([loadClientes(), loadServicos()]);
  switchTab('gestao');
});
