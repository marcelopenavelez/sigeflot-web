"""Safe, transactional importer for the official workbook."""
import argparse
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from openpyxl import load_workbook
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import Vehiculo, Conductor, Proveedor, OrdenServicio, Mantenimiento, Salida, CatalogoMantenimientoOrigen, CatalogoMantenimientoBIOrigen

SOURCE="Control_Flota_DIRESA"
def t(v): return str(v).strip() if v not in (None,"") else None
def p(v): return t(v).upper() if t(v) else None
def n(v):
    try:return int(float(v)) if v not in (None,"") else None
    except (TypeError,ValueError):return None
def d(v): return v.date() if isinstance(v,datetime) else (v if hasattr(v,"year") else None)
def m(v):
    try:return Decimal(str(v)) if v not in (None,"") else Decimal("0")
    except Exception:return Decimal("0")
def data(w,prefix):
    s=next(x for x in w.worksheets if x.title.casefold().startswith(prefix.casefold())); vs=list(s.values); return [dict(zip(vs[0],r)) for r in vs[1:] if any(x not in (None,"") for x in r)]
def put(session, model, column, value, values, stat):
    if not value: stat["SKIPPED"]+=1; return None
    old=session.scalar(select(model).where(column==value))
    if old: stat["EXISTS"]+=1; return old
    obj=model(**values); session.add(obj); session.flush(); stat["CREATED"]+=1; return obj
def validate_target(database, production, source, environment=None):
    """Require three independent controls before a production import."""
    environment = os.environ if environment is None else environment
    if database == "sigeflot_migration_test":
        if production:
            raise SystemExit("APPLY_BLOCKED: --production cannot target sigeflot_migration_test")
        return
    if not production:
        raise SystemExit("APPLY_BLOCKED: non-test targets require --production")
    if environment.get("APP_ENV") != "production":
        raise SystemExit("APPLY_BLOCKED: APP_ENV must be production")
    if environment.get("SIGEFLOT_ALLOW_PRODUCTION_IMPORT") != "true":
        raise SystemExit("APPLY_BLOCKED: production authorization is missing")
    if environment.get("SIGEFLOT_IMPORT_CONFIRMATION") != "CONTROL_FLOTA_DIRESA_2026":
        raise SystemExit("APPLY_BLOCKED: production confirmation is invalid")
    if Path(source).name != "Control_Flota_DIRESA.xlsx":
        raise SystemExit("APPLY_BLOCKED: official source filename is required")

def safe(args):
    database = make_url(get_settings().database_url).database
    validate_target(database, args.production, args.source)
    print(f"Target database: {database}")
