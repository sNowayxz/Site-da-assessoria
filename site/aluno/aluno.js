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
        aguardando: '#d97706',
        desenvolvendo: '#2563eb',
        finalizado: '#16a34a',
        finalizado_cobrar: '#7c3aed'
      };
      var STATUS_BG = {
        aguardando: 'rgba(217,119,6,0.15)',
        desenvolvendo: 'rgba(37,99,235,0.15)',
        finalizado: 'rgba(22,163,106,0.15)',
        finalizado_cobrar: 'rgba(124,58,237,0.15)'
      };

      container.innerHTML = exts.map(function(s) {
        var horas = s.horas || 0;
        var validadas = s.horas_validadas || 0;
        var restantes = Math.max(0, horas - validadas);
        var evolucao = horas > 0 ? Math.round((validadas / horas) * 100) : 0;
        if (evolucao > 100) evolucao = 100;
        var statusText = STATUS_LABELS[s.status] || s.status;
        var statusColor = STATUS_COLORS[s.status] || '#888';
        var statusBg = STATUS_BG[s.status] || 'rgba(136,136,136,0.15)';
        var isComplete = evolucao >= 100;
        var barGradient = isComplete
          ? 'linear-gradient(90deg, #16a34a, #34d399)'
          : 'linear-gradient(90deg, #f0c030, #f5d45a)';

        // Extract tema from observacoes
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

        // SVG circular progress
        var radius = 36;
        var circumference = 2 * Math.PI * radius;
        var offset = circumference - (evolucao / 100) * circumference;

        return '<div class="extensao-card' + (isComplete ? ' complete' : '') + '">' +

          // ── Dark top banner ──
          '<div class="extensao-top">' +
            '<div class="extensao-top-row">' +
              '<span class="extensao-status" style="background:' + statusBg + ';color:' + statusColor + ';">' + statusText + '</span>' +
              '<span class="extensao-date">' + formatDate(s.created_at) + '</span>' +
            '</div>' +
            (tema ? '<div class="extensao-tema">' + escapeHtml(tema) + '</div>' : '') +
          '</div>' +

          // ── Progress section: circle + bar ──
          '<div class="extensao-progress-section">' +
            '<div class="extensao-circle-wrap">' +
              '<svg viewBox="0 0 90 90">' +
                '<circle class="extensao-circle-bg" cx="45" cy="45" r="' + radius + '"/>' +
                '<circle class="extensao-circle-fg" cx="45" cy="45" r="' + radius + '" ' +
                  'stroke-dasharray="' + circumference + '" ' +
                  'stroke-dashoffset="' + offset + '"/>' +
              '</svg>' +
              '<div class="extensao-circle-text">' +
                '<span class="extensao-circle-pct">' + evolucao + '%</span>' +
                '<span class="extensao-circle-label">Progresso</span>' +
              '</div>' +
            '</div>' +
            '<div class="extensao-bar-section">' +
              '<div class="extensao-bar-label">Horas Completadas</div>' +
              '<div class="extensao-bar">' +
                '<div class="extensao-bar-fill" style="width:' + evolucao + '%;background:' + barGradient + ';"></div>' +
              '</div>' +
              '<div class="extensao-bar-numbers">' +
                '<span>' + validadas + 'h validadas</span>' +
                '<span>' + horas + 'h total</span>' +
              '</div>' +
            '</div>' +
          '</div>' +

          // ── Bottom metrics ──
          '<div class="extensao-details">' +
            '<div class="extensao-detail contracted">' +
              '<div class="extensao-detail-icon">📋</div>' +
              '<strong>' + horas + 'h</strong>' +
              '<small>Contratadas</small>' +
            '</div>' +
            '<div class="extensao-detail validated">' +
              '<div class="extensao-detail-icon">✅</div>' +
              '<strong>' + validadas + 'h</strong>' +
              '<small>Validadas</small>' +
            '</div>' +
            '<div class="extensao-detail remaining">' +
              '<div class="extensao-detail-icon">⏳</div>' +
              '<strong>' + restantes + 'h</strong>' +
              '<small>Restantes</small>' +
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
