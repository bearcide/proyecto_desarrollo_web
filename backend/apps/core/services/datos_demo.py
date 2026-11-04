"""Datos ficticios reproducibles para una demostración local independiente."""
import csv
import io


def csv_text(headers, rows):
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(headers); writer.writerows(rows)
    return out.getvalue()


def archivos_demo(cantidad=100):
    plans=[['Informática','Plan ficticio de informática'],['Gestión','Plan ficticio de gestión']]
    materias=[]; grupos=[]; alumnos=[]; solicitudes=[]
    for prefix,plan in (('INF','Informática'),('GES','Gestión')):
        for i,nombre in enumerate(('Introducción','Datos','Álgebra','Redes','Taller','Optativa'),1):
            key=f'{prefix}{i}'
            requisito=f'{prefix}1' if i==2 else (f'{prefix}3' if i==5 else '')
            materias.append([plan,key,nombre,6,1,requisito])
            for group in (1,2):
                day={1:'Viernes',2:'Lunes',3:'Martes',4:'Lunes',5:'Miercoles',6:'Jueves'}[i]
                start=8 if group==1 else 10
                grupos.append([key,f'G{group}',f'Profesor ficticio {prefix}{i}-{group}',20,f'{day}:{start:02d}:00-{start+2:02d}:00'])
    for i in range(1,cantidad+1):
        prefix,plan=('INF','Informática') if i%2 else ('GES','Gestión')
        approved=f'{prefix}1' if i%3 else ''
        if i%5==0: approved+=';'+f'{prefix}3'
        account=f'D{i:03d}'
        alumnos.append([account,f'Alumno ficticio {i:03d}','Demo','Local',plan,approved.strip(';'),'DemoLocal2026!'])
        for preference,subject in enumerate((2,3,4,6),1):
            solicitudes.append([account,f'{prefix}{subject}',preference,i%3])
    return {
        'planes':csv_text(['nombre','descripcion'],plans),
        'materias':csv_text(['plan','clave','nombre','creditos','semestre','prerrequisitos'],materias),
        'alumnos':csv_text(['matricula','nombre','apellido_paterno','apellido_materno','plan','aprobadas','password'],alumnos),
        'grupos':csv_text(['materia','clave','profesor','cupo','horarios'],grupos),
        'solicitudes':csv_text(['matricula','materia','preferencia','prioridad_institucional'],solicitudes),
    }
