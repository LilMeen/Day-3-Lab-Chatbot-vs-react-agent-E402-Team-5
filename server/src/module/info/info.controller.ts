import { BadRequestException, Body, Controller, Post } from '@nestjs/common';
import { InfoService } from './info.service';
import type { InfoRequestEntity } from './entity/info-request.entity';
import type { InfoResponseEntity } from './entity/info-response.entity';

@Controller('info')
export class InfoController {
  constructor(private readonly infoService: InfoService) {}

  @Post()
  async getInfo(@Body() payload: InfoRequestEntity): Promise<InfoResponseEntity> {
    const hasUrl = Boolean(payload?.url && payload.url.trim().length > 0);
    const hasKeyword = Boolean(payload?.keyword && payload.keyword.trim().length > 0);

    if (!hasUrl && !hasKeyword) {
      throw new BadRequestException('url or keyword is required');
    }

    return this.infoService.getInfo(payload);
  }
}
