/* ═══════════════════════════════════════════
   Vercel Serverless — Mercado Pago Webhook
   Recebe notificações de pagamento (IPN)
   ═══════════════════════════════════════════ */

module.exports = async function handler(req, res) {
  // MP precisa receber 200 rapidamente
  if (req.method === 'GET') return res.status(200).send('OK');
  if (req.method !== 'POST') return res.status(200).send('OK');

  const MP_TOKEN = process.env.MERCADO_PAGO_ACCESS_TOKEN;
  const SB_URL = process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co';
  const SB_KEY = process.env.SUPABASE_SERVICE_KEY;

  if (!MP_TOKEN || !SB_KEY) {
    console.error('Missing env vars');
    return res.status(200).send('OK');
  }

  try {
    const body = req.body || {};

    // Mercado Pago envia diferentes tipos de notificação
    var paymentId = null;

    if (body.type === 'payment' && body.data && body.data.id) {
      paymentId = body.data.id;
    } else if (body.action === 'payment.created' || body.action === 'payment.updated') {
      paymentId = body.data ? body.data.id : null;
    } else if (body.topic === 'payment' && body.resource) {
      // IPN format: resource is a URL, extract ID
      var parts = body.resource.split('/');
      paymentId = parts[parts.length - 1];
    }

    if (!paymentId) {
      console.log('Webhook sem payment ID:', JSON.stringify(body));
      return res.status(200).send('OK');
    }

    // Buscar detalhes do pagamento na API do MP
    var payResp = await fetch('https://api.mercadopago.com/v1/payments/' + paymentId, {
      headers: { 'Authorization': 'Bearer ' + MP_TOKEN },
    });

    if (!payResp.ok) {
      console.error('MP payment fetch error:', payResp.status);
      return res.status(200).send('OK');
    }

    var payment = await payResp.json();
    var externalRef = payment.external_reference;
    var mpStatus = payment.status; // approved, pending, rejected, etc.

    if (!externalRef) {
      console.log('Payment sem external_reference:', paymentId);
      return res.status(200).send('OK');
    }

    // Mapear status MP para status do pedido
    var pedidoStatus = 'aguardando_pagamento';
    if (mpStatus === 'approved') pedidoStatus = 'pago';
    else if (mpStatus === 'rejected' || mpStatus === 'cancelled') pedidoStatus = 'cancelado';

    // Atualizar pedido no Supabase via service_role
    var updateResp = await fetch(SB_URL + '/rest/v1/pedidos_extensao?id=eq.' + externalRef, {
      method: 'PATCH',
      headers: {
        'apikey': SB_KEY,
        'Authorization': 'Bearer ' + SB_KEY,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify({
        payment_id: String(paymentId),
        payment_status: mpStatus,
        status: pedidoStatus,
        updated_at: new Date().toISOString(),
      }),
    });

    if (!updateResp.ok) {
      console.error('Supabase update error:', updateResp.status, await updateResp.text());
    } else {
      console.log('Pedido atualizado:', externalRef, '->', pedidoStatus);
    }

  } catch (err) {
    console.error('Webhook error:', err);
  }

  return res.status(200).send('OK');
};
