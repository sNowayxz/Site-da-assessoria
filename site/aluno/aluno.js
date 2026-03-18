/* ═══════════════════════════════════════════
   Área do Aluno — Logic
   ═══════════════════════════════════════════ */

var SUPA_URL = 'https://lztfoprapoyicldunhzw.supabase.co';
var SUPA_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6dGZvcHJhcG95aWNsZHVuaHp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMzY0MzIsImV4cCI6MjA4ODkxMjQzMn0.8Qyq2bVA0oK8gji9hG2AWG-gQ3oH4nWm3QOqQ59S9IA';

function supaGet(path) {
  return fetch(SUPA_URL + '/rest/v1/' + path, {
    headers: {
      'apikey': SUPA_KEY,
      'Authorization': 'Bearer ' + SUPA_KEY
    }
  }).then(function(r) { return r.json(); });
}

// Elements
var loginScreen = document.getElementById('login-screen');
var dashScreen = document.getElementById('dashboard-screen');
var formRa = document.getElementById('form-ra');
var inputRa = document.getElementById('input-ra');
var btnEntrar = document.getElementById('btn-entrar');
var btnText = document.getElementById('btn-text');
var btnLoading = document.getElementById('btn-loading');
var loginError = document.getElementById('login-error');
var btnSair = document.getElementById('btn-sair');

// Check saved RA
var savedRa = sessionStorage.getItem('aluno-ra');
if (savedRa) {
  loadAluno(savedRa);
}

// Form submit
formRa.addEventListener('submit', function(e) {
  e.preventDefault();
  var ra = inputRa.value.trim();
  if (!ra) return;
  loginError.style.display = 'none';
  btnEntrar.disabled = true;
  btnText.style.display = 'none';
  btnLoading.style.display = 'inline';
  loadAluno(ra);
});

btnSair.addEventListener('click', function() {
  sessionStorage.removeItem('aluno-ra');
  dashScreen.style.display = 'none';
  loginScreen.style.display = 'block';
  inputRa.value = '';
});

