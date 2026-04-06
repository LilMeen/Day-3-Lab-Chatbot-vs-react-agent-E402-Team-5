export interface MovieScheduleEntity {
  theatre: string;
  day: string;
  time: string;
}

export interface InfoResponseEntity {
  movieId: string;
  movieUrl: string;
  title: string;
  description: string;
  posterUrl: string;
  total: number;
  firstSchedule: MovieScheduleEntity | null;
  schedules: MovieScheduleEntity[];
}
