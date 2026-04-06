import { HttpException, HttpStatus, Injectable } from '@nestjs/common';
import type { ChatRequestEntity } from './entity/chat-request.entity';
import type { ChatResponseEntity } from './entity/chat-response.entity';

@Injectable()
export class ChatRepository {
  private readonly aiServiceUrl = process.env.AI_SERVICE_URL ?? 'http://localhost:8000/chat';

  async askAI(payload: ChatRequestEntity): Promise<ChatResponseEntity> {
    try {
      const response = await fetch(this.aiServiceUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new HttpException(
          `AI service returned status ${response.status}`,
          HttpStatus.BAD_GATEWAY,
        );
      }

      const data = (await response.json()) as Partial<ChatResponseEntity>;

      return {
        reply: data.reply ?? '',
        conversationId: data.conversationId,
        model: data.model,
      };
    } catch (error) {
      if (error instanceof HttpException) {
        throw error;
      }

      throw new HttpException(
        'Cannot reach AI service',
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }
  }
}
