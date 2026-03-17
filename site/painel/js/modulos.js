/* ═══════════════════════════════════════════
   Módulos — Gestão de períodos acadêmicos
   ═══════════════════════════════════════════ */

var _modulos = [];

document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  await loadModulos();

  document.getElementById('btn-novo-modulo').addEventListener('click', function () {
    document.getElementById('modal-title-mod').textContent = 'Novo Módulo';
    document.getElementById('form-modulo').reset();
    document.getElementById('form-modulo').dataset.editId = '';
    openModal('modal-modulo');
  });

  document.getElementById('form-modulo').addEventListener('submit', handleSaveModulo);
});

async function loadModulos() {
  var { data, error } = await sb.from('modulos')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) { console.error(error); return; }
  _modulos = data || [];
  renderModulos(_modulos);
}

function renderModulos(modulos) {
  var container = document.getElementById('modulos-grid');
  if (!modulos.length) {
    container.innerHTML = '<div class="empty-state" style="padding:48px;text-align:center;color:#8892a4;">Nenhum módulo cadastrado</div>';
    return;
  }

  container.innerHTML = modulos.map(function (m) {
    var statusClass = m.situacao === 'aberto' ? 'badge-entregue' : 'badge-pendente';
    var statusText = m.situacao === 'aberto' ? 'Aberto' : 'Fechado';
    var dtInicio = m.dt_inicio ? new Date(m.dt_inicio + 'T12:00:00').toLocaleDateString('pt-BR') : '—';
    var dtFim = m.dt_fim ? new Date(m.dt_fim + 'T12:00:00').toLocaleDateString('pt-BR') : '—';

    return '<div class="modulo-card">' +
      '<div class="modulo-header">' +
        '<div>' +
          '<h3>' + escapeHtml(m.nome) + '</h3>' +
          '<span class="modulo-code">' + escapeHtml(m.codigo) + '</span>' +
        '</div>' +
        '<span class="badge ' + statusClass + '">' + statusText + '</span>' +
      '</div>' +
      '<div class="modulo-dates">' +
        '<span>📅 ' + dtInicio + ' — ' + dtFim + '</span>' +
      '</div>' +
      '<div class="modulo-actions">' +
        '<button class="btn btn-sm btn-outline" onclick="toggleModulo(\'' + m.id + '\', \'' + m.situacao + '\')">' +
          (m.situacao === 'aberto' ? '🔒 Fechar' : '🔓 Abrir') +
        '</button>' +
        '<button class="btn btn-sm btn-outline" onclick="editModulo(\'' + m.id + '\')">✏️ Editar</button>' +
        '<button class="btn btn-sm btn-outline" onclick="deleteModulo(\'' + m.id + '\')" style="color:#ef4444;">🗑️</button>' +
      '</div>' +
    '</div>';
  }).join('');
}

async function handleSaveModulo(e) {
  e.preventDefault();
  var form = e.target;
  var editId = form.dataset.editId;
  var data = {
    codigo: form.codigo.value.trim(),
    nome: form.nome.value.trim(),
    situacao: form.situacao.value,
    dt_inicio: form.dt_inicio.value || null,
    dt_fim: form.dt_fim.value || null
  };

  try {
    if (editId) {
      var { error } = await sb.from('modulos').update(data).eq('id', editId);
      if (error) throw error;
    } else {
      var { error } = await sb.from('modulos').insert(data);
      if (error) throw error;
    }
    closeModal('modal-modulo');
    await loadModulos();
  } catch (err) {
    alert('Erro: ' + err.message);
  }
}

async function editModulo(id) {
  var mod = _modulos.find(function (m) { return m.id === id; });
  if (!mod) return;

  document.getElementById('modal-title-mod').textContent = 'Editar Módulo';
  var form = document.getElementById('form-modulo');
  form.dataset.editId = id;
  form.codigo.value = mod.codigo;
  form.nome.value = mod.nome;
  form.situacao.value = mod.situacao;
  form.dt_inicio.value = mod.dt_inicio || '';
  form.dt_fim.value = mod.dt_fim || '';
  openModal('modal-modulo');
}

async function toggleModulo(id, current) {
  var next = current === 'aberto' ? 'fechado' : 'aberto';
  var { error } = await sb.from('modulos').update({ situacao: next }).eq('id', id);
  if (error) { alert('Erro: ' + error.message); return; }
  await loadModulos();
}

async function deleteModulo(id) {
  if (!confirm('Excluir este módulo?')) return;
  var { error } = await sb.from('modulos').delete().eq('id', id);
  if (error) { alert('Erro: ' + error.message); return; }
  await loadModulos();
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
