import typing
import logging as _logging
from youtube_dl import YoutubeDL
from contextlib import contextmanager

log = _logging.getLogger(__name__)


class DownloaderError(Exception):
    pass


class YtdlFile:
    """A wrapper around a youtube_dl downloaded file."""
    def __init__(self, info: "YtdlInfo", outtmpl="%(title)s-%(id)s.%(ext)s", progress_hooks=None, **ytdl_args):
        if progress_hooks is None:
            progress_hooks = []
        self.info: "YtdlInfo" = info
        self.filename: str
        self.downloaded_bytes: typing.Optional[int]
        self.elapsed: typing.Optional[float]
        # Download the file
        ytdl = YoutubeDL({
            "logger": log,  # Log messages to a logging.Logger instance.
            "quiet": True,  # Do not print messages to stdout.
            "noplaylist": True,  # Download single video instead of a playlist if in doubt.
            "no_warnings": True,  # Do not print out anything for warnings.
            "outtmpl": outtmpl,
            "progress_hooks": [self._progress_hook, *progress_hooks],
            **ytdl_args
        })
        ytdl.download([self.info.webpage_url])

    def _progress_hook(self, data: dict):
        # Check the status
        status = data.get("status")
        # Ignore unknown values
        if status not in ["downloading", "error", "finished"]:
            return
        # If the download is finished, set the filename
        if status == "finished":
            # Filename is always present
            self.filename = data["filename"]
            self.downloaded_bytes = data.get("downloaded_bytes")
            self.elapsed = data.get("elapsed")

    @staticmethod
    def create_from_url(url, outtmpl="%(title)s-%(id)s.%(ext)s", progress_hooks=None, **ytdl_args) -> typing.List["YtdlFile"]:
        info_list = YtdlInfo.create_from_url(url)
        return [info.download(outtmpl, progress_hooks, **ytdl_args) for info in info_list]


class YtdlInfo:
    """A wrapper around youtube_dl extracted info."""

    def __init__(self, info):
        self.id: typing.Optional[str] = info.get("id")
        self.uploader: typing.Optional[str] = info.get("uploader")
        self.uploader_id: typing.Optional[str] = info.get("uploader_id")
        self.uploader_url: typing.Optional[str] = info.get("uploader_url")
        self.channel_id: typing.Optional[str] = info.get("channel_id")
        self.channel_url: typing.Optional[str] = info.get("channel_url")
        self.upload_date: typing.Optional[str] = info.get("upload_date")
        self.license: typing.Optional[str] = info.get("license")
        self.creator: typing.Optional[...] = info.get("creator")
        self.title: typing.Optional[str] = info.get("title")
        self.alt_title: typing.Optional[...] = info.get("alt_title")
        self.thumbnail: typing.Optional[str] = info.get("thumbnail")
        self.description: typing.Optional[str] = info.get("description")
        self.categories: typing.Optional[typing.List[str]] = info.get("categories")
        self.tags: typing.Optional[typing.List[str]] = info.get("tags")
        self.subtitles: typing.Optional[dict] = info.get("subtitles")
        self.automatic_captions: typing.Optional[dict] = info.get("automatic_captions")
        self.duration: typing.Optional[int] = info.get("duration")
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
        self.start_time: typing.Optional[...] = info.get("start_time")
        self.end_time: typing.Optional[...] = info.get("end_time")
        self.series: typing.Optional[...] = info.get("series")
        self.season_number: typing.Optional[...] = info.get("season_number")
        self.episode_number: typing.Optional[...] = info.get("episode_number")
        self.track: typing.Optional[...] = info.get("track")
        self.artist: typing.Optional[...] = info.get("artist")
        self.extractor: typing.Optional[str] = info.get("extractor")
        self.webpage_url_basename: typing.Optional[str] = info.get("webpage_url_basename")
        self.extractor_key: typing.Optional[str] = info.get("extractor_key")
        self.playlist: typing.Optional[...] = info.get("playlist")
        self.playlist_index: typing.Optional[...] = info.get("playlist_index")
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
        self.vbr: typing.Optional[...] = info.get("vbr")
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

    def download(self, outtmpl="%(title)s-%(id)s.%(ext)s", progress_hooks=None, **ytdl_args) -> YtdlFile:
        return YtdlFile(self, outtmpl, progress_hooks=progress_hooks)

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
