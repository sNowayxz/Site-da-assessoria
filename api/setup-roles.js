/* ═══════════════════════════════════════════
   Setup Roles — Cria contas de assessoria
   Endpoint temporário — chamar uma vez e remover
   ═══════════════════════════════════════════ */

const { createClient } = require('@supabase/supabase-js');

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const SB_URL = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;
  if (!SB_KEY) return res.status(500).json({ error: 'SUPABASE_SERVICE_KEY não configurada' });

  const sb = createClient(SB_URL, SB_KEY, { auth: { autoRefreshToken: false, persistSession: false } });
  const results = [];

  const { action } = req.body || {};

  // ─── Step 1: Update DB schema ───
  if (action === 'setup-schema') {
    try {
      // Drop old constraint and add new one
      const { error: e1 } = await sb.rpc('exec_sql', {
        query: `
          ALTER TABLE assessores DROP CONSTRAINT IF EXISTS assessores_role_check;
          ALTER TABLE assessores ADD CONSTRAINT assessores_role_check
            CHECK (role IN ('admin','dono','assessoria','extensao','assessor','visualizador'));
          ALTER TABLE assessores ADD COLUMN IF NOT EXISTS label TEXT;
        `
      });
      results.push({ step: 'schema', error: e1 ? e1.message : null });
    } catch (e) {
      // If rpc doesn't exist, try direct SQL via management API
      results.push({ step: 'schema', error: e.message, note: 'Run SQL manually in Supabase dashboard' });
    }
    return res.status(200).json({ ok: true, results });
  }

  // ─── Step 2: List existing users ───
  if (action === 'list-users') {
    const { data: assessores } = await sb.from('assessores').select('*');
    const { data: { users } } = await sb.auth.admin.listUsers();
    return res.status(200).json({
      ok: true,
      assessores: assessores || [],
      authUsers: (users || []).map(u => ({ id: u.id, email: u.email }))
    });
  }

  // ─── Step 3: Create assessoria accounts ───
  if (action === 'create-accounts') {
    const accounts = [
      { email: 'einstein@assessoriaextensoes.com', password: 'Einstein2026!', nome: 'Einstein', role: 'assessoria', label: 'Assessoria Einstein' },
      { email: 'jed@assessoriaextensoes.com', password: 'JeD2026!', nome: 'J&D', role: 'assessoria', label: 'Assessoria J&D' },
      { email: 'dl@assessoriaextensoes.com', password: 'DL2026!', nome: 'DL', role: 'assessoria', label: 'Assessoria DL' },
      { email: 'ary@assessoriaextensoes.com', password: 'Ary2026!', nome: 'Ary', role: 'assessoria', label: 'Assessoria Ary' },
      { email: 'prime@assessoriaextensoes.com', password: 'Prime2026!', nome: 'Prime', role: 'assessoria', label: 'Assessoria Prime' },
      { email: 'azul@assessoriaextensoes.com', password: 'Azul2026!', nome: 'Azul', role: 'assessoria', label: 'Assessoria Azul' },
      { email: 'barbara@assessoriaextensoes.com', password: 'Barbara2026!', nome: 'Barbara', role: 'assessoria', label: 'Assessoria Barbara' },
      { email: 'renderizzi@assessoriaextensoes.com', password: 'Renderizzi2026!', nome: 'Renderizzi', role: 'assessoria', label: 'Assessoria Renderizzi' },
      { email: 'brayan@assessoriaextensoes.com', password: 'Brayan2026!', nome: 'Brayan', role: 'assessoria', label: 'Assessoria Brayan' },
      { email: 'exellence@assessoriaextensoes.com', password: 'Exellence2026!', nome: 'Exellence', role: 'assessoria', label: 'Assessoria Exellence' },
    ];

    for (const acc of accounts) {
      try {
        // Create auth user
        const { data: authData, error: authErr } = await sb.auth.admin.createUser({
          email: acc.email,
          password: acc.password,
          email_confirm: true,
        });

        if (authErr) {
          results.push({ email: acc.email, step: 'auth', error: authErr.message });
          continue;
        }

        // Insert into assessores table
        const { error: dbErr } = await sb.from('assessores').upsert({
          id: authData.user.id,
          nome: acc.nome,
          role: acc.role,
          label: acc.label,
        });

        results.push({
          email: acc.email,
          id: authData.user.id,
          step: 'complete',
          error: dbErr ? dbErr.message : null
        });
      } catch (e) {
        results.push({ email: acc.email, step: 'exception', error: e.message });
      }
    }

    return res.status(200).json({ ok: true, results });
  }

  // ─── Step 4: Update existing users (Augusto → dono, Gessica → extensao) ───
  if (action === 'update-existing') {
    const { data: assessores } = await sb.from('assessores').select('id, nome, role');

    for (const a of (assessores || [])) {
      const nomeUpper = (a.nome || '').toUpperCase();
      if (nomeUpper.includes('AUGUSTO')) {
        const { error } = await sb.from('assessores').update({ role: 'dono', label: 'Dono' }).eq('id', a.id);
        results.push({ nome: a.nome, newRole: 'dono', error: error ? error.message : null });
      } else if (nomeUpper.includes('GESSICA') || nomeUpper.includes('GÉSSICA') || nomeUpper.includes('JESSICA')) {
        const { error } = await sb.from('assessores').update({ role: 'extensao', label: 'Extensão' }).eq('id', a.id);
        results.push({ nome: a.nome, newRole: 'extensao', error: error ? error.message : null });
      } else if (nomeUpper.includes('GUSTAVO')) {
        const { error } = await sb.from('assessores').update({ role: 'admin', label: 'Administrador' }).eq('id', a.id);
        results.push({ nome: a.nome, newRole: 'admin', error: error ? error.message : null });
      }
    }

    return res.status(200).json({ ok: true, results });
  }

  return res.status(400).json({ error: 'action: setup-schema | list-users | create-accounts | update-existing' });
};
