from .ytdlinfo import YtdlInfo


class YtdlFile:
    """Information about a youtube-dl downloaded file."""

    def __init__(self,
                 url: str,
                 info: YtdlInfo = None,
                 filename: str):
        ...




class OldYtdlFile:
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

