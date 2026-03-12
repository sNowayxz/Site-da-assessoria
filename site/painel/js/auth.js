/* ═══════════════════════════════════════════
   Auth — Login/Logout/Proteção de Rotas
   ═══════════════════════════════════════════ */

async function getUser() {
  var { data: { user } } = await sb.auth.getUser();
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
    window.location.href = '/painel/app.html';
  }
}

async function handleLogin(email, password) {
  var { data, error } = await sb.auth.signInWithPassword({ email: email, password: password });
  if (error) throw error;
  return data;
}

async function handleLogout() {
  await sb.auth.signOut();
  window.location.href = '/painel/';
}

function getUserName(user) {
  if (!user) return 'Assessor';
  return user.user_metadata && user.user_metadata.nome ? user.user_metadata.nome : user.email.split('@')[0];
}
