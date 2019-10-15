import typing
import datetime
import dateparser
import youtube_dl
import discord
import royalnet.utils as u


class YtdlInfo:
    """A wrapper around youtube_dl extracted info."""

    _default_ytdl_args = {
        "quiet": True,  # Do not print messages to stdout.
        "noplaylist": True,  # Download single video instead of a playlist if in doubt.
        "no_warnings": True,  # Do not print out anything for warnings.
        "outtmpl": "%(title)s-%(id)s.%(ext)s",  # Use the default outtmpl.
        "ignoreerrors": True  # Ignore unavailable videos
    }

    def __init__(self, info: typing.Dict[str, typing.Any]):
        """Create a YtdlInfo from the dict returned by the :py:func:`youtube_dl.YoutubeDL.extract_info` function.

        Warning:
            Does not download the info, for that use :py:func:`royalnet.audio.YtdlInfo.retrieve_for_url`."""
        self.id: typing.Optional[str] = info.get("id")
        self.uploader: typing.Optional[str] = info.get("uploader")
        self.uploader_id: typing.Optional[str] = info.get("uploader_id")
        self.uploader_url: typing.Optional[str] = info.get("uploader_url")
        self.channel_id: typing.Optional[str] = info.get("channel_id")
        self.channel_url: typing.Optional[str] = info.get("channel_url")
        self.upload_date: typing.Optional[datetime.datetime] = dateparser.parse(u.ytdldateformat(info.get("upload_date")))
        self.license: typing.Optional[str] = info.get("license")
        self.creator: typing.Optional[...] = info.get("creator")
        self.title: typing.Optional[str] = info.get("title")
        self.alt_title: typing.Optional[...] = info.get("alt_title")
        self.thumbnail: typing.Optional[str] = info.get("thumbnail")
        self.description: typing.Optional[str] = info.get("description")
        self.categories: typing.Optional[typing.List[str]] = info.get("categories")
        self.tags: typing.Optional[typing.List[str]] = info.get("tags")
        self.subtitles: typing.Optional[typing.Dict[str, typing.List[typing.Dict[str, str]]]] = info.get("subtitles")
        self.automatic_captions: typing.Optional[dict] = info.get("automatic_captions")
        self.duration: typing.Optional[datetime.timedelta] = datetime.timedelta(seconds=info.get("duration", 0))
        self.age_limit: typing.Optional[int] = info.get("age_limit")
        self.annotations: typing.Optional[...] = info.get("annotations")
        self.chapters: typing.Optional[...] = info.get("chapters")
        self.webpage_url: typing.Optional[str] = info.get("webpage_url")
        self.view_count: typing.Optional[int] = info.get("view_count")
        self.like_count: typing.Optional[int] = info.get("like_count")
        self.dislike_count: typing.Optional[int] = info.get("dislike_count")
        self.average_rating: typing.Optional[...] = info.get("average_rating")
        self.formats: typing.Optional[list] = info.get("formats")
        self.is_live: typing.Optional[bool] = info.get("is_live")
        self.start_time: typing.Optional[float] = info.get("start_time")
        self.end_time: typing.Optional[float] = info.get("end_time")
        self.series: typing.Optional[str] = info.get("series")
        self.season_number: typing.Optional[int] = info.get("season_number")
        self.episode_number: typing.Optional[int] = info.get("episode_number")
        self.track: typing.Optional[...] = info.get("track")
        self.artist: typing.Optional[...] = info.get("artist")
        self.extractor: typing.Optional[str] = info.get("extractor")
        self.webpage_url_basename: typing.Optional[str] = info.get("webpage_url_basename")
        self.extractor_key: typing.Optional[str] = info.get("extractor_key")
        self.playlist: typing.Optional[str] = info.get("playlist")
        self.playlist_index: typing.Optional[int] = info.get("playlist_index")
        self.thumbnails: typing.Optional[typing.List[typing.Dict[str, str]]] = info.get("thumbnails")
        self.display_id: typing.Optional[str] = info.get("display_id")
        self.requested_subtitles: typing.Optional[...] = info.get("requested_subtitles")
        self.requested_formats: typing.Optional[tuple] = info.get("requested_formats")
        self.format: typing.Optional[str] = info.get("format")
        self.format_id: typing.Optional[str] = info.get("format_id")
        self.width: typing.Optional[int] = info.get("width")
        self.height: typing.Optional[int] = info.get("height")
        self.resolution: typing.Optional[...] = info.get("resolution")
        self.fps: typing.Optional[int] = info.get("fps")
        self.vcodec: typing.Optional[str] = info.get("vcodec")
        self.vbr: typing.Optional[int] = info.get("vbr")
        self.stretched_ratio: typing.Optional[...] = info.get("stretched_ratio")
        self.acodec: typing.Optional[str] = info.get("acodec")
        self.abr: typing.Optional[int] = info.get("abr")
        self.ext: typing.Optional[str] = info.get("ext")

    @classmethod
    def retrieve_for_url(cls, url, **ytdl_args) -> typing.List["YtdlInfo"]:
        """Fetch the info for an url through YoutubeDL.

        Returns:
            A :py:class:`list` containing the infos for the requested videos."""
        # So many redundant options!
        ytdl = youtube_dl.YoutubeDL({**cls._default_ytdl_args, **ytdl_args})
        first_info = ytdl.extract_info(url=url, download=False)
        # No video was found
        if first_info is None:
            return []
        # If it is a playlist, create multiple videos!
        if "entries" in first_info and first_info["entries"][0] is not None:
            second_info_list = []
            for second_info in first_info["entries"]:
                if second_info is None:
                    continue
                second_info_list.append(YtdlInfo(second_info))
            return second_info_list
        return [YtdlInfo(first_info)]

    def to_discord_embed(self) -> discord.Embed:
        """Return this info as a :py:class:`discord.Embed`."""
        colors = {
            "youtube": 0xCC0000,
            "soundcloud": 0xFF5400,
            "Clyp": 0x3DBEB3,
            "Bandcamp": 0x1DA0C3,
            "Peertube": 0x0A193C,
        }
        embed = discord.Embed(title=self.title,
                              colour=discord.Colour(colors.get(self.extractor, 0x4F545C)),
                              url=self.webpage_url if self.webpage_url is not None and self.webpage_url.startswith("http") else discord.embeds.EmptyEmbed)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        if self.uploader:
            embed.set_author(name=self.uploader, url=self.uploader_url if self.uploader_url is not None else discord.embeds.EmptyEmbed)
        # embed.set_footer(text="Source: youtube-dl", icon_url="https://i.imgur.com/TSvSRYn.png")
        if self.duration:
            embed.add_field(name="Duration", value=str(self.duration), inline=True)
        if self.upload_date:
            embed.add_field(name="Published on", value=self.upload_date.strftime("%d %b %Y"), inline=True)
        return embed

    def __repr__(self):
        if self.title:
            return f"<YtdlInfo of {self.title}>"
        if self.webpage_url:
            return f"<YtdlInfo for {self.webpage_url}>"
        return f"<YtdlInfo id={self.id} ...>"

    def __str__(self):
        """Return the video name."""
        if self.title:
            return self.title
        if self.webpage_url:
            return self.webpage_url
        return self.id
