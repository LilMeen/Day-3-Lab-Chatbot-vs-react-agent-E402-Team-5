import { baseApi } from "@/store/api/baseApi";

export type ChatRequest = {
  message: string;
  userId?: string;
  conversationId?: string;
};

export type ChatResponse = {
  reply: string;
  conversationId?: string;
  model?: string;
};

export const chatApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    sendMessage: builder.mutation<ChatResponse, ChatRequest>({
      query: (body) => ({
        url: "/chat",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Chat"],
    }),
  }),
});

export const { useSendMessageMutation } = chatApi;
