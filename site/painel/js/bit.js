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
  var parts = dateStr.split('-');
  if (parts.length !== 3) return dateStr;
  return parts[2] + '/' + parts[1] + '/' + parts[0];
}

function formatWhatsApp(num) {
  if (!num) return '—';
  var n = String(num).replace(/\D/g, '');
  if (n.length === 11) return '(' + n.slice(0, 2) + ') ' + n.slice(2, 7) + '-' + n.slice(7);
  if (n.length === 10) return '(' + n.slice(0, 2) + ') ' + n.slice(2, 6) + '-' + n.slice(6);
  return n;
}

function cleanPhone(num) {
  if (!num) return '';
  return String(num).replace(/\D/g, '');
}

function todayStr() {
  var d = new Date();
  var mm = String(d.getMonth() + 1).padStart(2, '0');
  var dd = String(d.getDate()).padStart(2, '0');
  return d.getFullYear() + '-' + mm + '-' + dd;
}

/* ── Tab Switching ──────────────────── */

function switchTab(tab) {
  currentTab = tab;
  currentFilter = 'todos';

  // Update tab buttons
  var tabs = document.querySelectorAll('.bit-tab');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].classList.remove('active');
  }
  document.getElementById('tab-btn-' + tab).classList.add('active');

  // Show/hide tab content
  var contents = document.querySelectorAll('.bit-tab-content');
  for (var j = 0; j < contents.length; j++) {
    contents[j].classList.remove('active');
  }
  document.getElementById('tab-' + tab).classList.add('active');

  // Reset filter buttons
  var activeContent = document.getElementById('tab-' + tab);
  var filters = activeContent.querySelectorAll('.bit-filter');
  for (var k = 0; k < filters.length; k++) {
    filters[k].classList.remove('active');
    if (filters[k].textContent === 'Todos') filters[k].classList.add('active');
  }

  // Load data
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
      .order('created_at', { ascending: false });
    if (error) throw error;
    gestaoData = data || [];
    renderGestao();
  } catch (e) {
    console.error('Erro ao carregar gestão:', e);
    showToast('Erro ao carregar gestão', 'error');
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
    console.error('Erro ao carregar serviços:', e);
  }
}

/* ── Rendering ──────────────────────── */

