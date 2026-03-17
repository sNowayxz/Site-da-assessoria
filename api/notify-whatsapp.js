/* ═══════════════════════════════════════════
   API: Enviar Notificação WhatsApp
   ═══════════════════════════════════════════
   POST /api/notify-whatsapp
   Body: { telefone, mensagem, aluno_id?, tipo? }

   Usa a API do WhatsApp via CallMeBot (gratuita) ou
   Evolution API (self-hosted) — configurável via env vars.

   Fallback: gera link wa.me para envio manual.
   ═══════════════════════════════════════════ */

const { createClient } = require('@supabase/supabase-js');

module.exports = async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { telefone, mensagem, aluno_id, tipo } = req.body || {};

    if (!telefone || !mensagem) {
      return res.status(400).json({ error: 'telefone e mensagem são obrigatórios' });
    }

    // Limpa telefone
    const tel = telefone.replace(/\D/g, '');
    const telFormatted = tel.startsWith('55') ? tel : '55' + tel;

    // Tenta enviar via Evolution API (se configurada)
    let sent = false;
    let errorMsg = null;

    if (process.env.EVOLUTION_API_URL && process.env.EVOLUTION_API_KEY) {
      try {
        const evoRes = await fetch(process.env.EVOLUTION_API_URL + '/message/sendText/' + (process.env.EVOLUTION_INSTANCE || 'default'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'apikey': process.env.EVOLUTION_API_KEY
          },
          body: JSON.stringify({
            number: telFormatted,
            text: mensagem
          })
        });
        if (evoRes.ok) sent = true;
        else errorMsg = 'Evolution API error: ' + evoRes.status;
      } catch (e) {
        errorMsg = 'Evolution API unreachable: ' + e.message;
      }
    }

    // Fallback: CallMeBot (se configurada)
    if (!sent && process.env.CALLMEBOT_API_KEY) {
      try {
        const encoded = encodeURIComponent(mensagem);
        const url = `https://api.callmebot.com/whatsapp.php?phone=${telFormatted}&text=${encoded}&apikey=${process.env.CALLMEBOT_API_KEY}`;
        const cmbRes = await fetch(url);
        if (cmbRes.ok) sent = true;
        else errorMsg = 'CallMeBot error: ' + cmbRes.status;
      } catch (e) {
        errorMsg = 'CallMeBot unreachable: ' + e.message;
      }
    }

    // Gera link manual como fallback
    const waLink = 'https://wa.me/' + telFormatted + '?text=' + encodeURIComponent(mensagem);

    // Log no banco
    if (process.env.SUPABASE_SERVICE_KEY) {
      try {
        const supabase = createClient(
          process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co',
          process.env.SUPABASE_SERVICE_KEY
        );
        await supabase.from('notificacoes').insert({
          aluno_id: aluno_id || null,
          tipo: tipo || 'geral',
          mensagem: mensagem,
          canal: 'whatsapp',
          enviado: sent,
          erro: sent ? null : (errorMsg || 'Nenhuma API configurada')
        });
      } catch (e) {
        console.warn('Erro ao logar notificação:', e.message);
      }
    }

    return res.status(200).json({
      success: true,
      sent: sent,
      waLink: waLink,
      message: sent ? 'Mensagem enviada com sucesso!' : 'Mensagem não enviada automaticamente. Use o link do WhatsApp.',
      error: sent ? null : errorMsg
    });

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
