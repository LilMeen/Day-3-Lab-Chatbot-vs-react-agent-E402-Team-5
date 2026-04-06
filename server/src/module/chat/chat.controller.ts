import { BadRequestException, Body, Controller, Post } from '@nestjs/common';
import { ChatService } from './chat.service';
import type { ChatRequestEntity } from './entity/chat-request.entity';
import type { ChatResponseEntity } from './entity/chat-response.entity';

@Controller('chat')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post()
  async chat(@Body() payload: ChatRequestEntity): Promise<ChatResponseEntity> {
    if (!payload?.message || payload.message.trim().length === 0) {
      throw new BadRequestException('message is required');
    }

    return this.chatService.chat(payload);
  }
}
