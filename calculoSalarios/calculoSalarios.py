import sys
sys.path.append('../')
import pandas
from datetime import datetime
from lib.libclass import *
from lib.RequestHandler import *
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def weekHoursBasedSalary(hours, base, baseHours):
    return base*hours/baseHours

def dailySalary(salary, workingDays):
    return salary/workingDays

def meanDailyHours(weeklyHours, workingDaysPerWeek):
    return weeklyHours/workingDaysPerWeek

# Crear PDF
def dataframe_to_pdf(header, footer, data, filename):
    # Crear documento
    doc = SimpleDocTemplate(filename, pagesize=letter)
    
    # Crear tabla
    data.insert(0, header)
    data.append(footer)
    table = Table(data)
    
    # Estilo de la tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        # En general alineado al centro
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        # Concepto a la izquierda
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        # Montos a la derecha
        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Ultima fila en negrita
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    ])
    
    table.setStyle(style)
    
    # Construir PDF
    elements = [table]
    doc.build(elements)

users: dict[str, list] = {"ruth":[],"jenny":[],"miriam":[], "xiomara":[],"yovana":[]}

# dias laborables en un mes
diasLaborales = 30.0
diasLaborablesSemanales = 6.0
standardWeeks = 4.0
# Para un trbajador que labora 6 dias a la semana, descansa 1 dia y trbaja 8 horas diarias
salarioBase = 1200.00
horasSemanalesBase = 48.00


horasQ1 = {
    "ruth": 30.00,
    "miriam": 30.00,
    "jenny": 24.00,
    }

horasQ2 = {
    "ruth": 13.00,
    "jenny": 6.50,
    "xiomara": 35.75,
    "yovana": 35.75,
    }

# Q1
print("Q1--------------------------")
salarioOperativoQ1 = round(salarioBase*7.0*12.0/horasSemanalesBase,2)
salarioOperativoDiarioQ1 = round(salarioOperativoQ1/diasLaborales,2)
print("Salario operativo:"+str(salarioOperativoQ1))
print("Salario Diario operativo:"+str(salarioOperativoDiarioQ1))


print("Salarios")
for user in horasQ1:
    salario = round(weekHoursBasedSalary(horasQ1[user], salarioBase, horasSemanalesBase),2)
    if user=='jenny':
        salario = 750.00
    print(user+" "+str(salario))
    users[user].append(['monto fijo', 'Q1', salario])

print("Feriados")
users['jenny'].append(['feriado', 'Q1 30/ago', salarioOperativoDiarioQ1])
users['ruth'].append(['feriado', 'Q1 06/ago', salarioOperativoDiarioQ1])

print("Pérdidas por Ajustes")
lossAdjust = round(-3.60,2)
users['jenny'].append(['perdidas por ajuste', 'Q1 01-agosto al 30-agosto', lossAdjust])
users['miriam'].append(['perdidas por ajuste', 'Q1 01-agosto al 30-agosto', lossAdjust])
users['ruth'].append(['perdidas por ajuste', 'Q1 01-agosto al 30-agosto', lossAdjust])

print("Pérdidas por Productos vencidos")
lossExpired = -32.13
users['jenny'].append(['perdidas por productos vencidos', 'Q1 01-agosto al 30-agosto', lossExpired])
users['miriam'].append(['perdidas por productos vencidos', 'Q1 01-agosto al 30-agosto', lossExpired])
users['ruth'].append(['perdidas por productos vencidos', 'Q1 01-agosto al 30-agosto', lossExpired])

print("Comisiones ventas")
users['jenny'].append(['Comisiones ventas', 'Q1 01-agosto al 31-agosto', 146.52])
users['miriam'].append(['Comisiones ventas', 'Q1 01-agosto al 31-agosto', 160.41])
users['ruth'].append(['Comisiones ventas', 'Q1 01-agosto al 31-agosto', 159.07])


print("Q2--------------------------")

salarioOperativoQ2 = round(salarioBase*7.0*13.0/horasSemanalesBase,2)
salarioOperativoDiarioQ2 = round(salarioOperativoQ2/diasLaborales,2)
print("Salario operativo:"+str(salarioOperativoQ2))
print("Salario Diario operativo:"+str(salarioOperativoDiarioQ2))


print("Salarios")
salarioQ2Ruth = 0.0
for user in horasQ2:
    salario = round(weekHoursBasedSalary(horasQ2[user], salarioBase, horasSemanalesBase),2)
    if user=='ruth':
        salarioQ2Ruth = salario
    print(user+" "+str(salario))
    users[user].append(['monto fijo', 'Q2', salario])


print("Ajustes")
print("Reemplazo ruth por jenny")
salarioQ2RuthXdia = round(salarioQ2Ruth/standardWeeks,2)

users['ruth'].append(['descuento por inasistencia full day', 'Q2 26/ago', -salarioQ2RuthXdia])
users['jenny'].append(['abono por cubrir horario full day', 'Q2 26/ago', +salarioQ2RuthXdia])

print("Feriado xiomara")
users['xiomara'].append(['feriado', 'Q2 06/ago', round(salarioOperativoDiarioQ2*0.5,2)])
users['xiomara'].append(['feriado', 'Q2 30/ago', round(salarioOperativoDiarioQ2*0.5,2)])
print("Feriado yovana")
users['yovana'].append(['feriado', 'Q2 06/ago', round(salarioOperativoDiarioQ2*0.5,2)])
users['yovana'].append(['feriado', 'Q2 30/ago', round(salarioOperativoDiarioQ2*0.5,2)])

print("Pasajes")
users['ruth'].append(['Bono pasaje', 'Q2', 15.0])
users['jenny'].append(['Bono pasaje', 'Q2', 25.0])


print("Pérdidas por Ajustes")
users['xiomara'].append(['perdidas por ajuste', 'Q2 01-agosto al 30-agosto', -31.75])
users['yovana'].append(['perdidas por ajuste', 'Q2 01-agosto al 30-agosto', -21.95])

print("Adelantos")
users['yovana'].append(['adelanto', 'Q2 quincena', -450.00])


headers = ['Concepto', 'Descripción', 'Monto']

now = datetime.now().strftime("%Y%m%d_%H%M")
for user in users:
    user_df = pandas.DataFrame(users[user], columns = headers)
    # Calcular la suma de la última columna
    suma_ultima_col = user_df.iloc[:, -1].sum()
    # Agregar fila al final
    footerData = ['Total', '', suma_ultima_col]
    user_df.loc[len(user_df)] = footerData
    
    excel_name = user+'_ReporteSalario_'+now+'.xlsx'
    with pandas.ExcelWriter(excel_name) as excel_writer:
        user_df.to_excel(excel_writer, sheet_name='Resumen', index=False)

    
    pdf_name = user+'_ReporteSalario_'+now+'.pdf'
    dataframe_to_pdf(headers, footerData, users[user], pdf_name)

        
print("------------------------  END ---------------------------")


