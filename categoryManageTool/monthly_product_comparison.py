import os
import sys
import pandas as pd
import calendar
from datetime import datetime
# Agregar la carpeta padre al path para que encuentre la carpeta lib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib.QantuConfiguration import QantuConfiguration

# Carpeta donde están los excel generados por categoryManageTool
data_folder = "./out"
output_folder = "./comparacion_meses"
os.makedirs(output_folder, exist_ok=True)

# Business ID desde config
config = QantuConfiguration()
business_id = config.business_

def construir_rango(mes: str) -> str:
    #Configura el excel a recoger(YYYY-MM-01toYYYY-MM-DD) al recibir (YYYY-MM)
    year, month = mes.split("-")
    last_day = calendar.monthrange(int(year), int(month))[1]
    return f"{mes}-01to{mes}-{last_day:02d}"

def buscar_archivo(rango: str):
    #Busca en la carpeta out, los excel que mantengan ese nombre
    for fname in os.listdir(data_folder):
        if str(business_id) in fname and rango in fname and fname.endswith(".xlsx"):
            return os.path.join(data_folder, fname)
    return None

def comparar_productos_por_nombre(mes1: str, mes2: str):
    rango1 = construir_rango(mes1)
    rango2 = construir_rango(mes2)

    file1 = buscar_archivo(rango1)
    file2 = buscar_archivo(rango2)

    if not file1 or not file2:
        print("[AVISO] No se encontraron archivos para los meses indicados.")
        return

    # Validar sufijo de ejecución
    sufijo1 = os.path.basename(file1).split("_")[-1].replace(".xlsx","")
    sufijo2 = os.path.basename(file2).split("_")[-1].replace(".xlsx","")
    if sufijo1 != sufijo2:
        print(f"[AVISO] Los archivos no tienen el mismo día de ejecución: {sufijo1} vs {sufijo2}")
        return
    hoy = datetime.now().strftime("%Y%m%d")
    if sufijo1 != hoy:
        print(f"[AVISO] Los archivos no corresponden a la fecha de hoy ({hoy}), sino a {sufijo1}")
        return

    # Leer hoja Utilidad
    df1 = pd.read_excel(file1, sheet_name="Utilidad")
    df2 = pd.read_excel(file2, sheet_name="Utilidad")

    col_nombre = "NOMBRE"
    col_total = "TOTAL"

    # Comparar por nombre
    df_merge = pd.merge(
        df1[[col_nombre, col_total]],
        df2[[col_nombre, col_total]],
        on=col_nombre,
        how="inner",
        suffixes=("_mes1", "_mes2")
    )

    df_merge["Diferencia"] = df_merge["TOTAL_mes2"] - df_merge["TOTAL_mes1"]
    df_merge["%Caida"] = (df_merge["Diferencia"] / df_merge["TOTAL_mes1"] * 100).round(2)

    # Filtrar solo los que bajaron
    df_caida = df_merge[df_merge["Diferencia"] < 0].sort_values("Diferencia")

    # Guardar resultados
    now = datetime.now().strftime("%Y%m%d")
    out_name = f"{business_id}_ComparacionPorMes_{rango1}_vs_{rango2}_{sufijo1}.xlsx"
    out_path = os.path.join(output_folder, out_name)

    with pd.ExcelWriter(out_path) as writer:
        df_caida.to_excel(writer, sheet_name="CaidaVentas", index=False)

    print(f"Archivo generado: {out_path}")
    print("\nProductos con caída de ventas (por nombre):")
    print(df_caida[[col_nombre, "TOTAL_mes1", "TOTAL_mes2", "Diferencia", "%Caida"]])

def run():
    mes1 = input("Ingrese primer mes (YYYY-MM): ").strip()
    mes2 = input("Ingrese segundo mes (YYYY-MM): ").strip()
    comparar_productos_por_nombre(mes1, mes2)

if __name__ == "__main__":
    run()
