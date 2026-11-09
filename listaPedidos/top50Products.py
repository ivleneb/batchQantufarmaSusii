import sys, math
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(r'../')
from lib.QantuConfiguration import QantuConfiguration
from lib.SusiiProductLoader import SusiiProductLoader

config = QantuConfiguration()
business_ = config.business_
NBR_DAYS = int(config.NBR_DAYS)
TOP_N = 50
OUT_DIR = Path("./out")
stockBase = 0
MAX_DAYS_HISTORY = 365


def load_product_and_package_data():
    loader = SusiiProductLoader(business_)
    products = loader.downloadProducts(downloadSaleData=True)
    if not products:
        print("Error: no se pudieron descargar los productos.")
        sys.exit(2)
    packages = loader.downloadPackages(downloadSaleData=True)
    if packages is None:
        print("Aviso: no se pudieron descargar paquetes; se continuará sin sumar sus ventas.")
        packages = {}
    return products, packages, loader.beginDt


def add_package_sales(products, packages):
    """Suma las unidades vendidas mediante paquetes sin fusionar códigos."""
    for package in packages.values():
        for product_code, quantity in package.getItems().items():
            if product_code in products:
                products[product_code].addSoldUnits(quantity * package.getSoldUnits())


def safe_get(obj, method_name, default=None):
    try:
        value = getattr(obj, method_name)()
        return default if value is None else value
    except (AttributeError, TypeError, ValueError):
        return default


def classify_product(product):
    generico = safe_get(product, "getGenerico")
    if generico == 2:
        return "GOLD"
    if generico == 1:
        return "GENÉRICO"
    return "OTRO / NO ESPECIFICADO"


def as_positive_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) and number > 0 else 0
    except (TypeError, ValueError):
        return 0


def calculate_active_days(product):
    active_days = as_positive_number(safe_get(product, "getActiveDays", 0))
    return active_days if active_days > 0 else 1


def calculate_replenishment(forecast_units, units_per_box, units_per_blister):
    """Menos de 3 blísteres: blísteres; desde 3: una caja."""
    if units_per_box <= 0:
        return 0, 0, 0, "SIN UNIT_CAJA"
    if forecast_units <= 0:
        return 0, 0, 0, "SIN PEDIDO"
    if units_per_blister > 1:
        blister_count = math.ceil(forecast_units / units_per_blister)
        if blister_count < 3:
            units_to_buy = blister_count * units_per_blister
            return 0, blister_count, units_to_buy, "BLÍSTER"
        return 1, 0, units_per_box, "CAJA"
    box_count = math.ceil(forecast_units / units_per_box)
    return box_count, 0, box_count * units_per_box, "CAJA"


