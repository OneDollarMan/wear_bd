from datetime import time

from mysql.connector import connect, Error


# Класс репозитория, общающийся с БД
class Repo:
    ROLE_STOREKEEPER = 1  # Переменные ролей
    ROLE_ADMINISTRATOR = 2

    def __init__(self, host, user, password, db, port):
        self.connection = None
        self.cursor = None
        self.connect_to_db(host, user, password, db, port)
        if self.connection is not None and self.cursor is not None:
            self.select_db(db)
            self.get_tables = lambda: self.raw_query("SHOW TABLES")

            # Запросы к пользователям
            self.get_user = lambda username: self.get_query(
                f"SELECT * FROM user WHERE username='{username}'")
            self.get_all_users = lambda: self.raw_query(
                "SELECT user.id, username, fio, role.name FROM user JOIN role ON user.role_id=role.id WHERE hidden='0' ORDER BY user.id")
            self.login_user = lambda username, password: self.get_query(
                f"SELECT * FROM user WHERE username='{username}' AND password='{password}' AND hidden='0'")
            self.add_u = lambda params: self.write_query(
                "INSERT INTO user SET fio=%(fio)s, username=%(username)s, password=%(password)s, role_id=%(role_id)s",
                params)
            self.rm_user = lambda id: self.write_query(f"DELETE FROM user WHERE id='{id}'")
            self.select_users = lambda: self.raw_query("SELECT id, fio FROM user WHERE role_id='1' AND hidden='0'")
            self.hide_user = lambda id: self.write_query(f"UPDATE user SET hidden='1' WHERE id='{id}'")
            self.get_user_by_id = lambda id: self.get_query(
                f"SELECT user.id, username, fio, role.name FROM user JOIN role ON user.role_id=role.id WHERE hidden='0' AND user.id='{id}'")

            # Запросы к ролям
            self.get_roles = lambda: self.raw_query("SELECT * from role")

            # Запросы к клиентам
            self.get_clients = lambda: self.raw_query("SELECT * FROM client WHERE hidden='0'")
            self.add_client = lambda params: self.write_query(f"INSERT INTO client SET fio=%(fio)s, phone=%(phone)s", params)
            self.select_clients = lambda: self.raw_query("SELECT id, fio FROM client WHERE hidden='0'")
            self.hide_client = lambda id: self.write_query(f"UPDATE client SET hidden='1' WHERE id='{id}'")
            self.get_client_by_fio_phone = lambda fio, phone: self.get_query(f"SELECT * FROM client WHERE fio='{fio}' AND phone='{phone}'")

            # Запросы к поставщикам
            self.get_suppliers = lambda: self.raw_query("SELECT * FROM supplier WHERE hidden='0'")
            self.add_supplier = lambda params: self.write_query(f"INSERT INTO supplier SET name=%(name)s, address=%(address)s, phone=%(phone)s", params)
            self.select_suppliers = lambda: self.raw_query("SELECT id, name FROM supplier WHERE hidden='0'")
            self.hide_supplier = lambda id: self.write_query(f"UPDATE supplier SET hidden='1' WHERE id='{id}'")
            self.get_supplier_by_name_address = lambda name, address: self.get_query(f"SELECT * FROM supplier WHERE name='{name}' AND address='{address}'")

            # Запросы к одежде
            self.get_wear = lambda: self.raw_query("SELECT w.id, s.name, w.name, amount FROM wear w JOIN supplier s ON w.supplier_id=s.id WHERE w.hidden='0' AND (s.hidden='0' OR amount > '0')")
            self.add_wear = lambda params: self.write_query(f"INSERT INTO wear SET name=%(name)s, amount='0', supplier_id=%(supplier_id)s", params)
            self.select_wear = lambda: self.raw_query("SELECT wear.id, wear.name FROM wear JOIN supplier s ON wear.supplier_id=s.id WHERE wear.hidden='0' AND (s.hidden='0' OR amount > '0')")
            self.hide_wear = lambda id: self.write_query(f"UPDATE wear SET hidden='1' WHERE id='{id}'")
            self.get_wear_by_name_supplier = lambda name, supplier_id: self.get_query(f"SELECT * FROM wear WHERE name='{name}' AND supplier_id='{supplier_id}'")
            self.add_wear_amount = lambda params: self.write_query("UPDATE wear SET amount=amount+%(amount)s WHERE id=%(wear_id)s", params)

            # Запросы к счетам
            self.get_invoices = lambda: self.raw_query("SELECT i.id, date, c.fio, s.name FROM invoice i JOIN client c, status s WHERE i.client_id=c.id AND i.status_id=s.id ORDER BY date")
            self.get_invoice = lambda id: self.get_query(f"SELECT i.id, date, c.fio, s.name, s.id FROM invoice i JOIN client c, status s WHERE i.client_id=c.id AND i.status_id=s.id AND i.id='{id}'")
            self.add_invoice = lambda params: self.write_query(f"INSERT INTO invoice SET date=%(date)s, client_id=%(client_id)s, user_id=%(user_id)s, status_id='1'", params)
            self.rm_invoice = lambda id: self.write_query(f"DELETE FROM invoice WHERE id='{id}'")
            self.change_invoice_status = lambda id, status_id: self.write_query(f"UPDATE invoice SET status_id='{status_id}' WHERE id='{id}'")

            # Запросы к одежде в счетах
            self.get_wear_of_invoice = lambda id: self.raw_query(f"SELECT w.id, w.name, iw.amount FROM invoice_has_wear iw JOIN wear w ON iw.wear_id=w.id WHERE iw.invoice_id='{id}'")
            self.add_wear_to_invoice = lambda params: self.write_query("INSERT INTO invoice_has_wear SET invoice_id=%(invoice_id)s, wear_id=%(wear_id)s, amount=%(amount)s", params)
            self.update_wear_to_invoice = lambda params: self.write_query("UPDATE invoice_has_wear SET amount=amount+%(amount)s WHERE invoice_id=%(invoice_id)s AND wear_id=%(wear_id)s", params)
            self.rm_wear_from_invoice = lambda invoice_id, wear_id: self.write_query(f"DELETE FROM invoice_has_wear WHERE invoice_id='{invoice_id}' AND wear_id='{wear_id}'")

            # Запросы к статусам
            self.select_statuses = lambda: self.raw_query("SELECT id, name FROM status")

            # Статистика
            self.get_stat_by_user = lambda: self.raw_query("SELECT u.id, u.fio, COUNT(*) FROM invoice i JOIN user u ON i.user_id=u.id GROUP BY user_id;")

    def connect_to_db(self, host, user, password, db, port):  # Функция подключения к БД
        try:
            self.connection = connect(host=host, user=user, password=password, port=port)
            self.cursor = self.connection.cursor()
            self.cursor.execute("SHOW DATABASES")
            for res in self.cursor:
                if res[0] == db:
                    self.cursor.fetchall()
                    return
            for line in open('dump.sql'):
                self.cursor.execute(line)
            self.connection.commit()
            print('dump loaded successfully')
        except Error as e:
            print(e)

    def select_db(self, db):
        self.cursor.execute(f"USE {db}")

    def raw_query(self, query, params=None):  # Функция, отправляющая запрос к БД
        if self.cursor and query:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()

    def write_query(self, query, params=None):  # Тоже
        if self.cursor and query:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.fetchall()

    def get_query(self, query):  # Тоже
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def get_one_query(self, query):  # Тоже
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]

    def add_user(self, params):  # Добавление юзера с проверкой
        if not self.get_user(params['username']):
            self.add_u(params)
            return True
        else:
            return False

    def add_client_check(self, params):  # Добавление клиента с проверкой
        if not self.get_client_by_fio_phone(params['fio'], params['phone']):
            self.add_client(params)
            return True
        return False

    def add_supplier_check(self, params):  # Добавление поставщика с проверкой
        if not self.get_supplier_by_name_address(params['name'], params['address']):
            self.add_supplier(params)
            return True
        return False

    def add_wear_check(self, params):  # Добавление одежды с проверкой
        if not self.get_wear_by_name_supplier(params['name'], params['supplier_id']):
            self.add_wear(params)
            return True
        return False

    def add_wear_to_invoice_check(self, params):  # Добавление одежды в счет
        a = self.get_query(f"SELECT amount FROM wear WHERE id='{params['wear_id']}'")
        if a[0] >= params['amount']:
            iw = self.get_query(f"SELECT * FROM invoice_has_wear WHERE invoice_id='{params['invoice_id']}' AND wear_id='{params['wear_id']}'")
            if iw is None:
                self.add_wear_to_invoice(params)
            else:
                self.update_wear_to_invoice(params)
            params['amount'] = -params['amount']
            self.add_wear_amount(params)
            return True
        return False

    def get_invoices_sorted(self, data):  # Вывод отфильтрованных счетов
        q = "SELECT i.id, date, c.fio, s.name FROM invoice i JOIN client c, status s WHERE i.client_id=c.id AND i.status_id=s.id"
        if data['client_id']:
            q = q + f" AND i.client_id='{data['client_id']}'"
        if data['date1']:
            q = q + f" AND date >= '{data['date1']}'"
        if data['date2']:
            q = q + f" AND date <= '{data['date2']}'"
        q = q + ' ORDER BY date'
        return self.raw_query(q)

    def remove_wear_from_invoice(self, id, wear_id):
        a = self.get_query(f"SELECT amount FROM invoice_has_wear WHERE invoice_id='{id}' AND wear_id='{wear_id}'")
        if a:
            self.add_wear_amount({'wear_id': wear_id, 'amount': a[0]})
            self.rm_wear_from_invoice(id, wear_id)
            return True
        return False

    def remove_invoice(self, id):  # Удаление листа
        wear = self.get_wear_of_invoice(id)
        for w in wear:
            self.remove_wear_from_invoice(id, w[0])
        self.rm_invoice(id)
