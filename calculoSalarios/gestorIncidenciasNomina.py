import sys
sys.path.append("../")
from lib.RequestHandler import RequestHandler
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal

CONFIGURACION_SEDES = {
    8132: {
        "DESCUENTO_AJUSTE": 7452,
        "DESCUENTO_VENCIMIENTO": 7453,
        "DESCUENTO_CAJA_CHICA": 7451,
        "ADELANTO": 7431,
        "INASISTENCIA": 7446,
        "JORNADA": 7450,
        "FERIADO": 7449
    },
    5053: {
        "DESCUENTO_AJUSTE": 7456,
        "DESCUENTO_VENCIMIENTO": 7457,
        "DESCUENTO_CAJA_CHICA": 7454,
        "ADELANTO": 7432,
        "INASISTENCIA": 7455,
        "JORNADA": 7443,
        "FERIADO": 7445
    }
}

def solicitarPeriodo():
    while True:
        entrada = input("Ingrese el periodo en formato AAAA-MM: ").strip()
        try:
            fecha = datetime.strptime(entrada, "%Y-%m")
            return fecha.year, fecha.month
        except ValueError:
            print("Periodo inválido. Ejemplo válido: 2026-07")
                
class GestorIncidenciasNomina:

    def __init__(self, configuracionSedes, year, month):
        self.configuracionSedes = configuracionSedes
        self.year = int(year)
        self.month = int(month)
        self.gastosPorSede = {}
        self.resultados = {}
        
    def obtenerFechaLocal(self, gasto):
        fechaTexto = gasto.get("date")
        if not fechaTexto:
            return None
        try:
            fechaUtc = datetime.fromisoformat(fechaTexto.replace("Z", "+00:00"))
            zonaPeru = ZoneInfo("America/Lima")
            fechaLocal = fechaUtc.astimezone(zonaPeru)
            return fechaLocal.strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            print(f"Advertencia: fecha inválida: {fechaTexto}")
            return None
        
    def obtenerRangoFechas(self):
        zonaPeru = ZoneInfo("America/Lima")
        fechaInicioLocal = datetime(self.year, self.month, 1, 0, 0, 0, tzinfo=zonaPeru)
        if self.month == 12:
            siguienteMesLocal = datetime(self.year + 1, 1, 1, tzinfo=zonaPeru)
        else:
            siguienteMesLocal = datetime(self.year, self.month + 1, 1, tzinfo=zonaPeru)
        fechaFinLocal = (siguienteMesLocal - timedelta(milliseconds=1))
        fechaInicioUtc = fechaInicioLocal.astimezone(timezone.utc)
        fechaFinUtc = fechaFinLocal.astimezone(timezone.utc)
        formato = "%Y-%m-%dT%H:%M:%S.%f"
        fechaInicioTexto = (fechaInicioUtc.strftime(formato)[:-3] + "Z")
        fechaFinTexto = (fechaFinUtc.strftime(formato)[:-3] + "Z")
        return fechaInicioTexto, fechaFinTexto
    
    def normalizarNombre(self, nombre):
            return " ".join(nombre.strip().upper().split())
    
    def cargarDatos(self):
        for businessId in self.configuracionSedes:
            self.obtenerGastosSede(businessId)
        
    def obtenerGastosSede(self, businessId):
        if businessId in self.gastosPorSede:
            return self.gastosPorSede[businessId]
        fechaInicio, fechaFin = self.obtenerRangoFechas()
        gastos = []
        pagina = 1
        while True:
            endpoint = (f"/sales/expenses/?page={pagina}&business={businessId}&date__lte={fechaFin}&date__gte={fechaInicio}")
            request = RequestHandler(endpoint, businessId=businessId)
            respuesta = request.execute()
            resultados = respuesta.get("results") or []
            total = respuesta.get("count")
            paginaSiguiente = respuesta.get("next")
            gastos.extend(resultados)
            print(f"Sede {businessId} - página {pagina}: {len(resultados)} de {total} registros.")
            if not resultados:
                break
            if total is not None and len(gastos) >= total:
                break
            if paginaSiguiente is None:
                break
            pagina += 1
        self.gastosPorSede[businessId] = gastos
        return gastos

    def perteneceAlPeriodo(self, gasto):
        fechaTexto = gasto.get("date")
        if not fechaTexto:
            return False
        try:
            fecha = datetime.fromisoformat(fechaTexto.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            print(f"Advertencia: fecha inválida: {fechaTexto}")
            return False
        return (fecha.year == self.year and fecha.month == self.month)

    def get(self, businessId, apartado, username):
        if businessId not in self.configuracionSedes:
            raise ValueError(f"La sede {businessId} no está configurada.")
        if not isinstance(apartado, str):
            raise TypeError("El apartado debe enviarse como texto.")
        if not isinstance(username, str):
            raise TypeError("El username debe enviarse como texto.")
        apartado = apartado.strip().upper()
        username = self.normalizarNombre(username)
        categorias = self.configuracionSedes[businessId]
        if apartado not in categorias:
            opciones = ", ".join(categorias.keys())
            raise ValueError(f"El apartado '{apartado}' no existe. Opciones disponibles: {opciones}.")
        categoriaId = categorias[apartado]
        gastos = self.obtenerGastosSede(businessId)
        registros = []
        total = Decimal("0.00")
        for gasto in gastos:
            if gasto.get("category") != categoriaId:
                continue
            if not gasto.get("is_active", True):
                continue
            if not self.perteneceAlPeriodo(gasto):
                continue
            nombre = gasto.get("description")
            if not nombre:
                continue
            nombre = self.normalizarNombre(nombre)
            if nombre != username:
                continue
            fecha = self.obtenerFechaLocal(gasto)
            if fecha is None:
                continue
            try:
                cantidad = Decimal(str(gasto.get("amount", "0.00")))
            except (ValueError, TypeError):
                print(f"Advertencia: cantidad inválida para {username} en {fecha}.")
                continue
            registros.append({
                "fecha": fecha,
                "cantidad": cantidad
            })
            total += cantidad
        registros.sort(key=lambda registro: registro["fecha"])
        return registros
    
def run():
    year, month = solicitarPeriodo()
    gestor = GestorIncidenciasNomina(configuracionSedes=CONFIGURACION_SEDES, year=year, month=month)
    
    print("Cargando información de las sedes...")
    gestor.cargarDatos()

    print("JORNADAS")
    jornada = gestor.get(8132, "JORNADA","Katherine")
    print(jornada)

if __name__ == "__main__":
    run()