all_music_query = """SELECT
  discord.royal_id,
  discord.discord_id,
  discord.name,
  discord.discriminator,
  discord.avatar_hex,
  fav_songs.fav_song,
  fav_songs.max_plays,
  last_songs.last_song,
  last_songs.last_play_time
FROM discord
LEFT JOIN (
  SELECT DISTINCT ON (ma.discord_id)
    ma.discord_id discord_id,
    fs.fav_song fav_song,
    ma.max_plays max_plays
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
) fav_songs ON fav_songs.discord_id = discord.discord_id
LEFT JOIN
(
  SELECT DISTINCT ON (playedmusic.enqueuer_id)
    playedmusic.enqueuer_id discord_id,
    playedmusic.filename    last_song,
    last_play_times.last_play_time
  FROM playedmusic
  JOIN (
      SELECT
        playedmusic.enqueuer_id discord_id,
        max(playedmusic.timestamp) last_play_time
      FROM playedmusic
      GROUP BY playedmusic.enqueuer_id
  ) last_play_times ON playedmusic.timestamp = last_play_times.last_play_time
) last_songs ON last_songs.discord_id = discord.discord_id;"""


# TODO: can and should be optimized, but I'm too lazy for that
one_music_query = """SELECT
  discord.royal_id,
  discord.discord_id,
  discord.name,
  discord.discriminator,
  discord.avatar_hex,
  fav_songs.fav_song,
  fav_songs.max_plays,
  last_songs.last_song,
  last_songs.last_play_time
FROM discord
LEFT JOIN (
  SELECT DISTINCT ON (ma.discord_id)
    ma.discord_id discord_id,
    fs.fav_song fav_song,
    ma.max_plays max_plays
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
) fav_songs ON fav_songs.discord_id = discord.discord_id
LEFT JOIN
(
  SELECT DISTINCT ON (playedmusic.enqueuer_id)
    playedmusic.enqueuer_id discord_id,
    playedmusic.filename    last_song,
    last_play_times.last_play_time
  FROM playedmusic
  JOIN (
      SELECT
        playedmusic.enqueuer_id discord_id,
        max(playedmusic.timestamp) last_play_time
      FROM playedmusic
      GROUP BY playedmusic.enqueuer_id
  ) last_play_times ON playedmusic.timestamp = last_play_times.last_play_time
) last_songs ON last_songs.discord_id = discord.discord_id
WHERE discord.royal_id = :royal;"""

top_songs = """SELECT playedmusic.filename, COUNT(*) c 
FROM playedmusic 
GROUP BY playedmusic.filename 
ORDER BY c DESC;"""

single_top_songs = """SELECT playedmusic.filename, COUNT(*) c 
FROM playedmusic 
WHERE playedmusic.enqueuer_id = :discordid 
GROUP BY playedmusic.filename 
ORDER BY c DESC;"""

vote_answers = """SELECT * 
FROM telegram 
LEFT JOIN 
  (
  SELECT voteanswer.question_id, voteanswer.user_id, voteanswer.choice 
  FROM votequestion 
  JOIN voteanswer 
  ON votequestion.id = voteanswer.question_id 
  WHERE votequestion.message_id = :message_id
  ) answer ON telegram.telegram_id = answer.user_id 
ORDER BY answer.choice;"""

activity_by_hour = """SELECT AVG(discord_members_online) online_members_avg,
       AVG(discord_members_ingame) ingame_members_avg,
       AVG(discord_members_cv) cv_members_avg,
       AVG(discord_channels_used) channels_used_avg,
       AVG(discord_cv) cv_avg,
       extract(hour from timestamp) h
FROM (
            SELECT *,
                   extract(month from timestamp) month_
            FROM activityreports
     ) withmonth
WHERE withmonth.month_ = :current_month
GROUP BY h
ORDER BY h;"""