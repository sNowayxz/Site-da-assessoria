/* ═══════════════════════════════════════════
   Financeiro — Pagamentos e receita
   ═══════════════════════════════════════════ */

var _pagamentos = [];
var _alunosFin = [];

document.addEventListener('DOMContentLoaded', async function () {
  var user = await requireAuth();
  if (!user) return;

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  await loadAlunosFinanceiro();
  await loadPagamentos();

  document.getElementById('btn-novo-pagamento').addEventListener('click', function () {
    document.getElementById('modal-title-pag').textContent = 'Novo Pagamento';
    document.getElementById('form-pagamento').reset();
    document.getElementById('form-pagamento').dataset.editId = '';
    openModal('modal-pagamento');
  });

  document.getElementById('form-pagamento').addEventListener('submit', handleSavePagamento);

  document.getElementById('filter-status-pag').addEventListener('change', filterPagamentos);
  document.getElementById('filter-tipo-pag').addEventListener('change', filterPagamentos);
  document.getElementById('filter-aluno-pag').addEventListener('input', filterPagamentos);
});

async function loadAlunosFinanceiro() {
  var { data } = await sb.from('alunos').select('id, nome, ra').order('nome');
  _alunosFin = data || [];

  var select = document.getElementById('pag-aluno-id');
  select.innerHTML = '<option value="">Selecione o aluno</option>';
  _alunosFin.forEach(function (a) {
    select.innerHTML += '<option value="' + a.id + '">' + escapeHtml(a.nome) + ' (' + escapeHtml(a.ra) + ')</option>';
  });
}

async function loadPagamentos() {
  var { data, error } = await sb.from('pagamentos')
    .select('*, alunos(nome, ra)')
    .order('created_at', { ascending: false });

  if (error) { console.error(error); return; }
  _pagamentos = data || [];
  renderPagamentos(_pagamentos);
  updateFinancialCounters(_pagamentos);
}

function updateFinancialCounters(pagamentos) {
  var totalReceita = 0;
  var totalPendente = 0;
  var totalPago = 0;
  var totalAtrasado = 0;

  pagamentos.forEach(function (p) {
    var v = parseFloat(p.valor) || 0;
    if (p.status === 'pago') totalPago += v;
    if (p.status === 'pendente') totalPendente += v;
    if (p.status === 'atrasado') totalAtrasado += v;
    totalReceita += v;
  });

  var el;
  el = document.getElementById('fin-total'); if (el) el.textContent = 'R$ ' + totalReceita.toFixed(2);
  el = document.getElementById('fin-pago'); if (el) el.textContent = 'R$ ' + totalPago.toFixed(2);
  el = document.getElementById('fin-pendente'); if (el) el.textContent = 'R$ ' + totalPendente.toFixed(2);
  el = document.getElementById('fin-atrasado'); if (el) el.textContent = 'R$ ' + totalAtrasado.toFixed(2);
}

function renderPagamentos(pagamentos) {
  var tbody = document.getElementById('pagamentos-table');
  if (!pagamentos.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhum pagamento registrado</td></tr>';
    return;
  }

  tbody.innerHTML = pagamentos.map(function (p) {
    var aluno = p.alunos || {};
    var vencimento = p.dt_vencimento ? new Date(p.dt_vencimento + 'T12:00:00').toLocaleDateString('pt-BR') : '—';
    var pgto = p.dt_pagamento ? new Date(p.dt_pagamento + 'T12:00:00').toLocaleDateString('pt-BR') : '—';

    return '<tr>' +
      '<td><span class="aluno-name">' + escapeHtml(aluno.nome || '—') + '</span></td>' +
      '<td><span class="badge badge-tipo">' + formatTipoPag(p.tipo) + '</span></td>' +
      '<td><strong>R$ ' + parseFloat(p.valor).toFixed(2) + '</strong></td>' +
      '<td>' + escapeHtml(p.referencia || '—') + '</td>' +
      '<td>' + vencimento + '</td>' +
      '<td>' + pgto + '</td>' +
      '<td><span class="badge badge-' + p.status + '">' + formatStatusPag(p.status) + '</span></td>' +
      '<td class="actions">' +
        (p.status !== 'pago' ? '<button class="btn-icon btn-status" onclick="marcarPago(\'' + p.id + '\')" title="Marcar como Pago">✅</button>' : '') +
        '<button class="btn-icon" onclick="editPagamento(\'' + p.id + '\')" title="Editar">✏️</button>' +
        '<button class="btn-icon btn-danger" onclick="deletePagamento(\'' + p.id + '\')" title="Excluir">🗑️</button>' +
      '</td>' +
      '</tr>';
  }).join('');
}

