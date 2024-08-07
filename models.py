from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'Usuarios'
    UsuarioID = db.Column(db.Integer, primary_key=True)
    Identificacion = db.Column(db.String(50), nullable=False)
    Apellidos = db.Column(db.String(100), nullable=False)
    Nombres = db.Column(db.String(100), nullable=False)
    CorreoElectronico = db.Column(db.String(120), unique=True, nullable=False)
    Telefono = db.Column(db.String(15), nullable=True)
    Direccion = db.Column(db.String(200), nullable=True)
    CiudadResidencia = db.Column(db.String(100), nullable=True)
    FechaNacimiento = db.Column(db.Date, nullable=True)
    Genero = db.Column(db.String(10), nullable=True)
    NombreUsuario = db.Column(db.String(20), unique=True, nullable=False)
    Contrasena = db.Column(db.String(60), nullable=False)
    FechaRegistro = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    UltimoAcceso = db.Column(db.DateTime, nullable=True)
    Estado = db.Column(db.String(10), nullable=True)
    RolID = db.Column(db.Integer, db.ForeignKey('Roles.RolID'), nullable=False)

    def get_id(self):
        return self.UsuarioID
    
    
class Rol(db.Model):
    __tablename__ = 'Roles'
    RolID = db.Column(db.Integer, primary_key=True)
    NombreRol = db.Column(db.String(20), unique=True, nullable=False)
    Descripcion = db.Column(db.String(100), nullable=False)
    usuarios = db.relationship('Usuario', backref='rol', lazy=True)

class Paciente(db.Model):
    __tablename__ = 'Pacientes'
    PacienteID = db.Column(db.Integer, primary_key=True)
    UsuarioID = db.Column(db.Integer, db.ForeignKey('Usuarios.UsuarioID'), nullable=False)
    GrupoSanguineo = db.Column(db.String(10), nullable=True)
    Identificacion = db.Column(db.String(50), nullable=False)
    Apellidos = db.Column(db.String(100), nullable=False)
    Nombres = db.Column(db.String(100), nullable=False)
    CorreoElectronico = db.Column(db.String(120), nullable=False)
    Telefono = db.Column(db.String(15), nullable=True)
    Direccion = db.Column(db.String(200), nullable=True)
    CiudadResidencia = db.Column(db.String(100), nullable=True)
    FechaNacimiento = db.Column(db.Date, nullable=True)
    Genero = db.Column(db.String(10), nullable=True)
    UsuarioRegistro = db.Column(db.Integer, db.ForeignKey('Usuarios.UsuarioID'), nullable=False)
    EstadoPaciente = db.Column(db.String(10), nullable=False, default='activo')
    
class Medico(db.Model):
    __tablename__ = 'Medicos'
    MedicoID = db.Column(db.Integer, primary_key=True)
    UsuarioID = db.Column(db.Integer, nullable=True)
    NumeroLicencia = db.Column(db.String(50), nullable=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Apellidos = db.Column(db.String(100), nullable=False)
    CorreoElectronico = db.Column(db.String(100), nullable=False)
    Telefono = db.Column(db.String(15), nullable=True)
    Direccion = db.Column(db.String(255), nullable=True)
    CiudadResidencia = db.Column(db.String(100), nullable=True)
    FechaNacimiento = db.Column(db.Date, nullable=True)
    Genero = db.Column(db.String(10), nullable=True)
    Especialidad = db.Column(db.String(100), nullable=False)
    FechaContratacion = db.Column(db.Date, nullable=True)
    EstadoMedico = db.Column(db.String(10), nullable=False, default='activo')

    # Relación con Horario
    horarios = db.relationship('Horario', backref='medico', lazy=True)




class Especialidad(db.Model):
    __tablename__ = 'Especialidades'
    EspecialidadID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Nombre = db.Column(db.String(100), nullable=False, unique=True)
    Descripcion = db.Column(db.Text, nullable=True)
    FechaRegistro = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    FechaModificacion = db.Column(db.DateTime, nullable=True, onupdate=db.func.current_timestamp())
    UsuarioRegistro = db.Column(db.Integer, db.ForeignKey('Usuarios.UsuarioID'), nullable=False)
    UsuarioModificacion = db.Column(db.Integer, nullable=True)
    Estado = db.Column(db.String(50), nullable=False, default='activo')


class Horario(db.Model):
    __tablename__ = 'Horarios'
    id = db.Column(db.Integer, primary_key=True)
    MedicoID = db.Column(db.Integer, db.ForeignKey('Medicos.MedicoID'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    estado = db.Column(db.String(10), default='activo', nullable=False)

class Cita(db.Model):
    __tablename__ = 'Citas'
    CitaID = db.Column(db.Integer, primary_key=True)
    PacienteID = db.Column(db.Integer, db.ForeignKey('Pacientes.PacienteID'), nullable=False)
    MedicoID = db.Column(db.Integer, db.ForeignKey('Medicos.MedicoID'), nullable=False)
    EspecialidadID = db.Column(db.Integer, db.ForeignKey('Especialidades.EspecialidadID'), nullable=False)
    FechaCita = db.Column(db.DateTime, nullable=False)
    Duracion = db.Column(db.Integer, nullable=False, default=30)
    Estado = db.Column(db.String(20), nullable=False)
    MotivoCita = db.Column(db.String(500), nullable=False)
    FechaRegistro = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    UsuarioRegistro = db.Column(db.Integer, nullable=False)

    paciente = db.relationship('Paciente', backref=db.backref('citas', lazy=True))
    medico = db.relationship('Medico', backref=db.backref('citas', lazy=True))
    especialidad = db.relationship('Especialidad', backref=db.backref('citas', lazy=True))
class MedicoEspecialidad(db.Model):
    __tablename__ = 'MedicosEspecialidades'
    MedicoEspecialidadID = db.Column(db.Integer, primary_key=True)
    MedicoID = db.Column(db.Integer, db.ForeignKey('Medicos.MedicoID'), nullable=False)
    EspecialidadID = db.Column(db.Integer, db.ForeignKey('Especialidades.EspecialidadID'), nullable=False)
    
    medico = db.relationship('Medico', backref='medicos_especialidades')
    especialidad = db.relationship('Especialidad', backref='medicos_especialidades')






