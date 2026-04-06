import { HttpException, HttpStatus, Injectable } from '@nestjs/common';
import type { InfoRequestEntity } from './entity/info-request.entity';
import type { InfoResponseEntity } from './entity/info-response.entity';

@Injectable()
export class InfoRepository {
  private readonly crawlServiceUrl =
    process.env.CRAWL_SERVICE_URL ?? 'http://localhost:8001/crawl/info';

  async getInfo(payload: InfoRequestEntity): Promise<InfoResponseEntity> {
    try {
      const response = await fetch(this.crawlServiceUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new HttpException(
          `Crawl service returned status ${response.status}`,
          HttpStatus.BAD_GATEWAY,
        );
      }

      const data = (await response.json()) as Partial<InfoResponseEntity>;

      return {
        title: data.title,
        summary: data.summary ?? '',
        content: data.content,
        source: data.source,
      };
    } catch (error) {
      if (error instanceof HttpException) {
        throw error;
      }

      throw new HttpException(
        'Cannot reach crawl service',
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }
  }
}
