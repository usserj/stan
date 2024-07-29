from flask import Flask,jsonify, render_template, url_for, flash, redirect, request
from forms import RegistrationForm, LoginForm, PacienteForm,MedicoForm,EspecialidadForm,CreateHorarioForm,CitaForm,AsignarEspecialidadForm
from models import db, Usuario, Paciente, bcrypt, login_manager, Medico,Especialidad,Horario,Cita,MedicoEspecialidad
from flask_login import login_user, current_user, logout_user, login_required
import urllib.parse
from datetime import datetime, timedelta,timezone, time  # Importa datetime y timedelta
from utils import export_to_excel
import tempfile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=Hospital_Loja;UID=Stalin_Utpl;PWD=Sds.152452.")
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect=%s" % params
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Usuario(
            NombreUsuario=form.username.data,
            CorreoElectronico=form.email.data,
            Contrasena=hashed_password,
            RolID=2,  # Ajusta el RolID según sea necesario
            Identificacion=form.identificacion.data,
            Apellidos=form.apellidos.data,
            Nombres=form.nombres.data,
            Telefono=form.telefono.data,
            Direccion=form.direccion.data,
            CiudadResidencia=form.ciudad_residencia.data,
            FechaNacimiento=form.fecha_nacimiento.data,
            Genero=form.genero.data
        )
        db.session.add(user)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('login'))
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

@app.route("/home")
@login_required
def home_page():
    return render_template('home.html', title='Inicio')

@app.route("/patients", methods=['GET', 'POST'])
@login_required
def manage_patients():
    patients = Paciente.query.all()
    #patients = Paciente.query.filter_by(EstadoPaciente='activo').all()  # Filtrar solo pacientes activos
    return render_template('manage_patients.html', title='Gestionar Pacientes', patients=patients)


@app.route('/patients/new', methods=['GET', 'POST'])
@login_required
def create_patient():
    form = PacienteForm()
    if form.validate_on_submit():
        if current_user and current_user.UsuarioID:
            patient = Paciente(
                UsuarioID=current_user.UsuarioID,
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
                UsuarioRegistro=current_user.UsuarioID,
                EstadoPaciente=form.estado_paciente.data
            )
            db.session.add(patient)
            db.session.commit()
            flash('Paciente creado exitosamente', 'success')
            return redirect(url_for('manage_patients'))
        else:
            flash('Error: Usuario no autenticado.', 'danger')
    return render_template('create_patient.html', title='Añadir Paciente', form=form)


@app.route("/patients/<int:patient_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Paciente.query.get_or_404(patient_id)
    form = PacienteForm(obj=patient)
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
    return render_template('edit_patient.html', title='Editar Paciente', form=form, patient=patient)

@app.route("/patients/<int:patient_id>/delete", methods=['POST'])
@login_required
def delete_patient(patient_id):
    patient = Paciente.query.get_or_404(patient_id)
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
        query = query.join(Paciente).filter(Paciente.Nombres.ilike(f'%{search_paciente}%') | Paciente.Apellidos.ilike(f'%{search_paciente}%'))
    
    if search_paciente_id:
        query = query.filter(Cita.PacienteID == search_paciente_id)
    
    citas = query.all()
    
    return render_template('manage_citas.html', citas=citas)

@app.route('/download_excel', methods=['GET'])
@login_required
def download_excel():
    search_paciente = request.args.get('search_paciente')
    search_paciente_id = request.args.get('search_paciente_id')
    
    query = Cita.query
    
    if search_paciente:
        query = query.join(Paciente).filter(Paciente.Nombres.ilike(f'%{search_paciente}%') | Paciente.Apellidos.ilike(f'%{search_paciente}%'))
    
    if search_paciente_id:
        query = query.filter(Cita.PacienteID == search_paciente_id)
    
    return export_to_excel(query.all())

@app.route('/create_cita', methods=['GET', 'POST'])
@login_required
def create_cita():
    form = CitaForm()
    
    # Configurar choices para los SelectFields con nombre completo
    form.PacienteID.choices = [(paciente.PacienteID, f"{paciente.Nombres} {paciente.Apellidos}") for paciente in Paciente.query.all()]  # Cambiar esta línea
    form.EspecialidadID.choices = [(especialidad.EspecialidadID, especialidad.Nombre) for especialidad in Especialidad.query.all()]
    form.MedicoID.choices = [(medico.MedicoID, f"{medico.Nombre} {medico.Apellidos}") for medico in Medico.query.all()]
    
    if form.validate_on_submit():
        try:
            print("Datos del formulario recibidos:", form.data)
            fecha_str = request.form['Fecha'] + ' ' + request.form['Hora']
            fecha_cita = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
            cita = Cita(
                PacienteID=form.PacienteID.data,
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

@app.route('/get_horas_disponibles/<int:medico_id>/<string:fecha>', methods=['GET'])
@login_required
def get_horas_disponibles(medico_id, fecha):
    try:
        print(f"Recibido medico_id: {medico_id}, fecha: {fecha}")
        fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        start_time = datetime.combine(fecha, time.min)
        end_time = datetime.combine(fecha, time.max)
        
        citas = Cita.query.filter(
            Cita.MedicoID == medico_id,
            Cita.FechaCita >= start_time,
            Cita.FechaCita <= end_time
        ).all()
        
        booked_hours = {cita.FechaCita.strftime('%H:%M') for cita in citas}
        available_hours = {f"{hour:02d}:00" for hour in range(8, 17)} - booked_hours
        
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
    
    # Configurar choices para los SelectFields
    form.PacienteID.choices = [(paciente.PacienteID, paciente.Nombres) for paciente in Paciente.query.all()]
    form.EspecialidadID.choices = [(especialidad.EspecialidadID, especialidad.Nombre) for especialidad in Especialidad.query.all()]
    form.MedicoID.choices = [(medico.MedicoID, medico.Nombre) for medico in Medico.query.all()]

    # Prellenar los campos Fecha y Hora con los valores actuales de la cita
    if request.method == 'GET':
        form.Fecha.data = cita.FechaCita.date()
        form.Hora.data = cita.FechaCita.time()

    if form.validate_on_submit():
        try:
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
    flash('Cita cancelada exitosamente!', 'success')
    return redirect(url_for('manage_citas'))






if __name__ == '__main__':
    app.run(debug=True)
