/* ═══════════════════════════════════════════
   Chat — Mensagens em Tempo Real
   ═══════════════════════════════════════════ */

var currentChannel = 'geral';
var currentUserId = null;
var currentUserName = '';
var realtimeSubscription = null;
var _assessorNamesCache = {};
var _pendingFile = null; // file staged for upload

// ─── Init ───
document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'dono', 'extensao', 'assessoria', 'assessor']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  setupSidebarPermissions(role);
  currentUserId = user.id;
  currentUserName = getUserName(user);
  document.getElementById('user-name').textContent = currentUserName;
  document.getElementById('user-avatar').textContent = currentUserName.charAt(0).toUpperCase();
  document.getElementById('btn-logout').addEventListener('click', handleLogout);

  // Enter key to send
  document.getElementById('chat-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // File input change
  document.getElementById('chat-file-input').addEventListener('change', handleFileSelected);

  // Pre-load assessor names
  await loadAssessorNames();

  await loadMessages(currentChannel);
  subscribeRealtime();
});

// ─── Load Assessor Names Cache ───
async function loadAssessorNames() {
  try {
    var { data } = await sb.from('assessores').select('id, nome');
    if (data) {
      for (var i = 0; i < data.length; i++) {
        _assessorNamesCache[data[i].id] = data[i].nome;
      }
    }
  } catch (e) {
    console.warn('[chat] Erro ao carregar nomes:', e.message);
  }
}

function getSenderName(senderId) {
  if (senderId === currentUserId) return currentUserName;
  return _assessorNamesCache[senderId] || 'Desconhecido';
}

// ─── Load Messages ───
async function loadMessages(channel) {
  var messagesEl = document.getElementById('chat-messages');

  try {
    var { data, error } = await sb
      .from('mensagens')
      .select('*')
      .eq('channel', channel)
      .order('created_at', { ascending: true })
      .limit(100);

    if (error) throw error;

    if (!data || data.length === 0) {
      messagesEl.innerHTML = '<div class="chat-empty">Nenhuma mensagem ainda. Comece a conversa!</div>';
      return;
    }

    renderMessages(data);
  } catch (e) {
    console.error('[chat] Erro ao carregar mensagens:', e);
    messagesEl.innerHTML = '<div class="chat-empty">Erro ao carregar mensagens.</div>';
    showToast('Erro ao carregar mensagens: ' + (e.message || e), 'error');
  }
}

// ─── Render Messages ───
function renderMessages(messages) {
  var messagesEl = document.getElementById('chat-messages');
  var html = '';
  var lastDate = '';

  for (var i = 0; i < messages.length; i++) {
    var msg = messages[i];
    html += buildMessageHTML(msg, lastDate);
    var createdAt = new Date(msg.created_at);
    lastDate = createdAt.toLocaleDateString('pt-BR');
  }

  messagesEl.innerHTML = html;
  scrollToBottom();
}

function buildMessageHTML(msg, lastDate) {
  var isOwn = msg.sender_id === currentUserId;
  var senderName = getSenderName(msg.sender_id);
  var createdAt = new Date(msg.created_at);
  var dateStr = createdAt.toLocaleDateString('pt-BR');
  var timeStr = createdAt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

  var html = '';

  // Date separator
  if (dateStr !== lastDate) {
    html += '<div class="chat-date-separator">' + dateStr + '</div>';
  }

  var bubbleClass = isOwn ? 'chat-bubble own' : 'chat-bubble other';

  html += '<div class="' + bubbleClass + '" data-msg-id="' + msg.id + '">';

  // Delete button (only for own messages)
  if (isOwn) {
    html += '<button class="btn-delete-msg" onclick="deleteMessage(\'' + msg.id + '\')" title="Apagar">✕</button>';
  }

  if (!isOwn) {
    html += '<div class="chat-sender">' + escapeHtml(senderName) + '</div>';
  }

  // Text content
  if (msg.content) {
    html += '<div class="chat-text">' + escapeHtml(msg.content) + '</div>';
  }

  // File attachment
  if (msg.file_url) {
    html += renderFileAttachment(msg.file_url, msg.file_name || 'arquivo');
  }

  html += '<div class="chat-time">' + timeStr + '</div>';
  html += '</div>';

  return html;
}