function filterPagamentos() {
  var status = document.getElementById('filter-status-pag').value;
  var tipo = document.getElementById('filter-tipo-pag').value;
  var aluno = document.getElementById('filter-aluno-pag').value.toLowerCase();

  var filtered = _pagamentos.filter(function (p) {
    var alunoData = p.alunos || {};
    return (!status || p.status === status) &&
           (!tipo || p.tipo === tipo) &&
           (!aluno || (alunoData.nome || '').toLowerCase().includes(aluno));
  });
  renderPagamentos(filtered);
}

async function handleSavePagamento(e) {
  e.preventDefault();
  var form = e.target;
  var editId = form.dataset.editId;
  var data = {
    aluno_id: form.aluno_id.value,
    valor: parseFloat(form.valor.value) || 0,
    tipo: form.tipo.value,
    status: form.status.value,
    referencia: form.referencia.value.trim(),
    dt_vencimento: form.dt_vencimento.value || null,
    dt_pagamento: form.dt_pagamento.value || null,
    observacoes: form.observacoes.value.trim()
  };

  if (!data.aluno_id) { alert('Selecione um aluno'); return; }

  try {
    if (editId) {
      var { error } = await sb.from('pagamentos').update(data).eq('id', editId);
      if (error) throw error;
    } else {
      var { error } = await sb.from('pagamentos').insert(data);
      if (error) throw error;
    }
    closeModal('modal-pagamento');
    await loadPagamentos();
  } catch (err) {
    alert('Erro: ' + err.message);
  }
}

async function editPagamento(id) {
  var pag = _pagamentos.find(function (p) { return p.id === id; });
  if (!pag) return;

  document.getElementById('modal-title-pag').textContent = 'Editar Pagamento';
  var form = document.getElementById('form-pagamento');
  form.dataset.editId = id;
  form.aluno_id.value = pag.aluno_id;
  form.valor.value = pag.valor;
  form.tipo.value = pag.tipo;
  form.status.value = pag.status;
  form.referencia.value = pag.referencia || '';
  form.dt_vencimento.value = pag.dt_vencimento || '';
  form.dt_pagamento.value = pag.dt_pagamento || '';
  form.observacoes.value = pag.observacoes || '';
  openModal('modal-pagamento');
}

async function marcarPago(id) {
  var today = new Date().toISOString().split('T')[0];
  var { error } = await sb.from('pagamentos').update({ status: 'pago', dt_pagamento: today }).eq('id', id);
  if (error) { alert('Erro: ' + error.message); return; }
  await loadPagamentos();
}

async function deletePagamento(id) {
  if (!confirm('Excluir este pagamento?')) return;
  var { error } = await sb.from('pagamentos').delete().eq('id', id);
  if (error) { alert('Erro: ' + error.message); return; }
  await loadPagamentos();
}

function formatTipoPag(t) {
  var map = { avulso: 'Avulso', mensalidade: 'Mensalidade', pacote: 'Pacote' };
  return map[t] || t;
}

function formatStatusPag(s) {
  var map = { pendente: 'Pendente', pago: 'Pago', atrasado: 'Atrasado', cancelado: 'Cancelado' };
  return map[s] || s;
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
