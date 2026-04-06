import { BadRequestException, Controller, Get, Query } from '@nestjs/common';
import { InfoService } from './info.service';
import type { InfoRequestEntity } from './entity/info-request.entity';
import type { InfoResponseEntity } from './entity/info-response.entity';

@Controller('info')
export class InfoController {
  constructor(private readonly infoService: InfoService) {}


    @Get('movie-schedules')
    async getMovieSchedules(
        @Query('movieId') movieId?: string,
        @Query('debugHtml') debugHtml?: string,
    ): Promise<InfoResponseEntity> {
        if (!movieId || movieId.trim().length === 0) {
        throw new BadRequestException('movieId is required');
        }

        const payload: InfoRequestEntity = {
        movieId,
        debugHtml: debugHtml === 'true',
        };

        return this.infoService.getMovieSchedules(payload);
    }
}
