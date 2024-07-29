from flask import Flask,jsonify, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm, PacienteForm,MedicoForm,EspecialidadForm,CreateHorarioForm,CitaForm,AsignarEspecialidadForm,ConsultorioForm, AsignarConsultorioForm
from models import db,Rol,user_roles, Usuario, Paciente, bcrypt, login_manager, Medico,Especialidad,Horario,Cita,MedicoEspecialidad,Catalogo,Consultorio, ConsultorioDoctor
from flask_login import login_user, current_user, logout_user, login_required
import urllib.parse
from datetime import datetime, timedelta,timezone, time  # Importa datetime y timedelta
from utils import export_to_excel
import tempfile
from decorators import role_required 
from flask import g


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Hospital_Loja;UID=Stalin_Utpl;PWD=Sds.152452.")
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect=%s" % params
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.before_request
def before_request():
    if current_user.is_authenticated:
        g.role = current_user.rol.NombreRol
    else:
        g.role = None

@app.context_processor
def inject_roles():
    return dict(role=g.role)


@login_manager.user_loader
def load_user(UsuarioID):
    return Usuario.query.get(int(UsuarioID))


@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home_page():
    return render_template('home.html', title='Inicio', role=g.role)



@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = RegistrationForm()

    # Cargar opciones de ciudades y grupo sanguíneo desde el catálogo
    form.ciudad_residencia.choices = [(c.id, c.valor) for c in Catalogo.query.filter_by(tipo='ciudad').all()]
    form.grupo_sanguineo.choices = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='grupo_sanguineo').all()]
    
    if form.validate_on_submit():
        try:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = Usuario(
                NombreUsuario=form.username.data,
                CorreoElectronico=form.email.data,
                Contrasena=hashed_password,
                RolID=2,  # Ajusta el RolID para que sea el valor correcto
                Identificacion=form.identificacion.data,
                Apellidos=form.apellidos.data,
                Nombres=form.nombres.data,
                Telefono=form.telefono.data,
                Direccion=form.direccion.data,
                CiudadResidencia=form.ciudad_residencia.data,
                FechaNacimiento=form.fecha_nacimiento.data,
                Genero=form.genero.data,
                GrupoSanguineo=form.grupo_sanguineo.data,
                Estado='activo',  # Añade el estado por defecto
                EstadoPaciente='activo'  # Añade el estado de paciente por defecto
            )
            db.session.add(user)
            db.session.commit()
            flash('¡Tu cuenta ha sido creada! Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            db.session.rollback()
            flash('Hubo un error al crear la cuenta. Inténtalo de nuevo.', 'danger')
    else:
        print("Errores de validación del formulario:", form.errors)
    
    return render_template('register.html', title='Registrar', form=form)




@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(CorreoElectronico=form.email.data).first()
        if user and bcrypt.check_password_hash(user.Contrasena, form.password.data):
            login_user(user, remember=form.remember.data)
            user.UltimoAcceso = db.func.current_timestamp()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home_page'))
        else:
            flash('Inicio de sesión fallido. Por favor verifica tu correo electrónico y contraseña', 'danger')
    return render_template('login.html', title='Iniciar sesión', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/patients", methods=['GET', 'POST'])
@login_required
@role_required('Administrador')
def manage_patients():
    # Obtener todos los usuarios con el rol de paciente
    patients = Usuario.query.join(user_roles).join(Rol).filter(Rol.NombreRol == 'Paciente').all()
    return render_template('manage_patients.html', title='Gestionar Pacientes', patients=patients)



@app.route('/patients/new', methods=['GET', 'POST'])
@login_required
def create_patient():
    form = PacienteForm()
    form.ciudad_residencia.choices = [(c.id, c.valor) for c in Catalogo.query.filter_by(tipo='ciudad').all()]
    form.genero.choices = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='genero').all()]
    form.grupo_sanguineo.choices = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='grupo_sanguineo').all()]
    
    if form.validate_on_submit():
        existing_user = Usuario.query.filter(
            (Usuario.Identificacion == form.identificacion.data) |
            (Usuario.CorreoElectronico == form.correo_electronico.data)
        ).first()
        
        if existing_user:
            flash('Error: Ya existe un paciente con esa identificación o correo electrónico.', 'danger')
        else:
            try:
                patient = Usuario(
                    Identificacion=form.identificacion.data,
                    Apellidos=form.apellidos.data,
                    Nombres=form.nombres.data,
                    CorreoElectronico=form.correo_electronico.data,
                    Telefono=form.telefono.data,
                    Direccion=form.direccion.data,
                    CiudadResidencia=form.ciudad_residencia.data,
                    FechaNacimiento=form.fecha_nacimiento.data,
                    Genero=form.genero.data,
                    GrupoSanguineo=form.grupo_sanguineo.data,
                    RolID=2,  # Rol de paciente
                    EstadoPaciente=form.estado_paciente.data,
                    Estado='activo'
                )
                db.session.add(patient)
                db.session.commit()
                flash('Paciente creado exitosamente', 'success')
                return redirect(url_for('manage_patients'))
            except Exception as e:
                db.session.rollback()
                flash('Error al crear el paciente: ' + str(e), 'danger')
    else:
        print(form.errors)  # Imprime los errores de validación en la consola
    return render_template('create_patient.html', title='Añadir Paciente', form=form)

