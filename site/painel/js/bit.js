/* ══════════════════════════════════════
   Bit — Gestão de Serviços / Contas  v3
   ══════════════════════════════════════ */

var currentTab = 'gestao';
var currentFilter = 'todos';
var gestaoData = [];
var cpData = [];
var crData = [];
var clientesList = [];
var servicosList = [];
var editingId = null;

/* ── SVG icon helpers ────────────────── */

var SVG_ICONS = {
  clipboard: '<svg viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1"/></svg>',
  check: '<svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
  alert: '<svg viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  dollar: '<svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
  clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  whatsapp: '<svg viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
  edit: '<svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  checkCircle: '<svg viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  copy: '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
  user: '<svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  lock: '<svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  empty: '<svg viewBox="0 0 24 24"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>'
};

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
      '<div class="bit-card c-blue"><div class="bit-card-icon i-blue">' + SVG_ICONS.clipboard + '</div><div class="bit-card-info"><div class="bit-card-label">Total</div><div class="bit-card-value">' + gestaoData.length + '</div></div></div>' +
      '<div class="bit-card c-green"><div class="bit-card-icon i-green">' + SVG_ICONS.check + '</div><div class="bit-card-info"><div class="bit-card-label">Ativos</div><div class="bit-card-value">' + ativos + '</div></div></div>' +
      '<div class="bit-card c-red"><div class="bit-card-icon i-red">' + SVG_ICONS.alert + '</div><div class="bit-card-info"><div class="bit-card-label">Expirados</div><div class="bit-card-value">' + expirados + '</div></div></div>' +
      '<div class="bit-card c-gold"><div class="bit-card-icon i-gold">' + SVG_ICONS.dollar + '</div><div class="bit-card-info"><div class="bit-card-label">Receita Total</div><div class="bit-card-value">' + formatBRL(totalReceita) + '</div></div></div>';
  } else if (currentTab === 'cp') {
    var abertos = 0, pagos = 0, vencidos = 0, totalAberto = 0;
    for (var j = 0; j < cpData.length; j++) {
      var c = cpData[j];
      if (c.situacao == 1) { pagos++; }
      else if (c.vencimento && c.vencimento < today) { vencidos++; totalAberto += (Number(c.valor) || 0) - (Number(c.valor_pago) || 0); }
      else { abertos++; totalAberto += (Number(c.valor) || 0) - (Number(c.valor_pago) || 0); }
    }
    html =
      '<div class="bit-card c-blue"><div class="bit-card-icon i-blue">' + SVG_ICONS.clipboard + '</div><div class="bit-card-info"><div class="bit-card-label">Total</div><div class="bit-card-value">' + cpData.length + '</div></div></div>' +
      '<div class="bit-card c-gold"><div class="bit-card-icon i-gold">' + SVG_ICONS.clock + '</div><div class="bit-card-info"><div class="bit-card-label">Abertos</div><div class="bit-card-value">' + abertos + '</div></div></div>' +
      '<div class="bit-card c-red"><div class="bit-card-icon i-red">' + SVG_ICONS.alert + '</div><div class="bit-card-info"><div class="bit-card-label">Vencidos</div><div class="bit-card-value">' + vencidos + '</div></div></div>' +
      '<div class="bit-card c-green"><div class="bit-card-icon i-green">' + SVG_ICONS.check + '</div><div class="bit-card-info"><div class="bit-card-label">Pagos</div><div class="bit-card-value">' + pagos + '</div></div></div>';
  } else if (currentTab === 'cr') {
    var crAbertos = 0, recebidos = 0, crVencidos = 0, crTotalAberto = 0;
    for (var k = 0; k < crData.length; k++) {
      var cr = crData[k];
      if (cr.situacao == 1) { recebidos++; }
      else if (cr.vencimento && cr.vencimento < today) { crVencidos++; crTotalAberto += (Number(cr.valor) || 0) - (Number(cr.valor_recebido) || 0); }
      else { crAbertos++; crTotalAberto += (Number(cr.valor) || 0) - (Number(cr.valor_recebido) || 0); }
    }
    html =
      '<div class="bit-card c-blue"><div class="bit-card-icon i-blue">' + SVG_ICONS.clipboard + '</div><div class="bit-card-info"><div class="bit-card-label">Total</div><div class="bit-card-value">' + crData.length + '</div></div></div>' +
      '<div class="bit-card c-gold"><div class="bit-card-icon i-gold">' + SVG_ICONS.clock + '</div><div class="bit-card-info"><div class="bit-card-label">Abertos</div><div class="bit-card-value">' + crAbertos + '</div></div></div>' +
      '<div class="bit-card c-red"><div class="bit-card-icon i-red">' + SVG_ICONS.alert + '</div><div class="bit-card-info"><div class="bit-card-label">Vencidos</div><div class="bit-card-value">' + crVencidos + '</div></div></div>' +
      '<div class="bit-card c-green"><div class="bit-card-icon i-green">' + SVG_ICONS.check + '</div><div class="bit-card-info"><div class="bit-card-label">Recebidos</div><div class="bit-card-value">' + recebidos + '</div></div></div>';
  }

  container.innerHTML = html;
}

