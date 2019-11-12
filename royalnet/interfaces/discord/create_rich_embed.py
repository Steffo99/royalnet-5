from discord import Embed, Colour
from discord.embeds import EmptyEmbed
from royalnet.bard import YtdlInfo


def create_rich_embed(yi: YtdlInfo) -> Embed:
    """Return this info as a :py:class:`discord.Embed`."""
    colors = {
        "youtube": 0xCC0000,
        "soundcloud": 0xFF5400,
        "Clyp": 0x3DBEB3,
        "Bandcamp": 0x1DA0C3,
    }
    embed = Embed(title=yi.title,
                  colour=Colour(colors.get(yi.extractor, 0x4F545C)),
                  url=yi.webpage_url if (yi.webpage_url and yi.webpage_url.startswith("http")) else EmptyEmbed)
    if yi.thumbnail:
        embed.set_thumbnail(url=yi.thumbnail)
    if yi.uploader:
        embed.set_author(name=yi.uploader,
                         url=yi.uploader_url if yi.uploader_url is not None else EmptyEmbed)
    # embed.set_footer(text="Source: youtube-dl", icon_url="https://i.imgur.com/TSvSRYn.png")
    if yi.duration:
        embed.add_field(name="Duration", value=str(yi.duration), inline=True)
    if yi.upload_date:
        embed.add_field(name="Published on", value=yi.upload_date.strftime("%d %b %Y"), inline=True)
    return embed
