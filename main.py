# pylint: skip-file
import imessage_reader
import contact_reader
import datetime

DB_LOCATION = '/Users/arimirsky/Documents/iMessageReader/chat.db'

messages = imessage_reader.read_messages(DB_LOCATION, 100, human_readable_date=False)
imessage_reader.print_messages(messages)

#print(imessage_reader.count_messages_sent_by_number(DB_LOCATION, start_date=datetime.datetime.fromisoformat('2024-01-01')))
