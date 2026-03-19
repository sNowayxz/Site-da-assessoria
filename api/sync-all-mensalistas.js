/**
 * Sync All Mensalistas — Sincroniza todos os mensalistas do Studeo de uma vez
 *
 * POST /api/sync-all-mensalistas
 * Body: { limit: 10 } (optional, default processes all)
 *
 * Busca alunos com tipo='mensalista' e studeo_senha preenchida,
 * chama sync-studeo para cada um e salva no studeo_sync.
 *
 * Pode ser chamado manualmente ou via cron/scheduled task.
 */

const SYNC_API = 'https://site-da-assessoria.vercel.app/api/sync-studeo';

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const SB_URL = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;
  if (!SB_KEY) return res.status(500).json({ error: 'SUPABASE_SERVICE_KEY não configurada' });

  const { limit } = req.body || {};
  const maxAlunos = limit || 999;

  try {
    // 1. Buscar todos mensalistas com senha
    const alunosResp = await fetch(
      `${SB_URL}/rest/v1/alunos?tipo=eq.mensalista&studeo_senha=not.is.null&studeo_senha=neq.&select=id,ra,nome,studeo_senha&limit=${maxAlunos}`,
      { headers: { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}` } }
    );
    const alunos = await alunosResp.json();

    if (!Array.isArray(alunos) || !alunos.length) {
      return res.status(200).json({ ok: true, message: 'Nenhum mensalista encontrado', synced: 0 });
    }

    console.log(`[sync-all] ${alunos.length} mensalistas para sincronizar`);

    const results = [];
    let synced = 0;
    let errors = 0;

    // 2. Sincronizar cada aluno (sequencial para não sobrecarregar)
    for (const aluno of alunos) {
      try {
        console.log(`[sync-all] Sincronizando ${aluno.nome} (${aluno.ra})...`);

        const syncResp = await fetch(SYNC_API, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'sync', ra: aluno.ra, senha: aluno.studeo_senha })
        });

        const syncData = await syncResp.json();

        if (!syncData.ok || !syncData.resultado) {
          results.push({ ra: aluno.ra, nome: aluno.nome, status: 'error', error: syncData.error || 'sync failed' });
          errors++;
          continue;
        }

        // 3. Salvar no studeo_sync
        // Primeiro limpar dados antigos deste aluno
        await fetch(
          `${SB_URL}/rest/v1/studeo_sync?aluno_id=eq.${aluno.id}`,
          { method: 'DELETE', headers: { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}` } }
        );

        // Inserir novos dados
        const rows = [];
        for (const disc of syncData.resultado) {
          for (const atv of (disc.atividades || [])) {
            rows.push({
              aluno_id: aluno.id,
              disciplina: disc.disciplina,
              cd_shortname: disc.cd_shortname,
              atividade: atv.descricao || atv.tipo || 'Atividade',
              data_final: atv.dataFinal || null,
              respondida: false
            });
          }
        }

        if (rows.length > 0) {
          await fetch(`${SB_URL}/rest/v1/studeo_sync`, {
            method: 'POST',
            headers: {
              'apikey': SB_KEY,
              'Authorization': `Bearer ${SB_KEY}`,
              'Content-Type': 'application/json',
              'Prefer': 'return=minimal'
            },
            body: JSON.stringify(rows)
          });
        }

        const totalAtividades = rows.length;
        results.push({ ra: aluno.ra, nome: aluno.nome, status: 'ok', atividades: totalAtividades });
        synced++;
        console.log(`[sync-all] ✅ ${aluno.nome}: ${totalAtividades} atividades`);

      } catch (e) {
        results.push({ ra: aluno.ra, nome: aluno.nome, status: 'error', error: e.message });
        errors++;
        console.error(`[sync-all] ❌ ${aluno.nome}: ${e.message}`);
      }

      // Small delay between requests to avoid rate limiting
      await new Promise(r => setTimeout(r, 1000));
    }

    return res.status(200).json({
      ok: true,
      total: alunos.length,
      synced,
      errors,
      results
    });

  } catch (e) {
    console.error('[sync-all] Erro geral:', e.message);
    return res.status(500).json({ ok: false, error: e.message });
  }
};
