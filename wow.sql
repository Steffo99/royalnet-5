SELECT *
FROM discord
LEFT JOIN (
  SELECT DISTINCT ON (ma.discord_id)
    ma.discord_id discord_id2,
    fs.fav_song fav_song2,
    ma.max_plays max_plays2
  FROM (
    SELECT
      discord_id,
      max(plays) max_plays
    FROM
      (
        SELECT
          playedmusic.enqueuer_id discord_id,
          playedmusic.filename    fav_song,
          count(*)                plays
        FROM playedmusic
        GROUP BY playedmusic.filename, playedmusic.enqueuer_id
        ORDER BY plays DESC
      ) play_counts
    GROUP BY discord_id
  ) ma
  INNER JOIN
  (
    SELECT
      playedmusic.enqueuer_id discord_id,
      playedmusic.filename    fav_song,
      count(*)                plays
    FROM playedmusic
    GROUP BY playedmusic.filename, playedmusic.enqueuer_id
    ORDER BY plays DESC
  ) fs ON fs.discord_id = ma.discord_id AND fs.plays = ma.max_plays
) fav_songs ON fav_songs.discord_id2 = discord.discord_id;