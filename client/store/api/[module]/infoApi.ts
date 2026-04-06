import { baseApi } from "@/store/api/baseApi";

export type InfoRequest = {
  movieId: string;
  debugHtml?: boolean;
};

export type MovieSchedule = {
  theatre: string;
  day: string;
  time: string;
};

export type InfoResponse = {
  movieId: string;
  movieUrl: string;
  title: string;
  description: string;
  posterUrl: string;
  total: number;
  firstSchedule: MovieSchedule | null;
  schedules: MovieSchedule[];
};

export const infoApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getMovieSchedules: builder.query<InfoResponse, InfoRequest>({
      query: ({ movieId, debugHtml }) => ({
        url: "/info/movie-schedules",
        method: "GET",
        params: {
          movieId,
          ...(debugHtml ? { debugHtml: "true" } : {}),
        },
      }),
      providesTags: ["Info"],
    }),
  }),
});

export const { 
  useGetMovieSchedulesQuery, 
  useLazyGetMovieSchedulesQuery 
} = infoApi;
