/* ═══════════════════════════════════════════
   Chat — Mensagens Privadas + Canais
   v2: DM extensão↔assessorias
   ═══════════════════════════════════════════ */

var currentChannel = 'geral';
var currentUserId = null;
var currentUserName = '';
var currentRole = null;
var realtimeSubscription = null;
var _assessorNamesCache = {};
var _assessorAvatarsCache = {};
var _pendingFile = null;
var _extensaoUserId = null; // ID do usuário extensão (Gessica)
var _contactsList = []; // Lista de contatos para extensão

// ─── Init ───
document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'dono', 'extensao', 'assessoria', 'assessor']);
  if (!result) return;
  var user = result.user;
  var role = result.role;
  currentRole = role;
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

  // Pre-load assessor names + avatars
  await loadAssessorNames();

  // Setup chat mode based on role
  if (role === 'extensao') {
    await setupExtensaoChat();
  } else if (role === 'assessoria') {
    await setupAssessoriaChat();
  } else {
    // admin/dono: show channel tabs (geral, urgente) + DMs
    setupAdminChat();
  }
});

// ─── Load Assessor Names Cache ───
async function loadAssessorNames() {
  try {
    var { data } = await sb.from('assessores').select('id, nome, label, role, avatar_url');
    if (data) {
      for (var i = 0; i < data.length; i++) {
        _assessorNamesCache[data[i].id] = data[i].nome || data[i].label || 'Sem nome';
        _assessorAvatarsCache[data[i].id] = data[i].avatar_url || '';
        if (data[i].role === 'extensao') {
          _extensaoUserId = data[i].id;
        }
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

// ─── DM Channel name (sorted IDs for consistency) ───
function dmChannel(id1, id2) {
  return id1 < id2 ? 'dm-' + id1 + '-' + id2 : 'dm-' + id2 + '-' + id1;
}

// ═══════════════════════════════════════════
// Extensão: vê lista de assessorias à esquerda
// ═══════════════════════════════════════════
async function setupExtensaoChat() {
  // Get all assessorias
  var { data: assessorias } = await sb.from('assessores')
    .select('id, nome, label, avatar_url')
    .eq('role', 'assessoria')
    .order('nome');

  _contactsList = assessorias || [];

  // Build contacts panel
  var tabsEl = document.getElementById('chat-tabs-area');
  tabsEl.innerHTML = '';
  tabsEl.className = 'chat-contacts-panel';

  var headerHtml = '<div class="contacts-header">💬 Conversas</div>';
  var listHtml = '<div class="contacts-list" id="contacts-list">';

  for (var i = 0; i < _contactsList.length; i++) {
    var c = _contactsList[i];
    var initial = (c.nome || 'A').charAt(0).toUpperCase();
    var avatarHtml = c.avatar_url
      ? '<img src="' + escapeHtml(c.avatar_url) + '" alt="" class="contact-avatar-img">'
      : '<span class="contact-avatar-letter">' + initial + '</span>';

    listHtml += '<div class="contact-item" data-contact-id="' + c.id + '" onclick="openDM(\'' + c.id + '\')">'
      + '<div class="contact-avatar">' + avatarHtml + '</div>'
      + '<div class="contact-info">'
      + '<div class="contact-name">' + escapeHtml(c.label || c.nome) + '</div>'
      + '<div class="contact-last" id="last-' + c.id + '">...</div>'
      + '</div>'
      + '<span class="contact-unread" id="unread-' + c.id + '" style="display:none;">0</span>'
      + '</div>';
  }
  listHtml += '</div>';
  tabsEl.innerHTML = headerHtml + listHtml;

  // Update topbar title
  var topbarH1 = document.querySelector('.topbar h1');
  if (topbarH1) topbarH1.textContent = 'Chat — Extensão';

  // Load last messages for preview
  loadContactPreviews();

  // Select first contact by default
  if (_contactsList.length > 0) {
    openDM(_contactsList[0].id);
  } else {
    document.getElementById('chat-messages').innerHTML = '<div class="chat-empty">Nenhuma assessoria cadastrada.</div>';
  }
}

async function loadContactPreviews() {
  for (var i = 0; i < _contactsList.length; i++) {
    var c = _contactsList[i];
    var ch = dmChannel(currentUserId, c.id);
    try {
      var { data } = await sb.from('mensagens')
        .select('content, created_at')
        .eq('channel', ch)
        .order('created_at', { ascending: false })
        .limit(1);
      var el = document.getElementById('last-' + c.id);
      if (el && data && data[0]) {
        var txt = data[0].content || '📎 Arquivo';
        el.textContent = txt.length > 30 ? txt.substring(0, 30) + '...' : txt;
      } else if (el) {
        el.textContent = 'Nenhuma mensagem';
      }
    } catch (e) {}
  }
}

// ═══════════════════════════════════════════
// Assessoria: vê apenas chat com Gessica
// ═══════════════════════════════════════════
async function setupAssessoriaChat() {
  var tabsEl = document.getElementById('chat-tabs-area');
  tabsEl.innerHTML = '';
  tabsEl.className = '';

  if (!_extensaoUserId) {
    document.getElementById('chat-messages').innerHTML = '<div class="chat-empty">Nenhum responsável de extensão encontrado.</div>';
    return;
  }

  // Show who they're chatting with
  var extName = _assessorNamesCache[_extensaoUserId] || 'Extensão';
  var topbarH1 = document.querySelector('.topbar h1');
  if (topbarH1) topbarH1.textContent = 'Chat com ' + extName;

  // Auto-open DM with extensão
  currentChannel = dmChannel(currentUserId, _extensaoUserId);
  await loadMessages(currentChannel);
  subscribeRealtime();
}

// ═══════════════════════════════════════════
// Admin/Dono: canais + DMs
// ═══════════════════════════════════════════
function setupAdminChat() {
  // Keep original tabs
  var tabsEl = document.getElementById('chat-tabs-area');
  tabsEl.className = 'chat-tabs';
  tabsEl.innerHTML = '<button class="chat-tab active" data-channel="geral" onclick="switchChannel(\'geral\')">Geral</button>'
    + '<button class="chat-tab" data-channel="urgente" onclick="switchChannel(\'urgente\')">Urgente</button>';

  loadMessages(currentChannel);
  subscribeRealtime();
}

// ─── Open DM (from contacts list) ───
window.openDM = async function(contactId) {
  var ch = dmChannel(currentUserId, contactId);
  currentChannel = ch;

  // Highlight selected contact
  document.querySelectorAll('.contact-item').forEach(function(el) {
    el.classList.toggle('active', el.getAttribute('data-contact-id') === contactId);
  });

  // Hide unread badge
  var unreadEl = document.getElementById('unread-' + contactId);
  if (unreadEl) unreadEl.style.display = 'none';

  // Update topbar with contact name
  var contactName = _assessorNamesCache[contactId] || 'Chat';
  var topbarH1 = document.querySelector('.topbar h1');
  if (topbarH1) topbarH1.textContent = 'Chat — ' + contactName;

  // Clear and reload
  document.getElementById('chat-messages').innerHTML = '<div class="chat-empty">Carregando...</div>';
  clearFilePreview();

  if (realtimeSubscription) {
    sb.removeChannel(realtimeSubscription);
    realtimeSubscription = null;
  }

  await loadMessages(ch);
  subscribeRealtime();
};

// ─── Load Messages ───
async function loadMessages(channel) {
  var messagesEl = document.getElementById('chat-messages');

  try {
    var { data, error } = await sb
      .from('mensagens')
      .select('*')
      .eq('channel', channel)
      .order('created_at', { ascending: true })
      .limit(200);

    if (error) throw error;

    if (!data || data.length === 0) {
      messagesEl.innerHTML = '<div class="chat-empty">Nenhuma mensagem ainda. Comece a conversa! 💬</div>';
      return;
    }

    renderMessages(data);
  } catch (e) {
    console.error('[chat] Erro ao carregar mensagens:', e);
    messagesEl.innerHTML = '<div class="chat-empty">Erro ao carregar mensagens.</div>';
  }
}

// ─── Render Messages ───
var _lastRenderedSenderId = null;

function renderMessages(messages) {
  var messagesEl = document.getElementById('chat-messages');
  var html = '';
  var lastDate = '';
  _lastRenderedSenderId = null;

  for (var i = 0; i < messages.length; i++) {
    var msg = messages[i];
    var prevSenderId = i > 0 ? messages[i - 1].sender_id : null;
    html += buildMessageHTML(msg, lastDate, prevSenderId);
    var createdAt = new Date(msg.created_at);
    lastDate = createdAt.toLocaleDateString('pt-BR');
    _lastRenderedSenderId = msg.sender_id;
  }

  // Scroll-to-bottom button
  html += '<div id="scroll-anchor"></div>';
  messagesEl.innerHTML = html;
  scrollToBottom();

  // Show scroll-to-bottom button on scroll
  messagesEl.addEventListener('scroll', handleChatScroll);
}

function handleChatScroll() {
  var el = document.getElementById('chat-messages');
  var btn = document.getElementById('btn-scroll-bottom');
  if (!btn || !el) return;
  var isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
  btn.style.display = isNearBottom ? 'none' : 'flex';
}

function formatDateLabel(dateStr) {
  var today = new Date().toLocaleDateString('pt-BR');
  var yesterday = new Date(Date.now() - 86400000).toLocaleDateString('pt-BR');
  if (dateStr === today) return 'Hoje';
  if (dateStr === yesterday) return 'Ontem';
  return dateStr;
}

function buildMessageHTML(msg, lastDate, prevSenderId) {
  var isOwn = msg.sender_id === currentUserId;
  var senderName = getSenderName(msg.sender_id);
  var createdAt = new Date(msg.created_at);
  var dateStr = createdAt.toLocaleDateString('pt-BR');
  var timeStr = createdAt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  var isGrouped = prevSenderId === msg.sender_id && dateStr === lastDate;

  var html = '';

  if (dateStr !== lastDate) {
    html += '<div class="chat-date-separator"><span>' + formatDateLabel(dateStr) + '</span></div>';
  }

  var bubbleClass = isOwn ? 'chat-bubble own' : 'chat-bubble other';
  if (isGrouped) bubbleClass += ' grouped';

  html += '<div class="' + bubbleClass + '" data-msg-id="' + msg.id + '">';

  if (isOwn) {
    html += '<button class="btn-delete-msg" onclick="deleteMessage(\'' + msg.id + '\')" title="Apagar">✕</button>';
  }

  // Show sender name only if not grouped and not own
  if (!isOwn && !isGrouped) {
    var avatarUrl = _assessorAvatarsCache[msg.sender_id];
    var avatarHtml = avatarUrl
      ? '<img src="' + avatarUrl + '" class="sender-mini-avatar">'
      : '';
    html += '<div class="chat-sender">' + avatarHtml + escapeHtml(senderName) + '</div>';
  }

  if (msg.content) {
    // Linkify URLs
    var escapedContent = escapeHtml(msg.content);
    escapedContent = escapedContent.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline;">$1</a>');
    html += '<div class="chat-text">' + escapedContent + '</div>';
  }

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

  if (!text && !_pendingFile) return;

  btn.disabled = true;
  input.disabled = true;

  try {
    var fileUrl = null;
    var fileName = null;

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

    // Update last message preview in contacts
    updateContactPreview(currentChannel, text || '📎 Arquivo');
  } catch (e) {
    console.error('[chat] Erro ao enviar:', e);
    showToast('Erro ao enviar mensagem: ' + (e.message || e), 'error');
  } finally {
    btn.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

function updateContactPreview(channel, text) {
  // Find which contact this channel belongs to
  for (var i = 0; i < _contactsList.length; i++) {
    var ch = dmChannel(currentUserId, _contactsList[i].id);
    if (ch === channel) {
      var el = document.getElementById('last-' + _contactsList[i].id);
      if (el) {
        el.textContent = text.length > 30 ? text.substring(0, 30) + '...' : text;
      }
      break;
    }
  }
}

// ─── File Upload ───
function handleFileSelected(e) {
  var file = e.target.files[0];
  if (!file) return;

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
  if (preview) {
    preview.style.display = 'none';
    preview.innerHTML = '';
  }
  var fileInput = document.getElementById('chat-file-input');
  if (fileInput) fileInput.value = '';
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function uploadFile(file) {
  var ext = file.name.split('.').pop();
  var path = 'chat/' + currentChannel.replace(/[^a-z0-9-]/g, '_') + '/' + Date.now() + '_' + Math.random().toString(36).substring(2, 8) + '.' + ext;

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

// ─── Switch Channel (admin tabs) ───
window.switchChannel = function(channel) {
  if (channel === currentChannel) return;
  currentChannel = channel;

  var tabs = document.querySelectorAll('.chat-tab');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].classList.toggle('active', tabs[i].getAttribute('data-channel') === channel);
  }

  clearFilePreview();
  document.getElementById('chat-messages').innerHTML = '<div class="chat-empty">Carregando mensagens...</div>';

  if (realtimeSubscription) {
    sb.removeChannel(realtimeSubscription);
    realtimeSubscription = null;
  }

  loadMessages(channel);
  subscribeRealtime();
};

// ─── Subscribe Realtime ───
function subscribeRealtime() {
  if (realtimeSubscription) {
    sb.removeChannel(realtimeSubscription);
    realtimeSubscription = null;
  }

  try {
    realtimeSubscription = sb
      .channel('chat-' + currentChannel.replace(/[^a-z0-9-]/g, '_'))
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

  var emptyEl = messagesEl.querySelector('.chat-empty');
  if (emptyEl) emptyEl.remove();

  var lastSeparator = messagesEl.querySelector('.chat-date-separator:last-of-type');
  var lastDateText = lastSeparator ? lastSeparator.querySelector('span') ? lastSeparator.querySelector('span').textContent : lastSeparator.textContent : '';
  // Convert "Hoje"/"Ontem" back to date string for comparison
  var today = new Date().toLocaleDateString('pt-BR');
  if (lastDateText === 'Hoje') lastDateText = today;

  var tempDiv = document.createElement('div');
  tempDiv.innerHTML = buildMessageHTML(msg, lastDateText, _lastRenderedSenderId);
  _lastRenderedSenderId = msg.sender_id;

  while (tempDiv.firstChild) {
    messagesEl.appendChild(tempDiv.firstChild);
  }

  scrollToBottom();

  // Play notification sound for messages from others
  if (msg.sender_id !== currentUserId) {
    playNotifSound();
  }

  // Update contact preview
  updateContactPreview(msg.channel, msg.content || '📎 Arquivo');
}

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

function scrollToBottom() {
  var messagesEl = document.getElementById('chat-messages');
  setTimeout(function() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }, 50);
}

window.scrollChatToBottom = function() {
  scrollToBottom();
  var btn = document.getElementById('btn-scroll-bottom');
  if (btn) btn.style.display = 'none';
};

// ─── Notification Sound ───
var _notifAudio = null;
function playNotifSound() {
  try {
    if (!_notifAudio) {
      // Generate a short beep using Web Audio API
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 800;
      gain.gain.value = 0.1;
      osc.start();
      osc.stop(ctx.currentTime + 0.15);
    }
  } catch(e) {}
}

// ─── Search Messages ───
window.toggleChatSearch = function() {
  var searchEl = document.getElementById('chat-search-bar');
  if (!searchEl) return;
  var isVisible = searchEl.style.display !== 'none';
  searchEl.style.display = isVisible ? 'none' : 'flex';
  if (!isVisible) {
    searchEl.querySelector('input').focus();
  }
};

window.searchMessages = function(query) {
  if (!query || query.length < 2) {
    // Remove highlights
    document.querySelectorAll('.chat-bubble.search-highlight').forEach(function(el) {
      el.classList.remove('search-highlight');
    });
    return;
  }
  query = query.toLowerCase();
  var bubbles = document.querySelectorAll('.chat-bubble');
  var found = false;
  bubbles.forEach(function(b) {
    var text = (b.querySelector('.chat-text') || {}).textContent || '';
    if (text.toLowerCase().indexOf(query) !== -1) {
      b.classList.add('search-highlight');
      if (!found) {
        b.scrollIntoView({ behavior: 'smooth', block: 'center' });
        found = true;
      }
    } else {
      b.classList.remove('search-highlight');
    }
  });
};
