import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const baseApi = createApi({
	reducerPath: "baseApi",
	baseQuery: fetchBaseQuery({
		baseUrl: process.env.NEXT_PUBLIC_SERVER_API_URL ?? "http://localhost:3000",
	}),
	tagTypes: ["Chat", "Info"],
	endpoints: () => ({}),
});
