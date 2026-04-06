import React from "react";
import styles from "./Sidebar.module.css";

interface Conversation {
  id: string;
  title: string;
}

interface SidebarProps {
  conversations: Conversation[];
  activeId: string;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onToggle?: () => void;
}

export default function Sidebar({
  conversations,
  activeId,
  onSelectConversation,
  onNewChat,
  onToggle,
}: SidebarProps) {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h2 className={styles.title}>Chat History</h2>
          {onToggle && (
            <button onClick={onToggle} className={styles.toggleBtn} title="Collapse">
              ◀
            </button>
          )}
        </div>
      </div>
      <div className={styles.conversations}>
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelectConversation(c.id)}
            className={`${styles.convItem} ${
              c.id === activeId ? styles.active : ""
            }`}
          >
            <div className={styles.avatar}>{c.title.charAt(0)}</div>
            <div className={styles.title}>{c.title}</div>
          </button>
        ))}
      </div>
      <div className={styles.footer}>
        <button onClick={onNewChat} className={styles.newChatBtn}>
          New Chat
        </button>
      </div>
    </aside>
  );
}
