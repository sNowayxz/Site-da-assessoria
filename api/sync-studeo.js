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
  'PREPARE-SE',
  'NIVELAMENTO',
  'GIRO EAD',
  'AULA INAUGURAL',
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

      // 1. Buscar disciplinas matriculadas (endpoint real do Studeo)
      const matriculadas = await buscarDisciplinasMatriculadas(token);
      console.log(`[sync] ${matriculadas.length} disciplinas matriculadas`);

      // 2. Buscar quais disciplinas têm atividades "a fazer"
      const shortnames = matriculadas.map(d => d.cdShortname);
      const afazer = await buscarAtividadesAFazer(token, shortnames);
      const afazerMap = {};
      for (const item of afazer) {
        afazerMap[item.shortname] = item.somaAtividades;
      }
      console.log(`[sync] ${afazer.length} disciplinas com atividades a fazer`);

      // 3. Só buscar detalhes das disciplinas que TÊM atividades pendentes
      const resultado = [];
      const discsComPendencia = matriculadas.filter(d => afazerMap[d.cdShortname] > 0);

      for (const disc of discsComPendencia) {
        const nomeUpper = (disc.nmDisciplina || '').toUpperCase();
        if (EXCLUIR.some(e => nomeUpper.includes(e))) continue;

        try {
          const [atividades, mapa] = await Promise.all([
            buscarAtividades(token, disc.cdShortname),
            buscarMapa(token, disc.cdShortname),
          ]);

          const atividadesNorm = normalizarAtividades(atividades, 'AV');
          const mapaNorm = normalizarAtividades(mapa, 'MAPA');

          resultado.push({
            disciplina: disc.nmDisciplina,
            cd_shortname: disc.cdShortname,
            ano: disc.ano || null,
            modulo: disc.semestre ? String(disc.semestre) : null,
            atividades: atividadesNorm,
            mapa: mapaNorm,
          });
        } catch (err) {
          console.error(`[sync] Erro em ${disc.nmDisciplina}:`, err.message);
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
    .filter(a => {
      if (!a) return false;
      // Accept anything with a name-like field
      return a.descricao || a.nome || a.titulo || a.title || a.nm_questionario || a.nmQuestionario || a.name;
    })
    .map(a => {
      const desc = a.descricao || a.nm_questionario || a.nmQuestionario || a.nome || a.titulo || a.title || a.name || '';
      const respondida = !!(
        a.respondida || a.concluida || a.finalizada
        || a.status === 'concluida' || a.status === 'CONCLUIDA'
        || a.flRespondida === 'S' || a.flRespondida === true
        || a.situacao === 'RESPONDIDA' || a.situacao === 'CONCLUIDA'
      );

      return {
        descricao: desc,
        idQuestionario: a.idQuestionario || a.id || a.cdQuestionario || null,
        dataInicial: normalizarData(a.dataInicial || a.dataInicio || a.data_inicio || a.dtInicio || a.dtLiberacao || null),
        dataFinal:   normalizarData(a.dataFinal   || a.dataFim    || a.data_fim    || a.dtFim    || a.dtEncerramento || null),
        tipo,
        respondida,
      };
    });
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
  const raStr = String(ra).trim();
  const senhaStr = String(senha).trim();

  // RA formats to try
  const raFormatos = [...new Set([
    raStr,
    raStr.replace(/[\s]/g, ''),
    raStr.replace(/[\s.\-]/g, ''),
    raStr.replace(/[^0-9]/g, ''),
  ])].filter(Boolean);

  // Senha formats: original, sem "55" no final (erro comum de export com DDI)
  const senhaFormatos = [senhaStr];
  if (senhaStr.endsWith('55') && senhaStr.length > 4) {
    senhaFormatos.push(senhaStr.slice(0, -2));
  }

  let lastError = 'Nenhuma combinação funcionou';

  for (const senhaTry of senhaFormatos) {
    for (const formato of raFormatos) {
      try {
        const resp = await fetch(`${STUDEO_API}/auth-api-controller/auth/token/create`, {
          method: 'POST',
          headers: HEADERS_BASE,
          body: JSON.stringify({ username: formato, password: senhaTry }),
        });

        const text = await resp.text();
        let data;
        try { data = JSON.parse(text); } catch { data = null; }

        if (data && data.valid === false) {
          lastError = `RA "${formato}" senha "${senhaTry.substring(0,3)}...": inválidas`;
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

        console.log(`[studeo] Login OK: RA=${formato} senha=${senhaTry === senhaStr ? 'original' : 'sem 55'}`);
        return data.token;

      } catch (err) {
        lastError = `RA "${formato}": ${err.message}`;
        continue;
      }
    }
  }

  throw new Error(`Login falhou. Último erro: ${lastError}`);
}

async function buscarDisciplinas(ra) {
  // Papiron API needs RA with dash (e.g. 21161906-5), not cleaned
  const raStr = String(ra).trim();

  let resp;
  try {
    resp = await fetch(`${PAPIRON_API}/ferramentas/informar_disciplinas_aluno_json/${raStr}`, {
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
    throw new Error(`Nenhuma disciplina encontrada para RA ${raStr}. Verifique se o RA está correto.`);
  }

  const all = data
    .map(d => ({
      nm_disciplina: d.nm_disciplina || d.disciplina || d.nome || '',
      cd_shortname:  d.cd_shortname  || d.shortname  || d.codigo || '',
      ano:    d.ano    || null,
      modulo: d.modulo || null,
    }))
    .filter(d => d.nm_disciplina && d.cd_shortname);

  // Only keep disciplines from current year (latest year found)
  const currentYear = new Date().getFullYear();
  const activeDiscs = all.filter(d => {
    const ano = Number(d.ano);
    // Keep current year and mod_curso != 9 (special/admin courses)
    return ano >= currentYear;
  });

  // If no current year disciplines, fallback to latest year
  if (activeDiscs.length === 0) {
    const maxYear = Math.max(...all.map(d => Number(d.ano) || 0));
    return all.filter(d => Number(d.ano) === maxYear);
  }

  return activeDiscs;
}

// Busca disciplinas matriculadas diretamente da API do Studeo (não do Papiron)
async function buscarDisciplinasMatriculadas(token) {
  try {
    const resp = await fetch(
      `${STUDEO_API}/ambiente-api-controller/api/aluno/disciplina/matriculados`,
      { headers: { ...HEADERS_BASE, Authorization: token } }
    );
    if (!resp.ok) return [];
    const data = await resp.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('[sync] Erro ao buscar matriculadas:', err.message);
    return [];
  }
}

// Busca quais disciplinas têm atividades "a fazer" (pendentes reais)
async function buscarAtividadesAFazer(token, shortnames) {
  try {
    const resp = await fetch(
      `${STUDEO_API}/objeto-ensino-api-controller/api/questionario/afazer/`,
      {
        method: 'POST',
        headers: { ...HEADERS_BASE, Authorization: token },
        body: JSON.stringify({ cdShortname: shortnames }),
      }
    );
    if (!resp.ok) return [];
    const data = await resp.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('[sync] Erro ao buscar afazer:', err.message);
    return [];
  }
}

function extractArray(data) {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    // Try common wrapper fields
    return data.content || data.data || data.items || data.questionarios
      || data.atividades || data.result || data.results || [];
  }
  return [];
}

async function buscarAtividades(token, cdShortname) {
  try {
    const resp = await fetch(
      `${STUDEO_API}/objeto-ensino-api-controller/api/questionario/disciplina/${cdShortname}`,
      { headers: { ...HEADERS_BASE, Authorization: token } }
    );
    if (!resp.ok) return [];
    const data = await resp.json();
    return extractArray(data);
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
    return extractArray(data);
  } catch { return []; }
}