def load(w,session,all_):
    S={x:{"CREATED":0,"EXISTS":0,"SKIPPED":0,"ERROR":0} for x in ["vehicles","drivers","providers","service-orders","maintenance","trips","catalogs"]}
    active,inactive=data(w,"Flota_Vehicular"),data(w,"Flota_Inactiva")
    for r in active:
      q=p(r.get("Placa")); put(session,Vehiculo,Vehiculo.placa,q,{"placa":q,"marca_modelo_origen":t(r.get("Marca_Modelo")),"anio":n(r.get("Año")),"tipo":t(r.get("Tipo_Vehiculo")),"kilometraje_actual":n(r.get("Kilometraje_Actual")),"estado":"OPERATIVO","soat_vencimiento":d(r.get("Fecha_Vencimiento_SOAT")),"revision_tecnica_vencimiento":d(r.get("Fecha_Venc_Rev_Tecnica")),"observaciones":t(r.get("Observaciones_Estado")),"es_historico":True,"fuente_origen":SOURCE},S["vehicles"])
    for r in inactive:
      q=p(r.get("Placa")); put(session,Vehiculo,Vehiculo.placa,q,{"placa":q,"estado":"INACTIVO","fecha_inactividad":d(r.get("Fecha_Inactividad_Inicio")),"causal_inactividad":t(r.get("Causal")),"es_historico":True,"fuente_origen":SOURCE},S["vehicles"])
    V={x.placa:x.id for x in session.scalars(select(Vehiculo)).all()}
    for r in data(w,"Choferes"):
      q=t(r.get("IDCHOFER")); put(session,Conductor,Conductor.id_chofer_origen,q,{"id_chofer_origen":q,"nombres":t(r.get("Nombre_Completo")),"documento":None,"licencia_vencimiento":d(r.get("Licencia_Vence")),"telefono":t(r.get("Telefono_Contacto")),"email":t(r.get("Correo electronico")),"es_historico":True,"fuente_origen":SOURCE},S["drivers"])
    names={}
    for r in data(w,"Orden")+data(w,"HIST"):
      q=t(r.get("Proveedor_Taller")); names.setdefault(q.casefold() if q else "",q)
    for q in names.values():
      old=session.scalar(select(Proveedor).where(func.lower(Proveedor.razon_social)==q.casefold())) if q else None
      if old:S["providers"]["EXISTS"]+=1
      elif q:session.add(Proveedor(razon_social=q,es_historico=True,fuente_origen=SOURCE)); session.flush();S["providers"]["CREATED"]+=1
    P={x.razon_social.casefold():x.id for x in session.scalars(select(Proveedor)).all()}
    for r in data(w,"Orden"):
      q=t(r.get("ID_Orden")); put(session,OrdenServicio,OrdenServicio.id_orden_origen,q,{"id_orden_origen":q,"numero_orden":q,"vehiculo_id":V.get(p(r.get("Placa"))),"proveedor_id":P.get((t(r.get("Proveedor_Taller")) or "").casefold()),"fecha":d(r.get("Fecha_Registro")),"descripcion":t(r.get("Checklist_Preventivo")) or t(r.get("Descripcion_Correctivo")) or "","monto":m(r.get("Costo_Total_Orden")),"estado":t(r.get("Estado_Archivo")) or "HISTORICO","es_historico":True,"fuente_origen":SOURCE},S["service-orders"])
    O={x.id_orden_origen:x.id for x in session.scalars(select(OrdenServicio)).all()}
    for r in data(w,"HIST"):
      q=t(r.get("ID_Registro")); typ=(t(r.get("Tipo_Mantenimiento")) or "").upper(); typ=typ if typ in {"PREVENTIVO","CORRECTIVO"} else None
      put(session,Mantenimiento,Mantenimiento.id_registro_origen,q,{"id_registro_origen":q,"orden_servicio_origen":t(r.get("Orden_Servicio")),"vehiculo_id":V.get(p(r.get("Placa"))),"orden_servicio_id":O.get(t(r.get("Orden_Servicio"))),"tipo":typ,"fecha":d(r.get("Fecha_Falla")),"kilometraje":n(r.get("Kilometraje")) or 0,"descripcion":t(r.get("Descripción_Reparación")) or "","costo":m(r.get("Costo_Total")),"estado":"HISTORICO","es_historico":True,"fuente_origen":SOURCE},S["maintenance"])
    for r in data(w,"Registro"):
      q=t(r.get("ID_Salida")); km=n(r.get("INGRESA TU KILOMETRAJE")); stamp=r.get("Marca temporal"); stamp=stamp if isinstance(stamp,datetime) else datetime.combine(d(stamp) or datetime.now().date(),datetime.min.time())
      if km is None or km<0:S["trips"]["SKIPPED"]+=1
      else:put(session,Salida,Salida.id_salida_origen,q,{"id_salida_origen":q,"vehiculo_id":V.get(p(r.get("INGRESA  TU PLACA"))),"fecha_hora_salida":stamp,"kilometraje_salida":km,"estado":"CERRADA","es_historico":True,"fuente_origen":SOURCE},S["trips"])
    for r in data(w,"Catálogo"):
      q=t(r.get("ID_Componente")); put(session,CatalogoMantenimientoOrigen,CatalogoMantenimientoOrigen.id_componente_origen,q,{"id_componente_origen":q,"tarea":t(r.get("Componente_o_Tarea")) or "","prioridad":t(r.get("Prioridad")),"intervalo_km":n(r.get("Intervalo_Km")),"intervalo_dias":n(r.get("Intervalo_Dias")),"umbral_alerta":m(r.get("Umbral_Alerta (%)")),"umbral_critico":m(r.get("Umbral_Critico (%)"))},S["catalogs"])
    exist={x.fila_origen for x in session.scalars(select(CatalogoMantenimientoBIOrigen)).all()}
    for row_number,r in enumerate(data(w,"Catalogo_Inteligente"), start=2):
      q=(t(r.get("Variante_o_Palabra_Clave")) or "",t(r.get("Tarea_Estandarizada")),t(r.get("Tipo")))
      if row_number in exist:S["catalogs"]["EXISTS"]+=1
      else:session.add(CatalogoMantenimientoBIOrigen(fila_origen=row_number,variante=q[0],tarea_estandarizada=q[1],tipo=q[2]));exist.add(row_number);S["catalogs"]["CREATED"]+=1
    return S
def main():
  a=argparse.ArgumentParser();a.add_argument("--source",required=True);a.add_argument("--dry-run",action="store_true");a.add_argument("--apply",action="store_true");a.add_argument("--production",action="store_true");a.add_argument("--all",action="store_true");args=a.parse_args();w=load_workbook(Path(args.source),read_only=True,data_only=True)
  if not args.apply: print("DRY_RUN: no database writes; sheets=%d"%len(w.worksheets));return
  safe(args)
  with SessionLocal.begin() as s: print(load(w,s,args.all))
if __name__=="__main__":main()
