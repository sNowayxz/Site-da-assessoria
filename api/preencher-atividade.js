/* ═══════════════════════════════════════════
   Vercel Serverless — Preencher Atividade via Modelitos
   Proxy para API do Modelitos (evita CORS)

   Fluxo:
   1. Login no Modelitos com credenciais do env
   2. Chama POST /alunos/api/preencher-atividade/
   3. Retorna resultado
   ═══════════════════════════════════════════ */

const MODELITOS_URL = 'https://www.modelitos.com.br';

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

module.exports = async function handler(req, res) {
  Object.entries(corsHeaders()).forEach(([k, v]) => res.setHeader(k, v));
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método não permitido' });

  const { action, idQuestionario, finalizar, ra, raw } = req.body || {};

  if (!action) return res.status(400).json({ error: 'Campo "action" obrigatório' });

  try {
    // Login no Modelitos
    const session = await loginModelitos();

    if (action === 'verificar') {
      // Buscar atividades pendentes de um RA no Modelitos
      if (!ra) return res.status(400).json({ error: 'Campo "ra" obrigatório' });
      const pendentes = await verificarPendentes(session, ra);
      return res.status(200).json({ ok: true, pendentes });
    }

    if (action === 'preencher') {
      // Aceita raw (valor completo do checkbox) ou idQuestionario
      const id = raw || idQuestionario;
      if (!id) return res.status(400).json({ error: 'Campo "idQuestionario" ou "raw" obrigatório' });
      const resultado = await preencherAtividade(session, id, finalizar !== false);
      return res.status(200).json({ ok: true, resultado });
    }

    return res.status(400).json({ error: 'Ação inválida. Use "verificar" ou "preencher".' });

  } catch (err) {
    console.error('[preencher-atividade] Erro:', err.message);
    return res.status(500).json({ ok: false, error: err.message || 'Erro interno' });
  }
};

async function loginModelitos() {
  const user = process.env.PAPIRON_USER;
  const pass = process.env.PAPIRON_PASS;

  if (!user || !pass) {
    throw new Error('PAPIRON_USER e PAPIRON_PASS não configurados no Vercel');
  }

  // 1. GET login page to get CSRF tokens
  const loginUrl = MODELITOS_URL + '/usuarios/login?action=logar';
  const r1 = await fetch(loginUrl);
  const html = await r1.text();

  // Extract csrftoken from cookies
  const cookies1 = r1.headers.get('set-cookie') || '';
  const csrfMatch = cookies1.match(/csrftoken=([^;]+)/);
  if (!csrfMatch) throw new Error('Não conseguiu obter csrftoken do Modelitos');
  const csrftoken = csrfMatch[1];

  // Extract csrfmiddlewaretoken from HTML form
  const middlewareMatch = html.match(/name="csrfmiddlewaretoken"\s+value="([^"]+)"/);
  if (!middlewareMatch) throw new Error('Não conseguiu obter csrfmiddlewaretoken');
  const csrfmiddlewaretoken = middlewareMatch[1];

  // 2. POST login
  const postdata = `csrfmiddlewaretoken=${csrfmiddlewaretoken}&id=None&next=&email=${encodeURIComponent(user)}&senha=${encodeURIComponent(pass)}`;

  const r2 = await fetch(loginUrl, {
    method: 'POST',
    headers: {
      'Cookie': `csrftoken=${csrftoken}`,
      'Content-Type': 'application/x-www-form-urlencoded',
      'Host': 'www.modelitos.com.br',
      'Origin': MODELITOS_URL,
      'Referer': loginUrl,
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
    body: postdata,
    redirect: 'manual',
  });

  // Extract sessionid from response cookies
  const cookies2 = r2.headers.get('set-cookie') || '';
  const sessionMatch = cookies2.match(/sessionid=([^;]+)/);
  if (!sessionMatch) throw new Error('Login falhou no Modelitos — sessionid não obtido');

  const sessionid = sessionMatch[1];
  const cookieStr = `csrftoken=${csrftoken};sessionid=${sessionid}`;

  console.log('[modelitos] Login OK');
  return { cookie: cookieStr, csrftoken };
}

async function verificarPendentes(session, ra) {
  const url = `${MODELITOS_URL}/alunos/verificar-atividades-pendentes/${ra}/`;

  const r = await fetch(url, {
    headers: {
      'Cookie': session.cookie,
      'Accept': 'text/html,application/xhtml+xml',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
  });

  if (!r.ok) throw new Error(`Erro ao verificar pendentes: HTTP ${r.status}`);

  const html = await r.text();

  // Parse checkboxes: value="343417 | 2026_26_EGRAD_TEOL12G"
  const regex = /type="checkbox"[^>]*value="([^"]+)"/g;
  const pendentes = [];
  let match;
  while ((match = regex.exec(html)) !== null) {
    const parts = match[1].split('|').map(s => s.trim());
    if (parts.length >= 2) {
      pendentes.push({
        idQuestionario: parts[0],
        shortname: parts[1],
        raw: match[1],
      });
    }
  }

  // Also try to extract activity names from the HTML
  // Look for labels or text near checkboxes
  const labelRegex = /<label[^>]*>([^<]+)<\/label>/g;
  const labels = [];
  while ((match = labelRegex.exec(html)) !== null) {
    labels.push(match[1].trim());
  }

  // Try to match labels with checkboxes
  for (let i = 0; i < pendentes.length && i < labels.length; i++) {
    pendentes[i].descricao = labels[i];
  }

  return pendentes;
}

async function preencherAtividade(session, idQuestionario, finalizar) {
  const url = `${MODELITOS_URL}/alunos/api/preencher-atividade/`;

  const r = await fetch(url, {
    method: 'POST',
    headers: {
      'Cookie': session.cookie,
      'Content-Type': 'application/json',
      'X-CSRFToken': session.csrftoken,
      'Accept': 'application/json',
      'Referer': MODELITOS_URL + '/alunos/verificar-atividades/',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    },
    body: JSON.stringify({
      idQuestionario: String(idQuestionario),
      finalizar: finalizar,
    }),
    redirect: 'manual',
  });

  const status = r.status;
  console.log(`[modelitos] Preencheu atividade ${idQuestionario}: HTTP ${status}`);

  // Modelitos pode retornar 200, 302 (redirect após sucesso), ou HTML
  // Considerar 200 e 302 como sucesso
  if (status === 200 || status === 301 || status === 302) {
    let data;
    try {
      const text = await r.text();
      try { data = JSON.parse(text); } catch { data = { status: status, preenchido: true }; }
    } catch {
      data = { status: status, preenchido: true };
    }
    return data;
  }

  // Erro real
  let errText = '';
  try { errText = await r.text(); } catch {}
  throw new Error(`HTTP ${status} — ${errText.substring(0, 200)}`);
}
