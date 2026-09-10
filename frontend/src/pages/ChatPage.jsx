import Header from '../components/layout/Header';
import AIChat from '../components/chat/AIChat';

export default function ChatPage() {
  return (
    <div>
      <Header title="AI Assistant" subtitle="Ask natural-language questions grounded in your case evidence" />
      <div className="max-w-2xl">
        <AIChat conversationId="chat-page-session" />
      </div>
    </div>
  );
}