/* ── Dynamic Filter Rendering ─────── */

function renderFilters() {
  var today = todayStr();

  if (currentTab === 'gestao') {
    var ativos = 0, expirados = 0;
    for (var i = 0; i < gestaoData.length; i++) {
      var g = gestaoData[i];
      if (g.data_expiracao && g.data_expiracao < today) expirados++;
      else ativos++;
    }
    var el = document.getElementById('gestao-filters');
    el.innerHTML =
      '<button class="bit-filter' + (currentFilter === 'todos' ? ' active' : '') + '" onclick="setFilter(\'todos\')">Todos <span class="fcount">' + gestaoData.length + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'ativos' ? ' active' : '') + '" onclick="setFilter(\'ativos\')">Ativos <span class="fcount">' + ativos + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'expirados' ? ' active' : '') + '" onclick="setFilter(\'expirados\')">Expirados <span class="fcount">' + expirados + '</span></button>';
  } else if (currentTab === 'cp') {
    var cpAbertos = 0, cpPagos = 0, cpVencidos = 0;
    for (var j = 0; j < cpData.length; j++) {
      var c = cpData[j];
      if (c.situacao == 1) cpPagos++;
      else if (c.vencimento && c.vencimento < today) cpVencidos++;
      else cpAbertos++;
    }
    var el2 = document.getElementById('cp-filters');
    el2.innerHTML =
      '<button class="bit-filter' + (currentFilter === 'todos' ? ' active' : '') + '" onclick="setFilter(\'todos\')">Todos <span class="fcount">' + cpData.length + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'abertos' ? ' active' : '') + '" onclick="setFilter(\'abertos\')">Abertos <span class="fcount">' + cpAbertos + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'vencidos' ? ' active' : '') + '" onclick="setFilter(\'vencidos\')">Vencidos <span class="fcount">' + cpVencidos + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'pagos' ? ' active' : '') + '" onclick="setFilter(\'pagos\')">Pagos <span class="fcount">' + cpPagos + '</span></button>';
  } else if (currentTab === 'cr') {
    var crAbertos = 0, crRecebidos = 0, crVencidos = 0;
    for (var k = 0; k < crData.length; k++) {
      var r = crData[k];
      if (r.situacao == 1) crRecebidos++;
      else if (r.vencimento && r.vencimento < today) crVencidos++;
      else crAbertos++;
    }
    var el3 = document.getElementById('cr-filters');
    el3.innerHTML =
      '<button class="bit-filter' + (currentFilter === 'todos' ? ' active' : '') + '" onclick="setFilter(\'todos\')">Todos <span class="fcount">' + crData.length + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'abertos' ? ' active' : '') + '" onclick="setFilter(\'abertos\')">Abertos <span class="fcount">' + crAbertos + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'vencidos' ? ' active' : '') + '" onclick="setFilter(\'vencidos\')">Vencidos <span class="fcount">' + crVencidos + '</span></button>' +
      '<button class="bit-filter' + (currentFilter === 'recebidos' ? ' active' : '') + '" onclick="setFilter(\'recebidos\')">Recebidos <span class="fcount">' + crRecebidos + '</span></button>';
  }
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

  if (tab === 'gestao') loadGestao();
  else if (tab === 'cp') loadContasPagar();
  else if (tab === 'cr') loadContasReceber();
}

