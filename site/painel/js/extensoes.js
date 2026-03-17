/* ═══════════════════════════════════════════
   Extensões — Google Sheets Integration
   ═══════════════════════════════════════════ */

var API_URL = localStorage.getItem('extensoes_api_url') || '';
var _extensoes = [];

// ── Init ──
(function init() {
  var urlInput = document.getElementById('apps-script-url');
  var configBar = document.getElementById('config-bar');

  if (API_URL) {
    urlInput.value = API_URL;
    configBar.classList.add('connected');
    loadExtensoes();
  }
})();

function saveApiUrl() {
  var url = document.getElementById('apps-script-url').value.trim();
  if (!url) return alert('Cole a URL do Google Apps Script.');
  localStorage.setItem('extensoes_api_url', url);
  API_URL = url;
  document.getElementById('config-bar').classList.add('connected');
  loadExtensoes();
}

// ── Fetch Data ──
async function loadExtensoes() {
  if (!API_URL) return;
  var tbody = document.getElementById('extensoes-table');
  tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Carregando...</td></tr>';

  try {
    var res = await fetch(API_URL + '?action=list');
    var json = await res.json();
    _extensoes = json.data || [];
    updateStats();
    renderTable(_extensoes);
  } catch (err) {
    console.error('Erro ao carregar extensões:', err);
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Erro ao conectar. Verifique a URL do Apps Script.</td></tr>';
  }
}

// ── Stats ──
function updateStats() {
  var total = _extensoes.length;
  var pagos = 0;
  var urgentes = 0;
  var horas = 0;

  _extensoes.forEach(function (r) {
    if ((r.status_pgto || '').toUpperCase() === 'PAGO') pagos++;
    if ((r.urgencia || '').toLowerCase().indexOf('sim') > -1 || (r.urgencia || '').toLowerCase() === 'sim') urgentes++;
    var h = parseFloat((r.horas_contratadas || '').replace(/[^\d]/g, ''));
    if (!isNaN(h)) horas += h;
  });

  document.getElementById('count-total').textContent = total;
  document.getElementById('count-pagos').textContent = pagos;
  document.getElementById('count-urgentes').textContent = urgentes;
  document.getElementById('count-horas').textContent = horas.toLocaleString('pt-BR') + 'h';
}

// ── Render Table ──
function renderTable(data) {
  var tbody = document.getElementById('extensoes-table');
  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nenhum aluno encontrado.</td></tr>';
    return;
  }

  tbody.innerHTML = data.map(function (r, i) {
    var nome = esc(r.nome || '—');
    var ra = esc(r.ra || '—');
    var assessor = esc(r.assessor || '—');
    var hContratadas = esc(r.horas_contratadas || '0');
    var hFeitas = esc(r.horas_feitas || '0');
    var hRestantes = esc(r.horas_restantes || '0');
    var valorPago = esc(r.valor_pago || 'R$ 0');
    var statusPgto = (r.status_pgto || '').toUpperCase();
    var urgencia = r.urgencia || '';

    // Progress bar
    var numContratadas = parseFloat((r.horas_contratadas || '0').replace(/[^\d]/g, '')) || 1;
    var numFeitas = parseFloat((r.horas_feitas || '0').replace(/[^\d]/g, '')) || 0;
    var pct = Math.min(100, Math.round((numFeitas / numContratadas) * 100));

    var badgePgto = statusPgto === 'PAGO'
      ? '<span class="badge badge-pago">PAGO</span>'
      : '<span class="badge badge-pendente">Pendente</span>';

    var badgeUrg = '';
    if (urgencia.toLowerCase().indexOf('sim') > -1) {
      badgeUrg = '<span class="badge badge-sim">Urgente</span>';
    } else if (urgencia.toLowerCase().indexOf('aguardando') > -1) {
      badgeUrg = '<span class="badge badge-aguardando">Aguardando</span>';
    } else {
      badgeUrg = '<span class="badge badge-nao">—</span>';
    }

    var realIndex = r._rowIndex; // original row index from Apps Script

    return '<tr onclick="openEditModal(' + realIndex + ')" style="cursor:pointer;">' +
      '<td><strong>' + nome + '</strong></td>' +
      '<td>' + ra + '</td>' +
      '<td>' + assessor + '</td>' +
      '<td>' +
        '<div class="horas-bar">' +
          '<span>' + hFeitas + '/' + hContratadas + '</span>' +
          '<div class="bar-track"><div class="bar-fill" style="width:' + pct + '%"></div></div>' +
        '</div>' +
      '</td>' +
      '<td class="valor-destaque">' + valorPago + '</td>' +
      '<td>' + badgePgto + '</td>' +
      '<td>' + badgeUrg + '</td>' +
      '<td><button class="btn-outline-sm" onclick="event.stopPropagation();openEditModal(' + realIndex + ')">✏️</button></td>' +
    '</tr>';
  }).join('');
}

// ── Filters ──
document.getElementById('filter-busca').addEventListener('input', applyFilters);
document.getElementById('filter-pagamento').addEventListener('change', applyFilters);
document.getElementById('filter-urgencia').addEventListener('change', applyFilters);

