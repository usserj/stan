import pandas as pd
from flask import send_file
import tempfile


def export_to_excel(query):
    citas = []
    for cita in query:
        citas.append({
            'Paciente': f"{cita.paciente.Nombres} {cita.paciente.Apellidos}",
            'Especialidad': cita.especialidad.Nombre,
            'Medico': f"{cita.medico.Nombre} {cita.medico.Apellidos}",
            'Fecha y Hora': cita.FechaCita,
            'Duracion': cita.Duracion,
            'Estado': cita.Estado,
            'Motivo de la Cita': cita.MotivoCita
        })
    
    df = pd.DataFrame(citas)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        df.to_excel(tmp.name, index=False, engine='openpyxl')
        tmp_path = tmp.name

    return send_file(tmp_path, as_attachment=True, download_name='citas.xlsx')



# utils.py

from datetime import datetime, timedelta, time
from models import Horario, Cita  # Asegúrate de que los modelos Horario y Cita estén en models.py

def update_horarios_disponibles(medico_id, fecha):
    try:
        print(f"Actualizando horarios disponibles para medico_id: {medico_id}, fecha: {fecha}")
        fecha = fecha.date()
        
        # Obtener los horarios del médico para el día especificado
        day_of_week = fecha.strftime('%A')
        horarios = Horario.query.filter_by(MedicoID=medico_id, day_of_week=day_of_week).all()
        print(f"Horarios del médico: {horarios}")
        
        # Obtener las citas del médico para el día especificado
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
        
        # Crear un conjunto de horas disponibles basadas en los horarios del médico
        available_hours = set()
        for horario in horarios:
            current_time = datetime.combine(fecha, horario.start_time)
            horario_end_time = datetime.combine(fecha, horario.end_time)
            while current_time < horario_end_time:
                if current_time.strftime('%H:%M') not in booked_hours:
                    available_hours.add(current_time.strftime('%H:%M'))
                current_time += timedelta(minutes=60)
        
        print(f"Available hours after update: {available_hours}")
        return sorted(available_hours)
    except Exception as e:
        print(f"Error al actualizar horarios disponibles: {e}")
        return []