function renderFileAttachment(url, fileName) {
  var ext = (fileName || '').split('.').pop().toLowerCase();
  var isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].indexOf(ext) !== -1;

  if (isImage) {
    return '<img class="chat-img-attach" src="' + escapeHtml(url) + '" alt="' + escapeHtml(fileName) + '" onclick="window.open(\'' + escapeHtml(url) + '\', \'_blank\')" loading="lazy">';
  }

  var iconMap = { pdf: '📄', doc: '📝', docx: '📝', xls: '📊', xlsx: '📊', zip: '📦', rar: '📦', txt: '📃' };
  var icon = iconMap[ext] || '📎';

  return '<a class="chat-file-attach" href="' + escapeHtml(url) + '" target="_blank" rel="noopener">'
    + '<span class="file-icon">' + icon + '</span>'
    + '<span>' + escapeHtml(fileName) + '</span>'
    + '</a>';
}

// ─── Send Message ───
async function sendMessage() {
  var input = document.getElementById('chat-input');
  var btn = document.getElementById('btn-send');
  var text = input.value.trim();

  // Need at least text or a file
  if (!text && !_pendingFile) return;

  btn.disabled = true;
  input.disabled = true;

  try {
    var fileUrl = null;
    var fileName = null;

    // Upload file if pending
    if (_pendingFile) {
      var uploadResult = await uploadFile(_pendingFile);
      fileUrl = uploadResult.url;
      fileName = uploadResult.name;
      clearFilePreview();
    }

    var record = {
      content: text || '',
      channel: currentChannel,
      sender_id: currentUserId
    };
    if (fileUrl) record.file_url = fileUrl;
    if (fileName) record.file_name = fileName;

    var { error } = await sb.from('mensagens').insert(record);

    if (error) throw error;

    input.value = '';
  } catch (e) {
    console.error('[chat] Erro ao enviar:', e);
    showToast('Erro ao enviar mensagem: ' + (e.message || e), 'error');
  } finally {
    btn.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

// ─── File Upload ───
function handleFileSelected(e) {
  var file = e.target.files[0];
  if (!file) return;

  // Max 10MB
  if (file.size > 10 * 1024 * 1024) {
    showToast('Arquivo muito grande. Máximo 10MB.', 'error');
    e.target.value = '';
    return;
  }

  _pendingFile = file;
  showFilePreview(file);
}

function showFilePreview(file) {
  var preview = document.getElementById('chat-upload-preview');
  var isImage = file.type.startsWith('image/');

  var html = '';
  if (isImage) {
    var url = URL.createObjectURL(file);
    html += '<img src="' + url + '" alt="preview">';
  } else {
    html += '<span style="font-size:1.4rem">📎</span>';
  }
  html += '<span class="upload-name">' + escapeHtml(file.name) + ' (' + formatFileSize(file.size) + ')</span>';
  html += '<button class="upload-cancel" onclick="clearFilePreview()" title="Cancelar">✕</button>';

  preview.innerHTML = html;
  preview.style.display = 'flex';
}

function clearFilePreview() {
  _pendingFile = null;
  var preview = document.getElementById('chat-upload-preview');
  preview.style.display = 'none';
  preview.innerHTML = '';
  document.getElementById('chat-file-input').value = '';
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function uploadFile(file) {
  var ext = file.name.split('.').pop();
  var path = 'chat/' + currentChannel + '/' + Date.now() + '_' + Math.random().toString(36).substring(2, 8) + '.' + ext;

  var { data, error } = await sb.storage
    .from('chat-files')
    .upload(path, file, { cacheControl: '3600', upsert: false });

  if (error) throw new Error('Erro no upload: ' + error.message);

  var { data: urlData } = sb.storage.from('chat-files').getPublicUrl(path);

  return { url: urlData.publicUrl, name: file.name };
}

// ─── Delete Message ───
async function deleteMessage(msgId) {
  if (!confirm('Apagar esta mensagem?')) return;

  try {
    var { error } = await sb.from('mensagens').delete().eq('id', msgId).eq('sender_id', currentUserId);
    if (error) throw error;

    // Remove from DOM
    var bubble = document.querySelector('[data-msg-id="' + msgId + '"]');
    if (bubble) {
      bubble.style.opacity = '0';
      bubble.style.transform = 'scale(0.8)';
      bubble.style.transition = 'all 0.2s ease';
      setTimeout(function () { bubble.remove(); }, 200);
    }

    showToast('Mensagem apagada', 'success');
  } catch (e) {
    console.error('[chat] Erro ao apagar:', e);
    showToast('Erro ao apagar: ' + (e.message || e), 'error');
  }
}

// ─── Switch Channel ───
function switchChannel(channel) {
  if (channel === currentChannel) return;
  currentChannel = channel;

  // Update tab UI
  var tabs = document.querySelectorAll('.chat-tab');
  for (var i = 0; i < tabs.length; i++) {
    if (tabs[i].getAttribute('data-channel') === channel) {
      tabs[i].classList.add('active');
    } else {
      tabs[i].classList.remove('active');
    }
  }

  // Clear pending file
  clearFilePreview();

  // Clear and reload
  document.getElementById('chat-messages').innerHTML = '<div class="chat-empty">Carregando mensagens...</div>';

  // Unsubscribe old and resubscribe
  if (realtimeSubscription) {
    sb.removeChannel(realtimeSubscription);
    realtimeSubscription = null;
  }

  loadMessages(channel);
  subscribeRealtime();
}

// ─── Subscribe Realtime ───
function subscribeRealtime() {
  if (realtimeSubscription) {
    sb.removeChannel(realtimeSubscription);
    realtimeSubscription = null;
  }

  try {
    realtimeSubscription = sb
      .channel('chat-' + currentChannel)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'mensagens',
        filter: 'channel=eq.' + currentChannel
      }, function (payload) {
        handleNewMessage(payload.new);
      })
      .on('postgres_changes', {
        event: 'DELETE',
        schema: 'public',
        table: 'mensagens'
      }, function (payload) {
        handleDeletedMessage(payload.old);
      })
      .subscribe();
  } catch (e) {
    console.warn('[chat] Realtime subscription error:', e.message);
  }
}

// ─── Handle New Message from Realtime ───
function handleNewMessage(msg) {
  var senderName = getSenderName(msg.sender_id);

  if (!_assessorNamesCache[msg.sender_id] && msg.sender_id !== currentUserId) {
    sb.from('assessores').select('nome').eq('id', msg.sender_id).single().then(function (res) {
      if (res.data && res.data.nome) {
        _assessorNamesCache[msg.sender_id] = res.data.nome;
        var bubble = document.querySelector('[data-msg-id="' + msg.id + '"]');
        if (bubble) {
          var senderEl = bubble.querySelector('.chat-sender');
          if (senderEl) senderEl.textContent = res.data.nome;
        }
      }
    }).catch(function () {});
  }

  var messagesEl = document.getElementById('chat-messages');

  // Remove empty state if present
  var emptyEl = messagesEl.querySelector('.chat-empty');
  if (emptyEl) emptyEl.remove();

  // Get last date for separator check
  var lastSeparator = messagesEl.querySelector('.chat-date-separator:last-of-type');
  var lastDateText = lastSeparator ? lastSeparator.textContent : '';

  var tempDiv = document.createElement('div');
  tempDiv.innerHTML = buildMessageHTML(msg, lastDateText);

  while (tempDiv.firstChild) {
    messagesEl.appendChild(tempDiv.firstChild);
  }

  scrollToBottom();
}

// ─── Handle Deleted Message from Realtime ───
function handleDeletedMessage(msg) {
  if (!msg || !msg.id) return;
  var bubble = document.querySelector('[data-msg-id="' + msg.id + '"]');
  if (bubble) {
    bubble.style.opacity = '0';
    bubble.style.transform = 'scale(0.8)';
    bubble.style.transition = 'all 0.2s ease';
    setTimeout(function () { bubble.remove(); }, 200);
  }
}

// ─── Scroll to Bottom ───
function scrollToBottom() {
  var messagesEl = document.getElementById('chat-messages');
  messagesEl.scrollTop = messagesEl.scrollHeight;
}
