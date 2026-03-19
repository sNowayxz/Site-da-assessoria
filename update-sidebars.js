const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, 'site', 'painel');

const newNavContent = `<nav class="sidebar-nav">
        <div class="sidebar-nav-label" data-category="geral">Vis&atilde;o Geral<svg class="sidebar-chevron" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></div>
        <div class="sidebar-category-links">
          <a href="app.html" class="sidebar-link"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>Dashboard</a>
          <a href="agenda.html" class="sidebar-link"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>Agenda</a>
          <a href="chat.html" class="sidebar-link"><svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>Chat</a>
        </div>
        <div class="sidebar-nav-label" data-category="academico">Acad&ecirc;mico<svg class="sidebar-chevron" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></div>
        <div class="sidebar-category-links">
          <a href="alunos.html" class="sidebar-link"><svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>Alunos</a>
          <a href="atividades.html" class="sidebar-link"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>Atividades</a>
          <a href="solicitar.html" class="sidebar-link"><svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>Solicitar</a>
          <a href="kanban.html" class="sidebar-link"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>Kanban</a>
          <a href="rastreio.html" class="sidebar-link"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>Rastreio</a>
        </div>
        <div class="sidebar-nav-label" data-category="extensao">Extens&atilde;o<svg class="sidebar-chevron" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></div>
        <div class="sidebar-category-links">
          <a href="acompanhar.html" class="sidebar-link"><svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>Acompanhar</a>
          <a href="extensoes.html" class="sidebar-link"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>Extens&otilde;es</a>
          <a href="depoimentos.html" class="sidebar-link"><svg viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>Depoimentos</a>
        </div>
        <div class="sidebar-nav-label" data-category="financeiro">Financeiro<svg class="sidebar-chevron" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></div>
        <div class="sidebar-category-links">
          <a href="financeiro.html" class="sidebar-link"><svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>Financeiro</a>
          <a href="pedidos.html" class="sidebar-link"><svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>Pedidos</a>
          <a href="relatorios.html" class="sidebar-link"><svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>Relat&oacute;rios</a>
        </div>
        <div class="sidebar-nav-label" data-category="sistema">Conta<svg class="sidebar-chevron" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg></div>
        <div class="sidebar-category-links">
          <a href="#" class="sidebar-link" id="btn-notificacoes" style="position:relative;"><svg viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>Notifica&ccedil;&otilde;es<span class="notif-badge" id="notif-badge" style="display:none"></span></a>
          <a href="perfil.html" class="sidebar-link"><svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>Perfil</a>
          <button class="sidebar-link" id="btn-logout"><svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>Sair</button>
        </div>
      </nav>`;

const files = fs.readdirSync(dir).filter(f => f.endsWith('.html'));
const modified = [];

for (const file of files) {
  const filePath = path.join(dir, file);
  let content = fs.readFileSync(filePath, 'utf8');

  // Match <nav class="sidebar-nav"> ... </nav> (the first closing </nav>)
  const navRegex = /<nav class="sidebar-nav">[\s\S]*?<\/nav>/;

  if (!navRegex.test(content)) {
    console.log(`SKIP (no sidebar-nav found): ${file}`);
    continue;
  }

  // Replace the nav content
  content = content.replace(navRegex, newNavContent);

  // Set active class for the current page
  // Find the link matching this filename and add "active"
  const hrefMatch = `href="${file}"`;
  // For index.html, check if there's a matching link (there isn't, so no active)
  if (content.includes(hrefMatch)) {
    // Replace the specific link's class to include active
    content = content.replace(
      new RegExp(`<a href="${file.replace('.', '\\.')}" class="sidebar-link"`),
      `<a href="${file}" class="sidebar-link active"`
    );
  }

  fs.writeFileSync(filePath, content, 'utf8');
  modified.push(file);
  console.log(`UPDATED: ${file}`);
}

console.log(`\nTotal files modified: ${modified.length}`);
console.log('Modified files:', modified.join(', '));