/* ── Data Loading ───────────────────── */

async function loadGestao() {
  try {
    var result = await sb
      .from('bit_gestao')
      .select('*, bit_clientes(id,nome,whatsapp), bit_servicos(id,descricao)')
      .order('data_expiracao', { ascending: false });
    if (result.error) throw result.error;
    gestaoData = result.data || [];
    renderFilters();
    renderGestao();
    updateSummary();
  } catch (e) {
    console.error('Erro ao carregar gestao:', e);
    showToast('Erro ao carregar gestão', 'error');
  }
}

async function loadContasPagar() {
  try {
    var result = await sb
      .from('bit_contas_pagar')
      .select('*')
      .order('vencimento', { ascending: false });
    if (result.error) throw result.error;
    cpData = result.data || [];
    renderFilters();
    renderContasPagar();
    updateSummary();
  } catch (e) {
    console.error('Erro ao carregar contas a pagar:', e);
    showToast('Erro ao carregar contas a pagar', 'error');
  }
}

async function loadContasReceber() {
  try {
    var result = await sb
      .from('bit_contas_receber')
      .select('*, bit_clientes(id,nome)')
      .order('vencimento', { ascending: false });
    if (result.error) throw result.error;
    crData = result.data || [];
    renderFilters();
    renderContasReceber();
    updateSummary();
  } catch (e) {
    console.error('Erro ao carregar contas a receber:', e);
    showToast('Erro ao carregar contas a receber', 'error');
  }
}

async function loadClientes() {
  try {
    var result = await sb
      .from('bit_clientes')
      .select('id, nome, whatsapp')
      .eq('ativo', true)
      .order('nome');
    if (result.error) throw result.error;
    clientesList = result.data || [];
  } catch (e) {
    console.error('Erro ao carregar clientes:', e);
  }
}

