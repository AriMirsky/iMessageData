# pylint: skip-file
import plistlib
import os
import getpass

def get_main_dir_path():
    return "/Users/" + getpass.getuser() + "/Library/Application Support/AddressBook/Sources/"

def get_source_subdirs():
    main_dir_path = get_main_dir_path()
    main_dir = os.fsencode(main_dir_path)
    sub_dirs = []
    for file in os.listdir(main_dir):
        filename = os.fsdecode(file)
        if not filename.endswith(".DS_Store"):
            sub_dirs.append(os.path.join(main_dir_path, filename))
    return sub_dirs

def get_contact_plist(path):
    try:
        contact_file = open(path, "rb")
        pl = plistlib.load(contact_file)
        return pl
    except PermissionError:
        print("[PermissionError] Unable to open file")
        return None
    except:
        print("[Unknown Error] Unable to generate plist object")
        return None
    
def get_contact_plist_for_name(name):
    first_name = name.split(" ")[0]
    last_name = name.split(" ")[1]
    
    dirs = get_source_subdirs()

    pls = []
    
    for dir in dirs:
        dir_path = dir + "/Metadata/"
        if os.path.isdir(dir_path): # because some folders may not contain the Metadata folder
            directory = os.fsencode(dir_path)
            #print(dir_path, "is a dir")
            for file in os.listdir(directory):
                filename = os.fsdecode(file)
                if filename.endswith(".abcdp"): 
                    contact_filepath = os.path.join(dir_path, filename)
                    contact_pl = get_contact_plist(contact_filepath)
                    if contact_pl is None:
                        print("[Err] Unable to get contact plist for", name)
                        return []
                    try:
                        if contact_pl['First'] == first_name and contact_pl['Last'] == last_name:
                            pls.append(contact_pl)
                    except:
                        ""
                        #print("[debug]No first or last name found for contact at path", contact_filepath)
    return pls

def get_contact_plist_for_number(number):
    dirs = get_source_subdirs()
    
    for dir in dirs:
        dir_path = dir + "/Metadata/"
        if os.path.isdir(dir_path): # because some folders may not contain the Metadata folder
            directory = os.fsencode(dir_path)
            #print(dir_path, "is a dir")
            for file in os.listdir(directory):
                filename = os.fsdecode(file)
                if filename.endswith(".abcdp"): 
                    contact_filepath = os.path.join(dir_path, filename)
                    contact_pl = get_contact_plist(contact_filepath)
                    if contact_pl is None:
                        print("[Err] Unable to get contact plist for", number)
                        return None
                    try:
                        if number in contact_pl['Phone']['values']:
                            return contact_pl
                    except:
                        ""
                        #print("[debug]No first or last name found for contact at path", contact_filepath)
    return None

def get_name_from_plist(pl):
    return f"{pl['First'] + ' ' if 'First' in pl else ''}{pl['Last'] if 'Last' in pl else ''}"

def get_name_for_number_string(number):
    pl = get_contact_plist_for_number(number)
    if pl is not None:
        try:
            return get_name_from_plist(pl)
        except:
            print("[Error] Contact does not contain name information")

def get_possible_numbers(number):
    base_number = []
    if len(number) == 10:
        base_number = number[:3], number[3:6], number[6:]
    elif len(number) == 11:
        # 1xxxyyyzzzz
        base_number = number[1:4], number[4:7], number[7:]
    elif len(number) == 12:
        # +1xxxyyyzzzz
        base_number = number[2:5], number[5:8], number[8:]
    elif len(number) == 14:
        # (xxx) yyy-zzzz
        base_number = number[1:4], number[6:9], number[10:]
    elif len(number) == 16:
        # 1 (xxx) yyy-zzzz
        base_number = number[3:6], number[8:11], number[12:]
    elif len(number) == 17:
        # +1 (xxx) yyy-zzzz
        base_number = number[4:7], number[9:12], number[13:]
    else:
        #print(f"{number} is not a phone number")
        return []

    possible_numbers = [
        f'{base_number[0]}{base_number[1]}{base_number[2]}',
        f'1{base_number[0]}{base_number[1]}{base_number[2]}',
        f'+1{base_number[0]}{base_number[1]}{base_number[2]}',
        f'({base_number[0]}) {base_number[1]}-{base_number[2]}',
        f'1 ({base_number[0]}) {base_number[1]}-{base_number[2]}',
        f'+1 ({base_number[0]}) {base_number[1]}-{base_number[2]}',
    ]

    return possible_numbers

