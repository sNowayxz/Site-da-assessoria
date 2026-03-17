/* ═══════════════════════════════════════════
   API: Exportar dados para Google Sheets
   ═══════════════════════════════════════════
   POST /api/export-sheets
   Body: { tabela: 'alunos'|'atividades'|'pagamentos', formato?: 'csv' }

   Retorna CSV para importação manual no Google Sheets
   ou usa Google Sheets API (se configurada via env vars).
   ═══════════════════════════════════════════ */

const { createClient } = require('@supabase/supabase-js');

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { tabela, auth_token } = req.body || {};

    if (!tabela) return res.status(400).json({ error: 'tabela é obrigatório' });

    const allowed = ['alunos', 'atividades', 'pagamentos', 'pedidos_extensao'];
    if (!allowed.includes(tabela)) return res.status(400).json({ error: 'Tabela inválida' });

    // Usa service key se disponível, senão usa token do user
    const supabaseKey = process.env.SUPABASE_SERVICE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6dGZvcHJhcG95aWNsZHVuaHp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzMzY0MzIsImV4cCI6MjA4ODkxMjQzMn0.8Qyq2bVA0oK8gji9hG2AWG-gQ3oH4nWm3QOqQ59S9IA';
    const supabase = createClient(
      process.env.SUPABASE_URL || 'https://lztfoprapoyicldunhzw.supabase.co',
      supabaseKey
    );

    // If auth_token provided, verify user is authenticated
    if (auth_token) {
      const { data: { user }, error } = await supabase.auth.getUser(auth_token);
      if (error || !user) return res.status(401).json({ error: 'Não autorizado' });
    }

    // Fetch data
    let query;
    const columns = {
      alunos: 'ra, nome, curso, tipo, telefone, email, situacao, created_at',
      atividades: 'tipo, descricao, status, valor, observacoes, prioridade, dt_entrega, created_at, alunos(nome, ra)',
      pagamentos: 'valor, tipo, status, referencia, dt_vencimento, dt_pagamento, created_at, alunos(nome, ra)',
      pedidos_extensao: 'nome_cliente, email, telefone, ra, curso, carga_horaria, tema, valor, status, created_at'
    };

    const { data, error } = await supabase.from(tabela).select(columns[tabela]).order('created_at', { ascending: false });
    if (error) return res.status(500).json({ error: error.message });

    // Convert to CSV
    if (!data || !data.length) {
      return res.status(200).json({ csv: '', message: 'Sem dados para exportar', rows: 0 });
    }

    // Flatten nested objects
    const flat = data.map(function(row) {
      const obj = {};
      Object.keys(row).forEach(function(key) {
        if (row[key] && typeof row[key] === 'object' && !Array.isArray(row[key])) {
          Object.keys(row[key]).forEach(function(subKey) {
            obj[key + '_' + subKey] = row[key][subKey];
          });
        } else {
          obj[key] = row[key];
        }
      });
      return obj;
    });

    const headers = Object.keys(flat[0]);
    const csvRows = [headers.join(',')];
    flat.forEach(function(row) {
      csvRows.push(headers.map(function(h) {
        var val = row[h];
        if (val === null || val === undefined) val = '';
        val = String(val).replace(/"/g, '""');
        return '"' + val + '"';
      }).join(','));
    });

    const csv = '\ufeff' + csvRows.join('\n'); // BOM for Excel UTF-8

    // If Google Sheets API is configured, push there too
    if (process.env.GOOGLE_SHEETS_ID && process.env.GOOGLE_SERVICE_KEY) {
      // TODO: Implement Google Sheets API push
      // For now, return CSV for manual import
    }

    res.setHeader('Content-Type', 'text/csv; charset=utf-8');
    res.setHeader('Content-Disposition', 'attachment; filename=' + tabela + '_export.csv');
    return res.status(200).send(csv);

  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
