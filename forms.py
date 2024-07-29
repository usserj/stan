from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,SelectMultipleField, BooleanField, DateField, SelectField, TextAreaField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import Usuario
from datetime import datetime, timedelta,timezone, time  # Importa datetime y timedelta


class RegistrationForm(FlaskForm):
    username = StringField('NombreUsuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('CorreoElectronico', validators=[DataRequired(), Email()])
    password = PasswordField('Contrasena', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contrasena', validators=[DataRequired(), EqualTo('password')])
    identificacion = StringField('Identificacion', validators=[DataRequired()])
    apellidos = StringField('Apellidos', validators=[DataRequired()])
    nombres = StringField('Nombres', validators=[DataRequired()])
    telefono = StringField('Telefono')
    direccion = StringField('Direccion')
    ciudad_residencia = StringField('CiudadResidencia')
    fecha_nacimiento = DateField('FechaNacimiento', format='%Y-%m-%d')
    genero = SelectField('Genero', choices=[('M', 'Masculino'), ('F', 'Femenino')])
    submit = SubmitField('Registrar')

    def validate_username(self, username):
        user = Usuario.query.filter_by(NombreUsuario=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya existe. Por favor elige otro.')

    def validate_email(self, email):
        user = Usuario.query.filter_by(CorreoElectronico=email.data).first()
        if user:
            raise ValidationError('Ese correo electrónico ya existe. Por favor elige otro.')

class LoginForm(FlaskForm):
    email = StringField('CorreoElectronico', validators=[DataRequired(), Email()])
    password = PasswordField('Contrasena', validators=[DataRequired()])
    remember = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar sesión')

# Asegúrate de importar el modelo Paciente
from models import Paciente

class PacienteForm(FlaskForm):
    identificacion = StringField('Identificacion', validators=[DataRequired()])
    apellidos = StringField('Apellidos', validators=[DataRequired()])
    nombres = StringField('Nombres', validators=[DataRequired()])
    correo_electronico = StringField('CorreoElectronico', validators=[DataRequired(), Email()])
    telefono = StringField('Telefono')
    direccion = StringField('Direccion')
    ciudad_residencia = StringField('CiudadResidencia')
    fecha_nacimiento = DateField('FechaNacimiento', format='%Y-%m-%d')
    genero = SelectField('Genero', choices=[('M', 'Masculino'), ('F', 'Femenino')])
    grupo_sanguineo = StringField('GrupoSanguineo')
    estado_paciente = SelectField('Estado Paciente', choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
    submit = SubmitField('Guardar')


class MedicoForm(FlaskForm):
    numero_licencia = StringField('Numero Licencia', validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellidos = StringField('Apellidos', validators=[DataRequired()])
    correo_electronico = StringField('Correo Electronico', validators=[DataRequired(), Email()])
    telefono = StringField('Telefono')
    direccion = StringField('Direccion')
    ciudad_residencia = StringField('Ciudad Residencia')
    fecha_nacimiento = DateField('Fecha Nacimiento', format='%Y-%m-%d')
    genero = SelectField('Genero', choices=[('M', 'Masculino'), ('F', 'Femenino')])
    especialidad = StringField('Especialidad', validators=[DataRequired()])
    fecha_contratacion = DateField('Fecha Contratacion', format='%Y-%m-%d')
    estado_medico = SelectField('Estado Medico', choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])  # Nuevo campo
    submit = SubmitField('Guardar')


class EspecialidadForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    descripcion = StringField('Descripción', validators=[DataRequired(), Length(max=100)])
    estado = SelectField('Estado', choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo')
    submit = SubmitField('Guardar')



class CreateHorarioForm(FlaskForm):
    MedicoID = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    day_of_week = SelectField('Día de la Semana', choices=[
        ('Lunes', 'Lunes'),         # Cambiar aquí
        ('Martes', 'Martes'),       # Cambiar aquí
        ('Miércoles', 'Miércoles'), # Cambiar aquí
        ('Jueves', 'Jueves'),       # Cambiar aquí
        ('Viernes', 'Viernes'),     # Cambiar aquí
        ('Sábado', 'Sábado'),       # Cambiar aquí
        ('Domingo', 'Domingo')      # Cambiar aquí
    ], validators=[DataRequired()])
    start_time = TimeField('Hora de Inicio', validators=[DataRequired()], default=time(9, 0))  # 09H00 por defecto
    end_time = TimeField('Hora de Fin', validators=[DataRequired()], default=time(12, 0))     # 12H00 por defecto
    estado = SelectField('Estado', choices=[
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo')
    ], validators=[DataRequired()])
    submit = SubmitField('Guardar')


from flask_wtf import FlaskForm
from wtforms import SelectField, DateTimeField, IntegerField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class CitaForm(FlaskForm):
    PacienteID = SelectField('Paciente', coerce=int, validators=[DataRequired()])
    EspecialidadID = SelectField('Especialidad', coerce=int, validators=[DataRequired()])
    MedicoID = SelectField('Médico', coerce=int, validators=[DataRequired()])
    Fecha = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])
    Hora = TimeField('Hora', format='%H:%M', validators=[DataRequired()])
    Duracion = IntegerField('Duración (minutos)', validators=[DataRequired()])
    Estado = SelectField('Estado', choices=[('programada', 'Programada'), ('completada', 'Completada'), ('cancelada', 'Cancelada')], validators=[DataRequired()])
    MotivoCita = TextAreaField('Motivo de la Cita', validators=[DataRequired()])

class AsignarEspecialidadForm(FlaskForm):
    MedicoID = SelectField('Médico', coerce=int, validators=[DataRequired()])
    EspecialidadID = SelectMultipleField('Especialidades', coerce=int, validators=[DataRequired()])
    Submit = SubmitField('Asignar Especialidades')

