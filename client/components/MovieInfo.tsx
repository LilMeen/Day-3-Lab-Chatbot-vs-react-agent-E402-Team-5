import React from "react";
import styles from "./MovieInfo.module.css";

interface MovieScheduleEntity {
  theatre: string;
  day: string;
  time: string;
}

interface MovieInfoProps {
  movieInfo: {
    movieId: string;
    movieUrl: string;
    title?: string;
    total: number;
    schedules: MovieScheduleEntity[];
  } | null;
}

export default function MovieInfo({ movieInfo }: MovieInfoProps) {
  return (
    <aside className={styles.panel}>
      {movieInfo ? (
        <>
          <div className={styles.poster}>
            <div className={styles.posterPlaceholder}>🎬 Poster</div>
          </div>
          <h4 className={styles.movieTitle}>
            {movieInfo.title || movieInfo.movieId}
          </h4>
          <p className={styles.scheduleCount}>
            Tìm thấy <strong>{movieInfo.total}</strong> suất chiếu
          </p>

          <div className={styles.schedulesSection}>
            <h5 className={styles.scheduleHeader}>Lịch chiếu</h5>
            {movieInfo.schedules && movieInfo.schedules.length > 0 ? (
              <ul className={styles.schedulesList}>
                {movieInfo.schedules.map((s, idx) => (
                  <li key={idx} className={styles.scheduleItem}>
                    <div className={styles.theatreName}>{s.theatre}</div>
                    <div className={styles.scheduleTime}>
                      {s.day} — {s.time}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className={styles.noSchedules}>Không tìm thấy lịch chiếu</p>
            )}
          </div>

          <div className={styles.bookingSection}>
            <button className={styles.bookBtn}>Đặt vé</button>
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
