"use client";

import { skipToken } from "@reduxjs/toolkit/query";
import React, { useMemo, useState } from "react";
import Sidebar from "./Sidebar";
import ChatArea from "./ChatArea";
import MovieInfo from "./MovieInfo";
import {
  useGetChatHistoryQuery,
  useGetChatSessionsQuery,
  useSendMessageMutation,
} from "@/store/api/[module]/chatApi";

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  text: string;
}

interface Conversation {
  id: string;
  title: string;
}

interface MovieScheduleEntity {
  theatre: string;
  day: string;
  time: string;
}

export default function ChatUI() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [chatError, setChatError] = useState<string | null>(null);
  const [sendMessageMutation, { isLoading: loading }] = useSendMessageMutation();
  const { data: sessionIds = [], refetch: refetchSessions } = useGetChatSessionsQuery();
  const {
    data: chatHistory = [],
    refetch: refetchHistory,
    isFetching: loadingHistory,
  } = useGetChatHistoryQuery(
    activeSessionId ? { sessionId: activeSessionId } : skipToken,
  );

  const [movieIds, setMovieIds] = useState<string[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showMovieInfo, setShowMovieInfo] = useState(false);

  const conversations: Conversation[] = useMemo(
    () =>
      sessionIds.map((id) => ({
        id,
        title: `Session ${id.slice(0, 8)}`,
      })),
    [sessionIds],
  );

  const messages: Message[] = useMemo(
    () =>
      chatHistory.map((m, index) => ({
        id: `${activeSessionId ?? "no-session"}-${index}`,
        role: m.role === "user" ? "user" : "assistant",
        text: m.message,
      })),
    [chatHistory, activeSessionId],
  );

  async function sendMessage(text: string) {
    if (!text.trim()) return;

    setInput("");
    setChatError(null);

    try {
      const data = await sendMessageMutation({
        message: text,
        sessionId: activeSessionId ?? undefined,
      }).unwrap();

      const nextSessionId = data.sessionId ?? activeSessionId;
      if (nextSessionId && nextSessionId !== activeSessionId) {
        setActiveSessionId(nextSessionId);
      }

      await refetchSessions();
      if (nextSessionId) {
        await refetchHistory();
      }

      const nextMovieIds = Array.isArray(data.movieIds)
        ? data.movieIds.filter((id): id is string => typeof id === "string" && id.trim().length > 0)
        : [];

      setMovieIds(nextMovieIds);
      setShowMovieInfo(nextMovieIds.length > 0);
    } catch (error) {
      setChatError("Gửi tin nhắn không thành công, vui lòng thử lại sau.");
    }
  }

  const activeTitle = activeSessionId
    ? `Session ${activeSessionId.slice(0, 8)}`
    : "New chat";

  return (
    <div style={{ display: "flex", height: "100vh", backgroundColor: "#f3f4f6", color: "#111827" }}>
      {/* Sidebar with animation */}
      {showSidebar && (
        <div style={{ animation: "slideIn 0.3s ease-out" }}>
          <Sidebar
            conversations={conversations}
            activeId={activeSessionId ?? ""}
            onSelectConversation={(id) => setActiveSessionId(id)}
            onNewChat={() => {
              setActiveSessionId(null);
              setInput("");
            }}
            onToggle={() => setShowSidebar(!showSidebar)}
          />
        </div>
      )}

      {/* Chat Area */}
      <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
        {chatError && (
          <div
            style={{
              margin: "8px 12px 0",
              padding: "8px 12px",
              borderRadius: 8,
              backgroundColor: "#fee2e2",
              color: "#991b1b",
              fontSize: 14,
            }}
          >
            {chatError}
          </div>
        )}
        <ChatArea
          title={activeTitle}
          messages={messages}
          loading={loading || loadingHistory}
          input={input}
          onInputChange={setInput}
          onSendMessage={sendMessage}
          onToggleSidebar={() => setShowSidebar(!showSidebar)}
          onToggleMovieInfo={() => setShowMovieInfo(!showMovieInfo)}
          sidebarVisible={showSidebar}
        />
      </div>

      {/* Movie Info with animation */}
      {showMovieInfo && (
        <div style={{ animation: "slideInRight 0.3s ease-out" }}>
          <MovieInfo movieIds={movieIds} />
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
