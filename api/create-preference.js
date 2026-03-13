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
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const MP_TOKEN = process.env.MERCADO_PAGO_ACCESS_TOKEN;
  if (!MP_TOKEN) return res.status(500).json({ error: 'Mercado Pago não configurado' });

  const { pedido_id, nome, email, curso, carga_horaria, tema, valor } = req.body || {};

  if (!pedido_id || !nome || !email || !valor) {
    return res.status(400).json({ error: 'Campos obrigatórios: pedido_id, nome, email, valor' });
  }

  // Determinar URL base
  const baseUrl = process.env.SITE_URL || ('https://' + (process.env.VERCEL_URL || 'localhost:3000'));

  try {
    const preference = {
      items: [{
        title: 'Projeto de Extensão - ' + curso + ' (' + carga_horaria + 'h)',
        description: tema ? tema.substring(0, 200) : 'Projeto de Extensão',
        quantity: 1,
        unit_price: parseFloat(valor),
        currency_id: 'BRL',
      }],
      payer: {
        name: nome,
        email: email,
      },
      back_urls: {
        success: baseUrl + '/extensao/status.html?pedido=' + pedido_id,
        failure: baseUrl + '/extensao/status.html?pedido=' + pedido_id + '&status=falha',
        pending: baseUrl + '/extensao/status.html?pedido=' + pedido_id + '&status=pendente',
      },
      auto_return: 'approved',
      external_reference: pedido_id,
      notification_url: baseUrl + '/api/webhook-mp',
      statement_descriptor: 'ASSESSORIA ACAD',
    };

    const resp = await fetch('https://api.mercadopago.com/checkout/preferences', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + MP_TOKEN,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(preference),
    });

    if (!resp.ok) {
      const text = await resp.text();
      console.error('MP error:', resp.status, text);
      return res.status(500).json({ error: 'Erro ao criar pagamento: ' + resp.status });
    }

    const data = await resp.json();
    return res.status(200).json({
      init_point: data.init_point,
      sandbox_init_point: data.sandbox_init_point,
      id: data.id,
    });

  } catch (err) {
    console.error('Create preference error:', err);
    return res.status(500).json({ error: err.message || 'Erro interno' });
  }
};