function applyFilters() {
  var q = document.getElementById('filter-busca').value.toLowerCase();
  var pgto = document.getElementById('filter-pagamento').value;
  var urg = document.getElementById('filter-urgencia').value;

  var filtered = _extensoes.filter(function (r) {
    var matchQ = !q ||
      (r.nome || '').toLowerCase().indexOf(q) > -1 ||
      (r.ra || '').toLowerCase().indexOf(q) > -1 ||
      (r.assessor || '').toLowerCase().indexOf(q) > -1;

    var matchPgto = !pgto ||
      (pgto === 'PAGO' && (r.status_pgto || '').toUpperCase() === 'PAGO') ||
      (pgto === 'pendente' && (r.status_pgto || '').toUpperCase() !== 'PAGO');

    var matchUrg = !urg ||
      (r.urgencia || '').toLowerCase().indexOf(urg.toLowerCase()) > -1;

    return matchQ && matchPgto && matchUrg;
  });

  renderTable(filtered);
}

// ── Modal: Edit ──
function openEditModal(rowIndex) {
  var row = _extensoes.find(function (r) { return r._rowIndex === rowIndex; });
  if (!row) return;

  document.getElementById('modal-ext-title').textContent = 'Editar — ' + (row.nome || 'Aluno');
  document.getElementById('ext-row-index').value = rowIndex;
  document.getElementById('ext-nome').value = row.nome || '';
  document.getElementById('ext-ra').value = row.ra || '';
  document.getElementById('ext-senha').value = row.senha || '';
  document.getElementById('ext-assessor').value = row.assessor || '';
  document.getElementById('ext-horas-contratadas').value = row.horas_contratadas || '';
  document.getElementById('ext-horas-feitas').value = row.horas_feitas || '';
  document.getElementById('ext-horas-restantes').value = row.horas_restantes || '';
  document.getElementById('ext-valor-hora').value = row.valor_hora || '';
  document.getElementById('ext-valor-pago').value = row.valor_pago || '';
  document.getElementById('ext-valor-restante').value = row.valor_restante || '';
  document.getElementById('ext-status-pgto').value = row.status_pgto || '';
  document.getElementById('ext-urgencia').value = row.urgencia || 'Aguardando';
  document.getElementById('ext-tipo-pgto').value = row.tipo_pgto || '';
  document.getElementById('ext-data-inicio').value = row.data_inicio || '';
  document.getElementById('ext-sistema').value = row.sistema || 'Sim';

  document.getElementById('btn-ext-delete').style.display = 'inline-flex';
  openModal('modal-ext');
}

// ── Modal: Add ──
function openAddModal() {
  document.getElementById('modal-ext-title').textContent = 'Novo Aluno de Extensão';
  document.getElementById('ext-row-index').value = '';
  document.getElementById('form-ext').reset();
  document.getElementById('ext-urgencia').value = 'Aguardando';
  document.getElementById('ext-sistema').value = 'Sim';
  document.getElementById('btn-ext-delete').style.display = 'none';
  openModal('modal-ext');
}

// ── Save ──
async function handleSave(e) {
  e.preventDefault();
  if (!API_URL) return alert('Configure a URL do Apps Script primeiro.');

  var rowIndex = document.getElementById('ext-row-index').value;
  var rowData = {
    status_pgto: document.getElementById('ext-status-pgto').value,
    urgencia: document.getElementById('ext-urgencia').value,
    nome: document.getElementById('ext-nome').value,
    ra: document.getElementById('ext-ra').value,
    senha: document.getElementById('ext-senha').value,
    assessor: document.getElementById('ext-assessor').value,
    horas_contratadas: document.getElementById('ext-horas-contratadas').value,
    horas_feitas: document.getElementById('ext-horas-feitas').value,
    horas_restantes: document.getElementById('ext-horas-restantes').value,
    valor_hora: document.getElementById('ext-valor-hora').value,
    valor_pago: document.getElementById('ext-valor-pago').value,
    valor_restante: document.getElementById('ext-valor-restante').value,
    tipo_pgto: document.getElementById('ext-tipo-pgto').value,
    data_inicio: document.getElementById('ext-data-inicio').value,
    sistema: document.getElementById('ext-sistema').value
  };

  var action = rowIndex ? 'update' : 'add';
  var body = { action: action, data: rowData };
  if (rowIndex) body.rowIndex = parseInt(rowIndex);

  try {
    var res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify(body)
    });
    var json = await res.json();
    if (json.success) {
      closeModal('modal-ext');
      loadExtensoes();
    } else {
      alert('Erro: ' + (json.error || 'Falha ao salvar'));
    }
  } catch (err) {
    console.error('Erro ao salvar:', err);
    alert('Erro de conexão ao salvar.');
  }
}

// ── Delete ──
async function handleDelete() {
  var rowIndex = document.getElementById('ext-row-index').value;
  if (!rowIndex) return;
  if (!confirm('Remover este aluno da planilha? Essa ação não pode ser desfeita.')) return;

  try {
    var res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify({ action: 'delete', rowIndex: parseInt(rowIndex) })
    });
    var json = await res.json();
    if (json.success) {
      closeModal('modal-ext');
      loadExtensoes();
    } else {
      alert('Erro: ' + (json.error || 'Falha ao remover'));
    }
  } catch (err) {
    console.error('Erro ao remover:', err);
    alert('Erro de conexão.');
  }
}

// ── Modal helpers ──
function openModal(id) {
  document.getElementById(id).classList.add('active');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

// ── Escape HTML ──
function esc(str) {
  var d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}
