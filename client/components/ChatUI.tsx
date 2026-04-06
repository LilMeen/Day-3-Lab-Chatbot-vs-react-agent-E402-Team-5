"use client";

import { skipToken } from "@reduxjs/toolkit/query";
import React, { useMemo, useState } from "react";
import Sidebar from "./Sidebar";
import ChatArea from "./ChatArea";
import MovieInfo from "./MovieInfo";
import {
  useGetChatHistoryQuery,
  useGetChatSessionsQuery,
  useLazyGetChatHistoryQuery,
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

export default function ChatUI() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [optimisticMessages, setOptimisticMessages] = useState<Message[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [sendMessageMutation, { isLoading: loading }] = useSendMessageMutation();
  const [triggerGetChatHistory] = useLazyGetChatHistoryQuery();
  const { data: sessionIds = [], refetch: refetchSessions } = useGetChatSessionsQuery();
  const {
    data: chatHistory = [],
    isFetching: loadingHistory,
  } = useGetChatHistoryQuery(
    activeSessionId ? { sessionId: activeSessionId } : skipToken,
    { refetchOnMountOrArgChange: true },
  );

  const [movieIds, setMovieIds] = useState<string[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showMovieInfo, setShowMovieInfo] = useState(false);
  const [model, setModel] = useState<"baseline" | "agent">("agent");
  const hasActiveSession = Boolean(activeSessionId);

  const conversations: Conversation[] = useMemo(
    () =>
      sessionIds.map((id) => ({
        id,
        title: `Session ${id.slice(0, 8)}`,
      })),
    [sessionIds],
  );

  const messages: Message[] = useMemo(
    () => {
      const historyMessages: Message[] = hasActiveSession
        ? chatHistory.map((m, index): Message => ({
            id: `${activeSessionId ?? "no-session"}-${index}`,
            role: m.role === "user" ? "user" : "assistant",
            text: m.message,
          }))
        : [];

      return [...historyMessages, ...optimisticMessages];
    },
    [chatHistory, activeSessionId, hasActiveSession, optimisticMessages],
  );

  async function sendMessage(text: string) {
    const trimmedText = text.trim();
    if (!trimmedText) return;

    setInput("");
    setChatError(null);
    const requestSessionId = activeSessionId ?? undefined;

    setOptimisticMessages((prev) => [
      ...prev,
      {
        id: `pending-${Date.now()}`,
        role: "user",
        text: trimmedText,
      },
    ]);

    try {
      const data = await sendMessageMutation({
        message: trimmedText,
        sessionId: requestSessionId,
        model,
      }).unwrap();

      const nextSessionId = data.sessionId?.trim() || requestSessionId || null;

      if (!nextSessionId) {
        throw new Error("Không nhận được sessionId từ server.");
      }

      await refetchSessions();

      // Force network fetch to avoid stale/empty cache on the first message of a session.
      await triggerGetChatHistory({ sessionId: nextSessionId }, false).unwrap();

      if (nextSessionId !== activeSessionId) {
        setActiveSessionId(nextSessionId);
      }

      // Server history is now synced, clear optimistic echoes.
      setOptimisticMessages([]);

      const nextMovieIds = Array.isArray(data.movieIds)
        ? data.movieIds.filter((id): id is string => typeof id === "string" && id.trim().length > 0)
        : [];

      setMovieIds(nextMovieIds);
      setShowMovieInfo(nextMovieIds.length > 0);
    } catch (error: unknown) {
      setOptimisticMessages([]);
      const fallbackMessage = "Gửi tin nhắn không thành công, vui lòng thử lại sau.";
      if (error instanceof Error && error.message) {
        setChatError(error.message);
        return;
      }

      type ApiErrorShape = { data?: { message?: string } };
      const maybeApiError = error as ApiErrorShape;
      setChatError(maybeApiError.data?.message ?? fallbackMessage);
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
            onSelectConversation={(id) => {
              setActiveSessionId(id);
              setOptimisticMessages([]);
            }}
            onNewChat={() => {
              setActiveSessionId(null);
              setInput("");
              setOptimisticMessages([]);
              setChatError(null);
              setMovieIds([]);
              setShowMovieInfo(false);
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
          loading={loading || (hasActiveSession && loadingHistory)}
          input={input}
          onInputChange={setInput}
          onSendMessage={sendMessage}
          model={model}
          onModelChange={setModel}
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