@app.route("/patients/<int:patient_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Usuario.query.get_or_404(patient_id)
    form = PacienteForm(obj=patient)
    
    # Cargar opciones de catálogos
    ciudades = [(c.id, c.valor) for c in Catalogo.query.filter_by(tipo='ciudad').all()]
    generos = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='genero').all()]
    grupos_sanguineos = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='grupo_sanguineo').all()]

    form.ciudad_residencia.choices = ciudades
    form.genero.choices = generos
    form.grupo_sanguineo.choices = grupos_sanguineos

    if form.validate_on_submit():
        patient.Identificacion = form.identificacion.data
        patient.Apellidos = form.apellidos.data
        patient.Nombres = form.nombres.data
        patient.CorreoElectronico = form.correo_electronico.data
        patient.Telefono = form.telefono.data
        patient.Direccion = form.direccion.data
        patient.CiudadResidencia = form.ciudad_residencia.data
        patient.FechaNacimiento = form.fecha_nacimiento.data
        patient.Genero = form.genero.data
        patient.GrupoSanguineo = form.grupo_sanguineo.data
        patient.EstadoPaciente = form.estado_paciente.data 
        db.session.commit()
        flash('Paciente actualizado exitosamente', 'success')
        return redirect(url_for('manage_patients'))

    # Preseleccionar valores actuales del paciente
    form.ciudad_residencia.data = patient.CiudadResidencia
    form.genero.data = patient.Genero
    form.grupo_sanguineo.data = patient.GrupoSanguineo

    return render_template('edit_patient.html', title='Editar Paciente', form=form, patient=patient)

@app.route("/patients/<int:patient_id>/delete", methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = Usuario.query.get_or_404(patient_id)
    patient.EstadoPaciente = 'inactivo'  # Cambia el estado a 'inactivo' en lugar de eliminar
    db.session.commit()
    flash('El estado del paciente ha sido cambiado a inactivo', 'success')
    return redirect(url_for('manage_patients'))


@app.route("/doctors", methods=['GET'])
@login_required
def manage_doctors():
    
    doctors = Medico.query.all()
    return render_template('manage_doctors.html', title='Gestionar Médicos', doctors=doctors)

@app.route("/doctors/create", methods=['GET', 'POST'])
@login_required
def create_doctor():
    form = MedicoForm()
    form.ciudad_residencia.choices = [(c.id, c.valor) for c in Catalogo.query.filter_by(tipo='ciudad').all()]
    form.genero.choices = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='genero').all()]
    form.especialidad.choices = [(e.EspecialidadID, e.Nombre) for e in Especialidad.query.all()]
    if form.validate_on_submit():
        doctor = Medico(
            UsuarioID=current_user.UsuarioID,
            NumeroLicencia=form.numero_licencia.data,
            Nombre=form.nombre.data,
            Apellidos=form.apellidos.data,
            CorreoElectronico=form.correo_electronico.data,
            Telefono=form.telefono.data,
            Direccion=form.direccion.data,
            CiudadResidencia=form.ciudad_residencia.data,
            FechaNacimiento=form.fecha_nacimiento.data,
            Genero=form.genero.data,
            Especialidad=form.especialidad.data,
            FechaContratacion=form.fecha_contratacion.data,
            EstadoMedico='activo'
        )
        db.session.add(doctor)
        db.session.commit()
        flash('El médico ha sido añadido exitosamente!', 'success')
        return redirect(url_for('manage_doctors'))
    return render_template('create_doctor.html', title='Añadir Médico', form=form)

