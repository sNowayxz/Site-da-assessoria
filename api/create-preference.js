/* ═══════════════════════════════════════════
   Vercel Serverless — Mercado Pago Checkout
   Cria preferência de pagamento
   ═══════════════════════════════════════════ */

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

  const MP_TOKEN = process.env.MERCADO_PAGO_ACCESS_TOKEN;
  const SB_URL   = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY   = process.env.SUPABASE_SERVICE_KEY;

  if (!MP_TOKEN) {
    console.error('[create-preference] MERCADO_PAGO_ACCESS_TOKEN não configurado');
    return res.status(500).json({ error: 'Pagamento não configurado. Contate o suporte.' });
  }

  const { pedido_id, nome, email, curso, carga_horaria, tema, valor } = req.body || {};

  if (!pedido_id || !nome || !email || !valor) {
    return res.status(400).json({ error: 'Campos obrigatórios: pedido_id, nome, email, valor' });
  }

  const valorFloat = parseFloat(valor);
  if (isNaN(valorFloat) || valorFloat <= 0) {
    return res.status(400).json({ error: 'Valor inválido' });
  }

  // URL base: preferir SITE_URL, fallback para VERCEL_URL
  const baseUrl = process.env.SITE_URL
    ? process.env.SITE_URL.replace(/\/$/, '')
    : ('https://' + (process.env.VERCEL_URL || 'site-da-assessoria.vercel.app'));

  try {
    const titulo = curso
      ? `Projeto de Extensão — ${curso} (${carga_horaria}h)`
      : `Projeto de Extensão (${carga_horaria}h)`;

    const preference = {
      items: [{
        title: titulo.substring(0, 256),
        description: tema ? tema.substring(0, 256) : 'Projeto de Extensão Universitária',
        quantity: 1,
        unit_price: valorFloat,
        currency_id: 'BRL',
      }],
      payer: { name: nome, email: email },
      back_urls: {
        success: `${baseUrl}/extensao/status.html?pedido=${pedido_id}`,
        failure: `${baseUrl}/extensao/status.html?pedido=${pedido_id}&status=falha`,
        pending: `${baseUrl}/extensao/status.html?pedido=${pedido_id}&status=pendente`,
      },
      auto_return: 'approved',
      external_reference: pedido_id,
      notification_url: `${baseUrl}/api/webhook-mp`,
      statement_descriptor: 'ASSESSORIA ACAD',
      expires: false,
    };

    const resp = await fetch('https://api.mercadopago.com/checkout/preferences', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + MP_TOKEN,
        'Content-Type': 'application/json',
        'X-Idempotency-Key': pedido_id,
      },
      body: JSON.stringify(preference),
    });

    const data = await resp.json();

    if (!resp.ok) {
      console.error('[create-preference] MP error:', resp.status, JSON.stringify(data));
      return res.status(502).json({
        error: 'Erro ao criar pagamento',
        detail: data.message || data.cause?.[0]?.description || resp.status,
      });
    }

    // Salvar preference_id no Supabase (se service_key disponível)
    if (SB_KEY && data.id) {
      try {
        await fetch(`${SB_URL}/rest/v1/pedidos_extensao?id=eq.${pedido_id}`, {
          method: 'PATCH',
          headers: {
            'apikey': SB_KEY,
            'Authorization': 'Bearer ' + SB_KEY,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal',
          },
          body: JSON.stringify({ preference_id: data.id, updated_at: new Date().toISOString() }),
        });
      } catch (sbErr) {
        console.warn('[create-preference] Supabase update falhou:', sbErr.message);
      }
    }

    return res.status(200).json({
      init_point: data.init_point,
      sandbox_init_point: data.sandbox_init_point,
      id: data.id,
    });

  } catch (err) {
    console.error('[create-preference] Erro inesperado:', err);
    return res.status(500).json({ error: err.message || 'Erro interno' });
  }
};
