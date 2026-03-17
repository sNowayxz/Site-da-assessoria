/* ═══════════════════════════════════════════
   Extensões — Google Sheets Integration v2
   ═══════════════════════════════════════════ */

var API_URL = localStorage.getItem('extensoes_api_url') || '';
var _extensoes = [];

// ── Init ──
(function init() {
  var urlInput = document.getElementById('apps-script-url');
  var configBar = document.getElementById('config-bar');

  if (API_URL) {
    urlInput.value = API_URL;
    configBar.classList.add('hidden');
    loadExtensoes();
  } else {
    configBar.classList.remove('hidden');
    document.getElementById('extensoes-list').innerHTML =
      '<div class="empty-card">⚙️ Configure a URL do Google Apps Script acima para começar.</div>';
  }
})();

function showConfig() {
  var bar = document.getElementById('config-bar');
  bar.classList.toggle('hidden');
}

function saveApiUrl() {
  var url = document.getElementById('apps-script-url').value.trim();
  if (!url) return alert('Cole a URL do Google Apps Script.');
  localStorage.setItem('extensoes_api_url', url);
  API_URL = url;
  document.getElementById('config-bar').classList.add('hidden');
  loadExtensoes();
}

// ── Fetch Data ──
async function loadExtensoes() {
  if (!API_URL) return;
  document.getElementById('extensoes-list').innerHTML =
    '<div class="empty-card">Carregando dados da planilha...</div>';

  try {
    var res = await fetch(API_URL + '?action=list');
    var json = await res.json();
    _extensoes = json.data || [];
    updateStats();
    applyFilters();
  } catch (err) {
    console.error('Erro ao carregar extensões:', err);
    document.getElementById('extensoes-list').innerHTML =
      '<div class="empty-card">❌ Erro ao conectar. Verifique a URL do Apps Script.<br><button class="btn-reconfig" onclick="showConfig()" style="margin-top:10px">⚙️ Reconfigurar</button></div>';
  }
}

// ── Stats ──
function updateStats() {
  var total = _extensoes.length;
  var pagos = 0, urgentes = 0, horas = 0;

  _extensoes.forEach(function (r) {
    if ((r.status_pgto || '').toUpperCase() === 'PAGO') pagos++;
    var urg = (r.urgencia || '').toLowerCase();
    if (urg === 'sim' || urg === 'yes') urgentes++;
    var h = parseFloat((r.horas_contratadas || '').replace(/[^\d.,]/g, '').replace(',', '.'));
    if (!isNaN(h)) horas += h;
  });

  document.getElementById('count-total').textContent = total;
  document.getElementById('count-pagos').textContent = pagos;
  document.getElementById('count-urgentes').textContent = urgentes;
  document.getElementById('count-horas').textContent = horas.toLocaleString('pt-BR') + 'h';
}

// ── Render Cards ──
function renderCards(data) {
  var container = document.getElementById('extensoes-list');
  document.getElementById('filter-count').textContent = data.length + ' aluno' + (data.length !== 1 ? 's' : '');

  if (!data.length) {
    container.innerHTML = '<div class="empty-card">Nenhum aluno encontrado.</div>';
    return;
  }

  container.innerHTML = data.map(function (r) {
    var nome = esc(r.nome || '—');
    var ra = esc(r.ra || '');
    var assessor = esc(r.assessor || '');
    var statusPgto = (r.status_pgto || '').toUpperCase();
    var isPago = statusPgto === 'PAGO';
    var urgencia = (r.urgencia || '').toLowerCase();
    var isUrgente = urgencia === 'sim' || urgencia === 'yes';

    // Hours
    var hContratadas = r.horas_contratadas || '0';
    var hFeitas = r.horas_feitas || '0';
    var numC = parseFloat(hContratadas.replace(/[^\d.,]/g, '').replace(',', '.')) || 1;
    var numF = parseFloat((hFeitas || '0').replace(/[^\d.,]/g, '').replace(',', '.')) || 0;
    var pct = Math.min(100, Math.round((numF / numC) * 100));
    var barClass = pct < 30 ? 'low' : pct < 70 ? 'mid' : '';

    // Values
    var valorPago = esc(r.valor_pago || '—');
    var valorRestante = esc(r.valor_restante || '');

    // Initial for avatar
    var initial = (r.nome || '?').charAt(0).toUpperCase();

    // Badges
    var badges = '';
    if (isPago) badges += '<span class="badge badge-pago">Pago</span>';
    else badges += '<span class="badge badge-pendente">Pendente</span>';
    if (isUrgente) badges += '<span class="badge badge-urgente">Urgente</span>';

    var rowIndex = r._rowIndex;

    return '<div class="ext-card" onclick="openEditModal(' + rowIndex + ')">' +
      '<div class="ext-card-main">' +
        '<div class="ext-avatar ' + (isPago ? 'pago' : 'pendente') + '">' + initial + '</div>' +
        '<div class="ext-info">' +
          '<div class="ext-name">' + nome + '</div>' +
          '<div class="ext-sub">' +
            (ra ? '<span>RA: ' + ra + '</span>' : '') +
            (assessor ? '<span>' + assessor + '</span>' : '') +
            '<span>' + esc(hFeitas) + ' / ' + esc(hContratadas) + '</span>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="ext-card-right">' +
        '<div class="ext-hours">' +
          '<div class="ext-hours-text">' + pct + '%</div>' +
          '<div class="ext-hours-bar"><div class="ext-hours-fill ' + barClass + '" style="width:' + pct + '%"></div></div>' +
        '</div>' +
        '<div class="ext-valor">' + valorPago + '</div>' +
        '<div class="ext-badges">' + badges + '</div>' +
      '</div>' +
    '</div>';
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

    var rUrg = (r.urgencia || '').toLowerCase();
    var matchUrg = !urg ||
      (urg === 'sim' && (rUrg === 'sim' || rUrg === 'yes')) ||
      (urg === 'aguardando' && rUrg.indexOf('aguardando') > -1);

    return matchQ && matchPgto && matchUrg;
  });

  renderCards(filtered);
}

// ── Modal: Edit ──
function openEditModal(rowIndex) {
  var row = _extensoes.find(function (r) { return r._rowIndex === rowIndex; });
  if (!row) return;

  document.getElementById('modal-ext-title').textContent = row.nome || 'Aluno';
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
  document.getElementById('modal-ext-title').textContent = 'Novo Aluno';
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

  var btn = document.querySelector('.btn-save');
  btn.textContent = 'Salvando...';
  btn.disabled = true;

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
  } finally {
    btn.textContent = '💾 Salvar';
    btn.disabled = false;
  }
}

// ── Delete ──
async function handleDelete() {
  var rowIndex = document.getElementById('ext-row-index').value;
  if (!rowIndex) return;
  if (!confirm('Remover este aluno da planilha?')) return;

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