@app.route("/doctors/<int:doctor_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    doctor = Medico.query.get_or_404(doctor_id)
    form = MedicoForm(obj=doctor)
    # Cargar opciones de catálogos
    CiudadResidencia = [(c.valor, c.valor) for c in Catalogo.query.filter_by(tipo='ciudad').all()]
    Genero = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='genero').all()]


    if form.validate_on_submit():

        doctor.NumeroLicencia = form.numero_licencia.data
        doctor.Nombre = form.nombre.data
        doctor.Apellidos = form.apellidos.data
        doctor.CorreoElectronico = form.correo_electronico.data
        doctor.Telefono = form.telefono.data
        doctor.Direccion = form.direccion.data
        doctor.CiudadResidencia = form.ciudad_residencia.data
        doctor.FechaNacimiento = form.fecha_nacimiento.data
        doctor.Genero = form.genero.data
        doctor.Especialidad = form.especialidad.data
        doctor.FechaContratacion = form.fecha_contratacion.data
        doctor.EstadoMedico = form.estado_medico.data
        db.session.commit()
        flash('El médico ha sido actualizado!', 'success')
        return redirect(url_for('manage_doctors'))
    return render_template('edit_doctor.html', title='Editar Médico', form=form, doctor=doctor)




@app.route("/doctors/<int:doctor_id>/delete", methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    doctor = Medico.query.get_or_404(doctor_id)
    doctor.EstadoMedico = 'inactivo'
    db.session.commit()
    flash('El médico ha sido desactivado!', 'success')
    return redirect(url_for('manage_doctors'))



@app.route('/manage_specialties', methods=['GET', 'POST'])
@login_required
def manage_specialties():
    specialties = Especialidad.query.all()
    #specialties = Especialidad.query.filter_by(Estado='activo').all()
    return render_template('manage_specialties.html', title='Gestionar Especialidades', specialties=specialties)


@app.route('/create_specialty', methods=['GET', 'POST'])
@login_required
def create_specialty():
    form = EspecialidadForm()
    if form.validate_on_submit():
        specialty = Especialidad(
            Nombre=form.nombre.data,
            Descripcion=form.descripcion.data,
            UsuarioRegistro=current_user.UsuarioID,
            Estado=form.estado.data
        )
        db.session.add(specialty)
        db.session.commit()
        flash('Especialidad creada exitosamente!', 'success')
        return redirect(url_for('manage_specialties'))
    return render_template('create_specialty.html', title='Crear Especialidad', form=form)


@app.route('/specialty/<int:specialty_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_specialty(specialty_id):
    specialty = Especialidad.query.get_or_404(specialty_id)
    form = EspecialidadForm(obj=specialty)
    if form.validate_on_submit():
        specialty.Nombre = form.nombre.data
        specialty.Descripcion = form.descripcion.data
        specialty.Estado = form.estado.data
        specialty.UsuarioModificacion = current_user.UsuarioID
        db.session.commit()
        flash('Especialidad actualizada exitosamente!', 'success')
        return redirect(url_for('manage_specialties'))
    return render_template('edit_specialty.html', title='Editar Especialidad', form=form, specialty=specialty)

@app.route('/specialty/<int:specialty_id>/delete', methods=['POST'])
@login_required
def delete_specialty(specialty_id):
    specialty = Especialidad.query.get_or_404(specialty_id)
    specialty.Estado = 'inactivo'
    specialty.UsuarioModificacion = current_user.UsuarioID
    db.session.commit()
    flash('Especialidad desactivada exitosamente!', 'success')
    return redirect(url_for('manage_specialties'))

@app.route('/create_horario', methods=['GET', 'POST'])
@login_required
def create_horario():
    form = CreateHorarioForm()
    
    # Configurar choices para el SelectField con nombre completo
    form.MedicoID.choices = [(medico.MedicoID, f"{medico.Nombre} {medico.Apellidos}") for medico in Medico.query.all()]

    if form.validate_on_submit():
        try:
            # Crear horarios por defecto de lunes a viernes
            days_of_week = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
            horarios = []
            for day in days_of_week:
                # Verificar si ya existe el horario de la mañana
                exists_morning = Horario.query.filter_by(
                    MedicoID=form.MedicoID.data,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(12, 0)
                ).first()
                
                if not exists_morning:
                    horario_morning = Horario(
                        MedicoID=form.MedicoID.data,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(12, 0),
                        estado=form.estado.data
                    )
                    horarios.append(horario_morning)
                
                # Verificar si ya existe el horario de la tarde
                exists_afternoon = Horario.query.filter_by(
                    MedicoID=form.MedicoID.data,
                    day_of_week=day,
                    start_time=time(16, 0),
                    end_time=time(18, 0)
                ).first()
                
                if not exists_afternoon:
                    horario_afternoon = Horario(
                        MedicoID=form.MedicoID.data,
                        day_of_week=day,
                        start_time=time(16, 0),
                        end_time=time(18, 0),
                        estado=form.estado.data
                    )
                    horarios.append(horario_afternoon)

            if horarios:
                db.session.add_all(horarios)
                db.session.commit()
                flash('Horarios creados exitosamente!', 'success')
            else:
                flash('No se crearon horarios porque ya existen.', 'info')
            
            return redirect(url_for('manage_horarios'))
        except Exception as e:
            db.session.rollback()
            flash('Error al crear los horarios: ' + str(e), 'error')

    return render_template('create_horario.html', title='Crear Horario', form=form)


@app.route('/edit_horario/<int:horario_id>', methods=['GET', 'POST'])
@login_required
def edit_horario(horario_id):
    horario = Horario.query.get_or_404(horario_id)
    form = CreateHorarioForm(obj=horario)
    form.MedicoID.choices = [(doctor.MedicoID, doctor.Nombre) for doctor in Medico.query.all()]

    if form.validate_on_submit():
        horario.MedicoID = form.MedicoID.data
        horario.day_of_week = form.day_of_week.data
        horario.start_time = form.start_time.data
        horario.end_time = form.end_time.data
        horario.estado = form.estado.data
        db.session.commit()
        flash('Horario actualizado exitosamente!', 'success')
        return redirect(url_for('manage_horarios'))
    
    form.estado.data = horario.estado  # Utilizar 'estado' en minúsculas
    return render_template('edit_horario.html', form=form, horario=horario)



@app.route('/manage_horarios')
def manage_horarios():
    horarios = Horario.query.all()
    dias_semana = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    return render_template('manage_horarios.html', horarios=horarios, dias_semana=dias_semana)


@app.route('/horario/<int:horario_id>/delete', methods=['POST'])
@login_required
def delete_horario(horario_id):
    horario = Horario.query.get_or_404(horario_id)
    horario.Estado = 'inactivo'
    db.session.commit()
    flash('Horario desactivado exitosamente!', 'success')
    return redirect(url_for('manage_horarios'))


@app.route('/asignar_especialidades', methods=['GET', 'POST'])
@login_required
def asignar_especialidades():
    form = AsignarEspecialidadForm()
    form.MedicoID.choices = [(m.MedicoID, f"{m.Nombre} {m.Apellidos}") for m in Medico.query.all()]
    form.EspecialidadID.choices = [(e.EspecialidadID, e.Nombre) for e in Especialidad.query.all()]

    if form.validate_on_submit():
        medico_id = form.MedicoID.data
        especialidades = form.EspecialidadID.data

        # Eliminar las especialidades existentes para el médico seleccionado
        MedicoEspecialidad.query.filter_by(MedicoID=medico_id).delete()

        # Añadir las nuevas especialidades seleccionadas si no existen
        for especialidad_id in especialidades:
            exists = MedicoEspecialidad.query.filter_by(MedicoID=medico_id, EspecialidadID=especialidad_id).first()
            if not exists:
                nueva_especialidad = MedicoEspecialidad(MedicoID=medico_id, EspecialidadID=especialidad_id)
                db.session.add(nueva_especialidad)

        db.session.commit()
        flash('Especialidades asignadas exitosamente!', 'success')
        return redirect(url_for('asignar_especialidades'))

    return render_template('asignar_especialidades.html', form=form)


@app.route('/get_medicos/<int:especialidad_id>')
@login_required
def get_medicos(especialidad_id):
    medicos = Medico.query.join(MedicoEspecialidad).filter(MedicoEspecialidad.EspecialidadID == especialidad_id).all()
    medicos_data = [{'MedicoID': medico.MedicoID, 'Nombre': medico.Nombre} for medico in medicos]
    return jsonify(medicos_data)




#citas-------------------------------------------

from utils import export_to_excel
import os


@app.route('/manage_citas', methods=['GET'])
@login_required
def manage_citas():
    search_paciente = request.args.get('search_paciente')
    search_paciente_id = request.args.get('search_paciente_id')
    
    query = Cita.query
    
    if search_paciente:
        query = query.join(Usuario).filter(Usuario.Nombres.ilike(f'%{search_paciente}%') | Usuario.Apellidos.ilike(f'%{search_paciente}%'))
    
    if search_paciente_id:
        query = query.filter(Cita.UsuarioID == search_paciente_id)  # Actualizado
    
    citas = query.all()
    
    return render_template('manage_citas.html', citas=citas)

@app.route('/download_excel', methods=['GET'])
@login_required
def download_excel():
    search_paciente = request.args.get('search_paciente')
    search_paciente_id = request.args.get('search_paciente_id')
    
    query = Cita.query
    
    if search_paciente:
        query = query.join(Usuario).filter(Usuario.Nombres.ilike(f'%{search_paciente}%') | Usuario.Apellidos.ilike(f'%{search_paciente}%'))
    
    if search_paciente_id:
        query = query.filter(Cita.UsuarioID == search_paciente_id)  # Actualizado
    
    return export_to_excel(query.all())

@app.route('/create_cita', methods=['GET', 'POST'])
@login_required
def create_cita():
    form = CitaForm()
    
    # Obtener pacientes (usuarios con el rol de Paciente)
    pacientes = Usuario.query.join(user_roles).join(Rol).filter(Rol.NombreRol == 'Paciente').all()
    form.PacienteID.choices = [(paciente.UsuarioID, f"{paciente.Nombres} {paciente.Apellidos}") for paciente in pacientes]
    
    # Configurar choices para los SelectFields con nombre completo
    form.EspecialidadID.choices = [(especialidad.EspecialidadID, especialidad.Nombre) for especialidad in Especialidad.query.all()]
    form.MedicoID.choices = [(medico.MedicoID, f"{medico.Nombre} {medico.Apellidos}") for medico in Medico.query.all()]
    
    if form.validate_on_submit():
        try:
            print("Datos del formulario recibidos:", form.data)
            fecha_str = request.form['Fecha'] + ' ' + request.form['Hora']
            fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
            cita = Cita(
                UsuarioID=form.PacienteID.data,
                MedicoID=form.MedicoID.data,
                EspecialidadID=form.EspecialidadID.data,
                FechaCita=fecha_cita,
                Duracion=form.Duracion.data,
                Estado=form.Estado.data,
                MotivoCita=form.MotivoCita.data,
                FechaRegistro=datetime.now(timezone.utc),
                UsuarioRegistro=current_user.UsuarioID  # Asigna el ID del usuario actual
            )
            print("Objeto cita creado:", cita)
            db.session.add(cita)
            db.session.commit()
            print("Cita guardada en la base de datos")
            flash('Cita creada exitosamente!', 'success')
            return redirect(url_for('manage_citas'))
        except Exception as e:
            print("Error al crear la cita:", str(e))
            db.session.rollback()
            flash('Error al crear la cita: ' + str(e), 'error')
    else:
        print("Errores de validación del formulario:", form.errors)
    
    return render_template('create_cita.html', title='Crear Cita', form=form)


# app.py

from utils import update_horarios_disponibles

# ... tu código existente ...

@app.route('/get_horas_disponibles/<int:medico_id>/<string:fecha>', methods=['GET'])
@login_required
def get_horas_disponibles(medico_id, fecha):
    try:
        print(f"Recibido medico_id: {medico_id}, fecha: {fecha}")
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        day_of_week = fecha.strftime('%A')  # Obtenemos el día de la semana en inglés
        
        # Traducción de los días de la semana al español
        days_translation = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        day_of_week_spanish = days_translation.get(day_of_week, '')
        
        # Verificar que day_of_week_spanish es correcto
        print(f"Día de la semana (español): {day_of_week_spanish}")

        # Obtener los horarios del médico para el día especificado
        horarios = Horario.query.filter_by(MedicoID=medico_id, day_of_week=day_of_week_spanish).all()
        print(f"Horarios del médico: {horarios}")

        if not horarios:
            return jsonify([])

        # Obtener las citas programadas del médico para el día especificado
        start_time = datetime.combine(fecha, time.min)
        end_time = datetime.combine(fecha, time.max)
        citas = Cita.query.filter(
            Cita.MedicoID == medico_id,
            Cita.FechaCita >= start_time,
            Cita.FechaCita <= end_time,
            Cita.Estado == 'programada'
        ).all()

        # Crear un conjunto de horas ocupadas
        booked_hours = {cita.FechaCita.strftime('%H:%M') for cita in citas}

        # Imprimir detalles de las citas ocupadas
        for cita in citas:
            print(f"Cita ocupada: {cita.FechaCita.strftime('%H:%M')} con estado {cita.Estado}")

        # Crear un conjunto de horas disponibles basadas en los horarios del médico
        available_hours = set()
        for horario in horarios:
            current_time = datetime.combine(fecha, horario.start_time)
            horario_end_time = datetime.combine(fecha, horario.end_time)
            while current_time < horario_end_time:
                hora_str = current_time.strftime('%H:%M')
                if hora_str not in booked_hours:
                    available_hours.add(hora_str)
                current_time += timedelta(minutes=60)

        print(f"Booked hours: {booked_hours}")
        print(f"Available hours: {available_hours}")

        return jsonify(sorted(available_hours))
    except ValueError as e:
        print(f"Error en el formato de fecha: {e}")
        return jsonify({"error": "Formato de fecha inválido"}), 400
    except Exception as e:
        print(f"Error inesperado: {e}")
        return jsonify({"error": "Error inesperado"}), 500


@app.route('/edit_cita/<int:cita_id>', methods=['GET', 'POST'])
@login_required
def edit_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    form = CitaForm(obj=cita)
    
    # Obtener pacientes (usuarios con el rol de Paciente)
    pacientes = Usuario.query.join(user_roles).join(Rol).filter(Rol.NombreRol == 'Paciente').all()
    form.PacienteID.choices = [(paciente.UsuarioID, f"{paciente.Nombres} {paciente.Apellidos}") for paciente in pacientes]
    
    # Configurar choices para los SelectFields
    form.EspecialidadID.choices = [(especialidad.EspecialidadID, especialidad.Nombre) for especialidad in Especialidad.query.all()]
    form.MedicoID.choices = [(medico.MedicoID, f"{medico.Nombre} {medico.Apellidos}") for medico in Medico.query.all()]

    # Prellenar los campos Fecha y Hora con los valores actuales de la cita
    if request.method == 'GET':
        form.Fecha.data = cita.FechaCita.date()
        form.Hora.data = cita.FechaCita.time()

    if form.validate_on_submit():
        try:
            # Verificar el número de citas programadas para el paciente
            num_citas_programadas = Cita.query.filter_by(
                UsuarioID=form.PacienteID.data,
                Estado='programada'
            ).count()

            if num_citas_programadas >= 2 and cita.Estado == 'programada' and form.Estado.data == 'programada':
                flash('El paciente ya tiene el máximo de 2 citas programadas.', 'error')
                return redirect(url_for('edit_cita', cita_id=cita_id))

            fecha_str = form.Fecha.data.strftime('%Y-%m-%d') + ' ' + form.Hora.data.strftime('%H:%M')
            fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
            cita.PacienteID = form.PacienteID.data
            cita.MedicoID = form.MedicoID.data
            cita.EspecialidadID = form.EspecialidadID.data
            cita.FechaCita = fecha_cita
            cita.Duracion = form.Duracion.data
            cita.Estado = form.Estado.data
            cita.MotivoCita = form.MotivoCita.data
            db.session.commit()
            flash('Cita actualizada exitosamente!', 'success')

            # Recalcular horarios disponibles solo si la cita fue cancelada
            if form.Estado.data == 'cancelada':
                update_horarios_disponibles(cita.MedicoID, fecha_cita)

            return redirect(url_for('manage_citas'))
        except Exception as e:
            print("Error al actualizar la cita:", str(e))
            db.session.rollback()
            flash('Error al actualizar la cita: ' + str(e), 'error')
    else:
        print("Errores de validación del formulario:", form.errors)

    return render_template('edit_cita.html', title='Editar Cita', form=form, cita=cita)

@app.route('/delete_cita/<int:cita_id>', methods=['POST'])
@login_required
def delete_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    cita.Estado = 'cancelada'
    db.session.commit()
    
    # Actualizar horarios disponibles
    update_horarios_disponibles(cita.MedicoID, cita.FechaCita)
    
    flash('Cita cancelada exitosamente!', 'success')
    return redirect(url_for('manage_citas'))

#rutas nuevas para el nuevo requerimiento



@app.route("/consultorios/new", methods=['GET', 'POST'])
@login_required
def create_consultorio():
    form = ConsultorioForm()
    if form.validate_on_submit():
        consultorio = Consultorio(
            codigo=form.codigo.data,
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            ubicacion=form.ubicacion.data,
            estado=form.estado.data
        )
        db.session.add(consultorio)
        db.session.commit()
        flash('Consultorio creado exitosamente', 'success')
        return redirect(url_for('manage_consultorios'))
    return render_template('create_consultorio.html', title='Añadir Consultorio', form=form)

@app.route("/consultorios")
@login_required
def manage_consultorios():
    consultorios = Consultorio.query.all()
    return render_template('manage_consultorios.html', title='Gestionar Consultorios', consultorios=consultorios)


@app.route("/asignar_consultorio", methods=['GET', 'POST'])
@login_required
def asignar_consultorio():
    form = AsignarConsultorioForm()
    form.consultorio_id.choices = [(c.id, c.nombre) for c in Consultorio.query.all()]
    form.doctor_id.choices = [(d.MedicoID, f"{d.Nombre} {d.Apellidos}") for d in Medico.query.all()]
    
    if form.validate_on_submit():
        fecha_asignacion = datetime.combine(form.fecha_asignacion.data, datetime.min.time()).replace(tzinfo=timezone.utc)
        asignacion = ConsultorioDoctor(
            consultorio_id=form.consultorio_id.data,
            doctor_id=form.doctor_id.data,
            fecha_asignacion=fecha_asignacion
        )
        db.session.add(asignacion)
        db.session.commit()
        flash('Consultorio asignado exitosamente!', 'success')
        return redirect(url_for('manage_asignaciones'))
    
    return render_template('asignar_consultorio.html', title='Asignar Consultorio', form=form)



@app.route("/asignaciones")
@login_required
def manage_asignaciones():
    asignaciones = ConsultorioDoctor.query.all()
    return render_template('manage_asignaciones.html', title='Gestionar Asignaciones', asignaciones=asignaciones)

@app.route("/reporte_consultorios", methods=['GET'])
@login_required
def reporte_consultorios():
    consultorios = db.session.query(
        Consultorio.id,
        Consultorio.nombre,
        Medico.Nombre,
        Medico.Apellidos,
        Especialidad.Nombre.label("especialidad_nombre"),
        ConsultorioDoctor.fecha_asignacion
    ).outerjoin(ConsultorioDoctor, Consultorio.id == ConsultorioDoctor.consultorio_id) \
    .outerjoin(Medico, ConsultorioDoctor.doctor_id == Medico.MedicoID) \
    .outerjoin(Especialidad, Medico.Especialidad == Especialidad.EspecialidadID).all()
    
    reporte_data = []
    for c in consultorios:
        estado = "Disponible" if c.Nombre is None else "No disponible"
        reporte_data.append({
            "consultorio": c.nombre,
            "doctor": f"{c.Nombre} {c.Apellidos}" if c.Nombre else "",
            "especialidad": c.especialidad_nombre if c.especialidad_nombre else "",
            "fecha_asignacion": c.fecha_asignacion.strftime('%Y-%m-%d') if c.fecha_asignacion else "",
            "estado": estado
        })
    
    return render_template('reporte_consultorios.html', title='Reporte de Consultorios', reporte_data=reporte_data)

@app.route("/perfil_paciente", methods=['GET', 'POST'])
@login_required
@role_required('Paciente')
def perfil_paciente():
    try:
        print("Accediendo a perfil_paciente...")
        print(f"ID del usuario actual: {current_user.UsuarioID}")
        print(f"Rol del usuario actual: {current_user.rol.NombreRol}")

        patient = Usuario.query.filter_by(UsuarioID=current_user.UsuarioID).first()

        if not patient:
            flash('No se encontró un perfil de paciente para este usuario.', 'error')
            return redirect(url_for('home_page'))

        form = PacienteForm(obj=patient)

        # Cargar opciones de catálogos
        ciudades = [(c.id, c.valor) for c in Catalogo.query.filter_by(tipo='ciudad').all()]
        generos = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='genero').all()]
        grupos_sanguineos = [(g.valor, g.valor) for g in Catalogo.query.filter_by(tipo='grupo_sanguineo').all()]

        form.ciudad_residencia.choices = ciudades
        form.genero.choices = generos
        form.grupo_sanguineo.choices = grupos_sanguineos

        if form.validate_on_submit():
            patient.Identificacion = form.identificacion.data
            patient.Apellidos = form.apellidos.data
            patient.Nombres = form.nombres.data
            patient.CorreoElectronico = form.correo_electronico.data
            patient.Telefono = form.telefono.data
            patient.Direccion = form.direccion.data
            patient.CiudadResidencia = form.ciudad_residencia.data
            patient.FechaNacimiento = form.fecha_nacimiento.data
            patient.Genero = form.genero.data
            patient.GrupoSanguineo = form.grupo_sanguineo.data

            # Actualizar contraseña si se proporciona una nueva
            if form.password.data:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                patient.Contrasena = hashed_password

            db.session.commit()
            flash('Perfil actualizado exitosamente', 'success')
            return redirect(url_for('perfil_paciente'))

        # Preseleccionar valores actuales del paciente
        form.identificacion.data = patient.Identificacion
        form.apellidos.data = patient.Apellidos
        form.nombres.data = patient.Nombres
        form.correo_electronico.data = patient.CorreoElectronico
        form.telefono.data = patient.Telefono
        form.direccion.data = patient.Direccion
        form.ciudad_residencia.data = patient.CiudadResidencia
        form.fecha_nacimiento.data = patient.FechaNacimiento
        form.genero.data = patient.Genero
        form.grupo_sanguineo.data = patient.GrupoSanguineo

        return render_template('perfil_paciente.html', title='Mi Perfil', form=form)
    except Exception as e:
        print(f"Error en perfil_paciente: {str(e)}")
        flash('Ocurrió un error al acceder al perfil del paciente.', 'error')
        return redirect(url_for('home_page'))




