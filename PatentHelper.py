#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Andrey Golubev
import locale
import sys
import configparser
import gi
import signal
import sqlite3
import smtplib
import locale
import configparser
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


gi.require_version('Gtk', '3.0')
# todo: switch to gtk4
#gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

# connect sqlite
conn = sqlite3.connect('C:\\ProgramData\\PatentHelper\\database.db')
cursor = conn.cursor()
# value for sort tables
count_search = 0

# gui window
class Application(object):
	def __init__(self):
		# main defs
		self.builder = Gtk.Builder()
		self.glade_file = 'ui.glade'
		self.builder.add_from_file(self.glade_file)
		self.window = self.builder.get_object('main')
		# add entry
		self.number = self.builder.get_object('certNum')
		self.chose = self.builder.get_object('type_chose')
		self.holder = self.builder.get_object('rightHolder')
		self.name = self.builder.get_object('name')
		self.date = self.builder.get_object('date')
		self.date_chose = self.builder.get_object('date_chose')
		self.email = self.builder.get_object('email')
		self.note = self.builder.get_object('note')
		# buttons
		self.add_button = self.builder.get_object("add")
		self.change_button = self.builder.get_object("change")
		self.delete_button = self.builder.get_object("delete")
		# db
		self.liststore = self.builder.get_object('ListStore')
		self.view = self.builder.get_object("TreeView")
		# add data to tables:
		for row in cursor.execute("select * from patents"):
			self.liststore.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]])
		# render gui
		self.builder.connect_signals(self)
		self.window.connect('delete-event', Gtk.main_quit)
		self.window.show_all()


	# calculate time to remind
	def calc_time(self, *args):
		# deps
		select = self.builder.get_object("TreeView").get_selection()
		model, treeiter = select.get_selected()
		## start calc
		value_date = (datetime.strptime((self.date.get_text()), ("%d.%m.%Y")).date())
		# trade mark time calk
		tm_start = value_date + relativedelta(years=9)
		tm_end = value_date + relativedelta(years=10)
		# invention time calk
		inv_start = value_date + relativedelta(years=1)
		inv_end = value_date + relativedelta(years=2)
		# utility model time calk
		um_start = value_date + relativedelta(months=0)
		um_end = value_date + relativedelta(months=12)
		# industrial design time calk
		if value_date < date(2015, 1, 1):
			id_start = value_date + relativedelta(years=9)
			id_end = value_date + relativedelta(years=10)
		else:
			id_start = value_date + relativedelta(years=4)
			id_end = value_date + relativedelta(years=5)
		# if combo box value = ... calc date to remind
		if self.chose.get_active() == 0:
			date_start, date_end = [tm_start, tm_end]
		elif self.chose.get_active() == 1:
			date_start, date_end = [inv_start, inv_end]
		elif self.chose.get_active() == 2:
			date_start, date_end = [um_start, um_end]
		elif self.chose.get_active() == 3:
			date_start, date_end = [id_start, id_end]

		# add years, needs to calc pay day next time
		remind_date = value_date + relativedelta(years=1)
		remind_date2 = value_date + relativedelta(years=2)

		# exclusions for pay dates
		if self.chose.get_active() == 0:
			remind_date = value_date + relativedelta(years=9)
			remind_date2 = value_date + relativedelta(years=10)
		if self.date_chose.get_active() == 1 and self.chose.get_active() == 3 and value_date < date(2015, 1, 1):
			remind_date = value_date + relativedelta(years=4)
			remind_date2 = value_date + relativedelta(years=5)
		if self.date_chose.get_active() == 1 and  self.chose.get_active() == 3:
			remind_date = remind_date + relativedelta(days=1)
		# calc year
		remind_date_str = (date.strftime(remind_date, "%Y"))
		remind_date_str2 = (date.strftime(remind_date2, "%Y"))
		# calc day and month
		remind_day_from_table = date(1980, 1, 1)
		if self.date_chose.get_active() == 1:
			remind_day_from_table = (datetime.strptime((str(model[treeiter][5])), ("%d.%m.%Y")).date())
		remind_day = (date.strftime(remind_day_from_table, "%d.%m."))

		# convert from data format to string
		if self.date_chose.get_active() == 0:
			date_start_str = (date.strftime(date_start, "%d.%m.%Y"))
			date_end_str = (date.strftime(date_end, "%d.%m.%Y"))
		# sum of 2 strings to make a date
		if self.date_chose.get_active() == 1:
			date_start_str = remind_day + remind_date_str
			date_end_str = remind_day + remind_date_str2
		return date_start_str, date_end_str

	# connect buttons (gui) and code
	# add button
	def click_add(self, add):
		cursor = conn.cursor()
		# time calc
		calc_time = self.calc_time()
		# get column count to set id
		value_id = len(self.liststore) + 1
		# another colums for import to table
		value_chose = (self.chose.get_active_text())
		value_number = int(self.number.get_text())
		value_name = (self.name.get_text())
		value_holder = (self.holder.get_text())
		value_email = (self.email.get_text())
		value_note = (self.note.get_text())

		iter = self.liststore.append()
		# add data from form to table
		self.liststore.set(iter, 0, (value_id))
		self.liststore.set(iter, 1, (value_chose))
		self.liststore.set(iter, 2, (value_number))
		self.liststore.set(iter, 3, (value_name))
		self.liststore.set(iter, 4, (value_holder))
		self.liststore.set(iter, 5, self.date.get_text())
		# calculate date of ending patents and add it to table
		self.liststore.set(iter, 6, (calc_time[0]))
		self.liststore.set(iter, 7, (calc_time[1]))
		# if client pay 1 time, we add it to base
		if self.date_chose.get_active() == 1:
			self.liststore.set(iter, 8, (self.date.get_text()))
		self.liststore.set(iter, 9, (value_email))
		self.liststore.set(iter, 10, (value_note))

		date_start_str_iso = (datetime.strptime((calc_time[0]), ("%d.%m.%Y")).date())
		date_end_str_iso = ((datetime.strptime((calc_time[1]), ("%d.%m.%Y")).date()) + relativedelta(months=6))
		priority_date_iso = (datetime.strptime((self.date.get_text()), ("%d.%m.%Y")).date())

		cursor.execute("""INSERT into patents (id,type,numCert,name,rightholder,priorityDate,pdUpdateStart,pdUpdateEnd,email,dateISO,dateEND,nextRemind,note,priorityDate_ISO) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
			""", (value_id, value_chose, value_number, value_name, value_holder, (self.date.get_text()), calc_time[0],
				  calc_time[1], value_email, date_start_str_iso, date_end_str_iso, date_start_str_iso, value_note, priority_date_iso))
		conn.commit()
		cursor.close()

	# edit button
	def click_edit(self, change):
		self.date = self.builder.get_object('date')
		# time calc
		calc_time = self.calc_time()
		# get column count to set id
		value_id = len(self.liststore) + 1
		# another colums for import to table
		value_chose = (self.chose.get_active_text())
		value_number = int(self.number.get_text())
		value_name = (self.name.get_text())
		value_holder = (self.holder.get_text())
		# don't wanna 'none' in a row, will be better if row is empty
		if self.email.get_text() is not None:
			value_email = (self.email.get_text())
		if self.note.get_text() is not None:
			value_note = (self.note.get_text())

		select = self.builder.get_object("TreeView").get_selection()
		model, treeiter = select.get_selected()
		date_start_str_iso = (datetime.strptime((calc_time[0]), ("%d.%m.%Y")).date())
		date_end_str_iso = (datetime.strptime((calc_time[1]), ("%d.%m.%Y")).date())
		i = (model[treeiter][0])

		# push values to db
		cursor = conn.cursor()
		cursor.execute("""UPDATE patents SET type = '{0}', numCert = '{1}', name = '{2}', 
			rightholder = '{3}', pdUpdateStart = '{4}', 
			pdUpdateEnd = '{5}', email = '{6}', dateISO = '{7}', dateEND = '{8}', note = '{9}' WHERE id = '{10}'
			""".format(value_chose, value_number, value_name, value_holder, calc_time[0],
					   calc_time[1], value_email, date_start_str_iso, date_end_str_iso, value_note, i))
		if self.date_chose.get_active() == 0:
			cursor.execute("""UPDATE patents SET priorityDate = '{0}', priorityDate_ISO = '{1}' WHERE id = '{2}'
			""".format(self.date.get_text(), (datetime.strptime((self.date.get_text()), ("%d.%m.%Y")).date()), i))
		if self.date_chose.get_active() == 1:
			cursor.execute("""UPDATE patents SET payDate = '{0}', payDate_ISO = '{1}' WHERE id = '{2}'
			""".format(self.date.get_text(), (datetime.strptime((self.date.get_text()), ("%d.%m.%Y")).date()), i))
		conn.commit()
		cursor.close()
		# push values to table gui
		self.liststore.set(treeiter, 1, (value_chose))
		self.liststore.set(treeiter, 2, (value_number))
		self.liststore.set(treeiter, 3, (value_name))
		self.liststore.set(treeiter, 4, (value_holder))
		if self.date_chose.get_active() == 0:
			self.liststore.set(treeiter, 5, (self.date.get_text()))
		self.liststore.set(treeiter, 6, (calc_time[0]))
		self.liststore.set(treeiter, 7, (calc_time[1]))
		if self.date_chose.get_active() == 1:
			self.liststore.set(treeiter, 8, (self.date.get_text()))
		self.liststore.set(treeiter, 9, (value_email))
		self.liststore.set(treeiter, 10, (value_note))

	# get values from table
	def on_clicked(self, clicked):
		select = self.builder.get_object("TreeView").get_selection()
		model, treeiter = select.get_selected()
		# set data to entrys
		i1 = (model[treeiter][1])
		if i1 == 'Товарный знак':
			self.chose.set_active(0)
		elif i1 == 'Изобретение':
			self.chose.set_active(1)
		elif i1 == 'Полезная модель':
			self.chose.set_active(2)
		elif i1 == 'Промышленный образец':
			self.chose.set_active(3)
		self.number.set_text(str(model[treeiter][2]))
		self.holder.set_text(str(model[treeiter][4]))
		self.name.set_text(str(model[treeiter][3]))
		# if no pay date => set priority date as main
		if str(model[treeiter][8]) == 'None':
			self.date_chose.set_active(0)
			self.date.set_text(str(model[treeiter][5]))
		else:
			self.date_chose.set_active(1)
			self.date.set_text(str(model[treeiter][8]))
		# hide email if data is empty
		if str(model[treeiter][9]) == 'None' or str(model[treeiter][9]) == '':
			self.note.set_text('')
		else:
			self.note.set_text(str(model[treeiter][9]))
		# same for note
		if str(model[treeiter][10]) == 'None' or str(model[treeiter][10]) == '':
			self.note.set_text('')
		else:
			self.note.set_text(str(model[treeiter][10]))

	# sort table values
	def on_search(self, on_search):
		cursor = conn.cursor()
		focus_column = on_search.get_title()
		count_dict = {'№': 'id', 'Тип': 'type', 'Номер': 'numCert', 'Название': 'name', 
		'Правообладатель': 'rightholder', 'Дата приоритета': 'priorityDate_ISO', 
		'Оплатить с': 'dateISO', 'Оплатить по': 'dateEND', 'Дата оплаты': 'payDate_ISO', 
		'email': 'email', 'Примечание': 'note'}
		sort_column = count_dict.get(focus_column)
		self.liststore.clear()
		global count_search
		if count_search == 0:
			for row in cursor.execute("SELECT * FROM patents ORDER by %s DESC" % (sort_column,)):
				self.liststore.append([row[0], row[1], row[2], row[3], row[4], 
							   row[5], row[6], row[7], row[8], row[9], row[10]])
				count_search = 1
		else:
			for row in cursor.execute("SELECT * FROM patents ORDER by %s ASC" % (sort_column,)):
				self.liststore.append([row[0], row[1], row[2], row[3], row[4], 
							   row[5], row[6], row[7], row[8], row[9], row[10]])
				count_search = 0	
		cursor.close()

	# del button connect
	def click_del(self, delete):
		cursor = conn.cursor()
		# get id for selected row
		select = self.builder.get_object("TreeView").get_selection()

		model, treeiter = select.get_selected()
		i = (model[treeiter][0])

		# del row from db
		if treeiter is not None:
			sql_delete_query = """DELETE from patents where id = ?"""
		cursor.execute(sql_delete_query, ((model[treeiter][0]),))
		# set right id to rows in db after delete
		cursor.execute("UPDATE patents SET id = id - 1 WHERE id > '%s'" % i)
		conn.commit()
		id_for_change = self.liststore.get_value(treeiter, 0)
		# remove from gui
		self.liststore.remove(treeiter)
		self.liststore.set_value(treeiter, 0, i)
		# set id right numbers
		while i < len(self.liststore):
			self.liststore.set_value(self.liststore.iter_next(treeiter), 0, i + 1)
			i+=1
			treeiter = self.liststore.iter_next(treeiter)
		cursor.close()

	# destroy button with sql connect close
	def onDestroy(self, *args):
		Gtk.main_quit()
		conn.close()

