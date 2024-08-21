# pylint: skip-file
import imessage_reader
import contact_reader
import datetime

DB_LOCATION = '/Users/arimirsky/Documents/iMessageReader/chat.db'

imessage_reader.all_data(DB_LOCATION, smooth_hours=24*30)