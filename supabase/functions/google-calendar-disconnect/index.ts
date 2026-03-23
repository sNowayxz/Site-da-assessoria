// Edge Function: google-calendar-disconnect
// Revoga tokens Google e limpa dados de sync

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(JSON.stringify({ error: 'Não autorizado' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

    // Verificar usuário
    const userClient = createClient(supabaseUrl, supabaseAnonKey, {
      global: { headers: { Authorization: authHeader } },
    })

    const { data: { user }, error: authError } = await userClient.auth.getUser()
    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Sessão inválida' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const adminClient = createClient(supabaseUrl, supabaseServiceKey)

    // Buscar token para revogar no Google
    const { data: tokenRow } = await adminClient
      .from('google_calendar_tokens')
      .select('access_token, refresh_token')
      .eq('user_id', user.id)
      .single()

    if (tokenRow) {
      // Revogar no Google (best effort)
      var tokenToRevoke = tokenRow.access_token || tokenRow.refresh_token
      if (tokenToRevoke) {
        try {
          await fetch('https://oauth2.googleapis.com/revoke?token=' + encodeURIComponent(tokenToRevoke), {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          })
        } catch (_) {
          // revogação é best-effort
        }
      }
    }

    // Limpar todas as tabelas relacionadas
    await Promise.all([
      adminClient.from('google_calendar_tokens').delete().eq('user_id', user.id),
      adminClient.from('google_calendar_sync').delete().eq('user_id', user.id),
      adminClient.from('google_calendar_imported').delete().eq('user_id', user.id),
    ])

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
