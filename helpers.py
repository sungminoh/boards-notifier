# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
import sqlite3
import os


class EmailHandler(object):
    @staticmethod
    def send_email(subject, sender, receiver, content, password=''):
        msg = MIMEText(content.encode('utf-8'), _charset='utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ', '.join(receiver)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(sender.split('@')[0], password)
            server.sendmail(sender, receiver, msg.as_string())
            server.close()
            print('successfully sent the mail to %s' % msg['To'])
        except Exception:
            print('send through localhost')
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, receiver, msg.as_string())
            s.quit()
            print('successfully sent the mail to %s' % msg['To'])


class DbManager(object):
    def __init__(self, name):
        self.table = os.path.splitext(os.path.basename(name))[0]

    def create(self, *columns):
        column_desc = ', '.join([' '.join(column) for column in columns])
        sql = f'create table if not exists {self.table} (id integer primary key, {column_desc})'
        print('Creating DB', sql, sep='\n')
        try:
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql)
        except Error as e:
            print(e)
        return self

    def connect(self):
        self.conn = sqlite3.connect(os.path.join('cache', self.table + '.db'))

    def contains(self, id):
        sql = f'select id from {self.table} where id = ?'
        # print('Cantains DB', sql, sep='\n')
        for row in self.conn.cursor().execute(sql, id):
            return True
        else:
            return False

    def select(self, dics=[], fields=None):
        placeholders = []
        values = []
        for dic in dics:
            columns = list(dic.keys())
            values.extend([dic[k] for k in dic])
            placeholders.append(' and '.join([f"{k}=?" if isinstance(v, str)
                                              else f'{k}=?' for k, v in dic.items()]))
        fields = ', '.join(fields) if fields else '*'
        if dics:
            placeholder = '(' + ') or ('.join(placeholders) + ')'
            sql = f'select {fields} from {self.table} where {placeholder}'
            return self.conn.cursor().execute(sql, values).fetchall()
        else:
            sql = f'select {fields} from {self.table}'
            return self.conn.cursor().execute(sql).fetchall()

    def insert(self, *rows, force=False):
        if not rows:
            return
        columns = list(rows[0].keys())
        values = [tuple(row[c] for c in columns) for row in rows]
        placeholder = ','.join(['?' for _ in columns])
        replace = 'or replace' if force else ''
        sql = f'insert {replace} into {self.table} ({",".join(columns)}) values ({placeholder})'
        # print('Insert DB', sql, sep='\n')
        self.conn.cursor().executemany(sql, values)
        self.conn.commit()