class MessageDialogWindow(Gtk.Window):
	# create error window (if something goes wrong)
	def error_window(error_title, error_text):
		Gtk.Window(title="Error!")
		dialog = Gtk.MessageDialog(
			flags=0,
			message_type=Gtk.MessageType.INFO,
			buttons=Gtk.ButtonsType.OK,
			text=error_title,
		)
		dialog.format_secondary_text(
			error_text
		)
		dialog.run()
		dialog.destroy()

# count rows to remind
class CountRows:
	# get number of rows
	def count_rows():
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(*) numCert FROM patents WHERE nextRemind < date('now') ORDER BY nextRemind")
		len_list = cursor.fetchone()
		cursor.close()
		return len_list[0]

# send email to user
class SendMail:
	# select table from db
	def sql_select_to_list(num, select_table):
		cursor = conn.cursor()
		list_n = []
		cursor.execute("SELECT %s FROM patents WHERE nextRemind < date('now') ORDER BY nextRemind" % (select_table,))
		list_sql = cursor.fetchall()
		for row in list_sql:
				list_n.append(row[0])
		cursor.close()
		return(list_n[num])

	# get month name to subject of mail
	def month_name():
		#set system locale
		locale.setlocale(locale.LC_TIME, "")
		current_month = (date.strftime((datetime.today()), "%B").lower())
		return(current_month)

	def read_config():
		# read configs from settings.ini
		config = configparser.ConfigParser()
		try:
			config.read("C:\\ProgramData\\PatentHelper\\settings.ini")
			# from
			message_from = config["Mail"]["from"]
			# pass
			password = config["Mail"]["password"]
			# to
			message_to = config["Mail"]["to"]
			# notification timer
			notification_days = config["Mail"]["days"]
			return(message_from, password, message_to, notification_days)
		except:
			# if somethong goes wrong, type info about error
			error_title = 'Config error'
			MessageDialogWindow.error_window(error_title, str('Файл settings.ini не найден или заполнен некорректно'))

	# sen email method
	def send_email(month, message_from, password, message_to, notification_days):
		len_list = CountRows.count_rows()
		if len_list > 0:
			# Subject of the mail
			subject = "Напоминание за %s" % (month)
			msg = MIMEMultipart()
			msg['Subject'] = subject
			# get info from read_config
			msg['From'] = str(message_from)
			password = str(password)
			msg['To'] = str(message_to)
			# read info from txt file and pass it to message
			mail_file = open("C:\\ProgramData\\PatentHelper\\LastMail.txt")
			msg.attach(MIMEText(mail_file.read(), 'plain'))
			sended = 0
			# try to login gmail and sending the mail
			try:
				server = smtplib.SMTP('smtp.gmail.com: 587')
				server.starttls()
				server.login(msg['From'], password)
				server.sendmail(msg['From'], msg['To'], msg.as_string())
				server.quit()
				# if email was sended, make a mark about it
				sended = 1
			except Exception as error_text:
				# if somethong goes wrong, type info about error
				error_title = 'Email error'
				MessageDialogWindow.error_window(error_title, str(error_text))
			mail_file.close()
			# if email was successfully sended, change dates for next remind
			if sended == 1:
				#make a mark about sended objects
				cursor = conn.cursor()
				cursor.execute("UPDATE patents set nextRemind = CASE WHEN nextRemind is NULL THEN dateISO ELSE nextRemind END")
				cursor.execute("UPDATE patents SET nextRemind = DATE(('now'), '+%s day') WHERE nextRemind < date('now')" % (notification_days,))
				conn.commit()
				cursor.close()

