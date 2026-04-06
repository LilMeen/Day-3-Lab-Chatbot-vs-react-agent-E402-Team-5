import React, { useEffect, useMemo, useState } from "react";
import styles from "./MovieInfo.module.css";
import { useGetMovieSchedulesQuery } from "@/store/api/[module]/infoApi";

interface MovieScheduleEntity {
  theatre: string;
  day: string;
  time: string;
}

interface MovieInfoProps {
  movieIds: string[];
}

type ActiveTab = "description" | "schedule";

export default function MovieInfo({ movieIds }: MovieInfoProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [activeTab, setActiveTab] = useState<ActiveTab>("description");

  useEffect(() => {
    setActiveIndex(0);
    setActiveTab("description");
  }, [movieIds]);

  const hasMovies = movieIds.length > 0;
  const currentMovieId = hasMovies ? movieIds[activeIndex] : "";

  const {
    data: movieInfo,
    isFetching,
    isError,
  } = useGetMovieSchedulesQuery(
    { movieId: currentMovieId },
    { skip: !currentMovieId },
  );

  const scheduleByTheatre = useMemo(() => {
    if (!movieInfo?.schedules?.length) {
      return [] as Array<{ theatre: string; slots: string[] }>;
    }

    const grouped = new Map<string, string[]>();

    for (const item of movieInfo.schedules) {
      const key = item.theatre;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)?.push(`${item.day} • ${item.time}`);
    }

    return Array.from(grouped.entries()).map(([theatre, slots]) => ({ theatre, slots }));
  }, [movieInfo]);

  function goPrevMovie() {
    if (!hasMovies) return;
    setActiveIndex((prev) => (prev - 1 + movieIds.length) % movieIds.length);
  }

  function goNextMovie() {
    if (!hasMovies) return;
    setActiveIndex((prev) => (prev + 1) % movieIds.length);
  }

  return (
    <aside className={styles.panel}>
      {hasMovies ? (
        <>
          <div className={styles.posterWrap}>
            <button
              className={styles.navBtn}
              onClick={goPrevMovie}
              aria-label="Phim trước"
              type="button"
            >
              ←
            </button>

            <div className={styles.poster}>
              {movieInfo?.posterUrl ? (
                <img
                  src={movieInfo.posterUrl}
                  alt={movieInfo.title || currentMovieId}
                  className={styles.posterImage}
                />
              ) : (
                <div className={styles.posterPlaceholder}>🎬 Không có poster</div>
              )}
            </div>

            <button
              className={styles.navBtn}
              onClick={goNextMovie}
              aria-label="Phim tiếp theo"
              type="button"
            >
              →
            </button>
          </div>

          <h4 className={styles.movieTitle}>
            {movieInfo?.title || currentMovieId}
          </h4>
          <p className={styles.movieMeta}>
            Phim {activeIndex + 1}/{movieIds.length}
          </p>

          <div className={styles.tabSwitch}>
            <button
              type="button"
              className={`${styles.tabBtn} ${
                activeTab === "description" ? styles.tabBtnActive : ""
              }`}
              onClick={() => setActiveTab("description")}
            >
              Mô tả
            </button>
            <button
              type="button"
              className={`${styles.tabBtn} ${
                activeTab === "schedule" ? styles.tabBtnActive : ""
              }`}
              onClick={() => setActiveTab("schedule")}
            >
              Lịch chiếu
            </button>
          </div>

          <div className={styles.contentSection}>
            {isFetching ? <p className={styles.loading}>Đang tải thông tin phim...</p> : null}
            {isError ? (
              <p className={styles.error}>Không tải được thông tin phim, vui lòng thử lại.</p>
            ) : null}

            {!isFetching && !isError && activeTab === "description" ? (
              <>
                <p className={styles.descriptionText}>
                  {movieInfo?.description?.trim() ||
                    "Hiện chưa có mô tả chi tiết cho bộ phim này."}
                </p>
              </>
            ) : null}

            {!isFetching && !isError && activeTab === "schedule" ? (
              <>
                <p className={styles.scheduleCount}>
                  Tìm thấy <strong>{movieInfo?.total ?? 0}</strong> suất chiếu
                </p>
                {scheduleByTheatre.length > 0 ? (
                  <ul className={styles.schedulesList}>
                    {scheduleByTheatre.map((group) => (
                      <li key={group.theatre} className={styles.scheduleItem}>
                        <div className={styles.theatreName}>{group.theatre}</div>
                        <div className={styles.scheduleTime}>{group.slots.join(" | ")}</div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className={styles.noSchedules}>Không tìm thấy lịch chiếu</p>
                )}
              </>
            ) : null}
          </div>
        </>
      ) : (
        <div className={styles.empty}>
          <p>Hãy gõ tin nhắn để tìm phim 🎥</p>
        </div>
      )}
    </aside>
  );
}
