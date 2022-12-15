import hashlib

from flask import url_for, render_template, request, redirect, send_from_directory, flash, session
from __init__ import app
import forms
from repo import *

# Создание объекта репозитория
repo = Repo(host=app.config['HOST'], user=app.config['USER'], password=app.config['PASSWORD'], db=app.config['DB'], port=app.config['PORT'])


def flash_errors(form):  # Вывод ошибок форм
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'warning')


@app.route("/")  # Главная страница
def index():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    return render_template('index.html', title="Главная", stat=repo.get_stat_by_user())


@app.route("/login", methods=['GET', 'POST'])  # Страница авторизации
def login():
    if session.get('loggedin'):
        return redirect(url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = repo.login_user(form.login.data, hashlib.md5(form.password.data.encode('utf-8')).hexdigest())
        if user:
            flash('Вы авторизовались!', 'info')
            session['loggedin'] = True
            session['id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[4]
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!', 'warning')
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')  # Страница логаута
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))


@app.route("/users", methods=['GET', 'POST'])  # Страница пользователей
def users():
    form = forms.UserForm()
    form.role_id.choices = repo.get_roles()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            data = form.data
            data['password'] = hashlib.md5(data['password'].encode('utf-8')).hexdigest()
            if not repo.add_user(data):
                flash('Пользователь уже существует', 'warning')
            else:
                app.logger.warning(f'User {form.username.data} with role id {form.role_id.data} was added by {session.get("username")}')
            return redirect(url_for('users'))
    return render_template('users.html', title='Пользователи', us=repo.get_all_users(), form=form)


@app.route("/users/rm/<int:id>")  # Страница удаления пользователя
def rm_user(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.hide_user(id)
    return redirect(url_for('users'))


@app.route("/clients", methods=['GET', 'POST'])  # Страница клиентов
def clients():
    form = forms.ClientForm()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_client_check(form.data):
                flash('Клиент уже существует', 'warning')
            return redirect(url_for('clients'))
    return render_template('clients.html', title="Клиенты", clients=repo.get_clients(), form=form)


@app.route("/clients/rm/<int:id>")  # Страница удаления клиента
def rm_clients(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.hide_client(id)
    return redirect(url_for("clients"))


@app.route("/suppliers", methods=['GET', 'POST'])  # Страница поставщиков
def suppliers():
    form = forms.SupplierForm()
    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_supplier_check(form.data):
                flash('Поставщик уже существует', 'warning')
            return redirect(url_for('suppliers'))

    return render_template('suppliers.html', title="Поставщики", suppliers=repo.get_suppliers(), form=form)


@app.route("/suppliers/rm/<int:id>")  # Страница удаления поставщика
def rm_supplier(id):
    if session.get('role') >= repo.ROLE_ADMINISTRATOR:
        if id:
            repo.hide_supplier(id)
    return redirect(url_for("suppliers"))


@app.route("/wear", methods=['GET', 'POST'])  # Страница одежды
def wear():
    form = forms.WearForm()
    form.supplier_id.choices = repo.select_suppliers()

    add_form = forms.AddForm()
    add_form.wear_id.choices = repo.select_wear()

    if form.validate_on_submit():
        if session.get('role') == repo.ROLE_ADMINISTRATOR:
            if not repo.add_wear_check(form.data):
                flash('Данный товар у данного поставщика уже существует', 'warning')
                return redirect(url_for('wear'))
            app.logger.warning(f'new wear was added by {session.get("username")}')
            return redirect(url_for('wear'))

    return render_template('wear.html', title="Одежда", wear=repo.get_wear(), form=form, add_form=add_form)


@app.route("/wear/add_amount", methods=['POST'])  # Страница удаления одежды
def add_wear():
    add_form = forms.AddForm()
    add_form.wear_id.choices = repo.select_wear()
    if session.get('role') == repo.ROLE_STOREKEEPER:
        if add_form.validate_on_submit():
            repo.add_wear_amount(add_form.data)
            flash('Количество товара добавлено', 'info')
    return redirect(url_for("wear"))


@app.route("/wear/rm/<int:id>")  # Страница удаления одежды
def rm_wear(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.hide_wear(id)
    return redirect(url_for("wear"))


@app.route('/invoices', methods=['GET', 'POST'])  # Страница счетов
def invoices():
    form = forms.InvoiceForm()
    form.client_id.choices = repo.select_clients()

    filter_form = forms.InvoiceFilterForm()
    filter_form.client_id.choices = [("", "---")] + repo.select_clients()

    if filter_form.validate_on_submit():
        return render_template('invoices.html', title="Счета", invoices=repo.get_invoices_sorted(filter_form.data), form=form, filter_form=filter_form)

    return render_template('invoices.html', title='Счета', invoices=repo.get_invoices(), form=form, filter_form=filter_form)


@app.route('/invoices/add', methods=['POST'])  # Страница добавления счета
def add_invoice():
    form = forms.InvoiceForm()
    form.client_id.choices = repo.select_clients()

    if form.validate_on_submit() and session.get('role') >= repo.ROLE_STOREKEEPER:
        data = form.data
        data['user_id'] = session.get('id')
        repo.add_invoice(data)
    else:
        flash_errors(form)
    return redirect(url_for('invoices'))


@app.route('/invoices/<int:id>', methods=['GET', 'POST'])  # Страница конкретного счета
def invoice(id):
    if session.get('role') >= repo.ROLE_STOREKEEPER:
        form = forms.InvoiceWearForm()
        form.wear_id.choices = repo.select_wear()
        status_form = forms.StatusForm()
        status_form.status.choices = repo.select_statuses()

        if status_form.validate_on_submit():
            repo.change_invoice_status(id, status_form.status.data)
            flash('Статус изменен', 'info')
            return redirect(url_for('invoice', id=id))
        return render_template('invoice.html', title='Счет', invoice=repo.get_invoice(id), wear=repo.get_wear_of_invoice(id), form=form, status_form=status_form)
    else:
        flash('Нет доступа', 'warning')
        return redirect(url_for('invoices'))


@app.route('/invoices/<int:id>/add', methods=['POST'])  # Страница добавления одежды в счет
def add_wear_to_invoice(id):
    form = forms.InvoiceWearForm()
    form.wear_id.choices = repo.select_wear()
    if form.validate_on_submit():
        data = form.data
        data['invoice_id'] = id
        if not repo.add_wear_to_invoice_check(data):
            flash('Недостаточно товара', 'warning')
    return redirect(url_for('invoice', id=id))


@app.route('/invoices/<int:id>/rm/<int:wear_id>', methods=['GET'])  # Страница удаления одежды из счета
def rm_wear_from_invoice(id, wear_id):
    if not repo.remove_wear_from_invoice(id, wear_id):
        flash('Что-то пошло не так', 'warning')
    else:
        flash('Позиция удалена, товар возвращен на склад', 'info')
    return redirect(url_for('invoice', id=id))


@app.route("/invoices/rm/<int:id>")  # Страница удаления счета
def rm_invoice(id):
    if session.get('role') == repo.ROLE_ADMINISTRATOR:
        if id:
            repo.remove_invoice(id)
    return redirect(url_for("invoices"))


# Вывод статических ресурсов
@app.route('/robots.txt')
@app.route('/sitemap.xml')
@app.route('/favicon.ico')
@app.route('/style.css')
@app.route('/script.js')
@app.route('/bus.jpg')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


# Обработка ошибки 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
