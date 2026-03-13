/* ═══════════════════════════════════════════
   Importar Alunos Mensalistas — Painel
   ═══════════════════════════════════════════ */

var loginsParsed = [];

document.addEventListener('DOMContentLoaded', async function () {
  var user = await requireAuth();
  if (!user) return;
  document.getElementById('user-name').textContent = getUserName(user);
  document.getElementById('btn-logout').addEventListener('click', handleLogout);
  document.getElementById('btn-parse').addEventListener('click', parseLista);
  document.getElementById('btn-import').addEventListener('click', iniciarImportacao);
});

// ─── Parse da lista colada ────────────────────────────
function parseLista() {
  var texto = document.getElementById('paste-area').value.trim();
  if (!texto) { alert('Cole a lista de logins primeiro.'); return; }

  var linhas = texto.split('\n');
  loginsParsed = [];

  linhas.forEach(function (linha) {
    linha = linha.trim();
    if (!linha) return;

    var partes;
    // Tenta separar por tab, vírgula, ponto-e-vírgula ou múltiplos espaços
    if (linha.includes('\t')) {
      partes = linha.split('\t');
    } else if (linha.includes(',')) {
      partes = linha.split(',');
    } else if (linha.includes(';')) {
      partes = linha.split(';');
    } else {
      // Espaço: RA termina com dígito ou -dígito, senha é o resto
      var match = linha.match(/^(\S+)\s+(.+)$/);
      partes = match ? [match[1], match[2]] : [];
    }

    var ra    = (partes[0] || '').trim();
    var senha = (partes[1] || '').trim();

    if (ra && senha) {
      loginsParsed.push({ ra, senha });
    }
  });

  if (!loginsParsed.length) {
    alert('Nenhum login válido encontrado. Verifique o formato: RA TAB/VÍRGULA Senha');
    return;
  }

  // Remove duplicatas por RA
  var seen = {};
  loginsParsed = loginsParsed.filter(function (l) {
    if (seen[l.ra]) return false;
    seen[l.ra] = true;
    return true;
  });

  mostrarPreview();
}

function mostrarPreview() {
  var tbody = document.getElementById('preview-tbody');
  tbody.innerHTML = loginsParsed.map(function (l, i) {
    return '<tr><td>' + (i + 1) + '</td><td><code>' + escapeHtml(l.ra) + '</code></td><td>••••••</td></tr>';
  }).join('');

  document.getElementById('preview-count').innerHTML =
    '<strong>' + loginsParsed.length + ' alunos</strong> identificados. Revise e clique em Importar.';
  document.getElementById('preview-section').style.display = 'block';
  document.getElementById('btn-import').disabled = false;
  document.getElementById('parse-count').textContent = loginsParsed.length + ' logins prontos';
}

// ─── Importação em lotes ──────────────────────────────
async function iniciarImportacao() {
  if (!loginsParsed.length) return;
  if (!confirm('Importar ' + loginsParsed.length + ' alunos como mensalistas? Credenciais serão verificadas no Studeo.')) return;

  document.getElementById('btn-import').disabled = true;
  document.getElementById('btn-parse').disabled  = true;
  document.getElementById('progress-box').style.display = 'block';
  document.getElementById('results-box').style.display  = 'none';

  var LOTE = 10; // envia 10 por vez
  var todos = [];
  var total = loginsParsed.length;

  for (var i = 0; i < total; i += LOTE) {
    var lote = loginsParsed.slice(i, i + LOTE);
    var progresso = Math.min(i + LOTE, total);

    atualizarProgresso(
      Math.round((progresso / total) * 100),
      'Importando ' + progresso + ' de ' + total + '...'
    );

    try {
      var resp = await fetch('/api/import-alunos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logins: lote }),
      });

      var data = await resp.json();
      if (data.resultados) {
        todos = todos.concat(data.resultados);
      } else {
        // Erro no lote inteiro
        lote.forEach(function (l) {
          todos.push({ ra: l.ra, ok: false, erro: data.error || 'Erro desconhecido' });
        });
      }
    } catch (err) {
      lote.forEach(function (l) {
        todos.push({ ra: l.ra, ok: false, erro: 'Erro de conexão' });
      });
    }
  }

  atualizarProgresso(100, 'Concluído!');
  mostrarResultados(todos);
}

function atualizarProgresso(pct, label) {
  document.getElementById('progress-bar').style.width = pct + '%';
  document.getElementById('progress-label').textContent = label;
}

function mostrarResultados(resultados) {
  var sucesso = resultados.filter(function (r) { return r.ok; }).length;
  var erros   = resultados.filter(function (r) { return !r.ok; }).length;

  document.getElementById('summary-box').innerHTML =
    '<div class="summary-item"><div class="num num-tot">' + resultados.length + '</div><div class="lbl">Total</div></div>' +
    '<div class="summary-item"><div class="num num-ok">' + sucesso + '</div><div class="lbl">Importados</div></div>' +
    '<div class="summary-item"><div class="num num-err">' + erros + '</div><div class="lbl">Com erro</div></div>';

  var tbody = document.getElementById('results-tbody');
  tbody.innerHTML = resultados.map(function (r) {
    if (r.ok) {
      return '<tr>' +
        '<td><code>' + escapeHtml(r.ra) + '</code></td>' +
        '<td>' + escapeHtml(r.nome || '—') + '</td>' +
        '<td class="result-ok">✅ Importado</td>' +
        '</tr>';
    } else {
      return '<tr>' +
        '<td><code>' + escapeHtml(r.ra) + '</code></td>' +
        '<td style="color:var(--gray-400);">—</td>' +
        '<td><span style="color:#ef4444;">❌ ' + escapeHtml(r.erro || 'Erro') + '</span></td>' +
        '</tr>';
    }
  }).join('');

  document.getElementById('results-box').style.display = 'block';
  document.getElementById('progress-box').style.display = 'none';
}

function reiniciar() {
  loginsParsed = [];
  document.getElementById('paste-area').value = '';
  document.getElementById('preview-section').style.display = 'none';
  document.getElementById('results-box').style.display = 'none';
  document.getElementById('progress-box').style.display = 'none';
  document.getElementById('btn-import').disabled = true;
  document.getElementById('btn-parse').disabled  = false;
  document.getElementById('parse-count').textContent = '';
}

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}
