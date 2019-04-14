import typing
import logging as _logging
from youtube_dl import YoutubeDL

log = _logging.getLogger(__name__)


class DownloaderError(Exception):
    pass


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
        self.license: typing.Optional[...] = info.get("license")
        self.creator: typing.Optional[...] = info.get("creator")
        self.title: typing.Optional[str] = info.get("title")
        self.alt_title: typing.Optional[...] = info.get("alt_title")
        self.thumbnail: typing.Optional[str] = info.get("thumbnail")
        self.description: typing.Optional[str] = info.get("description")
        self.categories: typing.Optional[list] = info.get("categories")
        self.tags: typing.Optional[list] = info.get("tags")
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
        self.is_live: typing.Optional[...] = info.get("is_live")
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
        self.thumbnails: typing.Optional[list] = info.get("thumbnails")
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
    def create_from_url(url) -> typing.List["YtdlInfo"]:
        # So many redundant options!
        ytdl = YoutubeDL({
            "logger": log,  # Log messages to a logging.Logger instance.
            "quiet": True,  # Do not print messages to stdout.
            "noplaylist": True,  # Download single video instead of a playlist if in doubt.
            "no_warnings": True  # Do not print out anything for warnings."
        })
        first_info = ytdl.extract_info(url=url, download=False)
        # If it is a playlist, create multiple videos!
        if "entries" in first_info:
            return [YtdlInfo(second_info) for second_info in first_info["entries"]]
        return [YtdlInfo(first_info)]
