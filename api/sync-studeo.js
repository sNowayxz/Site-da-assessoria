/* ═══════════════════════════════════════════
   Vercel Serverless Function — Studeo Sync
   Proxy para API do Studeo Unicesumar (evita CORS)
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

const EXCLUIR = [
  'ESTUDO CONTEMPORÂNEO E TRANSVERSAL',
  'FORMAÇÃO SOCIOCULTURAL E ÉTICA',
  'PREPARE-SE',
  'PROJETO DE ENSINO',
  'NIVELAMENTO',
];

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

  const { action, ra, senha } = req.body || {};

  if (!action) return res.status(400).json({ error: 'Campo "action" obrigatório' });
  if (!ra)     return res.status(400).json({ error: 'Campo "ra" obrigatório' });

  try {
    if (action === 'login') {
      const token = await studeoLogin(ra, senha);
      const disciplinas = await buscarDisciplinas(ra);
      return res.status(200).json({ ok: true, token, disciplinas });
    }

    if (action === 'sync') {
      if (!senha) return res.status(400).json({ error: 'Campo "senha" obrigatório para sync' });

      const token = await studeoLogin(ra, senha);
      const disciplinas = await buscarDisciplinas(ra);
      const resultado = [];

      for (const disc of disciplinas) {
        const nomeUpper = (disc.nm_disciplina || '').toUpperCase();
        if (EXCLUIR.some(e => nomeUpper.includes(e))) continue;

        try {
          const [atividades, mapa] = await Promise.all([
            buscarAtividades(token, disc.cd_shortname),
            buscarMapa(token, disc.cd_shortname),
          ]);

          resultado.push({
            disciplina: disc.nm_disciplina,
            cd_shortname: disc.cd_shortname,
            ano: disc.ano || null,
            modulo: disc.modulo || null,
            atividades: normalizarAtividades(atividades, 'AV'),
            mapa: normalizarAtividades(mapa, 'MAPA'),
          });
        } catch (err) {
          console.error(`[sync] Erro em ${disc.nm_disciplina}:`, err.message);
          resultado.push({
            disciplina: disc.nm_disciplina,
            cd_shortname: disc.cd_shortname,
            ano: disc.ano || null,
            modulo: disc.modulo || null,
            atividades: [],
            mapa: [],
            erro: err.message,
          });
        }
      }

      return res.status(200).json({ ok: true, resultado });
    }

    return res.status(400).json({ error: 'Ação inválida. Use "login" ou "sync".' });

  } catch (err) {
    console.error('[sync-studeo] Erro geral:', err.message);
    return res.status(500).json({ ok: false, error: err.message || 'Erro interno no servidor' });
  }
};

function normalizarAtividades(arr, tipo) {
  if (!Array.isArray(arr)) return [];
  return arr
    .filter(a => a && (a.descricao || a.nome || a.titulo || a.title))
    .map(a => ({
      descricao: a.descricao || a.nome || a.titulo || a.title || '',
      idQuestionario: a.idQuestionario || a.id || null,
      dataInicial: normalizarData(a.dataInicial || a.dataInicio || a.data_inicio || a.dtInicio || null),
      dataFinal:   normalizarData(a.dataFinal   || a.dataFim    || a.data_fim    || a.dtFim    || null),
      tipo,
      respondida: !!(a.respondida || a.concluida || a.finalizada || a.status === 'concluida'),
    }));
}

function normalizarData(val) {
  if (!val) return null;
  try {
    if (/^\d{4}-\d{2}-\d{2}/.test(String(val))) return String(val);
    if (/^\d{2}\/\d{2}\/\d{4}/.test(String(val))) {
      const [date, time] = String(val).split(' ');
      const [d, m, y] = date.split('/');
      return time ? `${y}-${m}-${d}T${time}:00` : `${y}-${m}-${d}`;
    }
    const parsed = new Date(val);
    if (!isNaN(parsed.getTime())) return parsed.toISOString();
    return null;
  } catch {
    return null;
  }
}

// Decodifica JWT e extrai nome do aluno
function extractNameFromJWT(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    let payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    while (payload.length % 4) payload += '=';
    const decoded = JSON.parse(Buffer.from(payload, 'base64').toString('utf-8'));
    return decoded.name || decoded.nomeAluno || decoded.nome
      || decoded.given_name || decoded.preferred_username || null;
  } catch { return null; }
}

async function studeoLogin(ra, senha) {
  // Tenta múltiplos formatos de RA: original, sem traço, só números
  const raStr = String(ra).trim();
  const formatos = [...new Set([
    raStr,                                    // original: 23136944-5
    raStr.replace(/[\s]/g, ''),               // sem espaços
    raStr.replace(/[\s.\-]/g, ''),            // sem traço/ponto: 231369445
    raStr.replace(/[^0-9]/g, ''),             // só números
  ])];

  let lastError = 'Nenhum formato de RA funcionou';

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

      // Credenciais inválidas neste formato — tenta o próximo
      if (data && data.valid === false) {
        lastError = `RA "${formato}": credenciais inválidas`;
        continue;
      }
      if (!resp.ok) {
        lastError = `RA "${formato}": HTTP ${resp.status}`;
        continue;
      }
      if (!data || !data.token) {
        lastError = `RA "${formato}": token não retornado`;
        continue;
      }

      // Sucesso!
      console.log(`[studeo] Login OK com formato: ${formato}`);
      return data.token;

    } catch (err) {
      lastError = `RA "${formato}": ${err.message}`;
      continue;
    }
  }

  throw new Error(`Login falhou em todos os formatos. Último erro: ${lastError}`);
}

async function buscarDisciplinas(ra) {
  const raClean = String(ra).replace(/[\s.\-]/g, '').trim();

  let resp;
  try {
    resp = await fetch(`${PAPIRON_API}/ferramentas/informar_disciplinas_aluno_json/${raClean}`, {
      headers: { 'Accept': 'application/json' },
    });
  } catch (err) {
    throw new Error('Não foi possível conectar ao serviço de disciplinas.');
  }

  if (!resp.ok) throw new Error(`Erro ao buscar disciplinas (status ${resp.status})`);

  let data;
  try { data = await resp.json(); } catch {
    throw new Error('Resposta inválida do serviço de disciplinas');
  }

  if (!Array.isArray(data) || data.length === 0) {
    throw new Error(`Nenhuma disciplina encontrada para RA ${raClean}. Verifique se o RA está correto.`);
  }

  return data
    .map(d => ({
      nm_disciplina: d.nm_disciplina || d.disciplina || d.nome || '',
      cd_shortname:  d.cd_shortname  || d.shortname  || d.codigo || '',
      ano:    d.ano    || null,
      modulo: d.modulo || null,
    }))
    .filter(d => d.nm_disciplina && d.cd_shortname);
}

async function buscarAtividades(token, cdShortname) {
  try {
    const resp = await fetch(
      `${STUDEO_API}/objeto-ensino-api-controller/api/questionario/disciplina/${cdShortname}`,
      { headers: { ...HEADERS_BASE, Authorization: token } }
    );
    if (!resp.ok) return [];
    const data = await resp.json();
    return Array.isArray(data) ? data : (data && (data.content || data.data || data.items || []));
  } catch { return []; }
}

async function buscarMapa(token, cdShortname) {
  try {
    const resp = await fetch(
      `${STUDEO_API}/objeto-ensino-api-controller/api/questionario/disciplina/${cdShortname}/MAPA`,
      { headers: { ...HEADERS_BASE, Authorization: token } }
    );
    if (!resp.ok) return [];
    const data = await resp.json();
    return Array.isArray(data) ? data : (data && (data.content || data.data || data.items || []));
  } catch { return []; }
}
