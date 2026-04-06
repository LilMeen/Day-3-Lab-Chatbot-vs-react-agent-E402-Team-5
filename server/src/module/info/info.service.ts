import { Injectable } from '@nestjs/common';
import { InfoRepository } from './info.repository';
import type { InfoRequestEntity } from './entity/info-request.entity';
import type { InfoResponseEntity } from './entity/info-response.entity';

@Injectable()
export class InfoService {
  constructor(private readonly infoRepository: InfoRepository) {}

  async getMovieSchedules(payload: InfoRequestEntity): Promise<InfoResponseEntity> {
    const movieId = payload.movieId.trim().replace(/^\/+|\/+$/g, '');
    const baseMovieUrl =
      process.env.CINESTAR_MOVIE_BASE_URL ?? 'https://cinestar.com.vn/movie';
    const movieUrl = `${baseMovieUrl.replace(/\/$/, '')}/${movieId}/`;

    return this.infoRepository.getMovieSchedules({
      movieId,
      movieUrl,
      debugHtml: payload.debugHtml,
    });
  }
}