async function loadServicos() {
  try {
    var result = await sb
      .from('bit_servicos')
      .select('id, descricao, valor')
      .eq('ativo', true)
      .order('descricao');
    if (result.error) throw result.error;
    servicosList = result.data || [];
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
    tbody.innerHTML = '<tr><td colspan="7"><div class="bit-empty">' + SVG_ICONS.empty + '<div class="bit-empty-text">Nenhum registro encontrado</div></div></td></tr>';
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
    var wppCell = '';
    if (wppClean) {
      wppCell = '<div class="bit-wpp-cell"><span class="bit-wpp-num">' + formatWhatsApp(whatsapp) + '</span>' +
        '<a href="https://wa.me/' + wppClean + '" target="_blank" class="bit-ab a-wpp" title="WhatsApp">' + SVG_ICONS.whatsapp + '</a></div>';
    } else {
      wppCell = '<span class="bit-wpp-num">—</span>';
    }

    // Login/senha credentials
    var cred = '';
    if (r.login || r.senha) {
      cred = '<div class="bit-cred">';
      if (r.login) {
        cred += SVG_ICONS.user + ' <code>' + escapeHtml(r.login) + '</code>' +
          '<button class="bit-ab a-copy" onclick="copyText(\'' + escapeHtml(r.login).replace(/'/g, "\\'") + '\')" title="Copiar login">' + SVG_ICONS.copy + '</button>';
      }
      if (r.senha) {
        cred += ' ' + SVG_ICONS.lock + ' <code>' + escapeHtml(r.senha) + '</code>' +
          '<button class="bit-ab a-copy" onclick="copyText(\'' + escapeHtml(r.senha).replace(/'/g, "\\'") + '\')" title="Copiar senha">' + SVG_ICONS.copy + '</button>';
      }
      cred += '</div>';
    }

    html += '<tr>' +
      '<td class="td-name"><strong>' + escapeHtml(clienteNome) + '</strong>' + cred + '</td>' +
      '<td>' + wppCell + '</td>' +
      '<td>' + escapeHtml(servicoDesc) + '</td>' +
      '<td class="td-r">' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.data_expiracao) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td class="td-a"><div class="bit-actions">' +
        '<button class="bit-ab a-edit" onclick="openModal(\'gestao\',' + r.id + ')" title="Editar">' + SVG_ICONS.edit + '</button>' +
        '<button class="bit-ab a-del" onclick="deleteRecord(\'bit_gestao\',' + r.id + ')" title="Excluir">' + SVG_ICONS.trash + '</button>' +
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
    tbody.innerHTML = '<tr><td colspan="8"><div class="bit-empty">' + SVG_ICONS.empty + '<div class="bit-empty-text">Nenhum registro encontrado</div></div></td></tr>';
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
      quitarBtn = '<button class="bit-ab a-ok" onclick="quitarConta(' + r.id + ',\'pagar\')" title="Quitar">' + SVG_ICONS.checkCircle + '</button>';
    } else {
      badge = '<span class="badge badge-aberto">Aberto</span>';
      quitarBtn = '<button class="bit-ab a-ok" onclick="quitarConta(' + r.id + ',\'pagar\')" title="Quitar">' + SVG_ICONS.checkCircle + '</button>';
    }

    var valorAberto = (Number(r.valor) || 0) - (Number(r.valor_pago) || 0);

    html += '<tr>' +
      '<td class="td-name"><strong>' + escapeHtml(r.fornecedor || '—') + '</strong></td>' +
      '<td>' + escapeHtml(r.num_documento || '—') + '</td>' +
      '<td class="td-r">' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.vencimento) + '</td>' +
      '<td class="td-r">' + formatBRL(r.valor_pago) + '</td>' +
      '<td class="td-r">' + formatBRL(valorAberto) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td class="td-a"><div class="bit-actions">' +
        quitarBtn +
        '<button class="bit-ab a-edit" onclick="openModal(\'cp\',' + r.id + ')" title="Editar">' + SVG_ICONS.edit + '</button>' +
        '<button class="bit-ab a-del" onclick="deleteRecord(\'bit_contas_pagar\',' + r.id + ')" title="Excluir">' + SVG_ICONS.trash + '</button>' +
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
    tbody.innerHTML = '<tr><td colspan="8"><div class="bit-empty">' + SVG_ICONS.empty + '<div class="bit-empty-text">Nenhum registro encontrado</div></div></td></tr>';
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
      receberBtn = '<button class="bit-ab a-ok" onclick="quitarConta(' + r.id + ',\'receber\')" title="Receber">' + SVG_ICONS.checkCircle + '</button>';
    } else {
      badge = '<span class="badge badge-aberto">Aberto</span>';
      receberBtn = '<button class="bit-ab a-ok" onclick="quitarConta(' + r.id + ',\'receber\')" title="Receber">' + SVG_ICONS.checkCircle + '</button>';
    }

    var valorAberto = (Number(r.valor) || 0) - (Number(r.valor_recebido) || 0);

    html += '<tr>' +
      '<td class="td-name"><strong>' + escapeHtml(clienteNome) + '</strong></td>' +
      '<td>' + escapeHtml(r.num_documento || '—') + '</td>' +
      '<td class="td-r">' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.vencimento) + '</td>' +
      '<td class="td-r">' + formatBRL(r.valor_recebido) + '</td>' +
      '<td class="td-r">' + formatBRL(valorAberto) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td class="td-a"><div class="bit-actions">' +
        receberBtn +
        '<button class="bit-ab a-edit" onclick="openModal(\'cr\',' + r.id + ')" title="Editar">' + SVG_ICONS.edit + '</button>' +
        '<button class="bit-ab a-del" onclick="deleteRecord(\'bit_contas_receber\',' + r.id + ')" title="Excluir">' + SVG_ICONS.trash + '</button>' +
      '</div></td>' +
    '</tr>';
  }
  tbody.innerHTML = html;
}

