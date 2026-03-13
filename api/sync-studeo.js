/* ═══════════════════════════════════════════
   Vercel Serverless Function — Studeo Sync
   Proxy para API do Studeo Unicesumar
   (evita CORS do navegador)
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

// Disciplinas excluídas do rastreio
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
  // CORS preflight
  Object.entries(corsHeaders()).forEach(([k, v]) => res.setHeader(k, v));
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { action, ra, senha } = req.body || {};

  try {
    if (action === 'login') {
      // Apenas testa login e retorna disciplinas
      const token = await studeoLogin(ra, senha);
      const disciplinas = await buscarDisciplinas(ra);
      return res.status(200).json({ ok: true, token, disciplinas });
    }

    if (action === 'sync') {
      // Login + buscar atividades de todas as disciplinas
      const token = await studeoLogin(ra, senha);
      const disciplinas = await buscarDisciplinas(ra);

      const resultado = [];
      for (const disc of disciplinas) {
        // Pular disciplinas excluídas
        if (EXCLUIR.some(e => disc.nm_disciplina.toUpperCase().includes(e))) continue;

        try {
          const atividades = await buscarAtividades(token, disc.cd_shortname);
          const mapa = await buscarMapa(token, disc.cd_shortname);

          resultado.push({
            disciplina: disc.nm_disciplina,
            cd_shortname: disc.cd_shortname,
            ano: disc.ano,
            modulo: disc.modulo,
            atividades: atividades.map(a => ({
              descricao: a.descricao || a.nome || '',
              idQuestionario: a.idQuestionario,
              dataInicial: a.dataInicial || null,
              dataFinal: a.dataFinal || null,
              tipo: 'AV',
              respondida: a.respondida || false,
            })),
            mapa: mapa.map(a => ({
              descricao: a.descricao || a.nome || '',
              idQuestionario: a.idQuestionario,
              dataInicial: a.dataInicial || null,
              dataFinal: a.dataFinal || null,
              tipo: 'MAPA',
              respondida: a.respondida || false,
            })),
          });
        } catch (err) {
          resultado.push({
            disciplina: disc.nm_disciplina,
            cd_shortname: disc.cd_shortname,
            ano: disc.ano,
            modulo: disc.modulo,
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
    console.error('Sync error:', err);
    return res.status(500).json({ error: err.message || 'Erro interno' });
  }
};

// ─── Studeo Auth ───────────────────────────
async function studeoLogin(ra, senha) {
  const resp = await fetch(`${STUDEO_API}/auth-api-controller/auth/token/create`, {
    method: 'POST',
    headers: HEADERS_BASE,
    body: JSON.stringify({ username: ra, password: senha }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Login falhou (${resp.status}): ${text}`);
  }

  const data = await resp.json();
  if (!data.token) throw new Error('Token não retornado pelo Studeo');
  return data.token;
}

// ─── Buscar Disciplinas via Papiron ────────
async function buscarDisciplinas(ra) {
  try {
    const resp = await fetch(`${PAPIRON_API}/ferramentas/informar_disciplinas_aluno_json/${ra}`, {
      headers: { 'Accept': 'application/json' },
    });

    if (!resp.ok) throw new Error(`Papiron status ${resp.status}`);

    const data = await resp.json();
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error('Nenhuma disciplina encontrada');
    }

    return data.map(d => ({
      nm_disciplina: d.nm_disciplina || d.disciplina || '',
      cd_shortname: d.cd_shortname || d.shortname || '',
      ano: d.ano || '',
      modulo: d.modulo || '',
    }));
  } catch (err) {
    throw new Error('Não foi possível buscar disciplinas: ' + err.message);
  }
}

// ─── Buscar Atividades da Disciplina ───────
async function buscarAtividades(token, cdShortname) {
  const headers = { ...HEADERS_BASE, Authorization: token };
  const resp = await fetch(
    `${STUDEO_API}/objeto-ensino-api-controller/api/questionario/disciplina/${cdShortname}`,
    { headers }
  );

  if (!resp.ok) return [];
  const data = await resp.json();
  return Array.isArray(data) ? data : [];
}

// ─── Buscar MAPA da Disciplina ─────────────
async function buscarMapa(token, cdShortname) {
  const headers = { ...HEADERS_BASE, Authorization: token };
  const resp = await fetch(
    `${STUDEO_API}/objeto-ensino-api-controller/api/questionario/disciplina/${cdShortname}/MAPA`,
    { headers }
  );

  if (!resp.ok) return [];
  const data = await resp.json();
  return Array.isArray(data) ? data : [];
}
