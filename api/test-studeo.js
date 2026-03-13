/* ═══════════════════════════════════════════
   Endpoint de diagnóstico — Studeo Unicesumar
   Testa login com múltiplos formatos de RA
   ═══════════════════════════════════════════ */

const STUDEO_API = 'https://studeoapi.unicesumar.edu.br';
const PAPIRON_API = 'https://www.papiron.com.br';

const HEADERS_BASE = {
  'Accept': 'application/json, text/plain, */*',
  'Content-Type': 'application/json;charset=UTF-8',
  'Origin': 'https://studeo.unicesumar.edu.br',
  'Referer': 'https://studeo.unicesumar.edu.br/',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
};

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { ra, senha } = req.method === 'GET' ? req.query : (req.body || {});
  if (!ra || !senha) {
    return res.status(400).json({ error: 'Informe ra e senha' });
  }

  const resultados = [];

  // Gera os formatos de RA a testar
  const raStr = String(ra).trim();
  const raOriginal  = raStr;
  const raSemTracao = raStr.replace(/[\-\.]/g, '');
  const raSoNumeros = raStr.replace(/[^0-9]/g, '');
  const raFormatos  = [...new Set([raOriginal, raSemTracao, raSoNumeros])];

  for (const formato of raFormatos) {
    const resultado = { formato, status: null, erro: null, nome: null, disciplinas: null };
    try {
      // 1. Tenta login
      const loginResp = await fetch(`${STUDEO_API}/auth-api-controller/auth/token/create`, {
        method: 'POST',
        headers: HEADERS_BASE,
        body: JSON.stringify({ username: formato, password: String(senha) }),
      });

      const loginText = await loginResp.text();
      let loginData;
      try { loginData = JSON.parse(loginText); } catch { loginData = null; }

      if (!loginResp.ok || (loginData && loginData.valid === false)) {
        resultado.status = 'login_falhou';
        resultado.erro = `HTTP ${loginResp.status}: ${loginText.substring(0, 200)}`;
        resultados.push(resultado);
        continue;
      }

      if (!loginData?.token) {
        resultado.status = 'sem_token';
        resultado.erro = loginText.substring(0, 200);
        resultados.push(resultado);
        continue;
      }

      // 2. Login OK — extrai nome do JWT
      resultado.status = 'login_ok';
      resultado.nome = extrairNomeJWT(loginData.token);

      // 3. Testa busca de disciplinas via Papiron
      try {
        const papResp = await fetch(`${PAPIRON_API}/ferramentas/informar_disciplinas_aluno_json/${raSoNumeros}`, {
          headers: { 'Accept': 'application/json' },
        });
        if (papResp.ok) {
          const discs = await papResp.json();
          resultado.disciplinas = Array.isArray(discs) ? discs.length : 0;
        } else {
          resultado.disciplinas = `Papiron erro ${papResp.status}`;
        }
      } catch (e) {
        resultado.disciplinas = `Papiron falhou: ${e.message}`;
      }

      resultados.push(resultado);
      break; // Login funcionou — não precisa testar outros formatos

    } catch (err) {
      resultado.status = 'excecao';
      resultado.erro = err.message;
      resultados.push(resultado);
    }
  }

  const loginOk = resultados.find(r => r.status === 'login_ok');

  return res.status(200).json({
    ok: !!loginOk,
    ra_testado: ra,
    ra_funcionou: loginOk?.formato || null,
    nome: loginOk?.nome || null,
    disciplinas: loginOk?.disciplinas ?? null,
    detalhes: resultados,
    server_ip_hint: 'Vercel serverless — IP externo (não BR)',
  });
};

function extrairNomeJWT(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    let payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    while (payload.length % 4) payload += '=';
    const decoded = JSON.parse(Buffer.from(payload, 'base64').toString('utf-8'));
    return decoded.name || decoded.nomeAluno || decoded.nome
      || decoded.given_name || decoded.preferred_username || decoded.sub || null;
  } catch { return null; }
}