# make txt file with info about subjects
class TxtFile:
	def make_txt_file(len_list):
		# if list is not null, make some text file
		if len_list != 0:
			# fill list for remind
			mail_file = open("C:\\ProgramData\\PatentHelper\\LastMail.txt", "w")
			for num in range(len_list):
				message = (str(num + 1) + '. ' + str(
					SendMail.sql_select_to_list(num, 'type')) + '; Наименование: ' + str(
					SendMail.sql_select_to_list(num, 'name')) + '; Правообладатель: ' + str(
					SendMail.sql_select_to_list(num, 'rightholder')) + '; Номер: ' + str(
					SendMail.sql_select_to_list(num, 'numCert')) + '; Дата приоритета: ' + str(
					SendMail.sql_select_to_list(num, 'priorityDate')) + '; Дата последнего платежа: ' + str(
					SendMail.sql_select_to_list(num, 'payDate')) + '; Оплатить с: ' + str(
					SendMail.sql_select_to_list(num, 'pdUpdateStart')) + '; Оплатить по: ' + str(
					SendMail.sql_select_to_list(num, 'pdUpdateEnd'))  + '; Примечание: ' + str(
					SendMail.sql_select_to_list(num, 'note'))
					## disabled now
					# + '; Отправить на почту: ' + str(
					#SendMail.sql_select_to_list(num, 'email')) + ';
					+ '\n')
				mail_file.write(message)
			mail_file.close()

	make_txt_file(CountRows.count_rows())


if __name__ == '__main__':
	# gen txt file
	TxtFile()
	# send email with txt file
	SendMail.send_email(SendMail.month_name(), SendMail.read_config()[0], SendMail.read_config()[1], SendMail.read_config()[2], SendMail.read_config()[3])
	# run gui
	Application()
	Gtk.main()