/* ═══════════════════════════════════════════
   Vercel Serverless — Importação em Lote de Alunos
   Faz login no Studeo, extrai nome do JWT,
   upserta na tabela alunos do Supabase
   ═══════════════════════════════════════════ */

const STUDEO_API = 'https://studeoapi.unicesumar.edu.br';
const HEADERS_BASE = {
  'Accept': 'application/json, text/plain, */*',
  'Content-Type': 'application/json;charset=UTF-8',
  'Origin': 'https://studeo.unicesumar.edu.br',
  'Referer': 'https://studeo.unicesumar.edu.br/',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// Decodifica JWT e extrai nome do aluno
function extractNameFromJWT(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    // base64url → base64
    let payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    while (payload.length % 4) payload += '=';
    const decoded = JSON.parse(Buffer.from(payload, 'base64').toString('utf-8'));
    // Campos possíveis com o nome
    return decoded.name
      || decoded.nomeAluno
      || decoded.nome
      || decoded.given_name
      || decoded.preferred_username
      || decoded.sub
      || null;
  } catch {
    return null;
  }
}

// Login Studeo + extrai nome (tenta múltiplos formatos de RA)
async function studeoLoginComNome(ra, senha) {
  const raStr = String(ra).trim();
  const formatos = [...new Set([raStr, raStr.replace(/[\s]/g, ''), raStr.replace(/[\s.\-]/g, ''), raStr.replace(/[^0-9]/g, '')])];

  for (const formato of formatos) {
    if (!formato) continue;
    try {
      const resp = await fetch(`${STUDEO_API}/auth-api-controller/auth/token/create`, {
        method: 'POST',
        headers: HEADERS_BASE,
        body: JSON.stringify({ username: formato, password: senha }),
      });
      const text = await resp.text();
      let data;
      try { data = JSON.parse(text); } catch { data = null; }

      if (data && data.valid === false) continue;
      if (!resp.ok) continue;
      if (!data || !data.token) continue;

      const nome = extractNameFromJWT(data.token);
      return { token: data.token, nome, raUsado: formato };
    } catch { continue; }
  }
  throw new Error('Credenciais inválidas (todos os formatos de RA testados)');
}

module.exports = async function handler(req, res) {
  Object.entries(corsHeaders()).forEach(([k, v]) => res.setHeader(k, v));
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método não permitido' });

  const SB_URL = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;

  if (!SB_KEY) return res.status(500).json({ error: 'SUPABASE_SERVICE_KEY não configurada' });

  const { logins } = req.body || {};
  if (!Array.isArray(logins) || logins.length === 0) {
    return res.status(400).json({ error: 'Campo "logins" deve ser um array não vazio' });
  }

  const resultados = [];
  const BATCH_SIZE = 5; // processa 5 por vez para não sobrecarregar

  for (let i = 0; i < logins.length; i++) {
    const { ra, senha } = logins[i];
    if (!ra || !senha) {
      resultados.push({ ra: ra || '?', ok: false, erro: 'RA ou senha ausente' });
      continue;
    }

    const raClean = String(ra).replace(/[\s]/g, '').trim();

    try {
      // 1. Login no Studeo para validar e pegar nome
      const { nome: nomeJwt } = await studeoLoginComNome(raClean, senha);
      const nome = nomeJwt || `Aluno ${raClean}`;

      // 2. Upsert no Supabase
      const sbResp = await fetch(`${SB_URL}/rest/v1/alunos`, {
        method: 'POST',
        headers: {
          'apikey': SB_KEY,
          'Authorization': 'Bearer ' + SB_KEY,
          'Content-Type': 'application/json',
          'Prefer': 'resolution=merge-duplicates,return=representation',
        },
        body: JSON.stringify({
          ra: raClean,
          nome,
          tipo: 'mensalista',
          studeo_senha: senha,
        }),
      });

      const sbData = await sbResp.json().catch(() => null);
      if (!sbResp.ok) {
        const errMsg = sbData?.message || sbData?.error || `Supabase ${sbResp.status}`;
        throw new Error(errMsg);
      }

      const inserted = Array.isArray(sbData) ? sbData[0] : sbData;
      resultados.push({
        ra: raClean,
        ok: true,
        nome: inserted?.nome || nome,
        id: inserted?.id,
      });

    } catch (err) {
      resultados.push({ ra: raClean, ok: false, erro: err.message });
    }

    // Pequena pausa a cada batch para não sobrecarregar o Studeo
    if ((i + 1) % BATCH_SIZE === 0 && i + 1 < logins.length) {
      await new Promise(r => setTimeout(r, 500));
    }
  }

  const sucesso = resultados.filter(r => r.ok).length;
  const erros   = resultados.filter(r => !r.ok).length;

  return res.status(200).json({ ok: true, sucesso, erros, resultados });
};
