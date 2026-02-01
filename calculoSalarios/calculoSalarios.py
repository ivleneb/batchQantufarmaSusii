import sys
sys.path.append('../')
import pandas
from datetime import datetime
#from lib.QantuSeller import QantuSeller
#from lib.RequestHandler import RequestHandler
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from comisionesVenta.CommissionManager import CommissionManager

def sellerPlusPlusBonification(prevSales, sales):
    if prevSales<sales:
        per = 100*(sales/prevSales-1)
        print("Percentage increase:"+str(per))
        if per<5.0:
            print("No vendedor++")
            return 0.0
        elif per<7.5:
            print("Vendedor plus++ +20")
            return 25.0
        elif per<10.0:
            print("Vendedor plus++ +50")
            return 50.0
        elif per<20.0:
            print("Vendedor plus++ +100")
            return 100.0
        elif per<30.0:
            print("Vendedor plus++ +200")
            return 200.0
        else:
            print("Vendedor plus++ +300")
            return 300.0
    else:
        print("No vendedor++")
        return 0.0

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


def getCommission(user:str, sellers):
    for seller, obj in sellers.items():
        if user in seller:
            return obj.getCommission()
        
    return 0.0


def run():
    users: dict[str, list] = {"RUTH":[],"JENNY":[],"miriam":[], "XIOMARA":[],"YOVANA":[], "rosangela":[]}

    # dias laborables en un mes
    diasLaborales = 30.0
    diasLaborablesSemanales = 6.0
    standardWeeks = 4.0
    # Para un trbajador que labora 6 dias a la semana, descansa 1 dia y trbaja 8 horas diarias
    salarioBase = 1200.00
    horasSemanalesBase = 48.00


    horasQ1 = {
        "RUTH": 45.5,
        "JENNY": 45.5,
        }

    horasQ2 = {
        "XIOMARA": 21,
        "YOVANA": 28
        }


    # calculo comisiones
    comm = CommissionManager()
    sellersCommDict = comm.run('2026', '01')
    if sellersCommDict is None:
        print("Fallo commissionManager")
        sys.exit(1)


    # Q1
    print("Q1--------------------------")
    salarioOperativoQ1 = round(salarioBase*7.0*13.0/horasSemanalesBase,2)
    salarioOperativoDiarioQ1 = round(salarioOperativoQ1/diasLaborales,2)
    print("Salario operativo:"+str(salarioOperativoQ1))
    print("Salario Diario operativo:"+str(salarioOperativoDiarioQ1))
    #salarioOperativoQ1_2 = round(salarioBase*7.0*13.0/horasSemanalesBase,2)
    #salarioOperativoDiarioQ1_2 = round(salarioOperativoQ1_2/diasLaborales,2)
    #print("Salario operativo:"+str(salarioOperativoQ1_2))
    #print("Salario Diario operativo:"+str(salarioOperativoDiarioQ1_2))


    print("Salarios")
    for user in horasQ1:
        salario = round(weekHoursBasedSalary(horasQ1[user], salarioBase, horasSemanalesBase),2)
        print(user+" "+str(salario))
        users[user].append(['monto fijo', 'Q1 1era quincena', salario])

    #for user in horasQ1_2:
    #    salario = round(weekHoursBasedSalary(horasQ1_2[user], salarioBase, horasSemanalesBase),2)*0.5
    #    print(user+" "+str(salario))
    #    users[user].append(['monto fijo', 'Q1 2da quincena', salario])

    #print("Inasistencias")
    #users['rosangela'].append(['cobertura full day', 'Q1 29/oct', salarioOperativoDiarioQ1_2])
    #users['miriam'].append(['cobertura full day', 'Q1 22/oct', salarioOperativoDiarioQ1_2])
    #users['RUTH'].append(['inasistencia full day', 'Q1 23/oct', -salarioOperativoDiarioQ1_2])

    print("Feriados")
    #users['rosangela'].append(['feriado', 'Q1 01/nov', salarioOperativoDiarioQ1])
    #users['JENNY'].append(['feriado', 'Q1 08/dic', salarioOperativoDiarioQ1])
    #users['RUTH'].append(['feriado', 'Q1 09/dic', salarioOperativoDiarioQ1])
    #users['JENNY'].append(['feriado', 'Q1 29/jul', 70.0])
    #users['RUTH'].append(['feriado', 'Q1 28/jul', 70.0])

    print("Pérdidas por Ajustes")
    lossAdjust = round(-6.45-1.3,2)
    users['JENNY'].append(['perdidas por ajuste', 'Q1 01-diciembre al 29-diciembre', lossAdjust])
    users['RUTH'].append(['perdidas por ajuste', 'Q1 01-diciembre al 29-diciembre', lossAdjust])
    
    print("Pérdidas por caja chica")
    users['RUTH'].append(['perdidas por caja chica', 'Q1 01-enero', -2.36])
    
    #print("Pérdidas por Productos vencidos")
    #lossExpired = -32.13
    #users['JENNY'].append(['perdidas por productos vencidos', 'Q1 01-agosto al 30-agosto', lossExpired])
    #users['miriam'].append(['perdidas por productos vencidos', 'Q1 01-agosto al 30-agosto', lossExpired])
    #users['RUTH'].append(['perdidas por productos vencidos', 'Q1 01-agosto al 30-agosto', lossExpired])

    print("Comisiones ventas")    
    for user in horasQ1:
        users[user].append(['Comisiones ventas', 'Q1 01-enero al 31-enero', getCommission(user, sellersCommDict)])

    print("Adelantos")
    users['RUTH'].append(['adelanto', 'Q1 quincena', round(-1000.00,2)])
    users['JENNY'].append(['adelanto', 'Q1 quincena', round(-600.00,2)])

    #bon = sellerPlusPlusBonification(JENNYSalesB, JENNYSales)
    #if bon>0:
    #    users['JENNY'].append(['Incentivo vendedor++', 'Q1 01-setiembre al 30-setiembre', bon])

    #bon = sellerPlusPlusBonification(RUTHSalesB, RUTHSales)
    #if bon>0:
    #    users['RUTH'].append(['Incentivo vendedor++', 'Q1 01-setiembre al 30-setiembre', bon])
        
    #bon = sellerPlusPlusBonification(miriamSalesB, miriamSales)
    #if bon>0:
    #    users['miriam'].append(['Incentivo vendedor++', 'Q1 01-setiembre al 30-setiembre', bon])

    print("Q2--------------------------")

    salarioOperativoQ2 = round(salarioBase*7.0*7.0/horasSemanalesBase,2)
    salarioOperativoDiarioQ2 = round(salarioOperativoQ2/diasLaborales,2)
    print("Salario operativo:"+str(salarioOperativoQ2))
    print("Salario Diario operativo:"+str(salarioOperativoDiarioQ2))


    print("Salarios")
    for user in horasQ2:
        salario = round(weekHoursBasedSalary(horasQ2[user], salarioBase, horasSemanalesBase),2)
        print(user+" "+str(salario))
        users[user].append(['monto fijo', 'Q2', salario])


    #print("Ajustes")
    #print("Angela inasistencia")
    #salarioQ2RosangelaXdia = round(users['rosangela'][0][2]/standardWeeks,2)

    #users['rosangela'].append(['inasistencia full day', 'Q2 06/set', -salarioQ2RosangelaXdia])
    #users['rosangela'].append(['inasistencia full day', 'Q2 27/set', -salarioQ2RosangelaXdia])
    #users['JENNY'].append(['abono por cubrir horario full day', 'Q2 26/ago', +salarioQ2RUTHXdia])

    print("Feriados")
    #print("Feriado XIOMARA")
    #users['XIOMARA'].append(['feriado', 'Q2 08/dic', round(salarioOperativoDiarioQ2,2)])
    #users['XIOMARA'].append(['feriado', 'Q2 28-29/jul', round(salarioOperativoDiarioQ2,2)*2])
    #print("Feriado YOVANA")
    #users['YOVANA'].append(['feriado', 'Q2 09/dic', round(salarioOperativoDiarioQ2,2)])
    #users['YOVANA'].append(['feriado', 'Q2 28-29/jul', round(salarioOperativoDiarioQ2,2)*2])
    #users['rosangela'].append(['feriado', 'Q2 01/nov', round(salarioOperativoDiarioQ2,2)])

    #print("Pasajes")
    #users['RUTH'].append(['Bono pasaje', 'Q2', 15.0])
    #users['JENNY'].append(['Bono pasaje', 'Q2', 25.0])


    print("Pérdidas por Ajustes")
    lossAdjust = round(-5-0.3,2)
    users['XIOMARA'].append(['perdidas por ajuste', 'Q2 01-enero al 31-enero', round(lossAdjust,2)])
    users['YOVANA'].append(['perdidas por ajuste', 'Q2 01-enero al 31-enero', round(lossAdjust,2)])
    #users['rosangela'].append(['perdidas por ajuste', 'Q2 01-noviembre al 29-noviembre', round(lossAdjust,2)])

    print("Adelantos")
    users['YOVANA'].append(['adelanto', 'Q2 quincena', round(-350.00,2)])
    users['XIOMARA'].append(['adelanto', 'Q2 quincena', round(-500.00,2)])
    #users['rosangela'].append(['adelanto', 'Q2 quincena', round(-200.00,2)])


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


run()
