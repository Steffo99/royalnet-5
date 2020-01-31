from typing import *
import asyncio as aio
import datetime
import dateparser
import logging
import royalnet.utils as ru
import youtube_dl


log = logging.getLogger(__name__)


class YtdlInfo:
    """A wrapper around `youtube_dl <https://ytdl-org.github.io/youtube-dl/index.html>`_ extracted info."""

    _default_ytdl_args = {
        "quiet": True,  # Do not print messages to stdout.
        "noplaylist": True,  # Download single video instead of a playlist if in doubt.
        "no_warnings": True,  # Do not print out anything for warnings.
        "outtmpl": "./downloads/%(epoch)s-%(title)s-%(id)s.%(ext)s",  # Use the default outtmpl.
        "ignoreerrors": True  # Ignore unavailable videos
    }

    def __init__(self, info: Dict[str, Any]):
        """Create a :class:`YtdlInfo` from the dict returned by the :func:`YoutubeDL.extract_info` function.

        Warning:
            Does not download the info, to do that use :func:`.retrieve_for_url`."""
        self.id: Optional[str] = info.get("id")
        self.uploader: Optional[str] = info.get("uploader")
        self.uploader_id: Optional[str] = info.get("uploader_id")
        self.uploader_url: Optional[str] = info.get("uploader_url")
        self.channel_id: Optional[str] = info.get("channel_id")
        self.channel_url: Optional[str] = info.get("channel_url")
        self.upload_date: Optional[datetime.datetime] = dateparser.parse(ru.ytdldateformat(info.get("upload_date")))
        self.license: Optional[str] = info.get("license")
        self.creator: Optional[...] = info.get("creator")
        self.title: Optional[str] = info.get("title")
        self.alt_title: Optional[...] = info.get("alt_title")
        self.thumbnail: Optional[str] = info.get("thumbnail")
        self.description: Optional[str] = info.get("description")
        self.categories: Optional[List[str]] = info.get("categories")
        self.tags: Optional[List[str]] = info.get("tags")
        self.subtitles: Optional[Dict[str, List[Dict[str, str]]]] = info.get("subtitles")
        self.automatic_captions: Optional[dict] = info.get("automatic_captions")
        self.duration: Optional[datetime.timedelta] = datetime.timedelta(seconds=info.get("duration", 0))
        self.age_limit: Optional[int] = info.get("age_limit")
        self.annotations: Optional[...] = info.get("annotations")
        self.chapters: Optional[...] = info.get("chapters")
        self.webpage_url: Optional[str] = info.get("webpage_url")
        self.view_count: Optional[int] = info.get("view_count")
        self.like_count: Optional[int] = info.get("like_count")
        self.dislike_count: Optional[int] = info.get("dislike_count")
        self.average_rating: Optional[...] = info.get("average_rating")
        self.formats: Optional[list] = info.get("formats")
        self.is_live: Optional[bool] = info.get("is_live")
        self.start_time: Optional[float] = info.get("start_time")
        self.end_time: Optional[float] = info.get("end_time")
        self.series: Optional[str] = info.get("series")
        self.season_number: Optional[int] = info.get("season_number")
        self.episode_number: Optional[int] = info.get("episode_number")
        self.track: Optional[...] = info.get("track")
        self.artist: Optional[...] = info.get("artist")
        self.extractor: Optional[str] = info.get("extractor")
        self.webpage_url_basename: Optional[str] = info.get("webpage_url_basename")
        self.extractor_key: Optional[str] = info.get("extractor_key")
        self.playlist: Optional[str] = info.get("playlist")
        self.playlist_index: Optional[int] = info.get("playlist_index")
        self.thumbnails: Optional[List[Dict[str, str]]] = info.get("thumbnails")
        self.display_id: Optional[str] = info.get("display_id")
        self.requested_subtitles: Optional[...] = info.get("requested_subtitles")
        self.requested_formats: Optional[tuple] = info.get("requested_formats")
        self.format: Optional[str] = info.get("format")
        self.format_id: Optional[str] = info.get("format_id")
        self.width: Optional[int] = info.get("width")
        self.height: Optional[int] = info.get("height")
        self.resolution: Optional[...] = info.get("resolution")
        self.fps: Optional[int] = info.get("fps")
        self.vcodec: Optional[str] = info.get("vcodec")
        self.vbr: Optional[int] = info.get("vbr")
        self.stretched_ratio: Optional[...] = info.get("stretched_ratio")
        self.acodec: Optional[str] = info.get("acodec")
        self.abr: Optional[int] = info.get("abr")
        self.ext: Optional[str] = info.get("ext")
        # Additional custom information
        self.album: Optional[str] = None

    @classmethod
    async def from_url(cls, url, loop: Optional[aio.AbstractEventLoop] = None, **ytdl_args) -> List["YtdlInfo"]:
        """Fetch the info for an url through :class:`YoutubeDL`.

        Returns:
            A :class:`list` containing the infos for the requested videos."""
        if loop is None:
            loop: aio.AbstractEventLoop = aio.get_event_loop()
        # So many redundant options!
        log.debug(f"Fetching info: {url}")
        with youtube_dl.YoutubeDL({**cls._default_ytdl_args, **ytdl_args}) as ytdl:
            first_info = await ru.asyncify(ytdl.extract_info, loop=loop, url=url, download=False)
        # No video was found
        if first_info is None:
            return []
        # If it is a playlist, create multiple videos!
        if "entries" in first_info:
            if len(first_info["entries"]) == 0:
                return []
            if first_info["entries"][0] is None:
                return []
            log.debug(f"Found a playlist: {url}")
            second_info_list = []
            for second_info in first_info["entries"]:
                if second_info is None:
                    continue
                second_info_list.append(YtdlInfo(second_info))
            return second_info_list
        log.debug(f"Found a single video: {url}")
        return [YtdlInfo(first_info)]

    def __repr__(self):
        if self.title:
            return f"<YtdlInfo of '{self.title}'>"
        if self.webpage_url:
            return f"<YtdlInfo for '{self.webpage_url}'>"
        return f"<YtdlInfo id={self.id} ...>"

    def __str__(self):
        if self.title:
            return self.title
        if self.webpage_url:
            return self.webpage_url
        return self.id
