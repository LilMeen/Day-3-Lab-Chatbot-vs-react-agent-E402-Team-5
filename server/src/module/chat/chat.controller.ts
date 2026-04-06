import { BadRequestException, Body, Controller, Get, Post, Query } from '@nestjs/common';
import { ChatService } from './chat.service';
import type { ChatRequestEntity } from './entity/chat-request.entity';
import type { ChatResponseEntity } from './entity/chat-response.entity';
import { ChatEntity } from './entity/chat.entity';

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

  @Get('chat-history')
  async getChatHistory(@Query('sessionId') sessionId?: string): Promise<ChatEntity[]> {
    if (!sessionId || sessionId.trim().length === 0) {
      throw new BadRequestException('sessionId is required');
    }

    return this.chatService.getChatHistory(sessionId);
  }

  @Get('chat-sessions')
  async getChatSessions(): Promise<string[]> {
    return this.chatService.getChatSessions();
  }
}
