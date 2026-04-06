import { Injectable } from '@nestjs/common';
import { ChatRepository } from './chat.repository';
import type { ChatRequestEntity } from './entity/chat-request.entity';
import type { ChatResponseEntity } from './entity/chat-response.entity';
import { ChatEntity } from './entity/chat.entity';
import { randomUUID } from 'crypto';

@Injectable()
export class ChatService {
  constructor(private readonly chatRepository: ChatRepository) {}

  private mapLineToChatEntity(line: string): ChatEntity {
    const splitIndex = line.indexOf(':');
    if (splitIndex === -1) {
      return {
        role: 'chatbot',
        message: line,
        timestamp: new Date(),
      };
    }

    const rawRole = line.slice(0, splitIndex).trim().toLowerCase();
    const message = line.slice(splitIndex + 1).trim();

    return {
      role: rawRole === 'user' ? 'user' : 'chatbot',
      message,
      timestamp: new Date(),
    };
  }

  async chat(payload: ChatRequestEntity): Promise<ChatResponseEntity> {
    const sessionId = payload.sessionId?.trim() || randomUUID();

    await this.chatRepository.upsertChatHistory(sessionId, {
      role: 'user',
      message: payload.message, 
    });

    const aiResponse = await this.chatRepository.askAI({
      ...payload,
      sessionId: sessionId,
    });

    await this.chatRepository.upsertChatHistory(sessionId, {
      role: 'chatbot',
      message: aiResponse.reply,
    });

    return {
      ...aiResponse,  
      sessionId: aiResponse.sessionId ?? sessionId,
    };
  }

  async getChatHistory(sessionId: string): Promise<ChatEntity[]> {
    const lines = await this.chatRepository.getChatHistory(sessionId);
    return lines.map((line) => this.mapLineToChatEntity(line));
  }

  async appendChatHistory(sessionId: string, chat: ChatEntity): Promise<void> {
    return this.chatRepository.upsertChatHistory(sessionId, chat);
  }

  async getChatSessions(): Promise<string[]> {
    return this.chatRepository.getChatSessions();
  }
}