#perfil del paciente
from utils import export_to_excel
import os


@app.route('/paciente/citas', methods=['GET'])
@login_required
@role_required('Paciente')
def paciente_citas():
    search_medico = request.args.get('search_medico')
    search_especialidad = request.args.get('search_especialidad')
    
    query = Cita.query.filter_by(UsuarioID=current_user.UsuarioID)
    
    if search_medico:
        query = query.join(Medico).filter(Medico.Nombre.ilike(f'%{search_medico}%') | Medico.Apellidos.ilike(f'%{search_medico}%'))
    
    if search_especialidad:
        query = query.join(Especialidad).filter(Especialidad.Nombre.ilike(f'%{search_especialidad}%'))
    
    citas = query.all()
    
    return render_template('paciente_citas.html', citas=citas)


@app.route("/paciente/citas/nueva", methods=['GET', 'POST'])
@login_required
@role_required('Paciente')
def paciente_crear_cita():
    form = CitaForm()
    form.EspecialidadID.choices = [(especialidad.EspecialidadID, especialidad.Nombre) for especialidad in Especialidad.query.all()]
    form.MedicoID.choices = [(medico.MedicoID, f"{medico.Nombre} {medico.Apellidos}") for medico in Medico.query.all()]
    
    # Verificar el número de citas programadas del paciente
    citas_programadas = Cita.query.filter_by(UsuarioID=current_user.UsuarioID, Estado='programada').count()
    if citas_programadas >= 2:
        flash('Ya tienes el número máximo de 2 citas programadas.', 'danger')
        return redirect(url_for('paciente_citas'))
    
    if form.validate_on_submit():
        fecha_str = request.form['Fecha'] + ' ' + request.form['Hora']
        fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
        cita = Cita(
            UsuarioID=current_user.UsuarioID,
            MedicoID=form.MedicoID.data,
            EspecialidadID=form.EspecialidadID.data,
            FechaCita=fecha_cita,
            Duracion=form.Duracion.data,
            Estado=form.Estado.data,
            MotivoCita=form.MotivoCita.data,
            FechaRegistro=datetime.now(timezone.utc),
            UsuarioRegistro=current_user.UsuarioID
        )
        db.session.add(cita)
        db.session.commit()
        flash('Cita creada exitosamente', 'success')
        return redirect(url_for('paciente_citas'))
    
    return render_template('paciente_crear_cita.html', title='Nueva Cita', form=form)


