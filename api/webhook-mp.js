/* ═══════════════════════════════════════════
   Vercel Serverless — Mercado Pago Webhook
   Recebe notificações de pagamento (IPN + Webhooks)
   ═══════════════════════════════════════════ */

module.exports = async function handler(req, res) {
  const MP_TOKEN = process.env.MERCADO_PAGO_ACCESS_TOKEN;
  const SB_URL   = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY   = process.env.SUPABASE_SERVICE_KEY;

  // MP exige resposta 200 imediata — sempre retornar OK
  // GET: formato IPN legado (?topic=payment&id=xxx)
  if (req.method === 'GET') {
    const { topic, id: qid } = req.query || {};
    if (topic === 'payment' && qid && MP_TOKEN && SB_KEY) {
      processarPagamento(qid, MP_TOKEN, SB_URL, SB_KEY).catch(e =>
        console.error('[webhook-mp] GET IPN error:', e.message)
      );
    }
    return res.status(200).send('OK');
  }

  if (req.method !== 'POST') return res.status(200).send('OK');

  if (!MP_TOKEN || !SB_KEY) {
    console.error('[webhook-mp] Variáveis de ambiente não configuradas');
    return res.status(200).send('OK');
  }

  try {
    const body = req.body || {};
    let paymentId = null;

    // Formato Webhooks: { "type": "payment", "data": { "id": "xxx" } }
    if (body.type === 'payment' && body.data?.id) {
      paymentId = body.data.id;
    }
    // Formato Webhooks v2: { "action": "payment.created", "data": { "id": "xxx" } }
    else if ((body.action === 'payment.created' || body.action === 'payment.updated') && body.data?.id) {
      paymentId = body.data.id;
    }
    // Formato IPN via POST: { "topic": "payment", "resource": "https://.../payments/xxx" }
    else if (body.topic === 'payment' && body.resource) {
      const parts = String(body.resource).split('/');
      paymentId = parts[parts.length - 1];
    }

    if (!paymentId) {
      console.log('[webhook-mp] Notificação sem payment ID:', JSON.stringify(body).substring(0, 200));
      return res.status(200).send('OK');
    }

    // Processar de forma assíncrona (não bloquear a resposta)
    processarPagamento(paymentId, MP_TOKEN, SB_URL, SB_KEY).catch(e =>
      console.error('[webhook-mp] Erro processando pagamento:', e.message)
    );

  } catch (err) {
    console.error('[webhook-mp] Erro no handler:', err.message);
  }

  return res.status(200).send('OK');
};

async function processarPagamento(paymentId, mpToken, sbUrl, sbKey) {
  // Buscar detalhes do pagamento na API do MP
  const payResp = await fetch(`https://api.mercadopago.com/v1/payments/${paymentId}`, {
    headers: { 'Authorization': 'Bearer ' + mpToken },
  });

  if (!payResp.ok) {
    console.error('[webhook-mp] Erro ao buscar pagamento', paymentId, ':', payResp.status);
    return;
  }

  const payment = await payResp.json();
  const externalRef = payment.external_reference;
  const mpStatus    = payment.status; // approved, pending, rejected, cancelled, etc.

  if (!externalRef) {
    console.log('[webhook-mp] Pagamento sem external_reference:', paymentId);
    return;
  }

  // Mapear status MP → status do pedido
  let pedidoStatus;
  switch (mpStatus) {
    case 'approved':  pedidoStatus = 'pago'; break;
    case 'rejected':
    case 'cancelled': pedidoStatus = 'cancelado'; break;
    default:          pedidoStatus = 'aguardando_pagamento';
  }

  // Atualizar pedido no Supabase
  const updateResp = await fetch(`${sbUrl}/rest/v1/pedidos_extensao?id=eq.${externalRef}`, {
    method: 'PATCH',
    headers: {
      'apikey': sbKey,
      'Authorization': 'Bearer ' + sbKey,
      'Content-Type': 'application/json',
      'Prefer': 'return=minimal',
    },
    body: JSON.stringify({
      payment_id:     String(paymentId),
      payment_status: mpStatus,
      status:         pedidoStatus,
      updated_at:     new Date().toISOString(),
    }),
  });

  if (updateResp.ok) {
    console.log(`[webhook-mp] Pedido ${externalRef} atualizado → ${pedidoStatus} (MP: ${mpStatus})`);
  } else {
    console.error('[webhook-mp] Supabase update error:', updateResp.status, await updateResp.text());
  }
}
