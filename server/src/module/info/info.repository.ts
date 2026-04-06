import { HttpException, HttpStatus, Injectable } from '@nestjs/common';
import type { InfoResponseEntity, MovieScheduleEntity } from './entity/info-response.entity';
import { promises as fs } from 'fs';
import path from 'path';

interface RepositoryInput {
  movieId: string;
  movieUrl: string;
  debugHtml?: boolean;
}

interface AiScheduleResponse {
  status: string;
  movie_url: string;
  total: number;
  movie?: {
    title?: string;
    description?: string;
    poster_url?: string;
  };
  schedules: unknown[];
}

function flattenGroupedSchedules(grouped: unknown[]): MovieScheduleEntity[] {
  const flat: MovieScheduleEntity[] = [];

  for (const locality of grouped) {
    if (!locality || typeof locality !== 'object') {
      continue;
    }

    const theatres = (locality as { theatres?: unknown }).theatres;
    if (!Array.isArray(theatres)) {
      continue;
    }

    for (const theatreNode of theatres) {
      if (!theatreNode || typeof theatreNode !== 'object') {
        continue;
      }

      const theatre = String((theatreNode as { theatre?: unknown }).theatre ?? '');
      const movies = (theatreNode as { movies?: unknown }).movies;
      if (!Array.isArray(movies)) {
        continue;
      }

      for (const movie of movies) {
        if (!movie || typeof movie !== 'object') {
          continue;
        }

        const schedule = (movie as { schedule?: unknown }).schedule;
        if (!Array.isArray(schedule)) {
          continue;
        }

        for (const dayNode of schedule) {
          if (!dayNode || typeof dayNode !== 'object') {
            continue;
          }

          const day = String((dayNode as { day?: unknown }).day ?? '');
          const showtimes = (dayNode as { showtimes?: unknown }).showtimes;
          if (!Array.isArray(showtimes)) {
            continue;
          }

          for (const time of showtimes) {
            flat.push({
              theatre,
              day,
              time: String(time ?? ''),
            });
          }
        }
      }
    }
  }

  return flat;
}

@Injectable()
export class InfoRepository {
  private readonly aiServiceBaseUrl = process.env.AI_SERVICE_URL ?? 'http://localhost:8000';
  private readonly aiTimeoutMs = Number(process.env.AI_SERVICE_TIMEOUT_MS ?? 60000);
  private readonly historyDir = path.resolve(
    process.cwd(),
    process.env.CHAT_HISTORY_DIR ?? 'chat_history',
  );


    async getMovieSchedules(input: RepositoryInput): Promise<InfoResponseEntity> {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.aiTimeoutMs);

        try {
        const endpoint = new URL('/api/v1/movie-schedules', this.aiServiceBaseUrl);
        endpoint.searchParams.set('movie_url', input.movieUrl);
        if (input.debugHtml) {
            endpoint.searchParams.set('debug_html', 'true');
        }

        const response = await fetch(endpoint.toString(), {
          method: 'GET',
          signal: controller.signal,
        });

        if (!response.ok) {
            throw new HttpException(
            `AI service returned status ${response.status}`,
            HttpStatus.BAD_GATEWAY,
            );
        }

        const data = (await response.json()) as Partial<AiScheduleResponse>;
        let schedules: MovieScheduleEntity[] = [];

        if (Array.isArray(data.schedules) && Array.isArray(data.schedules[0])) {
            schedules = (data.schedules as string[][])
            .filter((item): item is string[] => Array.isArray(item) && item.length >= 3)
            .map(([theatre, day, time]) => ({
                theatre: theatre ?? '',
                day: day ?? '',
                time: time ?? '',
            }));
        } else if (Array.isArray(data.schedules)) {
            schedules = flattenGroupedSchedules(data.schedules);
        }

        return {
            movieId: input.movieId,
            movieUrl: data.movie_url ?? input.movieUrl,
          title: data.movie?.title?.trim() || input.movieId,
          description: data.movie?.description?.trim() || '',
          posterUrl: data.movie?.poster_url?.trim() || '',
            total: schedules.length,
            firstSchedule: schedules[0] ?? null,
            schedules,
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
}
