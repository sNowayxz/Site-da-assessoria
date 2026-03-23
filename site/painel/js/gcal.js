/* ═══════════════════════════════════════════
   Google Calendar Integration — gcal.js
   ═══════════════════════════════════════════ */

var GCAL_CLIENT_ID = '345600364747-hujcipm7lg8bp1bucqbqcdld8k46urt6.apps.googleusercontent.com';
var GCAL_SCOPES = 'https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email';
var GCAL_API = 'https://www.googleapis.com/calendar/v3';

var _gcalAccessToken = null;
var _gcalTokenExpiry = null;
var _gcalConnected = false;
var _gcalEmail = '';
var _gcalCodeClient = null;

// ── Inicialização ──
function gcalInit(callback) {
  // Verificar se usuário já tem Google conectado
  sb.from('google_calendar_tokens')
    .select('google_email, token_expires_at')
    .eq('user_id', currentUserId)
    .single()
    .then(function (res) {
      if (res.data && !res.error) {
        _gcalConnected = true;
        _gcalEmail = res.data.google_email || '';
        gcalUpdateUI();
      }
      if (callback) callback();
    });
}

// ── Atualizar UI ──
function gcalUpdateUI() {
  var badge = document.getElementById('gcal-badge');
  var btnConnect = document.getElementById('btn-gcal-connect');
  var btnDisconnect = document.getElementById('btn-gcal-disconnect');

  if (!badge) return;

  if (_gcalConnected) {
    badge.style.display = 'flex';
    badge.querySelector('.gcal-email').textContent = _gcalEmail || 'Conectado';
    if (btnConnect) btnConnect.style.display = 'none';
    if (btnDisconnect) btnDisconnect.style.display = 'inline-flex';
  } else {
    badge.style.display = 'none';
    if (btnConnect) btnConnect.style.display = 'inline-flex';
    if (btnDisconnect) btnDisconnect.style.display = 'none';
  }
}

// ── Conectar Google Calendar ──
function gcalConnect() {
  if (!GCAL_CLIENT_ID) {
    showToast('Google Client ID não configurado.', 'error');
    return;
  }

  if (typeof google === 'undefined' || !google.accounts || !google.accounts.oauth2) {
    showToast('Google Identity Services não carregou. Recarregue a página.', 'error');
    return;
  }

  _gcalCodeClient = google.accounts.oauth2.initCodeClient({
    client_id: GCAL_CLIENT_ID,
    scope: GCAL_SCOPES,
    ux_mode: 'popup',
    callback: function (response) {
      if (response.error) {
        showToast('Erro na autenticação Google: ' + response.error, 'error');
        return;
      }
      _gcalExchangeCode(response.code);
    },
  });

  _gcalCodeClient.requestCode();
}

// ── Trocar code por tokens via Edge Function ──
function _gcalExchangeCode(code) {
  showToast('Conectando ao Google Calendar...', 'info');

  sb.auth.getSession().then(function (sessionRes) {
    var token = sessionRes.data.session ? sessionRes.data.session.access_token : null;
    if (!token) {
      showToast('Sessão expirada. Faça login novamente.', 'error');
      return;
    }

    fetch(SUPABASE_URL + '/functions/v1/google-calendar-auth', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'apikey': SUPABASE_ANON_KEY
      },
      body: JSON.stringify({ code: code, redirect_uri: 'postmessage' })
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.error) {
        showToast('Erro: ' + data.error, 'error');
        return;
      }
      _gcalAccessToken = data.access_token;
      _gcalTokenExpiry = Date.now() + (data.expires_in || 3600) * 1000;
      _gcalConnected = true;
      _gcalEmail = data.google_email || '';
      gcalUpdateUI();
      showToast('Google Calendar conectado!', 'success');

      // Recarregar agenda para mostrar eventos Google
      if (typeof renderCalendar === 'function') renderCalendar();
    })
    .catch(function (err) {
      showToast('Erro ao conectar: ' + err.message, 'error');
    });
  });
}

// ── Desconectar ──
function gcalDisconnect() {
  if (typeof showConfirm === 'function') {
    showConfirm('Desconectar Google Calendar?', function () { _doGcalDisconnect(); }, {
      title: 'Desconectar',
      confirmText: 'Desconectar',
      type: 'danger'
    });
  } else {
    _doGcalDisconnect();
  }
}