def build_report(products, time_window_days):
    rows = []
    for product in products.values():
        sold_units = as_positive_number(safe_get(product, "getSoldUnits", 0))
        active_days = min(calculate_active_days(product), time_window_days)
        daily_average = sold_units / active_days
        forecast_units = math.ceil(daily_average * NBR_DAYS) if sold_units > 0 else 0
        units_per_box = as_positive_number(safe_get(product, "getUnitsCaja", 0))
        units_per_blister = as_positive_number(safe_get(product, "getUnitsBlister", 0))

        boxes_needed, blisters_needed, units_to_order, presentation = calculate_replenishment(
            forecast_units, units_per_box, units_per_blister
        )

        raw_unit_cost = safe_get(product, "getLastCost")
        try:
            unit_cost = float(raw_unit_cost) if raw_unit_cost not in (None, "") else None
            if unit_cost is not None and (not math.isfinite(unit_cost) or unit_cost < 0):
                unit_cost = None
        except (TypeError, ValueError):
            unit_cost = None

        box_cost = unit_cost * units_per_box if unit_cost is not None and units_per_box > 0 else None
        blister_cost = unit_cost * units_per_blister if unit_cost is not None and units_per_blister > 1 else None

        if unit_cost is None:
            investment = None
        elif presentation == "CAJA":
            investment = box_cost * boxes_needed if box_cost is not None else None
        elif presentation == "BLÍSTER":
            investment = blister_cost * blisters_needed if blister_cost is not None else None
        else:
            investment = 0

        name = safe_get(product, "getName") or safe_get(product, "getMergedName", "")

        rows.append({
            "CODIGO": safe_get(product, "getCode", ""),
            "NOMBRE": name,
            "CATEGORIA": safe_get(product, "getCategory", ""),
            "PRINCIPIO_ACTIVO": safe_get(product, "getPrincipioActivo", ""),
            "TIPO": classify_product(product),
            "MARCA": safe_get(product, "getBrand", ""),
            "PROVEEDOR_ULTIMA_COMPRA": safe_get(product, "getLastProvider", ""),
            "VENTAS": sold_units,
            "DIAS_ACTIVOS_VENTAS": active_days,
            "PROM_VENTAxDIA": daily_average,
            "DIAS_COBERTURA": NBR_DAYS,
            "STOCK": stockBase,
            "STOCK_MINIMO": forecast_units,
            "UNIT_BLI": units_per_blister if units_per_blister > 0 else None,
            "UNIT_CAJA": units_per_box if units_per_box > 0 else None,
            "PRESENTACION_PEDIDO": presentation,
            "PEDIDOxCAJA": boxes_needed,
            "PEDIDOxBLI": blisters_needed,
            "UNIDADES_A_COMPRAR": units_to_order,
            "COSTO_UNITARIO": unit_cost,
            "COSTO_COMPRA_CAJA": box_cost,
            "COSTO_COMPRA_BLI": blister_cost,
            "INVERSION": investment
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["VENTAS"] = pd.to_numeric(df["VENTAS"], errors="coerce").fillna(0)
    df = df.sort_values(by=["VENTAS", "CODIGO"], ascending=[False, True], kind="stable")
    return df.head(TOP_N).reset_index(drop=True)


def export_excel(df, time_window_days):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = OUT_DIR / f"{business_}_Top50_Reposicion_{NBR_DAYS}dias_{timestamp}.xlsx"

    columns = [
        "RANKING", "CODIGO", "NOMBRE", "CATEGORIA", "PRINCIPIO_ACTIVO", "TIPO",
        "MARCA", "PROVEEDOR_ULTIMA_COMPRA", "VENTAS", "DIAS_ACTIVOS_VENTAS",
        "PROM_VENTAxDIA", "DIAS_COBERTURA", "STOCK", "STOCK_MINIMO", "UNIT_BLI",
        "UNIT_CAJA", "PRESENTACION_PEDIDO", "PEDIDOxCAJA", "PEDIDOxBLI",
        "UNIDADES_A_COMPRAR", "COSTO_UNITARIO", "COSTO_COMPRA_CAJA",
        "COSTO_COMPRA_BLI", "INVERSION"
    ]

    if df.empty:
        df = pd.DataFrame(columns=columns[1:])
    else:
        df = df.copy()
        df.insert(0, "RANKING", range(1, len(df) + 1))
    df = df.reindex(columns=columns)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Top 50", index=False)
        ws = writer.sheets["Top 50"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        widths = {
            "A": 10, "B": 16, "C": 38, "D": 20, "E": 28, "F": 22,
            "G": 20, "H": 28, "I": 14, "J": 18, "K": 18, "L": 16,
            "M": 12, "N": 16, "O": 12, "P": 12, "Q": 20, "R": 14,
            "S": 14, "T": 20, "U": 16, "V": 20, "W": 20, "X": 18
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width

        for row in range(2, ws.max_row + 1):
            for col in ("U", "V", "W", "X"):
                ws[f"{col}{row}"].number_format = '"S/" #,##0.00'
            for col in ("I", "J", "K", "L", "M", "N", "O", "P", "R", "S", "T"):
                ws[f"{col}{row}"].number_format = "0.##"

        total_row = ws.max_row + 2
        ws[f"W{total_row}"] = "INVERSIÓN TOTAL"
        ws[f"X{total_row}"] = f"=SUM(X2:X{ws.max_row})"
        ws[f"X{total_row}"].number_format = '"S/" #,##0.00'
        ws[f"W{total_row}"].font = ws[f"W{total_row}"].font.copy(bold=True)
        ws[f"X{total_row}"].font = ws[f"X{total_row}"].font.copy(bold=True)

        ws["Z1"] = "INICIO HISTORIAL"
        ws["Z2"] = (datetime.now().date() - timedelta(days=time_window_days)).strftime("%Y-%m-%d")
        ws["AA1"] = "DIAS HISTORIAL"
        ws["AA2"] = time_window_days
        ws.column_dimensions["Z"].width = 20
        ws.column_dimensions["AA"].width = 18

    print(f"Reporte generado: {output_path.resolve()}")
    print(f"Productos incluidos: {len(df)}")
    print(f"Días de historial: {time_window_days}")
    print(f"Días de cobertura: {NBR_DAYS}")
    print("Stock simulado: 0.")
    print("Productos individuales: no se fusionan genéricos ni GOLD.")


def run():
    print("---------------- TOP 50: REPOSICIÓN INICIO ----------------")
    print(f"Configuración de cobertura: {NBR_DAYS} días")

    products, packages, begin_date = load_product_and_package_data()
    add_package_sales(products, packages)

    begin = datetime.strptime(begin_date, "%Y-%m-%d").date()
    time_window_days = max(1, min(MAX_DAYS_HISTORY, (datetime.now().date() - begin).days))

    print(f"Inicio del historial: {begin_date}")
    print(f"Días considerados: {time_window_days}")

    report = build_report(products, time_window_days)
    export_excel(report, time_window_days)
    print("---------------- TOP 50: REPOSICIÓN FIN ----------------")


if __name__ == "__main__":
    run()