def get_contact_plist_for_email(email):
    dirs = get_source_subdirs()
    
    for dir in dirs:
        dir_path = dir + "/Metadata/"
        if os.path.isdir(dir_path): # because some folders may not contain the Metadata folder
            directory = os.fsencode(dir_path)
            #print(dir_path, "is a dir")
            for file in os.listdir(directory):
                filename = os.fsdecode(file)
                if filename.endswith(".abcdp"): 
                    contact_filepath = os.path.join(dir_path, filename)
                    contact_pl = get_contact_plist(contact_filepath)
                    if contact_pl is None:
                        print("[Err] Unable to get contact plist for", email)
                        return None
                    try:
                        if email in contact_pl['Email']['values']:
                            return contact_pl
                    except:
                        ""
                        #print("[debug]No first or last name found for contact at path", contact_filepath)
    return None

def get_name_for_email(email):
    pl = get_contact_plist_for_email(email)
    if pl is not None:
        try:
            return get_name_from_plist(pl)
        except:
            print("[Error] Contact does not contain name information")

def get_name_for_number(number):
    if number is None:
        return None
    
    possible_numbers = get_possible_numbers(number)

    for attempted_number in possible_numbers:
        attempted_name = get_name_for_number_string(attempted_number)
        if attempted_name is not None:
            print(f'{number} is {attempted_name}')
            return attempted_name
    
    attempted_name = get_name_for_email(number)
    if attempted_name is not None:
        print(f'{number} is {attempted_name}')
        return attempted_name
        
    print("[Err] Unable to get name for", number)
    return None

def get_number_for_name(name):
    pls = get_contact_plist_for_name(name)
    all_possible_numbers = []
    for pl in pls:
        if pl is not None:
            try:
                for number in pl['Phone']['values']:
                    all_possible_numbers.extend(get_possible_numbers(number))
            except:
                pass
    if all_possible_numbers == []:
        print("Phone number not found for", name)
    return all_possible_numbers
    
def get_email_for_name(name):
    pls = get_contact_plist_for_name(name)
    all_possible_emails = []
    for pl in pls:
        if pl is not None:
            try:
                for emails in pl['Email']['values']:
                    all_possible_emails.append(emails)
            except:
                pass
    if all_possible_emails == []:
        print("Email not found for", name)
    return all_possible_emails

def get_all_contacts():
    dirs = get_source_subdirs()

    contacts = []
    for dir in dirs:
        dir += "/Metadata/"
        if os.path.isdir(dir): # because some folders may not contain the Metadata folder
            for file in os.listdir(dir):
                filename = os.fsdecode(file)
                if not filename.endswith(".DS_Store"):
                    contact = get_contact_plist(os.path.join(dir, filename))
                    if contact is not None:
                        contacts.append(contact)
    return contacts

def print_all_contacts():
    contacts = get_all_contacts()

    for contact in contacts:
        try:
            print("First name:", contact['First'])
        except:
            print("First name: (null)")
            
        try:
            print("Last name:", contact['Last'])
        except:
            print("Last name: (null)")
        
        try:
            number = ''.join(filter(lambda x: x.isdigit(), contact['Phone']['values'][0]))
            print("Phone number:", number)
        except:
            print("Phone number: (null)")
            
        try:
            if len(contact['Email']['values']) > 0:
                print("Email: ", end="")
            for i in range(0, len(contact['Email']['values'])):
                if i == 0 :
                    print(contact['Email']['values'][i], end="")
                else:
                    print(",", contact['Email']['values'][i], end="")
            print()
        except:
            print("Email: (null)")    
            
        try:
            print("Street:", contact['Address']['values'][0]['Street'])
        except:
            ""
        
        try:
            print("State:", contact['Address']['values'][0]['State'])
        except:
            ""
        
        try:
            print("City:", contact['Address']['values'][0]['City'])
        except:
            ""
            
        try:
            print("Zip:", contact['Address']['values'][0]['Zip'])
        except:
            ""
            
        print()