/* ═══════════════════════════════════════════════════════════════
   Google Apps Script — API para Extensões

   INSTRUÇÕES DE DEPLOY:
   1. Acesse https://script.google.com
   2. Crie um novo projeto (+ Novo Projeto)
   3. Apague o conteúdo padrão e cole TODO este código
   4. Clique em "Implantar" → "Nova implantação"
   5. Tipo: "App da Web"
   6. "Executar como": sua conta
   7. "Quem pode acessar": "Qualquer pessoa"
   8. Clique em "Implantar"
   9. Autorize quando solicitado
   10. Copie a URL gerada e cole no campo do painel (extensoes.html)

   IMPORTANTE: Sempre que alterar o código, faça uma NOVA implantação
   (Implantar → Gerenciar implantações → Nova versão)
   ═══════════════════════════════════════════════════════════════ */

var SHEET_ID = '1yeFlBBZSMHqTziM7QBB3IVkMJQgXqTbvDEz9SvXXKDw';
var SHEET_NAME = 'extensões'; // Nome da aba principal
var DATA_START_ROW = 9;    // Linha onde começam os dados dos alunos

// Mapeamento de colunas (A=1, B=2, ...)
var COL = {
  status_pgto: 1,        // A
  urgencia: 2,           // B
  nome: 3,               // C
  ra: 4,                 // D
  // col E = vazio (5)
  senha: 6,              // F
  assessor: 7,           // G
  horas_contratadas: 8,  // H
  horas_feitas: 9,       // I
  horas_restantes: 10,   // J
  valor_hora: 11,        // K
  valor_pago: 12,        // L
  valor_restante: 13,    // M
  tipo_pgto: 14,         // N
  data_inicio: 15,       // O
  ultima_atualizacao: 16,// P
  dias: 17,              // Q
  sistema: 18            // R
};

// ── GET: Ler dados ──
function doGet(e) {
  var action = (e && e.parameter && e.parameter.action) || 'list';
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME);

  if (!sheet) {
    // Se não encontrar pelo nome, pega a primeira aba
    sheet = ss.getSheets()[0];
  }

  var result;

  if (action === 'list') {
    result = getAlunos(sheet);
  } else if (action === 'stats') {
    result = getStats(sheet);
  } else {
    result = { error: 'Ação inválida' };
  }

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// ── POST: Criar/Editar/Remover ──
function doPost(e) {
  var body;
  try {
    body = JSON.parse(e.postData.contents);
  } catch (err) {
    return jsonResponse({ success: false, error: 'JSON inválido' });
  }

  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.getSheets()[0];

  var action = body.action;
  var result;

  try {
    if (action === 'update') {
      result = updateRow(sheet, body.rowIndex, body.data);
    } else if (action === 'add') {
      result = addRow(sheet, body.data);
    } else if (action === 'delete') {
      result = deleteRow(sheet, body.rowIndex);
    } else {
      result = { success: false, error: 'Ação inválida: ' + action };
    }
  } catch (err) {
    result = { success: false, error: err.toString() };
  }

  return jsonResponse(result);
}

// ── Listar alunos ──
function getAlunos(sheet) {
  var lastRow = sheet.getLastRow();
  if (lastRow < DATA_START_ROW) return { data: [] };

  var range = sheet.getRange(DATA_START_ROW, 1, lastRow - DATA_START_ROW + 1, 18);
  var values = range.getValues();
  var data = [];

  for (var i = 0; i < values.length; i++) {
    var row = values[i];
    // Pula linhas vazias (sem nome)
    if (!row[COL.nome - 1] || String(row[COL.nome - 1]).trim() === '') continue;

    data.push({
      _rowIndex: DATA_START_ROW + i, // índice real na planilha
      status_pgto: String(row[COL.status_pgto - 1] || ''),
      urgencia: String(row[COL.urgencia - 1] || ''),
      nome: String(row[COL.nome - 1] || ''),
      ra: String(row[COL.ra - 1] || ''),
      senha: String(row[COL.senha - 1] || ''),
      assessor: String(row[COL.assessor - 1] || ''),
      horas_contratadas: String(row[COL.horas_contratadas - 1] || ''),
      horas_feitas: String(row[COL.horas_feitas - 1] || ''),
      horas_restantes: String(row[COL.horas_restantes - 1] || ''),
      valor_hora: String(row[COL.valor_hora - 1] || ''),
      valor_pago: String(row[COL.valor_pago - 1] || ''),
      valor_restante: String(row[COL.valor_restante - 1] || ''),
      tipo_pgto: String(row[COL.tipo_pgto - 1] || ''),
      data_inicio: String(row[COL.data_inicio - 1] || ''),
      ultima_atualizacao: String(row[COL.ultima_atualizacao - 1] || ''),
      dias: String(row[COL.dias - 1] || ''),
      sistema: String(row[COL.sistema - 1] || '')
    });
  }

  return { data: data };
}

// ── Stats (linhas 2-7) ──
function getStats(sheet) {
  var range = sheet.getRange(2, 1, 6, 18);
  var values = range.getValues();
  return {
    labels_row2: values[0],
    counts_row3: values[1],
    labels_row4: values[2],
    counts_row5: values[3],
    labels_row6: values[4],
    counts_row7: values[5]
  };
}

// ── Atualizar linha ──
function updateRow(sheet, rowIndex, data) {
  if (!rowIndex || rowIndex < DATA_START_ROW) {
    return { success: false, error: 'Índice inválido' };
  }

  var fields = ['status_pgto', 'urgencia', 'nome', 'ra', 'senha', 'assessor',
    'horas_contratadas', 'horas_feitas', 'horas_restantes', 'valor_hora',
    'valor_pago', 'valor_restante', 'tipo_pgto', 'data_inicio', 'sistema'];

  for (var i = 0; i < fields.length; i++) {
    var field = fields[i];
    if (data[field] !== undefined && COL[field]) {
      sheet.getRange(rowIndex, COL[field]).setValue(data[field]);
    }
  }

  // Atualiza "Última atualização" automaticamente
  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd/MM/yyyy');
  sheet.getRange(rowIndex, COL.ultima_atualizacao).setValue(today);

  return { success: true };
}

// ── Adicionar nova linha ──
function addRow(sheet, data) {
  var lastRow = sheet.getLastRow();
  var newRow = lastRow + 1;

  var fields = ['status_pgto', 'urgencia', 'nome', 'ra', 'senha', 'assessor',
    'horas_contratadas', 'horas_feitas', 'horas_restantes', 'valor_hora',
    'valor_pago', 'valor_restante', 'tipo_pgto', 'data_inicio', 'sistema'];

  for (var i = 0; i < fields.length; i++) {
    var field = fields[i];
    if (data[field] && COL[field]) {
      sheet.getRange(newRow, COL[field]).setValue(data[field]);
    }
  }

  // Seta data de criação
  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd/MM/yyyy');
  sheet.getRange(newRow, COL.ultima_atualizacao).setValue(today);

  return { success: true, rowIndex: newRow };
}

// ── Remover linha ──
function deleteRow(sheet, rowIndex) {
  if (!rowIndex || rowIndex < DATA_START_ROW) {
    return { success: false, error: 'Índice inválido' };
  }
  sheet.deleteRow(rowIndex);
  return { success: true };
}

// ── Helper ──
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
