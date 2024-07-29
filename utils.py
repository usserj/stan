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
