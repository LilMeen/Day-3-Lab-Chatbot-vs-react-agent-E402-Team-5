import { Injectable } from '@nestjs/common';
import { ChatRepository } from './chat.repository';
import type { ChatRequestEntity } from './entity/chat-request.entity';
import type { ChatResponseEntity } from './entity/chat-response.entity';

@Injectable()
export class ChatService {
  constructor(private readonly chatRepository: ChatRepository) {}

  async chat(payload: ChatRequestEntity): Promise<ChatResponseEntity> {
    return this.chatRepository.askAI(payload);
  }
}
