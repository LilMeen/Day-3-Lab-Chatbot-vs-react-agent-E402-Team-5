"use client";

import React, { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import ChatArea from "./ChatArea";
import MovieInfo from "./MovieInfo";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  text: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  conversationId?: string;
}

interface MovieScheduleEntity {
  theatre: string;
  day: string;
  time: string;
}

interface MovieInfo {
  movieId: string;
  movieUrl: string;
  title?: string;
  total: number;
  schedules: MovieScheduleEntity[];
}

export default function ChatUI() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [movieInfo, setMovieInfo] = useState<MovieInfo | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showMovieInfo, setShowMovieInfo] = useState(false);
  const [model, setModel] = useState<"baseline" | "agent">("agent");

  // Initialize first conversation on mount
  useEffect(() => {
    if (conversations.length === 0) {
      const initialId = String(Date.now());
      setConversations([
        {
          id: initialId,
          title: "New chat",
          messages: [],
        }
      ]);
      setActiveId(initialId);
    }
  }, []);

  const activeConv = conversations.find((c) => c.id === activeId) ?? conversations[0];

  async function sendMessage(text: string) {
    if (!text.trim()) return;
    
    const msg: Message = { id: String(Date.now()), role: "user", text };
    setConversations((prev) =>
      prev.map((c) => (c.id === activeConv.id ? { ...c, messages: [...c.messages, msg] } : c))
    );
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          conversationId: activeConv.conversationId,
          model,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      const reply: Message = {
        id: String(Date.now() + 1),
        role: "assistant",
        text: data.reply || "Xin lỗi, tôi không thể xử lý yêu cầu này.",
      };

      // Update conversation with conversationId from server
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConv.id
            ? {
                ...c,
                messages: [...c.messages, reply],
                conversationId: data.conversationId,
              }
            : c
        )
      );

      // If backend returns movie info, display it
      if (data.movieInfo) {
        setMovieInfo(data.movieInfo);
        setShowMovieInfo(true);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorReply: Message = {
        id: String(Date.now() + 1),
        role: "assistant",
        text: "Xin lỗi, có lỗi xảy ra khi kết nối tới server.",
      };
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConv.id ? { ...c, messages: [...c.messages, errorReply] } : c
        )
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", height: "100vh", backgroundColor: "#f3f4f6", color: "#111827" }}>
      {/* Sidebar with animation */}
      {showSidebar && (
        <div style={{ animation: "slideIn 0.3s ease-out" }}>
          <Sidebar
            conversations={conversations}
            activeId={activeId}
            onSelectConversation={setActiveId}
            onNewChat={() => {
              const id = String(Date.now());
              const newConv: Conversation = { id, title: "New chat", messages: [] };
              setConversations((s) => [newConv, ...s]);
              setActiveId(id);
            }}
            onToggle={() => setShowSidebar(!showSidebar)}
          />
        </div>
      )}

      {/* Chat Area */}
      <ChatArea
        title={activeConv?.title ?? "Chat"}
        messages={activeConv?.messages ?? []}
        loading={loading}
        input={input}
        onInputChange={setInput}
        onSendMessage={sendMessage}
        onToggleSidebar={() => setShowSidebar(!showSidebar)}
        onToggleMovieInfo={() => setShowMovieInfo(!showMovieInfo)}
        sidebarVisible={showSidebar}
        model={model}
        onModelChange={setModel}
      />

      {/* Movie Info with animation */}
      {showMovieInfo && (
        <div style={{ animation: "slideInRight 0.3s ease-out" }}>
          <MovieInfo movieInfo={movieInfo} />
        </div>
      )}

      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(-100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}
