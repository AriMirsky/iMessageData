# pylint: skip-file
import imessage_reader
import datetime
import os

DB_LOCATION = f'{os.path.expanduser("~")}/Library/Messages/chat.db'

imessage_reader.all_data(DB_LOCATION, smooth_hours=24*30)