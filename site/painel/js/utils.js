/* ═══════════════════════════════════════════
   Utils — Dark Mode, Toasts, PDF Export
   ═══════════════════════════════════════════ */

// ─── Dark Mode ───
(function initTheme() {
  var saved = localStorage.getItem('painel-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme');
  var next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('painel-theme', next);
  // Atualiza ícone do botão
  var btn = document.getElementById('btn-theme');
  if (btn) btn.textContent = next === 'dark' ? '☀️' : '🌙';
}

// Atualiza ícone ao carregar
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('btn-theme');
  if (btn) {
    var theme = document.documentElement.getAttribute('data-theme');
    btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    btn.addEventListener('click', toggleTheme);
  }
});


// ─── Toast Notifications ───
function ensureToastContainer() {
  var container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

function showToast(message, type) {
  type = type || 'info';
  var container = ensureToastContainer();
  var icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  var toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
  toast.innerHTML = '<span class="toast-icon">' + (icons[type] || 'ℹ️') + '</span><span>' + message + '</span>';
  container.appendChild(toast);
  setTimeout(function () {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 5000);
}


// ─── PDF Export (usando jsPDF) ───
function loadJsPDF(callback) {
  if (window.jspdf) { callback(); return; }
  var s = document.createElement('script');
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.2/jspdf.umd.min.js';
  s.onload = function () {
    var s2 = document.createElement('script');
    s2.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.4/jspdf.plugin.autotable.min.js';
    s2.onload = callback;
    document.head.appendChild(s2);
  };
  document.head.appendChild(s);
}

function exportTableToPDF(tableId, title, filename) {
  loadJsPDF(function () {
    var jsPDF = window.jspdf.jsPDF;
    var doc = new jsPDF('l', 'mm', 'a4');

    // Header
    doc.setFontSize(18);
    doc.setTextColor(26, 26, 46);
    doc.text(title || 'Relatório', 14, 20);

    doc.setFontSize(10);
    doc.setTextColor(136, 146, 164);
    doc.text('Assessoria Acadêmica — Gerado em ' + new Date().toLocaleDateString('pt-BR') + ' às ' + new Date().toLocaleTimeString('pt-BR'), 14, 28);

    // Tabela
    var table = document.querySelector('#' + tableId);
    if (!table) {
      // Tenta pegar do tbody
      table = document.querySelector('#' + tableId)?.closest('table');
    }

    // Se passou o ID do tbody, pega a table pai
    var tableEl = table;
    if (table && table.tagName === 'TBODY') {
      tableEl = table.closest('table');
    }
    if (!tableEl) {
      // Tenta qualquer tabela visível
      tableEl = document.querySelector('.table-wrap table');
    }

    if (tableEl) {
      doc.autoTable({
        html: tableEl,
        startY: 34,
        styles: {
          fontSize: 8,
          cellPadding: 3,
          lineColor: [200, 200, 200],
          lineWidth: 0.1,
        },
        headStyles: {
          fillColor: [26, 26, 46],
          textColor: [240, 192, 48],
          fontStyle: 'bold',
          fontSize: 8,
        },
        alternateRowStyles: {
          fillColor: [248, 249, 252],
        },
        // Remove a última coluna (Ações)
        columnStyles: {},
        didParseCell: function (data) {
          // Se a coluna header é "Ações", esconde
          if (data.column.index === data.table.columns.length - 1) {
            var headerText = '';
            try {
              headerText = data.table.columns[data.column.index].raw?.textContent || '';
            } catch (e) {}
            if (headerText.includes('Aç') || headerText.includes('Acoes')) {
              data.cell.styles.cellWidth = 0;
              data.cell.text = [];
            }
          }
        },
      });
    }

    // Footer
    var pageCount = doc.internal.getNumberOfPages();
    for (var i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text('Página ' + i + ' de ' + pageCount, doc.internal.pageSize.getWidth() - 30, doc.internal.pageSize.getHeight() - 10);
    }

    doc.save((filename || 'relatorio') + '.pdf');
    showToast('PDF exportado com sucesso!', 'success');
  });
}


// ─── CSV Export ───
function exportTableToCSV(tableId, filename) {
  var table = document.querySelector('#' + tableId);
  if (!table) table = document.querySelector('.table-wrap table');
  if (!table) { showToast('Nenhuma tabela encontrada', 'error'); return; }

  var rows = table.querySelectorAll('tr');
  var csv = [];

  rows.forEach(function (row) {
    var cols = row.querySelectorAll('th, td');
    var rowData = [];
    cols.forEach(function (col, idx) {
      // Ignora última coluna (Ações)
      if (idx === cols.length - 1 && col.classList.contains('actions')) return;
      var text = col.textContent.trim().replace(/"/g, '""');
      rowData.push('"' + text + '"');
    });
    csv.push(rowData.join(','));
  });

  var blob = new Blob(['\ufeff' + csv.join('\n')], { type: 'text/csv;charset=utf-8;' });
  var link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = (filename || 'relatorio') + '.csv';
  link.click();
  showToast('CSV exportado com sucesso!', 'success');
}


// ─── Supabase Realtime (notificações) ───
function subscribeToChanges(table, onInsert, onUpdate) {
  if (!window.sb) return;
  try {
    sb.channel('realtime-' + table)
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: table }, function (payload) {
        if (onInsert) onInsert(payload.new);
        showToast('Novo registro em ' + table, 'info');
      })
      .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: table }, function (payload) {
        if (onUpdate) onUpdate(payload.new);
      })
      .subscribe();
  } catch (e) {
    console.warn('[realtime] Não foi possível assinar:', e.message);
  }
}
