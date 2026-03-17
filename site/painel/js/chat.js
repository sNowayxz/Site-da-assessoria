/* ═══════════════════════════════════════════
   Chat — Mensagens em Tempo Real
   ═══════════════════════════════════════════ */

var currentChannel = 'geral';
var currentUserId = null;
var currentUserName = '';
var realtimeSubscription = null;

// ─── Init ───
document.addEventListener('DOMContentLoaded', async function () {
  var result = await requireRole(['admin', 'assessor']);
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

  await loadMessages(currentChannel);
  subscribeRealtime();
});

// ─── Load Messages ───
async function loadMessages(channel) {
  var messagesEl = document.getElementById('chat-messages');
  var emptyEl = document.getElementById('chat-empty');

  try {
    var { data, error } = await sb
      .from('mensagens')
      .select('*, assessores(nome)')
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
    var isOwn = msg.sender_id === currentUserId;
    var senderName = (msg.assessores && msg.assessores.nome) ? msg.assessores.nome : 'Desconhecido';
    var createdAt = new Date(msg.created_at);
    var dateStr = createdAt.toLocaleDateString('pt-BR');
    var timeStr = createdAt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    // Date separator
    if (dateStr !== lastDate) {
      html += '<div class="chat-date-separator">' + dateStr + '</div>';
      lastDate = dateStr;
    }

    var bubbleClass = isOwn ? 'chat-bubble own' : 'chat-bubble other';

    html += '<div class="' + bubbleClass + '">';
    if (!isOwn) {
      html += '<div class="chat-sender">' + escapeHtml(senderName) + '</div>';
    }
    html += '<div class="chat-text">' + escapeHtml(msg.content || '') + '</div>';
    html += '<div class="chat-time">' + timeStr + '</div>';
    html += '</div>';
  }

  messagesEl.innerHTML = html;
  scrollToBottom();
}

// ─── Send Message ───
async function sendMessage() {
  var input = document.getElementById('chat-input');
  var btn = document.getElementById('btn-send');
  var text = input.value.trim();
  if (!text) return;

  btn.disabled = true;
  input.disabled = true;

  try {
    var { error } = await sb.from('mensagens').insert({
      content: text,
      channel: currentChannel,
      sender_id: currentUserId
    });

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
      .subscribe();
  } catch (e) {
    console.warn('[chat] Realtime subscription error:', e.message);
  }
}

// ─── Handle New Message from Realtime ───
async function handleNewMessage(msg) {
  // Fetch sender name
  var senderName = 'Desconhecido';
  try {
    var { data } = await sb.from('assessores').select('nome').eq('id', msg.sender_id).single();
    if (data && data.nome) senderName = data.nome;
  } catch (e) {
    console.warn('[chat] Could not fetch sender name:', e.message);
  }

  var messagesEl = document.getElementById('chat-messages');

  // Remove empty state if present
  var emptyEl = messagesEl.querySelector('.chat-empty');
  if (emptyEl) emptyEl.remove();

  var isOwn = msg.sender_id === currentUserId;
  var createdAt = new Date(msg.created_at);
  var timeStr = createdAt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  var dateStr = createdAt.toLocaleDateString('pt-BR');

  // Check if we need a date separator
  var lastSeparator = messagesEl.querySelector('.chat-date-separator:last-of-type');
  var lastDateText = lastSeparator ? lastSeparator.textContent : '';
  if (dateStr !== lastDateText) {
    var sepDiv = document.createElement('div');
    sepDiv.className = 'chat-date-separator';
    sepDiv.textContent = dateStr;
    messagesEl.appendChild(sepDiv);
  }

  var bubbleDiv = document.createElement('div');
  bubbleDiv.className = isOwn ? 'chat-bubble own' : 'chat-bubble other';

  var html = '';
  if (!isOwn) {
    html += '<div class="chat-sender">' + escapeHtml(senderName) + '</div>';
  }
  html += '<div class="chat-text">' + escapeHtml(msg.content || '') + '</div>';
  html += '<div class="chat-time">' + timeStr + '</div>';
  bubbleDiv.innerHTML = html;

  messagesEl.appendChild(bubbleDiv);
  scrollToBottom();
}

// ─── Scroll to Bottom ───
function scrollToBottom() {
  var messagesEl = document.getElementById('chat-messages');
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ─── Escape HTML ───
function escapeHtml(text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.appendChild(document.createTextNode(text));
  return div.innerHTML;
}
