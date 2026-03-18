/* Setup Roles — Cria contas de assessoria (temporário) */

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const SB_URL = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;
  if (!SB_KEY) return res.status(500).json({ error: 'SUPABASE_SERVICE_KEY não configurada' });

  const headers = {
    'apikey': SB_KEY,
    'Authorization': `Bearer ${SB_KEY}`,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
  };

  const { action } = req.body || {};
  const results = [];

  // ─── List users ───
  if (action === 'list-users') {
    const r1 = await fetch(`${SB_URL}/rest/v1/assessores?select=*`, { headers });
    const assessores = await r1.json();

    const r2 = await fetch(`${SB_URL}/auth/v1/admin/users`, {
      headers: { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}` }
    });
    const authData = await r2.json();

    return res.status(200).json({
      ok: true,
      assessores,
      authUsers: (authData.users || []).map(u => ({ id: u.id, email: u.email }))
    });
  }

  // ─── Create 10 assessoria accounts ───
  if (action === 'create-accounts') {
    const accounts = [
      { email: 'einstein@assessoriaextensoes.com', password: 'Einstein2026!', nome: 'Einstein', label: 'Assessoria Einstein' },
      { email: 'jed@assessoriaextensoes.com', password: 'JeD2026!', nome: 'J&D', label: 'Assessoria J&D' },
      { email: 'dl@assessoriaextensoes.com', password: 'DL2026!', nome: 'DL', label: 'Assessoria DL' },
      { email: 'ary@assessoriaextensoes.com', password: 'Ary2026!', nome: 'Ary', label: 'Assessoria Ary' },
      { email: 'prime@assessoriaextensoes.com', password: 'Prime2026!', nome: 'Prime', label: 'Assessoria Prime' },
      { email: 'azul@assessoriaextensoes.com', password: 'Azul2026!', nome: 'Azul', label: 'Assessoria Azul' },
      { email: 'barbara@assessoriaextensoes.com', password: 'Barbara2026!', nome: 'Barbara', label: 'Assessoria Barbara' },
      { email: 'renderizzi@assessoriaextensoes.com', password: 'Renderizzi2026!', nome: 'Renderizzi', label: 'Assessoria Renderizzi' },
      { email: 'brayan@assessoriaextensoes.com', password: 'Brayan2026!', nome: 'Brayan', label: 'Assessoria Brayan' },
      { email: 'exellence@assessoriaextensoes.com', password: 'Exellence2026!', nome: 'Exellence', label: 'Assessoria Exellence' },
    ];

    for (const acc of accounts) {
      try {
        // Create auth user
        const authResp = await fetch(`${SB_URL}/auth/v1/admin/users`, {
          method: 'POST',
          headers: { 'apikey': SB_KEY, 'Authorization': `Bearer ${SB_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: acc.email,
            password: acc.password,
            email_confirm: true,
          }),
        });
        const authData = await authResp.json();

        if (!authResp.ok || !authData.id) {
          results.push({ email: acc.email, error: authData.msg || authData.message || JSON.stringify(authData) });
          continue;
        }

        // Insert into assessores
        const dbResp = await fetch(`${SB_URL}/rest/v1/assessores`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            id: authData.id,
            nome: acc.nome,
            role: 'assessoria',
            label: acc.label,
          }),
        });
        const dbData = await dbResp.json();

        results.push({
          email: acc.email,
          id: authData.id,
          ok: dbResp.ok,
          dbError: dbResp.ok ? null : JSON.stringify(dbData),
        });
      } catch (e) {
        results.push({ email: acc.email, error: e.message });
      }
    }

    return res.status(200).json({ ok: true, results });
  }

  // ─── Update existing users (Augusto→dono, Gessica→extensao, Gustavo→admin) ───
  if (action === 'update-existing') {
    const r = await fetch(`${SB_URL}/rest/v1/assessores?select=id,nome,role`, { headers });
    const assessores = await r.json();

    for (const a of (assessores || [])) {
      const nome = (a.nome || '').toUpperCase();
      let update = null;

      if (nome.includes('AUGUSTO')) update = { role: 'dono', label: 'Dono' };
      else if (nome.includes('GESSICA') || nome.includes('GÉSSICA')) update = { role: 'extensao', label: 'Extensão' };
      else if (nome.includes('GUSTAVO')) update = { role: 'admin', label: 'Administrador' };

      if (update) {
        const ur = await fetch(`${SB_URL}/rest/v1/assessores?id=eq.${a.id}`, {
          method: 'PATCH',
          headers,
          body: JSON.stringify(update),
        });
        results.push({ nome: a.nome, ...update, ok: ur.ok });
      }
    }

    return res.status(200).json({ ok: true, results });
  }

  return res.status(400).json({ error: 'action: list-users | create-accounts | update-existing' });
};
