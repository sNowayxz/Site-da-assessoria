/* ═══════════════════════════════════════════
   Auth — Login/Logout/Proteção de Rotas/Roles
   ═══════════════════════════════════════════ */

// ─── Cache de role ───
var _cachedRole = null;
var _cachedUser = null;

async function getUser() {
  if (_cachedUser) return _cachedUser;
  var { data: { user } } = await sb.auth.getUser();
  _cachedUser = user;
  return user;
}

async function requireAuth() {
  var user = await getUser();
  if (!user) {
    window.location.href = '/painel/';
    return null;
  }
  return user;
}

async function redirectIfLoggedIn() {
  var user = await getUser();
  if (user) {
    var role = await getUserRole(user);
    if (role === 'extensao') {
      window.location.href = '/painel/chat.html';
    } else {
      window.location.href = '/painel/app.html';
    }
  }
}

async function handleLogin(email, password) {
  var { data, error } = await sb.auth.signInWithPassword({ email: email, password: password });
  if (error) throw error;
  return data;
}

async function handleLogout() {
  _cachedRole = null;
  _cachedUser = null;
  sessionStorage.clear(); // Limpa cache de avatar e outros dados da sessão
  await sb.auth.signOut();
  window.location.href = '/painel/';
}

function getUserName(user) {
  if (!user) return 'Usuário';
  return user.user_metadata && user.user_metadata.nome ? user.user_metadata.nome : user.email.split('@')[0];
}


// ─── Role System ───

var _cachedLabel = null;

async function getUserRole(user) {
  if (_cachedRole) return _cachedRole;
  if (!user) user = await getUser();
  if (!user) return null;

  try {
    var { data, error } = await sb.from('assessores').select('role, label').eq('id', user.id).single();
    if (error || !data) {
      console.warn('[auth] Sem registro em assessores para user:', user.id);
      _cachedRole = null;
      return null;
    }
    _cachedRole = data.role;
    _cachedLabel = data.label || null;
    return _cachedRole;
  } catch (e) {
    console.error('[auth] Erro ao buscar role:', e.message);
    return null;
  }
}

function getUserLabel() {
  return _cachedLabel;
}

/**
 * Verifica autenticação + role.
 * @param {string[]} allowedRoles - ex: ['admin'], ['admin','assessor']
 * @returns {{ user, role }} ou null (redireciona)
 */
async function requireRole(allowedRoles) {
  var user = await requireAuth();
  if (!user) return null;

  var role = await getUserRole(user);

  // Se não tem role na tabela assessores, deslogar
  if (!role) {
    showToast && showToast('Conta sem permissão. Contate o administrador.', 'error');
    setTimeout(function () { handleLogout(); }, 2000);
    return null;
  }

  // dono tem mesmos acessos que admin (exceto alterar Gustavo)
  var effectiveRoles = allowedRoles.slice();
  if (effectiveRoles.indexOf('admin') !== -1 && effectiveRoles.indexOf('dono') === -1) {
    effectiveRoles.push('dono');
  }

  // Se role não é permitido nesta página, redirecionar para página padrão do role
  if (effectiveRoles.indexOf(role) === -1) {
    var defaultPages = {
      extensao: '/painel/chat.html',
      assessoria: '/painel/app.html'
    };
    window.location.href = defaultPages[role] || '/painel/app.html';
    return null;
  }

  return { user: user, role: role };
}

/**
 * Labels de role para exibição
 */
var ROLE_LABELS = {
  admin: 'Administrador',
  dono: 'Dono',
  extensao: 'Extensão',
  assessoria: 'Assessoria',
  assessor: 'Assessor',
  visualizador: 'Visualizador'
};

function getRoleLabel(role) {
  return ROLE_LABELS[role] || role;
}
