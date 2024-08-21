# pylint: skip-file
import sqlite3
import datetime
import subprocess
import os
import contact_reader
import matplotlib.pyplot as plt
import datetime
import numpy as np

def get_chat_mapping(db_location):
    conn = sqlite3.connect(db_location)
    cursor = conn.cursor()

    cursor.execute("SELECT room_name, display_name FROM chat")
    result_set = cursor.fetchall()

    mapping = {room_name: display_name for room_name, display_name in result_set}

    conn.close()

    """SELECT
        chat.chat_identifier,
        chat.display_name,
        count(chat.chat_identifier) AS message_count
    FROM
        chat
        JOIN chat_message_join ON chat. "ROWID" = chat_message_join.chat_id
        JOIN message ON chat_message_join.message_id = message. "ROWID"
    GROUP BY
        chat.chat_identifier
    ORDER BY
        message_count DESC;"""

    return mapping

def all_data(db_location, max=None, start_date=datetime.datetime(2001, 1, 1), end_date=datetime.datetime.today(), smooth_hours=24):
    name_counts = count_messages_sent_by_number(db_location, max, start_date, end_date)

    for name, count in name_counts:
        print(f'{name} sent {count} texts between {start_date} and {end_date}')
        count_messages_by_person(db_location, name, start_date, end_date, smooth_hours)

def count_messages_by_person(db_location, name, start_date=datetime.datetime(2001, 1, 1), end_date=datetime.datetime.today(), smooth_hours=24):
    conn = sqlite3.connect(db_location)
    cursor = conn.cursor()

    mod_date = int(datetime.datetime(2001, 1, 1).timestamp()) * 1000000000
    
    start_date_int = int(start_date.timestamp())*1000000000
    new_start_date = int(start_date_int - mod_date)

    end_date_int = int(end_date.timestamp())*1000000000
    new_end_date = int(end_date_int - mod_date)

    number = contact_reader.get_number_for_name(name)
    possible_numbers = ','.join(map(lambda n: f'"{n}"',number))
    email = contact_reader.get_email_for_name(name)
    possible_emails = ','.join(map(lambda e: f'"{e}"',email))

    query = f"""
    SELECT message.date / 1000000000 / 60 / 60 * 60 * 60, COUNT(*)
    FROM message
    LEFT JOIN handle ON message.handle_id = handle.ROWID
    WHERE (handle.id IN ({possible_numbers}) or handle.id IN ({possible_emails})) AND message.date > {new_start_date} AND message.date < {new_end_date}
    GROUP BY message.date / 1000000000 / 60 / 60
    ORDER BY message.date / 1000000000 / 60 / 60
    """

    results = cursor.execute(query).fetchall()
    conn.close()

    if end_date is None:
        end_date = datetime.datetime.today()

    fig, ax = plt.subplots()
    results = dict(results)

    x = list(range(int(start_date.timestamp()), int(end_date.timestamp()), 60*60))
    y = list(map(lambda t: results[t - int(datetime.datetime(2001, 1, 1).timestamp())] if t - int(datetime.datetime(2001, 1, 1).timestamp()) in results else 0, x))
    #print(y)
    y = smooth(y, smooth_hours)
    #print(y)

    try:
        first_nonzero = y.index(next(filter(lambda yy: yy!=0, y)))
    except StopIteration:
        print(f"No date found for {name} with query:\n{query}")
        return [], []
    x = x[first_nonzero:]
    y = y[first_nonzero:]
    ax.plot(list(map(lambda t: datetime.datetime.fromtimestamp(t), x)), y)

    ax.set_ylabel('Texts Recieved Per Hour')
    ax.set_title(f'Texts From {name} Over Time')
    ax.tick_params(axis='x', labelrotation=90)
    ax.set_ylim(0)

    plt.show()

    return x, y

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return list(y_smooth)

