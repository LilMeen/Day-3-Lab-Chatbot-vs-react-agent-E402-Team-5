import { baseApi } from "@/store/api/baseApi";

export type ChatRequest = {
  message: string;
  userId?: string;
  sessionId?: string;
};

export type ChatResponse = {
  reply: string;
  sessionId?: string;
  model?: string;
  movieIds?: string[];
};

export type ChatMessage = {
  role: "user" | "chatbot";
  message: string;
  timestamp: string;
};

export const chatApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    
    sendMessage: builder.mutation<ChatResponse, ChatRequest>({
      query: (body) => ({
        url: "/chat",
        method: "POST",
        body,
      }),
      invalidatesTags: (_result, _error, arg) => [
        { type: "Chat", id: "SESSIONS" },
        ...(arg.sessionId ? [{ type: "Chat" as const, id: arg.sessionId }] : []),
      ],
    }),

    getChatSessions: builder.query<string[], void>({
      query: () => ({
        url: "/chat/chat-sessions",
        method: "GET",
      }),
      providesTags: [{ type: "Chat", id: "SESSIONS" }],
    }),

    getChatHistory: builder.query<ChatMessage[], { sessionId: string }>({
      query: ({ sessionId }) => ({
        url: "/chat/chat-history",
        method: "GET",
        params: { sessionId },
      }),
      providesTags: (_result, _error, arg) => [{ type: "Chat", id: arg.sessionId }],
    }),
  }),
});

export const {
  useSendMessageMutation,
  useGetChatSessionsQuery,
  useLazyGetChatSessionsQuery,
  useGetChatHistoryQuery,
  useLazyGetChatHistoryQuery,
} = chatApi;
