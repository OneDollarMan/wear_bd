from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateTimeLocalField, SubmitField, PasswordField, DecimalField, TimeField, \
    DateField, SelectMultipleField
from wtforms.validators import Length, NumberRange, InputRequired, Optional, ValidationError, Regexp

rus_length = Length(min=1, max=45, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_number_range = NumberRange(min=1, max=99999999999, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_input_required = InputRequired(message='Заполните поле')
rus_price_range = NumberRange(min=1, max=10000, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')
rus_mileage_range = NumberRange(min=1, max=1000000, message='Значение поля должно быть длиной от %(min)d до %(max)d символов')


def datetime_check(form, field):
    if field is not None:
        if field.data < datetime.today():
            raise ValidationError('Введите не прошедшую дату')
    else:
        raise ValidationError('Введите правильную дату')


class LoginForm(FlaskForm):
    login = StringField('Логин', [rus_input_required, rus_length])
    password = PasswordField('Пароль', [rus_input_required, rus_length])
    submit = SubmitField('Войти')


class UserForm(FlaskForm):
    username = StringField('Имя пользователя', [rus_input_required, rus_length])
    password = PasswordField('Пароль', [rus_input_required, rus_length])
    fio = StringField('ФИО', [rus_input_required, rus_length])
    role_id = SelectField('Выберите роль', [rus_input_required])
    submit = SubmitField('Добавить')


class ClientForm(FlaskForm):
    fio = StringField('ФИО', [Optional(), rus_length])
    phone = DecimalField('Номер телефона', [Optional(), rus_number_range])
    submit = SubmitField('Добавить')


class SupplierForm(FlaskForm):
    name = StringField('Наименование юр. лица', [rus_input_required, rus_length])
    address = StringField('Адрес', [rus_input_required, rus_length])
    phone = DecimalField('Номер телефона', [Optional(), rus_number_range])
    submit = SubmitField('Добавить')


class WearForm(FlaskForm):
    supplier_id = SelectField('Выберите поставщика', validators=[rus_input_required])
    name = StringField('Название', [rus_input_required, rus_length])
    submit = SubmitField('Добавить')


class AddForm(FlaskForm):
    wear_id = SelectField('Выберите товар', validators=[rus_input_required])
    amount = DecimalField('Количество', [rus_input_required, rus_price_range])
    submit2 = SubmitField('Добавить')


class InvoiceForm(FlaskForm):
    date = DateTimeLocalField('Дата', format='%Y-%m-%dT%H:%M', validators=[rus_input_required, datetime_check])
    client_id = SelectField('Выберите клиента', [rus_input_required])
    submit = SubmitField('Добавить')


class InvoiceFilterForm(FlaskForm):
    client_id = SelectField('Выберите клиента', [Optional()])
    date1 = DateField('Дата от', validators=[Optional()])
    date2 = DateField('Дата до', validators=[Optional()])
    submit2 = SubmitField('Показать')


class InvoiceWearForm(FlaskForm):
    wear_id = SelectField('Выберите вещь', [rus_input_required])
    amount = DecimalField('Количество', [rus_input_required, rus_price_range])
    submit = SubmitField('Добавить')


class StatusForm(FlaskForm):
    status = SelectField('Выберите статус', validators=[rus_input_required])
    submit2 = SubmitField('Изменить')
