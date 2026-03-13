/* ═══════════════════════════════════════════
   Status do Pedido — Consulta
   ═══════════════════════════════════════════ */

var SUPABASE_URL = 'https://lztfoprapoyicldunhzw.supabase.co';
var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6dGZvcHJhcG95aWNsZHVuaHp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMzY0MzIsImV4cCI6MjA4ODkxMjQzMn0.8Qyq2bVA0oK8gji9hG2AWG-gQ3oH4nWm3QOqQ59S9IA';
var sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

var STATUS_LABELS = {
  aguardando_pagamento: 'Aguardando Pagamento',
  pago: 'Pago',
  em_andamento: 'Em Andamento',
  concluido: 'Concluído',
  cancelado: 'Cancelado',
};

// Verificar se veio pedido_id na URL (redirect do MP)
document.addEventListener('DOMContentLoaded', function () {
  var params = new URLSearchParams(window.location.search);
  var pedidoId = params.get('pedido');

  if (pedidoId) {
    loadPedidoById(pedidoId);
  }
});

async function loadPedidoById(id) {
  var container = document.getElementById('results');
  container.innerHTML = '<div class="empty">Carregando...</div>';

  var { data, error } = await sb.from('pedidos_extensao')
    .select('*')
    .eq('id', id)
    .single();

  if (error || !data) {
    container.innerHTML = '<div class="empty">Pedido não encontrado.</div>';
    return;
  }

  // Preencher email no campo de busca
  document.getElementById('search-email').value = data.email;

  renderPedidos([data]);
}

async function searchByEmail() {
  var email = document.getElementById('search-email').value.trim();
  if (!email) { alert('Informe seu e-mail.'); return; }

  var container = document.getElementById('results');
  container.innerHTML = '<div class="empty">Buscando...</div>';

  var { data, error } = await sb.from('pedidos_extensao')
    .select('*')
    .eq('email', email)
    .order('created_at', { ascending: false });

  if (error) {
    container.innerHTML = '<div class="empty">Erro na busca: ' + error.message + '</div>';
    return;
  }

  if (!data || !data.length) {
    container.innerHTML = '<div class="empty">Nenhum pedido encontrado para este e-mail.</div>';
    return;
  }

  renderPedidos(data);
}

function renderPedidos(pedidos) {
  var container = document.getElementById('results');
  var html = '';

  pedidos.forEach(function (p) {
    var statusLabel = STATUS_LABELS[p.status] || p.status;
    var valor = p.valor ? 'R$ ' + parseFloat(p.valor).toFixed(2).replace('.', ',') : '—';
    var data = new Date(p.created_at).toLocaleDateString('pt-BR');
    var prazo = p.prazo ? new Date(p.prazo + 'T00:00:00').toLocaleDateString('pt-BR') : '—';

    html += '<div class="status-card ' + p.status + '">'
      + '<div class="status-header">'
      + '<h3>' + escapeHtml(p.curso) + ' — ' + p.carga_horaria + 'h</h3>'
      + '<span class="badge badge-' + p.status + '">' + statusLabel + '</span>'
      + '</div>'
      + '<div class="detail-row"><span class="detail-label">Tema</span><span class="detail-value">' + escapeHtml(p.tema) + '</span></div>'
      + '<div class="detail-row"><span class="detail-label">Valor</span><span class="detail-value">' + valor + '</span></div>'
      + '<div class="detail-row"><span class="detail-label">Prazo</span><span class="detail-value">' + prazo + '</span></div>'
      + '<div class="detail-row"><span class="detail-label">Pedido em</span><span class="detail-value">' + data + '</span></div>'
      + '<div class="detail-row"><span class="detail-label">ID</span><span class="detail-value" style="font-size:0.78rem;font-family:monospace;">' + p.id.substring(0, 8) + '...</span></div>'
      + '</div>';
  });

  container.innerHTML = html;
}

function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
