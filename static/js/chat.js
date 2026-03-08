/**
 * WhisperLeaf Chat — front-end controller.
 * Streaming, session persistence, request lock, watchdog, and UI helpers.
 */
const ChatController = {
  state: {
    isSending: false,
    sessionId: null,
    selectedMode: 'system',
    history: [],
    currentStreamingBubble: null,
    streamWatchdog: null,
  },

  els: {},

  init() {
    this.cacheElements();
    this.initState();
    this.bindEvents();
    this.loadSessionHistory();
  },

  cacheElements() {
    this.els.chatMessages = document.querySelector('.chat-window');
    this.els.chatWindow = document.getElementById('chatWindow');
    this.els.messageInput = document.getElementById('messageInput');
    this.els.sendBtn = document.getElementById('sendBtn');
    this.els.clearBtn = document.getElementById('clearBtn');
    this.els.chatForm = document.getElementById('chatForm');
    this.els.jumpBottomBtn = document.getElementById('jumpBottomBtn');
    this.els.chatOwl = document.getElementById('chatOwl');
    this.els.owl = document.querySelector('.owl-icon-wrap');
    this.els.modeButtons = document.querySelectorAll('.mode-button');
  },

  initState() {
    this.state.sessionId = sessionStorage.getItem('whisperleaf_session_id') || crypto.randomUUID();
    sessionStorage.setItem('whisperleaf_session_id', this.state.sessionId);
  },

  bindEvents() {
    const { chatForm, messageInput, chatMessages, jumpBottomBtn, clearBtn, chatOwl, modeButtons } = this.els;

    if (chatOwl) {
      chatOwl.addEventListener('click', () => { window.location.href = '/'; });
    }

    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.sendMessage();
      });
    }

    if (messageInput) {
      messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
      messageInput.addEventListener('input', () => this.autoResizeInput());
    }

    if (chatMessages && jumpBottomBtn) {
      chatMessages.addEventListener('scroll', () => this.updateScrollButtonVisibility());
      jumpBottomBtn.addEventListener('click', () => {
        this.scrollToBottom(chatMessages);
        this.updateScrollButtonVisibility();
      });
    }

    if (clearBtn) clearBtn.addEventListener('click', () => this.clearSession());

    if (modeButtons && modeButtons.length) {
      modeButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
          modeButtons.forEach((b) => b.classList.remove('active'));
          btn.classList.add('active');
          this.state.selectedMode = btn.getAttribute('data-mode') || 'system';
        });
      });
    }
  },

  // --- Scroll
  isNearBottom(container, threshold = 100) {
    if (!container) return true;
    return container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
  },

  scrollToBottom(container) {
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
  },

  scrollToBottomIfNearBottom() {
    if (this.isNearBottom(this.els.chatMessages)) this.scrollToBottom(this.els.chatMessages);
  },

  updateScrollButtonVisibility() {
    if (!this.els.jumpBottomBtn) return;
    this.els.jumpBottomBtn.classList.toggle('hidden', this.isNearBottom(this.els.chatMessages));
  },

  // --- Input
  autoResizeInput() {
    const el = this.els.messageInput;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 8 * 16) + 'px';
  },

  resetInputHeight() {
    const el = this.els.messageInput;
    if (el) el.style.height = 'auto';
  },

  // --- Owl
  startThinking() {
    if (this.els.owl) this.els.owl.classList.add('owl-thinking');
  },

  stopThinking() {
    if (this.els.owl) this.els.owl.classList.remove('owl-thinking');
  },

  // --- Sending state
  setSendingState(sending) {
    this.state.isSending = sending;
    if (this.els.sendBtn) this.els.sendBtn.disabled = sending;
  },

  // --- Watchdog
  startWatchdog() {
    this.stopWatchdog();
    this.state.streamWatchdog = setTimeout(() => {
      console.warn('Stream watchdog triggered');
      this.stopThinking();
      this.setSendingState(false);
    }, 25000);
  },

  stopWatchdog() {
    if (this.state.streamWatchdog) {
      clearTimeout(this.state.streamWatchdog);
      this.state.streamWatchdog = null;
    }
  },

  // --- Copy button (assistant messages only)
  addCopyButtonToBubble(bubble, getText) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-copy-msg';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const text = typeof getText === 'function' ? getText() : getText;
      if (text != null) navigator.clipboard.writeText(String(text)).catch(() => {});
    });
    bubble.appendChild(btn);
  },

  // --- Message rendering
  appendMessage(role, text) {
    if (!text && role !== 'assistant') return;
    const { chatWindow } = this.els;
    if (!chatWindow) return;

    const div = document.createElement('div');
    div.className = 'message ' + role;
    if (role === 'assistant') {
      const wrap = document.createElement('div');
      wrap.className = 'message-wrap';
      const body = document.createElement('span');
      body.className = 'message-body';
      body.textContent = text || '';
      wrap.appendChild(body);
      this.addCopyButtonToBubble(wrap, () => body.textContent);
      div.appendChild(wrap);
    } else {
      div.textContent = text || '';
    }
    chatWindow.appendChild(div);
    this.scrollToBottomIfNearBottom();
    this.updateScrollButtonVisibility();
  },

  createStreamingBubble() {
    const { chatWindow } = this.els;
    if (!chatWindow) return null;

    const div = document.createElement('div');
    div.className = 'message assistant';
    const textSpan = document.createElement('span');
    textSpan.className = 'streaming-text';
    textSpan.textContent = '';
    const cursorSpan = document.createElement('span');
    cursorSpan.className = 'streaming-cursor';
    cursorSpan.textContent = '\u258C';
    div.appendChild(textSpan);
    div.appendChild(cursorSpan);
    chatWindow.appendChild(div);
    this.state.currentStreamingBubble = div;
    this.scrollToBottomIfNearBottom();
    return div;
  },

  updateStreamingBubble(textChunk) {
    const bubble = this.state.currentStreamingBubble;
    if (!bubble) return;
    const textEl = bubble.querySelector('.streaming-text');
    if (textEl) textEl.textContent = textChunk;
    this.scrollToBottomIfNearBottom();
    this.updateScrollButtonVisibility();
  },

  finalizeStreamingBubble() {
    const bubble = this.state.currentStreamingBubble;
    if (bubble) {
      const cursor = bubble.querySelector('.streaming-cursor');
      if (cursor) cursor.remove();
      const textEl = bubble.querySelector('.streaming-text');
      const content = textEl ? textEl.textContent : '';
      const wrap = document.createElement('div');
      wrap.className = 'message-wrap';
      const body = document.createElement('span');
      body.className = 'message-body';
      body.textContent = content;
      wrap.appendChild(body);
      this.addCopyButtonToBubble(wrap, () => body.textContent);
      bubble.innerHTML = '';
      bubble.appendChild(wrap);
    }
    this.state.currentStreamingBubble = null;
  },

  setStreamingBubbleError(message) {
    const bubble = this.state.currentStreamingBubble;
    if (bubble) {
      bubble.className = 'message error';
      bubble.textContent = message || 'Error';
    }
    this.finalizeStreamingBubble();
  },

  // --- SSE parsing
  parseSSEBlock(block) {
    const lines = block.split(/\r?\n/);
    let event = '';
    const dataLines = [];
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('event:')) {
        event = trimmed.replace(/^event:\s*/, '').trim();
      } else if (trimmed.startsWith('data:')) {
        dataLines.push(trimmed.replace(/^data:\s?/, ''));
      }
    }
    const data = dataLines.join('\n');
    if (!event && !data) return null;
    if (data.trim() === '[DONE]') return { event: 'done', data: '' };
    return { event, data };
  },

  processStreamBuffer(buffer) {
    const parts = buffer.split(/\n\n+/);
    const remainder = parts.pop() || '';
    return { blocks: parts, remainder };
  },

  // --- Session
  async loadSessionHistory() {
    try {
      const res = await fetch(`/api/chat/history?session_id=${encodeURIComponent(this.state.sessionId)}`);
      if (!res.ok) return;
      const data = await res.json();
      const list = data.history || [];
      if (list.length === 0) return;
      this.els.chatWindow.innerHTML = '';
      this.state.history = list;
      for (const msg of list) {
        if (msg.role) this.appendMessage(msg.role, msg.content || '');
      }
      if (this.state.history.length > 0) this.scrollToBottomIfNearBottom();
      this.updateScrollButtonVisibility();
    } catch (_) {}
  },

  async clearSession() {
    try {
      await fetch('/api/chat/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: this.state.sessionId }),
      });
    } catch (_) {}
    this.els.chatWindow.innerHTML = '';
    this.state.history = [];
  },

  // --- Stream response (reader loop)
  async streamAssistantResponse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullReply = '';
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const { blocks, remainder } = this.processStreamBuffer(buffer);
      buffer = remainder;

      for (const block of blocks) {
        const parsed = this.parseSSEBlock(block);
        if (parsed === null) continue;
        const { event, data } = parsed;

        if (event === 'chunk' && data !== undefined) {
          fullReply += data;
          this.updateStreamingBubble(fullReply);
        } else if (event === 'done') {
          this.stopWatchdog();
          this.stopThinking();
          this.state.history.push({ role: 'assistant', content: fullReply || '' });
          this.finalizeStreamingBubble();
          return;
        } else if (event === 'error') {
          this.stopWatchdog();
          this.stopThinking();
          this.setStreamingBubbleError((data || '').trim() || 'Error');
          return;
        }
      }
    }

    if (buffer.trim()) {
      const parsed = this.parseSSEBlock(buffer);
      if (parsed !== null) {
        const { event, data } = parsed;
        if (event === 'chunk' && data !== undefined) {
          fullReply += data;
          this.updateStreamingBubble(fullReply);
        } else if (event === 'error') {
          this.stopWatchdog();
          this.stopThinking();
          this.setStreamingBubbleError((data || '').trim() || 'Error');
          return;
        }
      }
    }

    this.stopWatchdog();
    this.stopThinking();
    this.state.history.push({ role: 'assistant', content: fullReply || '' });
    this.finalizeStreamingBubble();
  },

  // --- Send (single path; request lock + watchdog)
  async sendMessage() {
    if (this.state.isSending) return;
    const text = (this.els.messageInput?.value || '').trim();
    if (!text) return;

    this.setSendingState(true);
    this.els.messageInput.value = '';
    this.resetInputHeight();
    this.appendMessage('user', text);
    this.state.history.push({ role: 'user', content: text });
    this.startThinking();
    this.createStreamingBubble();
    this.startWatchdog();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: this.state.history,
          session_id: this.state.sessionId,
        }),
      });

      if (!res.ok) {
        this.stopWatchdog();
        this.stopThinking();
        const err = await res.json().catch(() => ({}));
        this.setStreamingBubbleError(err.detail || 'Request failed');
        return;
      }

      if (!res.body) {
        this.stopWatchdog();
        this.stopThinking();
        this.setStreamingBubbleError('No response body');
        return;
      }

      await this.streamAssistantResponse(res);
    } catch (e) {
      this.stopWatchdog();
      this.stopThinking();
      this.setStreamingBubbleError('Network error: ' + (e && e.message ? e.message : 'Unknown error'));
    } finally {
      this.setSendingState(false);
    }
  },
};

document.addEventListener('DOMContentLoaded', () => ChatController.init());