@app.route('/paciente/citas/<int:cita_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('Paciente')
def paciente_edit_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    if cita.UsuarioID != current_user.UsuarioID:
        flash('No tienes permiso para editar esta cita.', 'error')
        return redirect(url_for('paciente_citas'))

    form = CitaForm(obj=cita)
    
    form.EspecialidadID.choices = [(especialidad.EspecialidadID, especialidad.Nombre) for especialidad in Especialidad.query.all()]
    form.MedicoID.choices = [(medico.MedicoID, f"{medico.Nombre} {medico.Apellidos}") for medico in Medico.query.all()]

    # Prellenar los campos Fecha y Hora con los valores actuales de la cita
    if request.method == 'GET':
        form.Fecha.data = cita.FechaCita.date()
        form.Hora.data = cita.FechaCita.time()

    if form.validate_on_submit():
        try:
            fecha_str = form.Fecha.data.strftime('%Y-%m-%d') + ' ' + form.Hora.data.strftime('%H:%M')
            fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
            cita.MedicoID = form.MedicoID.data
            cita.EspecialidadID = form.EspecialidadID.data
            cita.FechaCita = fecha_cita
            cita.Duracion = form.Duracion.data
            cita.Estado = form.Estado.data
            cita.MotivoCita = form.MotivoCita.data
            db.session.commit()
            flash('Cita actualizada exitosamente!', 'success')
            return redirect(url_for('paciente_citas'))
        except Exception as e:
            print("Error al actualizar la cita:", str(e))
            db.session.rollback()
            flash('Error al actualizar la cita: ' + str(e), 'error')
    else:
        print("Errores de validación del formulario:", form.errors)

    return render_template('paciente_edit_cita.html', title='Editar Cita', form=form, cita=cita)


@app.route('/paciente/citas/<int:cita_id>/cancelar', methods=['POST'])
@login_required
@role_required('Paciente')
def paciente_cancelar_cita(cita_id):
    cita = Cita.query.get_or_404(cita_id)
    if cita.UsuarioID != current_user.UsuarioID:
        flash('No tienes permiso para cancelar esta cita.', 'error')
        return redirect(url_for('paciente_citas'))

    cita.Estado = 'cancelada'
    db.session.commit()
    flash('Cita cancelada exitosamente!', 'success')
    return redirect(url_for('paciente_citas'))



if __name__ == '__main__':
    app.run(debug=True)