function _doGcalDisconnect() {
  sb.auth.getSession().then(function (sessionRes) {
    var token = sessionRes.data.session ? sessionRes.data.session.access_token : null;
    if (!token) return;

    fetch(SUPABASE_URL + '/functions/v1/google-calendar-disconnect', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'apikey': SUPABASE_ANON_KEY
      },
      body: JSON.stringify({})
    })
    .then(function (res) { return res.json(); })
    .then(function () {
      _gcalAccessToken = null;
      _gcalTokenExpiry = null;
      _gcalConnected = false;
      _gcalEmail = '';
      gcalUpdateUI();
      showToast('Google Calendar desconectado.', 'success');
      if (typeof renderCalendar === 'function') renderCalendar();
    });
  });
}

// ── Garantir token válido ──
function gcalEnsureToken(callback) {
  if (!_gcalConnected) { callback(null); return; }

  // Token ainda válido (com 60s de margem)
  if (_gcalAccessToken && _gcalTokenExpiry && Date.now() < _gcalTokenExpiry - 60000) {
    callback(_gcalAccessToken);
    return;
  }

  // Renovar via Edge Function
  sb.auth.getSession().then(function (sessionRes) {
    var token = sessionRes.data.session ? sessionRes.data.session.access_token : null;
    if (!token) { callback(null); return; }

    fetch(SUPABASE_URL + '/functions/v1/google-calendar-refresh', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'apikey': SUPABASE_ANON_KEY
      },
      body: JSON.stringify({})
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.error) {
        console.warn('Erro ao renovar token Google:', data.error);
        _gcalConnected = false;
        gcalUpdateUI();
        callback(null);
        return;
      }
      _gcalAccessToken = data.access_token;
      _gcalTokenExpiry = Date.now() + (data.expires_in || 3600) * 1000;
      callback(_gcalAccessToken);
    })
    .catch(function () { callback(null); });
  });
}

// ── Sync: Painel → Google (criar/atualizar) ──
function gcalSyncEventToGoogle(evento) {
  if (!_gcalConnected) return;

  gcalEnsureToken(function (token) {
    if (!token) return;

    // Verificar se já existe mapeamento
    sb.from('google_calendar_sync')
      .select('google_event_id')
      .eq('user_id', currentUserId)
      .eq('evento_id', evento.id)
      .single()
      .then(function (res) {
        var googleBody = _gcalBuildEventBody(evento);

        if (res.data && res.data.google_event_id) {
          // Atualizar evento existente
          fetch(GCAL_API + '/calendars/primary/events/' + res.data.google_event_id, {
            method: 'PATCH',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify(googleBody)
          }).catch(function (e) { console.warn('Erro ao atualizar evento Google:', e); });
        } else {
          // Criar novo evento
          fetch(GCAL_API + '/calendars/primary/events', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
            body: JSON.stringify(googleBody)
          })
          .then(function (r) { return r.json(); })
          .then(function (gEvent) {
            if (gEvent.id) {
              sb.from('google_calendar_sync').insert({
                user_id: currentUserId,
                evento_id: evento.id,
                google_event_id: gEvent.id
              });
            }
          })
          .catch(function (e) { console.warn('Erro ao criar evento Google:', e); });
        }
      });
  });
}

// ── Sync: Deletar do Google ──
function gcalDeleteFromGoogle(eventoId) {
  if (!_gcalConnected) return;

  gcalEnsureToken(function (token) {
    if (!token) return;

    sb.from('google_calendar_sync')
      .select('google_event_id')
      .eq('user_id', currentUserId)
      .eq('evento_id', eventoId)
      .single()
      .then(function (res) {
        if (res.data && res.data.google_event_id) {
          fetch(GCAL_API + '/calendars/primary/events/' + res.data.google_event_id, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
          }).catch(function (e) { console.warn('Erro ao deletar evento Google:', e); });

          sb.from('google_calendar_sync')
            .delete()
            .eq('user_id', currentUserId)
            .eq('evento_id', eventoId);
        }
      });
  });
}

