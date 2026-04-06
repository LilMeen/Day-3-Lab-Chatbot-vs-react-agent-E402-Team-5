import { HttpException, HttpStatus, Injectable } from '@nestjs/common';
import type { InfoResponseEntity, MovieScheduleEntity } from './entity/info-response.entity';

interface RepositoryInput {
  movieId: string;
  movieUrl: string;
  debugHtml?: boolean;
}

interface AiScheduleResponse {
  status: string;
  movie_url: string;
  total: number;
  schedules: string[][];
}

@Injectable()
export class InfoRepository {
  private readonly aiServiceBaseUrl = process.env.AI_SERVICE_URL ?? 'http://localhost:8000';

  async getMovieSchedules(input: RepositoryInput): Promise<InfoResponseEntity> {
    try {
      const endpoint = new URL('/api/v1/movie-schedules', this.aiServiceBaseUrl);
      endpoint.searchParams.set('movie_url', input.movieUrl);
      if (input.debugHtml) {
        endpoint.searchParams.set('debug_html', 'true');
      }

      const response = await fetch(endpoint.toString(), { method: 'GET' });

      if (!response.ok) {
        throw new HttpException(
          `AI service returned status ${response.status}`,
          HttpStatus.BAD_GATEWAY,
        );
      }

      const data = (await response.json()) as Partial<AiScheduleResponse>;
      const schedules: MovieScheduleEntity[] = Array.isArray(data.schedules)
        ? data.schedules
            .filter((item): item is string[] => Array.isArray(item) && item.length >= 3)
            .map(([theatre, day, time]) => ({
              theatre: theatre ?? '',
              day: day ?? '',
              time: time ?? '',
            }))
        : [];

      return {
        movieId: input.movieId,
        movieUrl: data.movie_url ?? input.movieUrl,
        total: schedules.length,
        firstSchedule: schedules[0] ?? null,
        schedules,
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
