from typing import Optional
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField, BooleanField, DateField, SelectField, TextAreaField, TimeField, IntegerField,HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional as OptionalValidator
from flask_login import current_user  # Agregado
from models import Usuario, Especialidad, Medico, user_roles, Rol  # Agregado
from datetime import datetime, timedelta, timezone, time  # Importa datetime y timedelta


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
    ciudad_residencia = SelectField('CiudadResidencia', choices=[], validators=[DataRequired()])
    fecha_nacimiento = DateField('FechaNacimiento', format='%Y-%m-%d', validators=[DataRequired()])
    genero = SelectField('Genero', choices=[('M', 'Masculino'), ('F', 'Femenino')])
    grupo_sanguineo = SelectField('GrupoSanguineo', choices=[], validators=[DataRequired()])
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
    identificacion = StringField('Identificación', validators=[DataRequired()])
    apellidos = StringField('Apellidos', validators=[DataRequired()])
    nombres = StringField('Nombres', validators=[DataRequired()])
    correo_electronico = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono')
    direccion = StringField('Dirección')
    ciudad_residencia = SelectField('Ciudad de Residencia', choices=[], validators=[DataRequired()])
    fecha_nacimiento = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[DataRequired()])
    genero = SelectField('Género', choices=[('M', 'Masculino'), ('F', 'Femenino')], validators=[DataRequired()])
    grupo_sanguineo = SelectField('Grupo Sanguíneo', choices=[], validators=[DataRequired()])
    
    current_password = PasswordField('Contraseña Actual', validators=[OptionalValidator()])
    password = PasswordField('Nueva Contraseña', validators=[OptionalValidator(), EqualTo('confirm_password', message='Las contraseñas deben coincidir')])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[OptionalValidator()])
    
    submit = SubmitField('Guardar')

class MedicoForm(FlaskForm):
    numero_cedula = StringField('Número de Cédula', validators=[Length(max=50)])
    nombre = StringField('Nombre', validators=[DataRequired(), Length(max=100)])
    apellidos = StringField('Apellidos', validators=[DataRequired(), Length(max=100)])
    correo_electronico = StringField('Correo Electrónico', validators=[DataRequired(), Email(), Length(max=100)])
    telefono = StringField('Teléfono', validators=[Length(max=15)])
    direccion = StringField('Dirección', validators=[Length(max=255)])
    ciudad_residencia = SelectField('Ciudad de Residencia', choices=[], validators=[DataRequired()])
    fecha_nacimiento = DateField('Fecha de Nacimiento', format='%Y-%m-%d')
    genero = SelectField('Género', choices=[])
    especialidad = SelectField('Especialidad', choices=[])
    fecha_contratacion = DateField('Fecha de Contratación', format='%Y-%m-%d')
    estado_medico = SelectField('Estado Médico', choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')])
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
    PacienteID = SelectField('Paciente', coerce=int, validators=[OptionalValidator()])
    EspecialidadID = SelectField('Especialidad', coerce=int, validators=[DataRequired()])
    MedicoID = SelectField('Médico', coerce=int, validators=[DataRequired()])
    Fecha = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])
    Hora = TimeField('Hora', format='%H:%M', validators=[DataRequired()])
    Duracion = IntegerField('Duración (minutos)', default=60, validators=[DataRequired()])  # Valor por defecto  # Valor por defecto y oculto
    Estado = SelectField('Estado', choices=[('programada', 'Programada'), ('completada', 'Completada'), ('cancelada', 'Cancelada')], validators=[DataRequired()])
    MotivoCita = TextAreaField('Motivo de la Cita', validators=[DataRequired()])
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super(CitaForm, self).__init__(*args, **kwargs)
        if current_user.is_authenticated:
            if 'Paciente' in [role.NombreRol for role in current_user.roles]:
                self.PacienteID.choices = [(current_user.UsuarioID, f"{current_user.Nombres} {current_user.Apellidos}")]
            else:
                self.PacienteID.choices = [(paciente.UsuarioID, f"{paciente.Nombres} {paciente.Apellidos}") for paciente in Usuario.query.join(user_roles).join(Rol).filter(Rol.NombreRol == 'Paciente').all()]
            self.EspecialidadID.choices = [(especialidad.EspecialidadID, especialidad.Nombre) for especialidad in Especialidad.query.all()]
            self.MedicoID.choices = [(medico.MedicoID, f"{medico.Nombre} {medico.Apellidos}") for medico in Medico.query.all()]



class AsignarEspecialidadForm(FlaskForm):
    MedicoID = SelectField('Médico', coerce=int, validators=[DataRequired()])
    EspecialidadID = SelectMultipleField('Especialidades', coerce=int, validators=[DataRequired()])
    Submit = SubmitField('Asignar Especialidades')

class ConsultorioForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción')
    ubicacion = StringField('Ubicación')
    estado = SelectField('Estado', choices=[('Disponible', 'Disponible'), ('No disponible', 'No disponible')], default='Disponible')
    submit = SubmitField('Guardar')

class AsignarConsultorioForm(FlaskForm):
    consultorio_id = SelectField('Consultorio', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    fecha_asignacion = DateField('Fecha de Asignación', validators=[DataRequired()])
    submit = SubmitField('Asignar')