/* ── Filtering & Search ─────────────── */

function setFilter(filter) {
  currentFilter = filter;
  renderFilters();

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
    title = editingId ? 'Editar Gestão' : 'Nova Gestão';
    var clienteOpts = '<option value="">Selecione o cliente</option>';
    for (var i = 0; i < clientesList.length; i++) {
      clienteOpts += '<option value="' + clientesList[i].id + '">' + escapeHtml(clientesList[i].nome) + '</option>';
    }
    var servicoOpts = '<option value="">Selecione o serviço</option>';
    for (var j = 0; j < servicosList.length; j++) {
      servicoOpts += '<option value="' + servicosList[j].id + '">' + escapeHtml(servicosList[j].descricao) + ' (' + formatBRL(servicosList[j].valor) + ')</option>';
    }
    bodyHtml =
      '<label>Cliente</label><select id="m-cliente">' + clienteOpts + '</select>' +
      '<label>Serviço</label><select id="m-servico" onchange="preencherValorServico()">' + servicoOpts + '</select>' +
      '<label>Valor (R$)</label><input type="number" id="m-valor" step="0.01" min="0" placeholder="0.00">' +
      '<label>Data de Expiração</label><input type="date" id="m-expiracao">' +
      '<label>Login</label><input type="text" id="m-login" placeholder="Login de acesso">' +
      '<label>Senha</label><input type="text" id="m-senha" placeholder="Senha de acesso">' +
      '<label>Observação</label><textarea id="m-obs" placeholder="Observações..."></textarea>';
  } else if (type === 'cp') {
    title = editingId ? 'Editar Conta a Pagar' : 'Nova Conta a Pagar';
    bodyHtml =
      '<label>Fornecedor</label><input type="text" id="m-fornecedor" placeholder="Nome do fornecedor">' +
      '<label>Nº Documento</label><input type="text" id="m-numdoc" placeholder="Nº do documento">' +
      '<label>Valor (R$)</label><input type="number" id="m-valor" step="0.01" min="0" placeholder="0.00">' +
      '<label>Emissão</label><input type="date" id="m-emissao">' +
      '<label>Vencimento</label><input type="date" id="m-vencimento">' +
      '<label>Observação</label><textarea id="m-obs" placeholder="Observações..."></textarea>';
  } else if (type === 'cr') {
    title = editingId ? 'Editar Conta a Receber' : 'Nova Conta a Receber';
    var crClienteOpts = '<option value="">Selecione o cliente</option>';
    for (var k = 0; k < clientesList.length; k++) {
      crClienteOpts += '<option value="' + clientesList[k].id + '">' + escapeHtml(clientesList[k].nome) + '</option>';
    }
    bodyHtml =
      '<label>Cliente</label><select id="m-cliente">' + crClienteOpts + '</select>' +
      '<label>Nº Documento</label><input type="text" id="m-numdoc" placeholder="Nº do documento">' +
      '<label>Valor (R$)</label><input type="number" id="m-valor" step="0.01" min="0" placeholder="0.00">' +
      '<label>Emissão</label><input type="date" id="m-emissao">' +
      '<label>Vencimento</label><input type="date" id="m-vencimento">' +
      '<label>Observação</label><textarea id="m-obs" placeholder="Observações..."></textarea>';
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
        showToast('Selecione cliente e serviço', 'error');
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
    var result = await sb.from(table).delete().eq('id', id);
    if (result.error) throw result.error;

    showToast('Registro excluído!', 'success');

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

    var result = await sb.from(table).update(payload).eq('id', id);
    if (result.error) throw result.error;

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
