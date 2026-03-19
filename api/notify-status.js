/**
 * Notificação por email quando status de solicitação muda
 *
 * POST /api/notify-status
 * Body: { solicitacao_id, novo_status, aluno_nome, ra, horas }
 *
 * Requer: RESEND_API_KEY no Vercel Environment Variables
 * Cadastre-se grátis em https://resend.com (100 emails/dia)
 */

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });

  const RESEND_KEY = process.env.RESEND_API_KEY;
  const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'contato@assessoriaextensoes.com';

  if (!RESEND_KEY) {
    // Se não tem Resend configurado, apenas loga e retorna OK
    console.log('RESEND_API_KEY não configurada — notificação ignorada');
    return res.status(200).json({ ok: true, skipped: true, reason: 'RESEND_API_KEY not set' });
  }

  const { aluno_nome, ra, novo_status, horas, email_aluno } = req.body || {};
  if (!aluno_nome || !novo_status) {
    return res.status(400).json({ error: 'aluno_nome + novo_status required' });
  }

  const EXTENSAO_EMAIL = process.env.EXTENSAO_EMAIL || 'gessica@assessoriaextensoes.com';

  const STATUS_LABELS = {
    aguardando: '⏳ Aguardando',
    desenvolvendo: '🔄 Em Desenvolvimento',
    finalizado: '✅ Finalizado',
    finalizado_cobrar: '💰 Finalizado (a Cobrar)',
    novo_pedido: '🆕 Novo Pedido'
  };

  const isNewOrder = novo_status === 'novo_pedido';
  const statusLabel = STATUS_LABELS[novo_status] || novo_status;

  // Template diferente para novo pedido (enviado para Gessica) vs atualização (enviado para aluno)
  const htmlBody = isNewOrder ? `
    <div style="font-family:Inter,Arial,sans-serif;max-width:500px;margin:0 auto;background:#f0f7ff;padding:30px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h2 style="color:#1a1a2e;margin:0;">🆕 Novo Pedido de Extensão</h2>
        <p style="color:#8892a4;font-size:0.85rem;">Um aluno acabou de solicitar extensão pelo site</p>
      </div>
      <div style="background:white;padding:24px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
        <div style="background:#3b82f6;color:white;padding:12px 20px;border-radius:10px;text-align:center;font-weight:700;font-size:1.1rem;margin:0 0 16px;">
          ${aluno_nome}
        </div>
        ${ra ? '<p style="color:#4a5568;margin:8px 0;"><strong>RA:</strong> ' + ra + '</p>' : ''}
        ${horas ? '<p style="color:#4a5568;margin:8px 0;"><strong>Horas:</strong> ' + horas + 'h</p>' : ''}
        ${email_aluno ? '<p style="color:#4a5568;margin:8px 0;"><strong>Email:</strong> ' + email_aluno + '</p>' : ''}
        <hr style="border:none;border-top:1px solid #eef1f6;margin:20px 0;">
        <p style="color:#3b82f6;font-weight:600;text-align:center;margin:0;">
          <a href="https://assessoriaextensoes.com/painel/acompanhar.html" style="color:#3b82f6;">Acessar Painel →</a>
        </p>
      </div>
    </div>
  ` : `
    <div style="font-family:Inter,Arial,sans-serif;max-width:500px;margin:0 auto;background:#f8f9fc;padding:30px;border-radius:16px;">
      <div style="text-align:center;margin-bottom:24px;">
        <h2 style="color:#1a1a2e;margin:0;">Assessoria Extensões</h2>
        <p style="color:#8892a4;font-size:0.85rem;">Atualização de Status</p>
      </div>
      <div style="background:white;padding:24px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
        <p style="margin:0 0 16px;color:#2d3748;">Olá <strong>${aluno_nome}</strong>,</p>
        <p style="margin:0 0 16px;color:#4a5568;">O status da sua solicitação de extensão foi atualizado:</p>
        <div style="background:#f0c030;color:#1a1a2e;padding:12px 20px;border-radius:10px;text-align:center;font-weight:700;font-size:1.1rem;margin:16px 0;">
          ${statusLabel}
        </div>
        ${ra ? '<p style="color:#8892a4;font-size:0.85rem;margin:8px 0;">RA: <strong>' + ra + '</strong></p>' : ''}
        ${horas ? '<p style="color:#8892a4;font-size:0.85rem;margin:8px 0;">Horas contratadas: <strong>' + horas + 'h</strong></p>' : ''}
        <hr style="border:none;border-top:1px solid #eef1f6;margin:20px 0;">
        <p style="color:#8892a4;font-size:0.82rem;margin:0;">Acompanhe seu projeto em <a href="https://assessoriaextensoes.com/aluno/" style="color:#3b82f6;">Área do Aluno</a></p>
      </div>
      <p style="text-align:center;color:#8892a4;font-size:0.75rem;margin-top:16px;">© 2026 Assessoria Extensões</p>
    </div>
  `;

  try {
    // Novo pedido: envia para Gessica + admin. Atualização: envia para aluno + admin
    const recipients = [ADMIN_EMAIL];
    if (isNewOrder) {
      recipients.push(EXTENSAO_EMAIL);
    }
    if (email_aluno && email_aluno.includes('@') && !isNewOrder) {
      recipients.push(email_aluno);
    }

    const resp = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RESEND_KEY}`
      },
      body: JSON.stringify({
        from: 'Assessoria Extensões <noreply@assessoriaextensoes.com>',
        to: recipients,
        subject: `${statusLabel} — ${aluno_nome}`,
        html: htmlBody
      })
    });

    const result = await resp.json();

    if (resp.ok) {
      return res.status(200).json({ ok: true, email_id: result.id });
    } else {
      console.error('Resend error:', result);
      return res.status(200).json({ ok: true, warning: 'Email failed but operation continues', error: result });
    }
  } catch (e) {
    // Não bloqueia a operação se email falhar
    console.error('Email error:', e.message);
    return res.status(200).json({ ok: true, warning: 'Email error: ' + e.message });
  }
};