def count_messages_sent_by_number(db_location, max=None, start_date=datetime.datetime(2001, 1, 1), end_date=datetime.datetime.today()):
    conn = sqlite3.connect(db_location)
    cursor = conn.cursor()

    mod_date = int(datetime.datetime(2001, 1, 1).timestamp()) * 1000000000
    
    start_date_int = int(start_date.timestamp())*1000000000
    new_start_date = int(start_date_int - mod_date)

    end_date_int = int(end_date.timestamp())*1000000000
    new_end_date = int(end_date_int - mod_date)

    query = f"""
    SELECT handle.id, COUNT(*)
    FROM message
    LEFT JOIN handle ON message.handle_id = handle.ROWID
    WHERE message.date > {new_start_date} AND message.date < {new_end_date}
    GROUP BY handle.id
    """

    results = cursor.execute(query).fetchall()
    named_results = {}
    for result in results:
        number, count = result
        name = contact_reader.get_name_for_number(number)
        if name is not None:
            if name in named_results:
                named_results[name] += count
            else:
                named_results[name] = count
    conn.close()

    sorted_results = sorted(named_results.items(), key=lambda r: r[1], reverse=True)
    if max is not None:
        sorted_results = sorted_results[:max]
    names = list(map(lambda r: r[0], sorted_results))
    counts = list(map(lambda r: r[1], sorted_results))

    fig, ax = plt.subplots()

    ax.bar(names, counts)

    ax.set_ylabel('Texts Recieved')
    title = f'Texts Recieved from Top {max} Texters'
    if max is None:
        title = 'Texts Recieved from Everyone'
    if start_date is not None:
        title += f' Since {start_date}'
    ax.set_title(title)
    ax.set_xticklabels(names, rotation=45, ha='right')

    plt.show()

    return sorted_results

def read_messages(db_location, n=None, self_number='Me', human_readable_date=True):
    conn = sqlite3.connect(db_location)
    cursor = conn.cursor()

    query = """
    SELECT message.ROWID, message.date, message.text, message.attributedBody, handle.id, message.is_from_me, message.cache_roomnames
    FROM message
    LEFT JOIN handle ON message.handle_id = handle.ROWID
    """

    if n is not None:
        query += f" ORDER BY message.date DESC LIMIT {n}"

    results = cursor.execute(query).fetchall()
    messages = []

    for result in results:
        rowid, date, text, attributed_body, handle_id, is_from_me, cache_roomname = result

        if handle_id is None:
            phone_number = self_number
        else:
            phone_number = handle_id

        if text is not None:
            body = text
        elif attributed_body is None:
            continue
        else:
            attributed_body = attributed_body.decode('utf-8', errors='replace')

            if "NSNumber" in str(attributed_body):
                attributed_body = str(attributed_body).split("NSNumber")[0]
                if "NSString" in attributed_body:
                    attributed_body = str(attributed_body).split("NSString")[1]
                    if "NSDictionary" in attributed_body:
                        attributed_body = str(attributed_body).split("NSDictionary")[0]
                        attributed_body = attributed_body[6:-12]
                        body = attributed_body

        if human_readable_date:
            date_string = '2001-01-01'
            mod_date = datetime.datetime.strptime(date_string, '%Y-%m-%d')
            unix_timestamp = int(mod_date.timestamp())*1000000000
            new_date = int((date+unix_timestamp)/1000000000)
            date = datetime.datetime.fromtimestamp(new_date).strftime("%Y-%m-%d %H:%M:%S")

        mapping = get_chat_mapping(db_location)

        try:
            mapped_name = mapping[cache_roomname]
        except:
            mapped_name = None

        messages.append(
            {"rowid": rowid, "date": date, "body": body, "phone_number": phone_number, "is_from_me": is_from_me,
             "cache_roomname": cache_roomname, 'group_chat_name' : mapped_name})

    conn.close()
    return messages


def print_messages(messages):
    for message in messages:
        print(f"RowID: {message['rowid']}")
        print(f"Body: {message['body']}")
        print(f"Phone Number: {message['phone_number']}")
        print(f"Is From Me: {message['is_from_me']}")
        print(f"Cache Roomname: {message['cache_roomname']}")
        print(f"Group Chat Name: {message['group_chat_name']}")
        print(f"Date: {message['date']}")
        print("\n")


def send_message(message, phone_number, group_chat = False):
    # creating a file - note: text files end up being sent as normal text messages, so this is handy for
    # sending messages that osascript doesn't like due to strange formatting or characters
    file_path = os.path.abspath('imessage_tmp.txt')

    with open(file_path, 'w') as f:
        f.write(message)

    if not group_chat:
        command = f'tell application "Messages" to send (read (POSIX file "{file_path}") as «class utf8») to buddy "{phone_number}"'
    else:
        command = f'tell application "Messages" to send (read (POSIX file "{file_path}") as «class utf8») to chat "{phone_number}"'

    subprocess.run(['osascript', '-e', command])

    print(f"Sent message to {phone_number}: {message}")