function renderGestao() {
  var tbody = document.getElementById('gestao-table');
  var today = todayStr();
  var search = (document.getElementById('bit-search').value || '').toLowerCase();

  var filtered = gestaoData.filter(function (r) {
    // Filter by search
    var nome = (r.bit_clientes && r.bit_clientes.nome) ? r.bit_clientes.nome.toLowerCase() : '';
    if (search && nome.indexOf(search) === -1) return false;

    // Filter by status
    var expired = r.data_expiracao && r.data_expiracao < today;
    if (currentFilter === 'ativos' && expired) return false;
    if (currentFilter === 'expirados' && !expired) return false;
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Nenhum registro encontrado</td></tr>';
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
      ? '<span class="badge-expirado">Expirado</span>'
      : '<span class="badge-ativo">Ativo</span>';

    var wppClean = cleanPhone(whatsapp);
    var wppLink = wppClean
      ? '<a href="https://wa.me/55' + wppClean + '" target="_blank" class="bit-btn bit-btn-wpp" title="WhatsApp">📱</a>'
      : '';

    html += '<tr>' +
      '<td>' + clienteNome + '</td>' +
      '<td>' + formatWhatsApp(whatsapp) + ' ' + wppLink + '</td>' +
      '<td>' + servicoDesc + '</td>' +
      '<td>' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.data_expiracao) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td>' +
        '<button class="bit-btn bit-btn-edit" onclick="openModal(\'gestao\',' + r.id + ')">Editar</button> ' +
        '<button class="bit-btn bit-btn-del" onclick="deleteRecord(\'bit_gestao\',' + r.id + ')">Excluir</button>' +
      '</td>' +
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
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhum registro encontrado</td></tr>';
    return;
  }

  var html = '';
  for (var i = 0; i < filtered.length; i++) {
    var r = filtered[i];
    var pago = r.situacao == 1;
    var vencido = !pago && r.vencimento && r.vencimento < today;
    var badge, quitarBtn = '';

    if (pago) {
      badge = '<span class="badge-pago">Pago</span>';
    } else if (vencido) {
      badge = '<span class="badge-vencido">Vencido</span>';
      quitarBtn = '<button class="bit-btn bit-btn-quitar" onclick="quitarConta(' + r.id + ',\'pagar\')">Quitar</button> ';
    } else {
      badge = '<span class="badge-aberto">Aberto</span>';
      quitarBtn = '<button class="bit-btn bit-btn-quitar" onclick="quitarConta(' + r.id + ',\'pagar\')">Quitar</button> ';
    }

    var valorAberto = (Number(r.valor) || 0) - (Number(r.valor_pago) || 0);

    html += '<tr>' +
      '<td>' + (r.fornecedor || '—') + '</td>' +
      '<td>' + (r.num_documento || '—') + '</td>' +
      '<td>' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.vencimento) + '</td>' +
      '<td>' + formatBRL(r.valor_pago) + '</td>' +
      '<td>' + formatBRL(valorAberto) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td>' +
        quitarBtn +
        '<button class="bit-btn bit-btn-edit" onclick="openModal(\'cp\',' + r.id + ')">Editar</button> ' +
        '<button class="bit-btn bit-btn-del" onclick="deleteRecord(\'bit_contas_pagar\',' + r.id + ')">Excluir</button>' +
      '</td>' +
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
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhum registro encontrado</td></tr>';
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
      badge = '<span class="badge-recebido">Recebido</span>';
    } else if (vencido) {
      badge = '<span class="badge-vencido">Vencido</span>';
      receberBtn = '<button class="bit-btn bit-btn-quitar" onclick="quitarConta(' + r.id + ',\'receber\')">Receber</button> ';
    } else {
      badge = '<span class="badge-aberto">Aberto</span>';
      receberBtn = '<button class="bit-btn bit-btn-quitar" onclick="quitarConta(' + r.id + ',\'receber\')">Receber</button> ';
    }

    var valorAberto = (Number(r.valor) || 0) - (Number(r.valor_recebido) || 0);

    html += '<tr>' +
      '<td>' + clienteNome + '</td>' +
      '<td>' + (r.num_documento || '—') + '</td>' +
      '<td>' + formatBRL(r.valor) + '</td>' +
      '<td>' + formatDate(r.vencimento) + '</td>' +
      '<td>' + formatBRL(r.valor_recebido) + '</td>' +
      '<td>' + formatBRL(valorAberto) + '</td>' +
      '<td>' + badge + '</td>' +
      '<td>' +
        receberBtn +
        '<button class="bit-btn bit-btn-edit" onclick="openModal(\'cr\',' + r.id + ')">Editar</button> ' +
        '<button class="bit-btn bit-btn-del" onclick="deleteRecord(\'bit_contas_receber\',' + r.id + ')">Excluir</button>' +
      '</td>' +
    '</tr>';
  }
  tbody.innerHTML = html;
}

/* ── Filtering & Search ─────────────── */

function setFilter(filter) {
  currentFilter = filter;

  // Update active filter button in current tab
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
    title = editingId ? 'Editar Gestão' : 'Nova Gestão';
    var clienteOpts = '<option value="">Selecione o cliente</option>';
    for (var i = 0; i < clientesList.length; i++) {
      clienteOpts += '<option value="' + clientesList[i].id + '">' + clientesList[i].nome + '</option>';
    }
    var servicoOpts = '<option value="">Selecione o serviço</option>';
    for (var j = 0; j < servicosList.length; j++) {
      servicoOpts += '<option value="' + servicosList[j].id + '">' + servicosList[j].descricao + ' (' + formatBRL(servicosList[j].valor) + ')</option>';
    }
    bodyHtml =
      '<label>Cliente</label><select id="m-cliente">' + clienteOpts + '</select>' +
      '<label>Serviço</label><select id="m-servico" onchange="preencherValorServico()">' + servicoOpts + '</select>' +
      '<label>Valor (R$)</label><input type="number" id="m-valor" step="0.01" min="0" placeholder="0.00">' +
      '<label>Data de Expiração</label><input type="date" id="m-expiracao">' +
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
      crClienteOpts += '<option value="' + clientesList[k].id + '">' + clientesList[k].nome + '</option>';
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

  // If editing, fill the form
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
    document.getElementById('m-expiracao').value = rec.data_expiracao || '';
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
      // Don't overwrite valor_pago/valor_recebido/situacao on edit
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
      // Find the record to get valor
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
