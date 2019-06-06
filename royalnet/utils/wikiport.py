import os
import re
import datetime
import difflib
import uuid
from royalnet.database import Alchemy
from royalnet.database.tables import Royal, WikiPage, WikiRevision


if __name__ == "__main__":
    alchemy = Alchemy(os.environ["DB_PATH"], {Royal, WikiPage, WikiRevision})
    with open(r"data.txt") as file, alchemy.session_cm() as session:
        for line in file.readlines():
            match = re.match("^([^\t]+)\t([^\t]+)\t([tf])$", line)
            if match is None:
                continue
            title = match.group(1)
            content = match.group(2).replace(r"\r\n", "\n").replace(r"\t", "\t")
            page = alchemy.WikiPage(page_id=uuid.uuid4(),
                                    title=title,
                                    content=content)
            session.flush()
            revision = alchemy.WikiRevision(revision_id=uuid.uuid4(),
                                            page=page,
                                            author_id=31,  # Royalbot
                                            timestamp=datetime.datetime.now(),
                                            reason="Imported from 'four' database",
                                            diff="\n".join(difflib.unified_diff([], content.split("\n"))))
            session.add(page)
            session.add(revision)
            print(f"{title} done.")
        session.commit()
