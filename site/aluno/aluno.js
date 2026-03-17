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
