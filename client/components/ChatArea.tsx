import React from "react";
import styles from "./ChatArea.module.css";

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
}

interface ChatAreaProps {
  title: string;
  messages: Message[];
  loading: boolean;
  input: string;
  onInputChange: (text: string) => void;
  onSendMessage: (text: string) => void;
  onToggleSidebar?: () => void;
  onToggleMovieInfo?: () => void;
  sidebarVisible?: boolean;
}

export default function ChatArea({
  title,
  messages,
  loading,
  input,
  onInputChange,
  onSendMessage,
  onToggleSidebar,
  onToggleMovieInfo,
  sidebarVisible,
}: ChatAreaProps) {
  return (
    <main className={styles.chatMain}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          {!sidebarVisible && onToggleSidebar && (
            <button onClick={onToggleSidebar} className={styles.toggleBtn} title="Show history">
              ▶
            </button>
          )}
          <h3 className={styles.title}>{title}</h3>
          <div className={styles.toggles}>
            {onToggleMovieInfo && (
              <button onClick={onToggleMovieInfo} className={styles.toggleBtn} title="Toggle movie info">
                ℹ
              </button>
            )}
          </div>
        </div>
      </div>

      <div className={styles.messagesContainer}>
        {messages.map((m) => (
          <div
            key={m.id}
            className={`${styles.messageRow} ${
              m.role === "user" ? styles.userRow : ""
            }`}
          >
            <div
              className={`${styles.message} ${
                m.role === "user" ? styles.userMessage : styles.assistantMessage
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className={styles.loadingRow}>
            <span>Đang xử lý...</span>
            <div className={styles.dots}>
              <div></div>
              <div></div>
              <div></div>
            </div>
          </div>
        )}
      </div>

      <div className={styles.inputArea}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSendMessage(input);
          }}
          className={styles.form}
        >
          <input
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            disabled={loading}
            className={styles.input}
            placeholder="Gõ tin nhắn, ví dụ: tìm vé 'Dune' tối nay"
          />
          <button type="submit" disabled={loading} className={styles.sendBtn}>
            Gửi
          </button>
        </form>
      </div>
    </main>
  );
}
