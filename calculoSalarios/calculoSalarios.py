import sys
sys.path.append('../')
import pandas
from gestorIncidenciasNomina import GestorIncidenciasNomina
from gestorIncidenciasNomina import CONFIGURACION_SEDES as config_sede
from datetime import datetime
from decimal import Decimal
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

def getPeriod():
    while True:
        year = input("Enter year YYYY: ")
        month = input("Enter month mm: ")
        
        if year.isdigit() and month.isdigit():
            monthNum = int(month)
            if monthNum > 12 or monthNum<1:
                print("Valor inválido de month ["+month+"].")
                continue
            else:
                return year, month
        else:
            print("Valor no numérico en periodo ["+year+"]["+month+"].")
            continue

def run():
    
    year, month = getPeriod()
    gestor = GestorIncidenciasNomina(configuracionSedes=config_sede, year=year, month=month)
    
    # calculo comisiones Q1
    comm = CommissionManager(5053)
    sellersCommDict = comm.run(year, month)
    if sellersCommDict is None:
        print("Fallo commissionManager")
        sys.exit(1)
    
    users: dict[str, list] = {"RUTH":[],"JENNY":[],"miriam":[], "XIOMARA":[],"YOVANA":[], "rosangela":[],"KATHERINE": [], "ISAI":[]}
    userLogistic = {"KATHERINE": Decimal('0.5'), "ISAI":Decimal('0.5')}

    # dias laborables en un mes
    diasLaborales = 30.0
    diasLaborablesSemanales = 6.0
    standardWeeks = 4.0
    # Para un trbajador que labora 6 dias a la semana, descansa 1 dia y trbaja 8 horas diarias
    salarioBase = 1200.00
    horasSemanalesBase = 48.00
    # logistica
    salarioBaseLogistica = 1200.0
    horasSemanalesBaseLogistica = 48
    salarioDiarioLogistica = Decimal(str(round(salarioBaseLogistica/30, 2)))
    

    horasQ1 = {
        "RUTH": 45.5,
        "JENNY": 45.5,
        "KATHERINE": 24
        }

    horasQ2 = {
        "XIOMARA": 45.5,
        "YOVANA": 45.5,
        "KATHERINE": 0,
        "ISAI":24
        }

    # Q1
    print("Q1--------------------------")
    businessIdQ1 = 5053
    listUser = list(horasQ1.keys())
    salarioOperativoQ1 = round(salarioBase*7.0*13.0/horasSemanalesBase,2)
    salarioOperativoDiarioQ1 = round(salarioOperativoQ1/diasLaborales,2)
    salarioDiarioDecimalQ1 = Decimal(str(salarioOperativoDiarioQ1))
    print("Salario operativo:"+str(salarioOperativoQ1))
    print("Salario Diario operativo:"+str(salarioOperativoDiarioQ1))


    print("Salarios")
    for user in horasQ1:
        salario = round(weekHoursBasedSalary(horasQ1[user], salarioBase, horasSemanalesBase),2)
        print(user+" "+str(salario))
        users[user].append(['monto fijo', 'Q1 mes', salario])

    print("Inasistencias")
    for username in listUser:
        registros = gestor.get(businessIdQ1,"INASISTENCIA",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            
            descuento = 0.0
            if username in userLogistic:
                journalType = userLogistic[username]
                descuento = round(cantidad * salarioDiarioLogistica * journalType,2)
            else:
                descuento = round(cantidad * salarioDiarioDecimalQ1,2)
            users[username].append(["inasistencia",f"Q1 {fecha}",-float(descuento)])

    print("Feriados")
    for username in listUser:
        registros = gestor.get(businessIdQ1,"Feriado",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            bono = round(cantidad * salarioDiarioDecimalQ1*2,2)
            users[username].append(["Feriado",f"Q1 {fecha}",+float(bono)])

    print("Jornadas Extras")        
    for username in listUser:
        registros = gestor.get(businessIdQ1,"Jornada",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            jornada = round(cantidad * salarioDiarioDecimalQ1,2)
            users[username].append(["jornadas extras",f"Q1 {fecha}",+float(jornada)])

    print("Pérdidas por Ajustes")
    for username in listUser:
        registros = gestor.get(businessIdQ1,"descuento_ajuste",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            descuento_ajuste = cantidad
            users[username].append(["descuento por ajuste",f"Q1 {fecha}",-float(descuento_ajuste)])
    
    print("Pérdidas por caja chica")
    for username in listUser:
        registros = gestor.get(businessIdQ1,"descuento_caja_chica",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            descuento_caja = cantidad
            users[username].append(["descuento por caja chica",f"Q1 {fecha}",-float(descuento_caja)])
    
    print("Pérdidas por Vencimiento")
    for username in listUser:
        registros = gestor.get(businessIdQ1,"descuento_vencimiento",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            descuento_vencimiento = cantidad
            users[username].append(["descuento por vencidos",f"Q1 {fecha}",-float(descuento_vencimiento)])

    print("Comisiones ventas")    
    for user in horasQ1:
        users[user].append(['Comisiones ventas', 'Q1 01-enero al 31-enero', getCommission(user, sellersCommDict)])

    print("Adelantos")
    for username in listUser:
        registros = gestor.get(businessIdQ1,"Adelanto",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            adelanto = cantidad
            users[username].append(["Adelanto",f"Q1 {fecha}",-float(adelanto)])

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
    businessIdQ3 = 8132
    listUser = list(horasQ2.keys())
    salarioOperativoQ2 = round(salarioBase*7.0*13.0/horasSemanalesBase,2)
    salarioOperativoDiarioQ2 = round(salarioOperativoQ2/diasLaborales,2)
    salarioDiarioDecimal = Decimal(str(salarioOperativoDiarioQ2))
    print("Salario operativo:"+str(salarioOperativoQ2))
    print("Salario Diario operativo:"+str(salarioOperativoDiarioQ2))


    print("Salarios")
    for user in horasQ2:
        salario = round(weekHoursBasedSalary(horasQ2[user], salarioBase, horasSemanalesBase),2)
        print(user+" "+str(salario))
        users[user].append(['monto fijo', 'Q2', salario])

    print("Inasistencias")
    for username in listUser:
        registros = gestor.get(businessIdQ3,"INASISTENCIA",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            ddescuento = 0.0
            if username in userLogistic:
                journalType = userLogistic[username]
                descuento = round(cantidad * salarioDiarioLogistica * journalType,2)
            else:
                descuento = round(cantidad * salarioDiarioDecimalQ1,2)
            users[username].append(["inasistencia",f"Q1 {fecha}",-float(descuento)])

    print("Feriados")
    for username in listUser:
        registros = gestor.get(businessIdQ3,"Feriado",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            bono = round(cantidad * salarioDiarioDecimal*2,2)
            users[username].append(["Feriado",f"Q3 {fecha}",+float(bono)])
            
    print("Jornadas Extras")
    for username in listUser:
        registros = gestor.get(businessIdQ3,"Jornada",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            jornada = round(cantidad * salarioDiarioDecimal,2)
            users[username].append(["jornadas extras",f"Q3 {fecha}",+float(jornada)])

    print("Pérdidas por Ajustes")
    for username in listUser:
        registros = gestor.get(businessIdQ3,"descuento_ajuste",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            descuento_ajuste = cantidad
            users[username].append(["descuento por ajuste",f"Q3 {fecha}",-float(descuento_ajuste)])
            
    print("Pérdidas por Caja Chica")
    for username in listUser:
        registros = gestor.get(businessIdQ3,"descuento_caja_chica",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            descuento_caja = cantidad
            users[username].append(["descuento por caja chica",f"Q3 {fecha}",-float(descuento_caja)])
            
    print("Pérdidas por Vencimiento")
    for username in listUser:
        registros = gestor.get(businessIdQ3,"descuento_vencimiento",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            descuento_vencimiento = cantidad
            users[username].append(["descuento por vencidos",f"Q3 {fecha}",-float(descuento_vencimiento)])

    print("Adelantos")
    for username in listUser:
        registros = gestor.get(businessIdQ3,"Adelanto",username)
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            adelanto = cantidad
            users[username].append(["Adelanto",f"Q3 {fecha}",-float(adelanto)])

    """print("Ejemplo de Como hacer caso de Katherine: line 416")
    print("Feriados de Katherine en ambas sedes")
    for businessId in [5053, 8132]:
        registros = gestor.get(businessId,"feriado","KATHERINE")
        if businessId == 5053:
            salarioDiario = Decimal(str(salarioOperativoDiarioQ1))
            sede = "Q1"
        else:
            salarioDiario = Decimal(str(salarioOperativoDiarioQ2))
            sede = "Q3"
        for registro in registros:
            fecha = registro["fecha"]
            cantidad = registro["cantidad"]
            if cantidad <= 0:
                continue
            bono = round(cantidad * salarioDiario, 2)
            users["KATHERINE"].append(["feriado",f"{sede} {fecha}",+float(bono)])"""
        
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
        path = './out'
        fullpath = path + '/' +excel_name
        with pandas.ExcelWriter(fullpath) as excel_writer:
            user_df.to_excel(excel_writer, sheet_name='Resumen', index=False)

        
        pdf_name = user+'_ReporteSalario_'+now+'.pdf'
        path = './out'
        fullpath_pdf = path + '/' + pdf_name
        dataframe_to_pdf(headers, footerData, users[user], fullpath_pdf)

            
    print("------------------------  END ---------------------------")


run()
