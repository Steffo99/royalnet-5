import typing
import logging as _logging
import discord
import os
import dateparser
import datetime
from youtube_dl import YoutubeDL
from ..utils import ytdldateformat

log = _logging.getLogger(__name__)


class DownloaderError(Exception):
    pass


class InterruptDownload(DownloaderError):
    """Raised from a progress_hook to interrupt the video download."""


class YtdlFile:
    """A wrapper around a youtube_dl downloaded file."""

    ytdl_args = {
        "logger": log,  # Log messages to a logging.Logger instance.
        "quiet": True,  # Do not print messages to stdout.
        "noplaylist": True,  # Download single video instead of a playlist if in doubt.
        "no_warnings": True,  # Do not print out anything for warnings.
    }

    def __init__(self, info: "YtdlInfo", outtmpl="%(title)s-%(id)s.%(ext)s", **ytdl_args):
        self.info: "YtdlInfo" = info
        self.video_filename: str
        # Create a local args copy
        ytdl_args["outtmpl"] = outtmpl
        self.ytdl_args = {**self.ytdl_args, **ytdl_args}
        # Create the ytdl
        ytdl = YoutubeDL(ytdl_args)
        # Find the file name
        self.video_filename = ytdl.prepare_filename(self.info.__dict__)
        # Download the file
        ytdl.download([self.info.webpage_url])
        # Final checks
        assert os.path.exists(self.video_filename)

    def __repr__(self):
        return f"<YtdlFile {self.video_filename}>"

    @staticmethod
    def create_from_url(url, outtmpl="%(title)s-%(id)s.%(ext)s", **ytdl_args) -> typing.List["YtdlFile"]:
        """Download the videos at the specified url.
        
        Parameters:
            url: The url to download the videos from.
            outtmpl: The filename that the downloaded videos are going to have. The name can be formatted according to the `outtmpl documentation <https://github.com/ytdl-org/youtube-dl/blob/master/README.md#output-template>`_.
            ytdl_args: Other arguments to be passed to the YoutubeDL object.
        
        Returns:
            A :py:class:`list` of YtdlFiles."""
        info_list = YtdlInfo.create_from_url(url)
        return [info.download(outtmpl, **ytdl_args) for info in info_list]

    def _stop_download(self):
        """I have no clue of what this does, or why is it here. Possibly remove it?
        
        Raises:
            InterruptDownload: ...uhhh, always?"""
        raise InterruptDownload()

    def delete_video_file(self):
        """Delete the file located at ``self.video_filename``.
        
        Note:
            No checks are done when deleting, so it may try to delete a non-existing file and raise an exception or do some other weird stuff with weird filenames."""
        os.remove(self.video_filename)


class YtdlInfo:
    """A wrapper around youtube_dl extracted info."""

    def __init__(self, info: typing.Dict[str, typing.Any]):
        """Create a YtdlInfo from the dict returned by the :py:func:`youtube_dl.YoutubeDL.extract_info` function.

        Warning:
            Does not download the info, for that use :py:func:`royalnet.audio.YtdlInfo.create_from_url`."""
        self.id: typing.Optional[str] = info.get("id")
        self.uploader: typing.Optional[str] = info.get("uploader")
        self.uploader_id: typing.Optional[str] = info.get("uploader_id")
        self.uploader_url: typing.Optional[str] = info.get("uploader_url")
        self.channel_id: typing.Optional[str] = info.get("channel_id")
        self.channel_url: typing.Optional[str] = info.get("channel_url")
        self.upload_date: typing.Optional[datetime.datetime] = dateparser.parse(ytdldateformat(info.get("upload_date")))
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

    @staticmethod
    def create_from_url(url, **ytdl_args) -> typing.List["YtdlInfo"]:
        # So many redundant options!
        ytdl = YoutubeDL({
            "logger": log,  # Log messages to a logging.Logger instance.
            "quiet": True,  # Do not print messages to stdout.
            "noplaylist": True,  # Download single video instead of a playlist if in doubt.
            "no_warnings": True,  # Do not print out anything for warnings.
            **ytdl_args
        })
        first_info = ytdl.extract_info(url=url, download=False)
        # If it is a playlist, create multiple videos!
        if "entries" in first_info:
            return [YtdlInfo(second_info) for second_info in first_info["entries"]]
        return [YtdlInfo(first_info)]

    def download(self, outtmpl="%(title)s-%(id)s.%(ext)s", **ytdl_args) -> YtdlFile:
        return YtdlFile(self, outtmpl, **ytdl_args)

    def to_discord_embed(self) -> discord.Embed:
        embed = discord.Embed(title=self.title,
                              colour=discord.Colour(0xcc0000),
                              url=self.webpage_url)
        embed.set_thumbnail(
            url=self.thumbnail)
        embed.set_author(name=self.uploader, url=self.uploader_url)
        embed.set_footer(text="Source: youtube-dl", icon_url="https://i.imgur.com/TSvSRYn.png")
        embed.add_field(name="Duration", value=str(self.duration), inline=True)
        embed.add_field(name="Published on", value=self.upload_date.strftime("%d %b %Y"), inline=True)
        return embed

    def __repr__(self):
        if self.title:
            return f"<YtdlInfo of {self.title}>"
        if self.webpage_url:
            return f"<YtdlInfo for {self.webpage_url}>"
        return f"<YtdlInfo id={self.id} ...>"

    def __str__(self):
        if self.title:
            return self.title
        if self.webpage_url:
            return self.webpage_url
        return self.id
