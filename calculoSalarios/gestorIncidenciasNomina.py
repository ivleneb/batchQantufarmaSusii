import sys
sys.path.append("../")
from lib.RequestHandler import RequestHandler
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
        "INASISTENCIA_LOGISTICA": 7536,
        "JORNADA": 7450,
        "JORNADA_LOGISTICA": 7538,
        "FERIADO": 7449
    },
    5053: {
        "DESCUENTO_AJUSTE": 7456,
        "DESCUENTO_VENCIMIENTO": 7457,
        "DESCUENTO_CAJA_CHICA": 7454,
        "ADELANTO": 7432,
        "INASISTENCIA": 7455,
        "INASISTENCIA_LOGISTICA": 7537,
        "JORNADA": 7443,
        "JORNADA_LOGISTICA": 7539,
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
    
    def indicarSede(self, businessId):
        if businessId==8132:
            Sede = "Retamas"
        else:
            Sede = "Cobian"
        return Sede
    
    def validarGastos(self, businessId, apartado):
        errores = []
        sede = self.indicarSede(businessId)
        categorias = self.configuracionSedes.get(businessId)
        gastos = self.obtenerGastosSede(businessId)
        for gasto in gastos:
            amount = gasto.get("amount")
            #Validaciones
            if not amount:
                errores.append(f"Gasto sin monto en sede {sede}, fecha: {gasto.get('date')} "
                               f"de user: {gasto.get('description')}")
            else:
                try: amount = Decimal(str(amount))
                except (ValueError, TypeError):
                    errores.append(f"Monto no numérico en sede {sede}, fecha: {gasto.get('date')}"
                                   f"de user: {gasto.get('description')}")
                else:
                    if amount <= 0:
                        errores.append(f"Monto inválido (<=0) en sede {sede}, fecha: {gasto.get('date')}"
                                       f"de user: {gasto.get('description')}")
            if not gasto.get("description"):
                errores.append(f"Gasto sin nombre asignado en sede {sede}, fecha: {gasto.get('date')}"
                               f"de user: {gasto.get('description')}")
            if not gasto.get("category"):
                errores.append(f"Gasto sin categoria asignada en sede {sede}, fecha: {gasto.get('date')}"
                               f"de user: {gasto.get('description')}")
            if not categorias:
                errores.append(f"La sede {businessId} no está configurada.")
            elif apartado not in categorias:
                opciones = ", ".join(categorias.keys())
                errores.append(f"El apartado '{apartado}' no existe. Opciones disponibles: {opciones}.")
            else:
                categoriaId = categorias[apartado]
        # Si hubo errores, detener el programa
        if errores:
            mensaje_final = "Se encontraron errores de validación:\n" + "\n".join(errores)
            raise ValueError(mensaje_final)
        # Si no hubo errores, continua
        return categoriaId

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
        ids = []
        pagina = 1
        while True:
            endpoint = (f"/sales/expenses/?page={pagina}&business={businessId}&date__lte={fechaFin}&date__gte={fechaInicio}")
            request = RequestHandler(endpoint, businessId=businessId)
            respuesta = request.execute()
            resultados = respuesta.get("results") or []
            #gastos.extend(resultados)
            for res in resultados:
                if not res['id'] in ids:
                    ids.append(res['id'])
                    gastos.append(res)
            print(f"Sede {businessId} - página {pagina}: {len(resultados)} registros obtenidos. Acumulados: {len(gastos)} ")
            if not resultados:
                break
            pagina += 1
        self.gastosPorSede[businessId] = gastos
        return gastos

    def perteneceAlPeriodo(self, gasto):
        fechaTexto = gasto.get("date")
        if not fechaTexto:
            return False
        try:
            fechaUtc = datetime.fromisoformat(fechaTexto.replace("Z", "+00:00"))
            fechaLocal = fechaUtc.astimezone(ZoneInfo("America/Lima"))
        except (TypeError, ValueError):
            print(f"Advertencia: fecha inválida: {fechaTexto}")
            return False
        return (fechaLocal.year == self.year and fechaLocal.month == self.month)

    def get(self, businessId, apartado, username):
        if businessId not in self.configuracionSedes:
            raise ValueError(f"La sede {businessId} no está configurada.")
        if not isinstance(apartado, str):
            raise TypeError("El apartado debe enviarse como texto.")
        if not isinstance(username, str):
            raise TypeError("El username debe enviarse como texto.")
        apartado = apartado.strip().upper()
        username = self.normalizarNombre(username)
        categoriaId = self.validarGastos(businessId, apartado)
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
            nombre = self.normalizarNombre(gasto.get("description"))
            if nombre != username:
                continue
            fecha = self.obtenerFechaLocal(gasto)
            if fecha is None:
                continue
            observations = gasto.get("observations")
            cantidad = Decimal(str(gasto.get("amount", "0.00")))
            registros.append({
                "fecha": fecha,
                "cantidad": cantidad,
                "observations": observations
            })
            total += cantidad
        registros.sort(key=lambda registro: registro["fecha"])
        return registros
    
def run():
    year, month = solicitarPeriodo()
    gestor = GestorIncidenciasNomina(configuracionSedes=CONFIGURACION_SEDES, year=year, month=month)
    
    print("Cargando información de las sedes...")
    gestor.cargarDatos()

    print("INASISTENCIA_LOGISTICA")
    jornada = gestor.get(5053, "INASISTENCIA","Ruth")
    print(jornada)
    print("JORNADA_LOGISTICA")
    jornada = gestor.get(8132, "JORNADA_LOGISTICA","TEST")
    print(jornada)

if __name__ == "__main__":
    run()