
"""
Коннектор для sqlite3
для записи имен пользователей
и их пожеланий

"""

import logging

def inadmissible_symbol(stri):
    count = 0
    symbols = ""
    for i in stri:
        if not i.isalpha() and not i == ' ':
            count += 1
            symbols += i

    if count != 0:
        return f'Недопустимых символов {count} :  {symbols}  '
    else:
        return False


import sqlite3

DATABASE_URL = "deepflower.db"
TB_USERS = "users"
TB_EVENTS = "events"

class SqliteDb(object):

    def __init__(self, db_path=DATABASE_URL):
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()


    def create_events_table(self,table_name=TB_EVENTS):
        with self.connection:
            try:
                self.cursor.execute("CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY AUTOINCREMENT, tgid INTEGER, event_id INTEGER, add_date TEXT, start_point TEXT,session INTEGER, prenotice BOOLEAN, paynotice BOOLEAN)".format(table_name))
                return True
            except Exception as exc:
                logging.error(f"database {exc.args}")

    def insert_event(self, tgid, event_id, start_point, add_date, prenotice=False, paynotice=False, session=None, table_name=TB_EVENTS):
        with self.connection:
            try:
                self.cursor.execute(f"INSERT INTO {table_name} (tgid, event_id , add_date, start_point, session, prenotice, paynotice) VALUES ('{tgid}','{event_id}','{add_date}', '{start_point}','{session}','{prenotice}', '{paynotice}')")
            except Exception as exc:
                logging.error(f"database {exc.args}")
    def delete_event(self, tgid, event_id, table_name=TB_EVENTS):
        with self.connection:
            try:
                self.cursor.execute(f"DELETE FROM {table_name} WHERE tgid = '{tgid}' AND event_id = '{event_id}'")
            except Exception as exc:
                logging.error(f"database {exc.args}")

    def select_pre_events(self, table_name=TB_EVENTS):
        with self.connection:
            try:
                self.cursor.execute(f"SELECT * FROM {table_name} WHERE prenotice = 'False'")
                q = self.cursor.fetchall()
                return q
            except Exception as exc:
                logging.error(f"database {exc.args}")
    def select_pay_events(self, table_name=TB_EVENTS):
        with self.connection:
            try:
                self.cursor.execute(f"SELECT * FROM {table_name} WHERE paynotice = 'False'")
                q = self.cursor.fetchall()
                return q
            except Exception as exc:
                logging.error(f"database {exc.args}")
    def update_notice(self, id, prenotice, paynotice, table_name=TB_EVENTS):
        with self.connection:
            try:
                self.cursor.execute(f"UPDATE {table_name} SET prenotice='{prenotice}',paynotice='{paynotice}' WHERE id={id}")
            except Exception as exc:
                logging.error(f"database {exc.args}")

    def get_events(self, tgid, table_name=TB_EVENTS):
        with self.connection:
            try:
                self.cursor.execute(f"SELECT event_id, add_date, start_point FROM {table_name} WHERE tgid = {tgid}")
                q = self.cursor.fetchall()
                return q
            except Exception as exc:
                logging.error(f"database {exc.args}")



    def create_table(self, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute("CREATE TABLE IF NOT EXISTS {} (id INTEGER PRIMARY KEY AUTOINCREMENT,tgid INTEGER UNIQUE, chatid INTEGER UNIQUE, name TEXT, description TEXT, level INTEGER)".format(table_name))
                return True
            except Exception as exc:
                logging.error(f"database {exc.args}")

    def get_table(self, tgid, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute(f"SELECT chatid, name, description, level FROM {table_name} WHERE tgid = {tgid}")
                q = self.cursor.fetchall()
                return q
            except Exception as exc:
                logging.error(f"database {exc.args}")

    def select_all(self, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute(f"SELECT * FROM {table_name}")
                q = self.cursor.fetchall()
                return q
            except Exception as exc:
                logging.error(f"database {exc.args}")


    def update_name(self, name, tgid, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute(f"UPDATE {table_name} SET name='{name}' WHERE tgid={tgid}")
            except Exception as exc:
                logging.error(f"database {exc.args}")
    def update_description(self,description, tgid, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute(f"UPDATE {table_name} SET description='{description}' WHERE tgid={tgid}")
            except Exception as exc:
                logging.error(f"database {exc.args}")
    def update_level(self,level, tgid, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute(f"UPDATE {table_name} SET level='{level}' WHERE tgid={tgid}")
            except Exception as exc:
                logging.error(f"database {exc.args}")

    def insert_table(self, tgid, name, description, chatid, level, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute(f"INSERT INTO {table_name} (tgid, chatid , name, description, level) VALUES ('{tgid}','{chatid}','{name}','{description}', '{level}')")
            except Exception as exc:
                logging.error(f"database {exc.args}")
    def drop_table(self, table_name=TB_USERS):
        with self.connection:
            try:
                self.cursor.execute('DROP TABLE {}'.format(table_name))
            except Exception as exc:
                logging.error(f"database {exc.args}")