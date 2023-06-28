from gtts import gTTS
import os
from newspaper import Article
from bs4 import BeautifulSoup as bs
import requests
import sqlite3
from sqlite3 import Error

# DB funcs
def create_connection(path):
    """Creates connection to the SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return conn

def execute_query(conn, query, data_tuple=()):
    """Executes SQL query for creating/populating a table"""
    cursor = conn.cursor()
    try:
        cursor.execute(query, data_tuple)
        conn.commit()
        if query == create_books_table:
            print(f"Table was created successfully")
        elif query == insert_into_books_table:
            print(f"Values were inserted successfully")
        else:
            print(f"Query {query} executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

create_books_table = """ 
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_title TEXT NOT NULL UNIQUE ON CONFLICT FAIL,
    url_address TEXT NOT NULL,
    author_name TEXT NOT NULL);
"""
insert_into_books_table = """
INSERT INTO books 
    (book_title, url_address, author_name) 
    VALUES (?, ?, ?);
"""

def get_titles():
    """Executes SELECT query to show a book list"""
    with conn:
        cursor.execute("""SELECT id, book_title, author_name FROM books""")
        result = cursor.fetchall()
        for line in result:
            print(f'{line[0]}) {line[1]} (by {line[2]})')

def user_choise():
    """"Choose a book from list"""
    user_input = input('Please choose a book title inputting the number: ')
    try:
        with conn:
            cursor.execute("""SELECT * FROM books WHERE id = ?""", [int(user_input)])
            result = cursor.fetchone()
            user_chosen_book = result[1]
            book_url = result[2]
            book_author = result[3]
            print(f'You have chosen "{user_chosen_book}" written by {book_author}')
            return user_chosen_book, book_url, book_author
    except:
        print("Can't find the book in my database. Try again")
        return user_choise()


# parse funcs
def title_url_author_parser():
    """"Parse book title, url address and author name and insert into SQL Database"""
    for a in soup.findAll('a', href=True, title=True):
        book_title = a['title']
        url = a['href']
        try:
            author_name = bs(requests.get(url).content, "lxml").find('span', class_='entry-tags').text
        except:
            author_name = 'unknown author'
        execute_query(conn, insert_into_books_table, (book_title, url, author_name))
    print('The table is now complete')

def text_parser(book_info):
    """"Parse user chosen book summary"""
    book_summary = Article(book_info[1], language='en')
    book_summary.download()
    book_summary.parse()
    book_text = f'{book_info[0]}\nby {book_info[2]}\n\n{book_summary.text}'
    return book_text

# funcs for making text and audio files
def make_text(title, content):
    """"Make text file"""
    filename = f'Summaries/{title.lower().replace(" ", "_")}.txt'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding="utf-8") as text_file:
        text_file.write(content)
    print('The text file was successfully saved ')

def make_audio(title, content):
    """"Make audio file"""
    speech = gTTS(text=content, lang='en')
    filename = f'Audios/{title.lower().replace(" ", "_")}.mp3'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    print('Saving the audio file. Please wait for a while')
    speech.save(filename)
    print('The audio file was successfully saved')
    # os.system(filename)

# user input funcs
def choose_another_book():
    """"Let user choose another book from a list"""
    while True:
        user_answer = input('Would you like to pick another book? Input yes/no: ')
        if user_answer.lower() in ['нет', 'no']:
            print("Got it. I'm finishing up the program. Good luck!")
            break
        elif user_answer.lower() in ['да', 'yes']:
            main_process()
        else:
            return choose_another_book()

def text_or_audio(book_info, content):
    """"Ask user whether he/she wants to save text or audio file"""
    user_input = input('Save content to a text or audio file? Input text/audio: ')
    if user_input.lower() == 'текст' or user_input.lower() == 'text':
        make_text(book_info[0], content)
    elif user_input.lower() == 'аудио' or user_input.lower() == 'audio':
        make_audio(book_info[0], content)
    else:
        print("Didn't get it...")
        text_or_audio(book_info, content)
    choose_another_book()

def main_process():
    get_titles()
    book_info = user_choise()
    text_parser(book_info)
    content = text_parser(book_info)
    text_or_audio(book_info,content)

#************************************** starting the programm **********************************************************

site_url = 'https://www.booksummary.net/summaries/'
r = requests.get(site_url)
soup = bs(r.content, "lxml")
numbers_of_books = len(soup.findAll('a', href=True, title=True))
conn = create_connection('books.db')
cursor = conn.cursor()

try:
    is_books_table_empty = cursor.execute("""SELECT COUNT(*) FROM books; """).fetchall()
    if is_books_table_empty[0][0] == numbers_of_books:
        print('Ready to work')
        main_process()
    elif is_books_table_empty[0][0] < numbers_of_books:
        print('Table is not full. Starting to add data into the table...')
        title_url_author_parser()
        main_process()
except:
    print("Books table doesn't exist")
    execute_query(conn, create_books_table)
    title_url_author_parser()
    main_process()

conn.close()