// ── Pull: Google → Painel ──
function gcalPullFromGoogle(startDate, endDate, callback) {
  if (!_gcalConnected) { if (callback) callback([]); return; }

  gcalEnsureToken(function (token) {
    if (!token) { if (callback) callback([]); return; }

    var timeMin = startDate + 'T00:00:00Z';
    var timeMax = endDate + 'T23:59:59Z';

    fetch(GCAL_API + '/calendars/primary/events?timeMin=' + encodeURIComponent(timeMin) +
      '&timeMax=' + encodeURIComponent(timeMax) +
      '&singleEvents=true&orderBy=startTime&maxResults=250', {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (!data.items) { if (callback) callback([]); return; }

      var events = data.items.map(function (item) {
        return _gcalMapToEvent(item);
      }).filter(function (ev) { return ev !== null; });

      // Salvar no Supabase para cache
      _gcalUpsertImported(events);

      if (callback) callback(events);
    })
    .catch(function (e) {
      console.warn('Erro ao puxar eventos Google:', e);
      // Fallback: ler do cache local
      sb.from('google_calendar_imported')
        .select('*')
        .eq('user_id', currentUserId)
        .gte('data', startDate)
        .lte('data', endDate)
        .then(function (res) {
          var cached = (res.data || []).map(function (row) {
            return {
              type: 'google',
              text: row.titulo,
              date: row.data,
              hora: row.hora,
              descricao: row.descricao || '',
              cor: row.cor || '#ea4335',
              google_event_id: row.google_event_id,
              deletable: false
            };
          });
          if (callback) callback(cached);
        });
    });
  });
}

// ── Helpers ──
function _gcalBuildEventBody(evento) {
  var body = {
    summary: evento.titulo || evento.text || 'Evento',
    description: evento.descricao || '',
  };

  if (evento.hora) {
    body.start = { dateTime: evento.data + 'T' + evento.hora + ':00', timeZone: 'America/Sao_Paulo' };
    body.end = { dateTime: evento.data + 'T' + evento.hora + ':00', timeZone: 'America/Sao_Paulo' };
  } else {
    body.start = { date: evento.data };
    body.end = { date: evento.data };
  }

  // Cor: mapear para colorId do Google (1-11)
  var corMap = {
    '#8b5cf6': '1', '#dc2626': '11', '#2563eb': '9',
    '#16a34a': '10', '#f0c030': '5', '#ea4335': '11'
  };
  if (evento.cor && corMap[evento.cor]) {
    body.colorId = corMap[evento.cor];
  }

  return body;
}

function _gcalMapToEvent(googleEvent) {
  if (!googleEvent.start) return null;

  var startDate, startTime;
  if (googleEvent.start.date) {
    startDate = googleEvent.start.date;
    startTime = null;
  } else if (googleEvent.start.dateTime) {
    var dt = new Date(googleEvent.start.dateTime);
    startDate = dt.getFullYear() + '-' +
      String(dt.getMonth() + 1).padStart(2, '0') + '-' +
      String(dt.getDate()).padStart(2, '0');
    startTime = String(dt.getHours()).padStart(2, '0') + ':' +
      String(dt.getMinutes()).padStart(2, '0');
  } else {
    return null;
  }

  return {
    type: 'google',
    text: googleEvent.summary || '(Sem título)',
    date: startDate,
    hora: startTime,
    descricao: googleEvent.description || '',
    cor: '#ea4335',
    google_event_id: googleEvent.id,
    deletable: false
  };
}

function _gcalUpsertImported(events) {
  if (!events.length) return;

  var rows = events.map(function (ev) {
    return {
      user_id: currentUserId,
      google_event_id: ev.google_event_id,
      titulo: ev.text,
      data: ev.date,
      hora: ev.hora,
      descricao: ev.descricao,
      cor: ev.cor || '#ea4335',
      last_synced_at: new Date().toISOString()
    };
  });

  sb.from('google_calendar_imported')
    .upsert(rows, { onConflict: 'user_id,google_event_id' })
    .then(function (res) {
      if (res.error) console.warn('Erro ao cachear eventos Google:', res.error);
    });
}
