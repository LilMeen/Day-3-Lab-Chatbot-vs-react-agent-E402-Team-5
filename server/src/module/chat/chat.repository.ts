import { HttpException, HttpStatus, Injectable } from '@nestjs/common';
import type { ChatRequestEntity } from './entity/chat-request.entity';
import type { ChatResponseEntity } from './entity/chat-response.entity';
import { promises as fs } from 'fs';
import path from 'path';

@Injectable()
export class ChatRepository {
  private readonly aiAgentServiceUrl =
    process.env.AI_AGENT_SERVICE_URL ?? 'http://localhost:8000/api/v1/agent';
  private readonly aiBaselineServiceUrl =
    process.env.AI_BASELINE_SERVICE_URL ?? 'http://localhost:8000/api/v1/baseline';

  private readonly historyDir = path.resolve(
    process.cwd(),
    process.env.CHAT_HISTORY_DIR ?? 'chat_history',
  );
  private readonly aiTimeoutMs = Number(process.env.AI_SERVICE_TIMEOUT_MS ?? 60000);

  private normalizeSessionId(sessionId: string): string {
    const normalized = sessionId.trim();
    if (!/^[a-zA-Z0-9_-]+$/.test(normalized)) {
      throw new HttpException('Invalid conversationId format', HttpStatus.BAD_REQUEST);
    }
    return normalized;
  }

  private async ensureHistoryDir(): Promise<void> {
    await fs.mkdir(this.historyDir, { recursive: true });
  }

  private getHistoryFilePath(sessionId: string): string {
    const safeSessionId = this.normalizeSessionId(sessionId);
    return path.join(this.historyDir, `${safeSessionId}.txt`);
  }

  async askAI(payload: ChatRequestEntity): Promise<ChatResponseEntity> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.aiTimeoutMs);

    try {
      const aiServiceUrl = payload.model === 'agent' ? this.aiAgentServiceUrl : this.aiBaselineServiceUrl;
  
      const response = await fetch(aiServiceUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_message: payload.message }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new HttpException(
          `AI service returned status ${response.status}`,
          HttpStatus.BAD_GATEWAY,
        );
      }

      const data = (await response.json()) as Partial<{
        reply: string;
        bot_type: 'baseline' | 'react_agent' | string;
        movie_ids: string[];
        movieIds: string[];
      }>;

      const normalizedMovieIds = Array.isArray(data.movie_ids)
        ? data.movie_ids
        : Array.isArray(data.movieIds)
          ? data.movieIds
          : undefined;

      return {
        reply: data.reply ?? '',
        model: payload.model,
        movieIds: normalizedMovieIds,
      };
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new HttpException('AI service timeout', HttpStatus.GATEWAY_TIMEOUT);
      }

      if (error instanceof HttpException) {
        throw error;
      }

      throw new HttpException(
        'Cannot reach AI service',
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    } finally {
      clearTimeout(timeout);
    }
  }

  async getChatHistory(sessionId: string): Promise<string[]> {
    const filePath = this.getHistoryFilePath(sessionId);
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      return content
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        return [];
      }
      throw new HttpException('Cannot read chat history', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  async upsertChatHistory(
    sessionId: string,
    chat: { role: 'user' | 'chatbot'; message: string },
  ): Promise<void> {
    await this.ensureHistoryDir();
    const filePath = this.getHistoryFilePath(sessionId);
    const line = `${chat.role}: ${chat.message}\n`;

    try {
      await fs.appendFile(filePath, line, 'utf-8');
    } catch (error) {
      throw new HttpException('Cannot write chat history', HttpStatus.INTERNAL_SERVER_ERROR);
    }
  }

  async getChatSessions(): Promise<string[]> {
    await this.ensureHistoryDir();
    const files = await fs.readdir(this.historyDir, { withFileTypes: true });

    return files
      .filter((entry) => entry.isFile() && entry.name.endsWith('.txt'))
      .map((entry) => entry.name.replace(/\.txt$/, ''))
      .sort();
  }
}