function loadAluno(ra) {
  supaGet('alunos?ra=eq.' + encodeURIComponent(ra) + '&select=*').then(function(data) {
    if (!data || !data.length) {
      showError('RA não encontrado. Verifique e tente novamente.');
      return;
    }

    var aluno = data[0];
    sessionStorage.setItem('aluno-ra', ra);

    // Show dashboard
    loginScreen.style.display = 'none';
    dashScreen.style.display = 'block';

    document.getElementById('aluno-nome').textContent = 'Olá, ' + aluno.nome.split(' ')[0] + '!';
    document.getElementById('aluno-info').textContent = 'RA: ' + aluno.ra + ' | Curso: ' + (aluno.curso || 'Não informado');

    // Load atividades
    supaGet('atividades?aluno_id=eq.' + aluno.id + '&select=*&order=created_at.desc').then(function(atvs) {
      atvs = atvs || [];
      var pendentes = atvs.filter(function(a) { return a.status === 'pendente'; }).length;
      var andamento = atvs.filter(function(a) { return a.status === 'em_andamento'; }).length;
      var entregues = atvs.filter(function(a) { return a.status === 'entregue'; }).length;

      document.getElementById('stat-total').textContent = atvs.length;
      document.getElementById('stat-pendentes').textContent = pendentes;
      document.getElementById('stat-andamento').textContent = andamento;
      document.getElementById('stat-entregues').textContent = entregues;

      var container = document.getElementById('aluno-atividades');
      if (!atvs.length) {
        container.innerHTML = '<div class="aluno-empty">Nenhuma atividade encontrada.</div>';
        return;
      }

      container.innerHTML = atvs.map(function(a) {
        return '<div class="aluno-activity-card status-' + a.status + '">' +
          '<div class="activity-info">' +
            '<h4>' + escapeHtml(a.tipo.charAt(0).toUpperCase() + a.tipo.slice(1)) + (a.descricao ? ' — ' + escapeHtml(a.descricao) : '') + '</h4>' +
            '<p>' + formatDate(a.created_at) + (a.dt_entrega ? ' · Entrega: ' + formatDate(a.dt_entrega) : '') + '</p>' +
          '</div>' +
          '<span class="activity-badge badge-' + a.status + '">' + formatStatus(a.status) + '</span>' +
          '</div>';
      }).join('');
    });

    // Load pagamentos
    supaGet('pagamentos?aluno_id=eq.' + aluno.id + '&select=*&order=created_at.desc').then(function(pags) {
      pags = pags || [];
      var totalPago = 0, totalPendente = 0;
      pags.forEach(function(p) {
        var v = parseFloat(p.valor) || 0;
        if (p.status === 'pago') totalPago += v;
        else if (p.status === 'pendente' || p.status === 'atrasado') totalPendente += v;
      });

      document.getElementById('fin-pagos').textContent = 'R$ ' + totalPago.toFixed(2).replace('.', ',');
      document.getElementById('fin-pendentes').textContent = 'R$ ' + totalPendente.toFixed(2).replace('.', ',');

      var container = document.getElementById('aluno-pagamentos');
      if (!pags.length) {
        container.innerHTML = '<div class="aluno-empty">Nenhum pagamento encontrado.</div>';
        return;
      }

      container.innerHTML = pags.map(function(p) {
        return '<div class="aluno-activity-card status-' + (p.status === 'pago' ? 'entregue' : 'pendente') + '">' +
          '<div class="activity-info">' +
            '<h4>R$ ' + parseFloat(p.valor).toFixed(2).replace('.', ',') + ' — ' + escapeHtml(p.tipo) + '</h4>' +
            '<p>' + (p.referencia ? escapeHtml(p.referencia) + ' · ' : '') + formatDate(p.created_at) +
            (p.dt_vencimento ? ' · Venc: ' + formatDate(p.dt_vencimento) : '') + '</p>' +
          '</div>' +
          '<span class="activity-badge badge-' + p.status + '">' + p.status.charAt(0).toUpperCase() + p.status.slice(1) + '</span>' +
          '</div>';
      }).join('');
    });

    // Load extensão (projeto de extensão pelo RA)
    supaGet('solicitacoes?ra=eq.' + encodeURIComponent(ra) + '&select=*&order=created_at.desc').then(function(exts) {
      console.log('[aluno] extensões encontradas:', exts);
      // Handle Supabase error object
      if (exts && exts.message) {
        console.error('[aluno] Erro solicitacoes:', exts.message);
        exts = [];
      }
      exts = exts || [];
      var panel = document.getElementById('panel-extensao');
      var container = document.getElementById('extensao-content');

      if (!exts.length) {
        panel.style.display = 'none';
        return;
      }

      panel.style.display = 'block';
      var STATUS_LABELS = {
        aguardando: 'Aguardando',
        desenvolvendo: 'Em Desenvolvimento',
        finalizado: 'Finalizado',
        finalizado_cobrar: 'Finalizado'
      };
      var STATUS_COLORS = {
        aguardando: '#b45309',
        desenvolvendo: '#1d4ed8',
        finalizado: '#15803d',
        finalizado_cobrar: '#6d28d9'
      };
      var STATUS_BG = {
        aguardando: 'rgba(180,83,9,0.1)',
        desenvolvendo: 'rgba(29,78,216,0.1)',
        finalizado: 'rgba(21,128,61,0.1)',
        finalizado_cobrar: 'rgba(109,40,217,0.1)'
      };

      container.innerHTML = exts.map(function(s) {
        var horas = s.horas || 0;
        var validadas = s.horas_validadas || 0;
        var restantes = Math.max(0, horas - validadas);
        var pct = horas > 0 ? Math.round((validadas / horas) * 100) : 0;
        if (pct > 100) pct = 100;
        var statusText = STATUS_LABELS[s.status] || s.status;
        var statusColor = STATUS_COLORS[s.status] || '#666';
        var statusBg = STATUS_BG[s.status] || 'rgba(102,102,102,0.1)';
        var isComplete = pct >= 100;
        var barColor = isComplete ? '#22c55e' : '#f0c030';

        // Extrair tema
        var obs = s.observacoes || '';
        var tema = '';
        if (obs.indexOf('Tema: ') !== -1) {
          var parts = obs.split(' | ');
          for (var p = 0; p < parts.length; p++) {
            if (parts[p].indexOf('Tema: ') === 0) {
              tema = parts[p].replace('Tema: ', '');
              break;
            }
          }
        }

        return '<div class="extensao-card' + (isComplete ? ' complete' : '') + '">' +

          '<div class="extensao-header">' +
            '<span class="extensao-status" style="background:' + statusBg + ';color:' + statusColor + ';">' +
              '<span class="extensao-status-dot" style="background:' + statusColor + ';"></span>' +
              statusText +
            '</span>' +
            '<span class="extensao-date">' + formatDate(s.created_at) + '</span>' +
          '</div>' +

          (tema ? '<div class="extensao-tema">' + escapeHtml(tema) + '</div>' : '') +

          '<div class="extensao-pct-row">' +
            '<span class="extensao-pct-num">' + pct + '%</span>' +
            '<span class="extensao-pct-label">concluído</span>' +
          '</div>' +

          '<div class="extensao-bar-wrap">' +
            '<div class="extensao-bar">' +
              '<div class="extensao-bar-fill" style="width:' + pct + '%;background:' + barColor + ';"></div>' +
            '</div>' +
            '<div class="extensao-bar-info">' +
              '<span>' + validadas + ' de ' + horas + ' horas</span>' +
              '<span>' + restantes + 'h restantes</span>' +
            '</div>' +
          '</div>' +

          '<div class="extensao-metrics">' +
            '<div class="extensao-metric m-contratadas">' +
              '<div class="extensao-metric-num">' + horas + 'h</div>' +
              '<div class="extensao-metric-label">Contratadas</div>' +
            '</div>' +
            '<div class="extensao-metric m-validadas">' +
              '<div class="extensao-metric-num">' + validadas + 'h</div>' +
              '<div class="extensao-metric-label">Validadas</div>' +
            '</div>' +
            '<div class="extensao-metric m-restantes">' +
              '<div class="extensao-metric-num">' + restantes + 'h</div>' +
              '<div class="extensao-metric-label">Restantes</div>' +
            '</div>' +
          '</div>' +

        '</div>';
      }).join('');
    }).catch(function(err) {
      console.error('[aluno] Erro ao carregar extensões:', err);
    });

  }).catch(function() {
    showError('Erro de conexão. Tente novamente.');
  });
}

function showError(msg) {
  loginError.textContent = msg;
  loginError.style.display = 'block';
  btnEntrar.disabled = false;
  btnText.style.display = 'inline';
  btnLoading.style.display = 'none';
}

function formatStatus(s) {
  var m = { pendente: 'Pendente', em_andamento: 'Em Andamento', entregue: 'Entregue', revisao: 'Revisão' };
  return m[s] || s;
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('pt-BR');
}

function escapeHtml(t) {
  var d = document.createElement('div');
  d.textContent = t || '';
  return d.innerHTML;
}
