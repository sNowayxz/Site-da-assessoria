/* ═══════════════════════════════════════════
   Pedido de Extensão — Formulário + Pagamento
   ═══════════════════════════════════════════ */

var SUPABASE_URL = 'https://lztfoprapoyicldunhzw.supabase.co';
var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6dGZvcHJhcG95aWNsZHVuaHp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMzY0MzIsImV4cCI6MjA4ODkxMjQzMn0.8Qyq2bVA0oK8gji9hG2AWG-gQ3oH4nWm3QOqQ59S9IA';
var sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

function calcularPreco(horas) {
  if (horas <= 0) return 0;
  if (horas < 30) return horas * 4.00;
  if (horas <= 169) return horas * 3.50;
  return horas * 3.00;
}

function getFaixaTexto(horas) {
  if (horas < 30) return horas + 'h x R$ 4,00';
  if (horas <= 169) return horas + 'h x R$ 3,50';
  return horas + 'h x R$ 3,00';
}

function formatCurrency(val) {
  return 'R$ ' + val.toFixed(2).replace('.', ',');
}

// Atualizar preço em tempo real
document.getElementById('carga_horaria').addEventListener('input', function () {
  var horas = parseInt(this.value) || 0;
  var priceEl = document.getElementById('price-amount');
  var detailEl = document.getElementById('price-detail');

  if (horas > 0) {
    var valor = calcularPreco(horas);
    priceEl.textContent = formatCurrency(valor);
    priceEl.classList.remove('empty');
    detailEl.textContent = getFaixaTexto(horas);
  } else {
    priceEl.textContent = 'Digite as horas';
    priceEl.classList.add('empty');
    detailEl.textContent = '';
  }
});

// Submit form
document.getElementById('form-pedido').addEventListener('submit', async function (e) {
  e.preventDefault();
  var btn = document.getElementById('btn-submit');
  var errorEl = document.getElementById('error-msg');
  errorEl.classList.remove('show');

  var nome = document.getElementById('nome').value.trim();
  var email = document.getElementById('email').value.trim();
  var telefone = document.getElementById('telefone').value.trim();
  var ra = document.getElementById('ra').value.trim();
  var curso = document.getElementById('curso').value.trim();
  var ch = parseInt(document.getElementById('carga_horaria').value) || 0;
  var prazo = document.getElementById('prazo').value || null;
  var tema = document.getElementById('tema').value.trim();
  var observacoes = document.getElementById('observacoes').value.trim();

  // Validação
  if (!nome || !email || !curso || !ch || !tema) {
    errorEl.textContent = 'Preencha todos os campos obrigatórios (*)';
    errorEl.classList.add('show');
    return;
  }

  if (ch < 1 || ch > 1000) {
    errorEl.textContent = 'Carga horária deve ser entre 1 e 1000 horas';
    errorEl.classList.add('show');
    return;
  }

  var valor = calcularPreco(ch);

  btn.disabled = true;
  btn.textContent = 'Processando...';

  try {
    // 1. Inserir pedido no Supabase
    var { data, error } = await sb.from('pedidos_extensao').insert({
      nome_cliente: nome,
      email: email,
      telefone: telefone,
      ra: ra,
      curso: curso,
      carga_horaria: ch,
      tema: tema,
      prazo: prazo,
      observacoes: observacoes,
      valor: valor,
      status: 'aguardando_pagamento',
    }).select().single();

    if (error) throw new Error(error.message);

    // 2. Criar preferência Mercado Pago
    var resp = await fetch('/api/create-preference', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pedido_id: data.id,
        nome: nome,
        email: email,
        curso: curso,
        carga_horaria: ch,
        tema: tema,
        valor: valor,
      }),
    });

    var mpResult = await resp.json();

    if (!resp.ok || !mpResult.init_point) {
      // Se MP falhar, redirecionar para status com instruções
      window.location.href = 'status.html?pedido=' + data.id + '&mp=erro';
      return;
    }

    // 3. Redirecionar para Mercado Pago
    window.location.href = mpResult.init_point;

  } catch (err) {
    errorEl.textContent = 'Erro: ' + err.message;
    errorEl.classList.add('show');
    btn.disabled = false;
    btn.textContent = 'Prosseguir para Pagamento';
  }
});
