import { useEffect, useRef, useState } from 'react';
import { api } from '../../api/apiClient';
import { Send, Bot, User, Loader2, RotateCcw, Sparkles } from 'lucide-react';

// Drop this component anywhere — the sidebar chat panel, or full-page
// via pages/ChatPage.jsx. It talks to Member 6's /chat/ endpoints and
// keeps its own conversation_id so it doesn't collide with other chats.
export default function AIChat({ caseId = null, conversationId = 'dashboard-session', compact = false }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "I'm CrimeNet AI. Ask me about suspects, connections, or flagged transactions in this case." }
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [samples, setSamples] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.getSampleQuestions().then(r => setSamples(r.data?.sample_questions || [])).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, sending]);

  const send = async (text) => {
    const question = (text ?? input).trim();
    if (!question || sending) return;

    setMessages(prev => [...prev, { role: 'user', text: question }]);
    setInput('');
    setSending(true);

    try {
      const res = await api.sendChatMessage(question, conversationId, caseId);
      const answer = res.data?.message || "I wasn't able to generate a response.";
      setMessages(prev => [...prev, { role: 'assistant', text: answer }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Could not reach the AI Assistant service (port 8004). Make sure it is running.'
      }]);
    } finally {
      setSending(false);
    }
  };

  const reset = async () => {
    try { await api.resetChat(conversationId); } catch (e) { /* ignore */ }
    setMessages([{ role: 'assistant', text: 'Conversation reset. Ask me anything about this case.' }]);
  };

  return (
    <div className={`flex flex-col bg-base-surface rounded-lg border border-base-border overflow-hidden ${compact ? 'h-[420px]' : 'h-[calc(100vh-140px)]'}`}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-base-border">
        <div className="flex items-center gap-2">
          <div className="relative w-6 h-6 rounded-full bg-signal/10 flex items-center justify-center">
            <Bot size={13} className="text-signal" />
          </div>
          <span className="text-ink-primary font-medium text-sm">AI Assistant</span>
        </div>
        <button
          onClick={reset}
          className="text-ink-faint hover:text-ink-primary transition-colors focus-ring rounded p-1"
          title="Reset conversation"
        >
          <RotateCcw size={14} />
        </button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5 ${
              m.role === 'user' ? 'bg-base-raised' : 'bg-signal/10'
            }`}>
              {m.role === 'user' ? <User size={12} className="text-ink-muted" /> : <Bot size={12} className="text-signal" />}
            </div>
            <div className={`max-w-[80%] rounded-lg px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
              m.role === 'user'
                ? 'bg-signal text-white rounded-tr-sm'
                : 'bg-base-raised text-ink-primary rounded-tl-sm border border-base-border'
            }`}>
              {m.text}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex gap-2.5">
            <div className="shrink-0 w-6 h-6 rounded-full bg-signal/10 flex items-center justify-center mt-0.5">
              <Bot size={12} className="text-signal" />
            </div>
            <div className="bg-base-raised border border-base-border rounded-lg rounded-tl-sm px-3.5 py-2.5 text-sm text-ink-faint flex items-center gap-2">
              <Loader2 size={13} className="animate-spin" /> thinking…
            </div>
          </div>
        )}
      </div>

      {messages.length <= 1 && samples.length > 0 && (
        <div className="px-4 pb-3 flex flex-wrap gap-1.5">
          {samples.slice(0, 3).map((q, i) => (
            <button
              key={i}
              onClick={() => send(q)}
              className="text-[11px] text-ink-muted border border-base-border rounded-full px-2.5 py-1 hover:border-signal/50 hover:text-signal transition-colors flex items-center gap-1"
            >
              <Sparkles size={10} /> {q}
            </button>
          ))}
        </div>
      )}

      <div className="border-t border-base-border p-3 flex items-center gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ask about a suspect, case, or connection…"
          className="flex-1 bg-base-raised border border-base-border rounded-md px-3 py-2 text-sm text-ink-primary placeholder-ink-faint focus:outline-none focus:border-signal/60 transition-colors"
        />
        <button
          onClick={() => send()}
          disabled={sending || !input.trim()}
          className="bg-signal text-white rounded-md p-2 hover:bg-signal-dim disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-ring"
        >
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}
