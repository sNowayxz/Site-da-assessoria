/* ═══════════════════════════════════════════
   Alunos — CRUD
   ═══════════════════════════════════════════ */

var currentEditId = null;

document.addEventListener('DOMContentLoaded', async function () {
  var user = await requireAuth();
  if (!user) return;

  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Load
  await loadAlunos();

  // Modal controls
  document.getElementById('btn-novo-aluno').addEventListener('click', function () {
    currentEditId = null;
    document.getElementById('modal-title').textContent = 'Novo Aluno';
    document.getElementById('form-aluno').reset();
    openModal('modal-aluno');
  });

  document.getElementById('form-aluno').addEventListener('submit', handleSaveAluno);

  // Filters
  document.getElementById('filter-curso').addEventListener('input', filterAlunos);
  document.getElementById('filter-tipo').addEventListener('change', filterAlunos);
});

async function loadAlunos() {
  var { data, error } = await supabase
    .from('alunos')
    .select('*')
    .order('nome');

  if (error) { console.error(error); return; }
  window._alunos = data || [];
  renderAlunos(window._alunos);
}

function renderAlunos(alunos) {
  var tbody = document.getElementById('alunos-table');
  if (!alunos.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nenhum aluno cadastrado</td></tr>';
    return;
  }

  tbody.innerHTML = alunos.map(function (a) {
    return '<tr>' +
      '<td>' + escapeHtml(a.ra) + '</td>' +
      '<td>' + escapeHtml(a.nome) + '</td>' +
      '<td>' + escapeHtml(a.curso || '—') + '</td>' +
      '<td><span class="badge badge-' + a.tipo + '">' + (a.tipo === 'mensalista' ? 'Mensalista' : 'Avulso') + '</span></td>' +
      '<td>' + escapeHtml(a.telefone || '—') + '</td>' +
      '<td class="actions">' +
        '<button class="btn-icon" onclick="editAluno(\'' + a.id + '\')" title="Editar">✏️</button>' +
        '<button class="btn-icon btn-danger" onclick="deleteAluno(\'' + a.id + '\')" title="Excluir">🗑️</button>' +
      '</td>' +
      '</tr>';
  }).join('');
}

function filterAlunos() {
  var curso = document.getElementById('filter-curso').value.toLowerCase();
  var tipo = document.getElementById('filter-tipo').value;
  var filtered = (window._alunos || []).filter(function (a) {
    var matchCurso = !curso || (a.curso || '').toLowerCase().includes(curso);
    var matchTipo = !tipo || a.tipo === tipo;
    return matchCurso && matchTipo;
  });
  renderAlunos(filtered);
}

async function handleSaveAluno(e) {
  e.preventDefault();
  var form = e.target;
  var data = {
    ra: form.ra.value.trim(),
    nome: form.nome.value.trim(),
    curso: form.curso.value.trim(),
    tipo: form.tipo.value,
    telefone: form.telefone.value.trim(),
    observacoes: form.observacoes.value.trim()
  };

  try {
    if (currentEditId) {
      await supabase.from('alunos').update(data).eq('id', currentEditId);
    } else {
      await supabase.from('alunos').insert(data);
    }
    closeModal('modal-aluno');
    await loadAlunos();
  } catch (err) {
    alert('Erro: ' + err.message);
  }
}

async function editAluno(id) {
  var aluno = (window._alunos || []).find(function (a) { return a.id === id; });
  if (!aluno) return;

  currentEditId = id;
  document.getElementById('modal-title').textContent = 'Editar Aluno';
  var form = document.getElementById('form-aluno');
  form.ra.value = aluno.ra;
  form.nome.value = aluno.nome;
  form.curso.value = aluno.curso || '';
  form.tipo.value = aluno.tipo;
  form.telefone.value = aluno.telefone || '';
  form.observacoes.value = aluno.observacoes || '';
  openModal('modal-aluno');
}

async function deleteAluno(id) {
  if (!confirm('Tem certeza que deseja excluir este aluno? As atividades vinculadas também serão excluídas.')) return;
  await supabase.from('alunos').delete().eq('id', id);
  await loadAlunos();
}

// Modal helpers
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

function escapeHtml(text) {
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
