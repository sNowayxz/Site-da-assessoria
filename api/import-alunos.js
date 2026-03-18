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

  const { action, logins, alunos } = req.body || {};

  // ── Ação "bulk": import direto sem login Studeo ──
  if (action === 'bulk') {
    if (!Array.isArray(alunos) || alunos.length === 0) {
      return res.status(400).json({ error: 'Campo "alunos" (array) obrigatório para action=bulk' });
    }

    // Sanitizar registros
    const records = alunos
      .filter(a => a.ra)
      .map(a => ({
        ra: String(a.ra).trim(),
        nome: a.nome || '',
        curso: a.curso || '',
        studeo_senha: a.studeo_senha || a.senha || '',
        telefone: a.telefone || '',
        tipo: a.tipo || 'mensalista',
        situacao: a.situacao || 'cursando',
        observacoes: a.observacoes || a.polo || '',
        email: a.email || '',
        cpf: a.cpf || '',
      }));

    let inserted = 0;
    const errors = [];

    for (let i = 0; i < records.length; i += 50) {
      const chunk = records.slice(i, i + 50);
      const sbResp = await fetch(`${SB_URL}/rest/v1/alunos?on_conflict=ra`, {
        method: 'POST',
        headers: {
          'apikey': SB_KEY,
          'Authorization': 'Bearer ' + SB_KEY,
          'Content-Type': 'application/json',
          'Prefer': 'resolution=merge-duplicates',
        },
        body: JSON.stringify(chunk),
      });

      if (sbResp.ok || sbResp.status === 201) {
        inserted += chunk.length;
      } else {
        const errText = await sbResp.text();
        errors.push(`Chunk ${Math.floor(i/50)}: ${sbResp.status} - ${errText.substring(0, 200)}`);
      }
    }

    return res.status(200).json({ ok: true, inserted, total: records.length, errors: errors.length, errorDetails: errors.slice(0, 5) });
  }

  // ── Ação padrão: login Studeo individual ──
  if (!Array.isArray(logins) || logins.length === 0) {
    return res.status(400).json({ error: 'Campo "logins" deve ser um array não vazio, ou use action="bulk"' });
  }

  const resultados = [];
  const BATCH_SIZE = 5;

  for (let i = 0; i < logins.length; i++) {
    const { ra, senha } = logins[i];
    if (!ra || !senha) {
      resultados.push({ ra: ra || '?', ok: false, erro: 'RA ou senha ausente' });
      continue;
    }

    const raClean = String(ra).replace(/[\s]/g, '').trim();

    try {
      const { nome: nomeJwt } = await studeoLoginComNome(raClean, senha);
      const nome = nomeJwt || `Aluno ${raClean}`;

      const sbResp = await fetch(`${SB_URL}/rest/v1/alunos`, {
        method: 'POST',
        headers: {
          'apikey': SB_KEY,
          'Authorization': 'Bearer ' + SB_KEY,
          'Content-Type': 'application/json',
          'Prefer': 'resolution=merge-duplicates,return=representation',
        },
        body: JSON.stringify({ ra: raClean, nome, tipo: 'mensalista', studeo_senha: senha }),
      });

      const sbData = await sbResp.json().catch(() => null);
      if (!sbResp.ok) throw new Error(sbData?.message || `Supabase ${sbResp.status}`);

      resultados.push({ ra: raClean, ok: true, nome: sbData?.[0]?.nome || nome });
    } catch (err) {
      resultados.push({ ra: raClean, ok: false, erro: err.message });
    }

    if ((i + 1) % BATCH_SIZE === 0 && i + 1 < logins.length) {
      await new Promise(r => setTimeout(r, 500));
    }
  }

  return res.status(200).json({ ok: true, sucesso: resultados.filter(r => r.ok).length, erros: resultados.filter(r => !r.ok).length, resultados });
};
