from datetime import date
from app.models import CatalogoMantenimientoOrigen, OrdenServicio, OrdenServicioPreventivo, Proveedor, Vehiculo
from .conftest import token

def h(client, role='ADMINISTRADOR'): return {'Authorization': f'Bearer {token(client, role.lower()+"@example.com")}' }
def seed(db):
    v=Vehiculo(placa='F11-001',estado='OPERATIVO',kilometraje_actual=100); p=Proveedor(razon_social='Activo',activo=True); c=CatalogoMantenimientoOrigen(id_componente_origen='F11-C',tarea='Tarea')
    db.add_all([v,p,c]);db.flush();o=OrdenServicio(numero_orden='F11-ORD',vehiculo_id=v.id,proveedor_id=p.id,fecha=date.today(),descripcion='Correctivo: x',descripcion_correctivo='x',kilometraje_orden=100,monto=None,dias_parada=None,estado='ABIERTA',estado_archivo='PENDIENTE',es_historico=False,fuente_origen='OPERATIVO');o.preventivos=[OrdenServicioPreventivo(catalogo=c)];db.add(o);db.commit();db.refresh(o);return o,v,p,c
def test_update_roles_and_validation(client,db_session):
    o,v,p,c=seed(db_session); url=f'/api/v1/ordenes-servicio/{o.id}'
    for role in ('ADMINISTRADOR','MECANICO'): assert client.patch(url,headers=h(client,role),json={'monto':12.5}).status_code==200
    for role in ('CONSULTA','CHOFER'): assert client.patch(url,headers=h(client,role),json={'monto':1}).status_code==403
    for body in ({'monto':-1},{'dias_parada':-1},{'kilometraje_orden':-1},{'preventivo_ids':[c.id,c.id]},{'preventivo_ids':[],'descripcion_correctivo':''},{'proveedor_id':9999}): assert client.patch(url,headers=h(client),json=body).status_code==422
    inactive=Proveedor(razon_social='Inactivo',activo=False);db_session.add(inactive);db_session.commit();assert client.patch(url,headers=h(client),json={'proveedor_id':inactive.id}).status_code==422
def test_history_closed_and_mileage(client,db_session):
    o,v,p,c=seed(db_session); url=f'/api/v1/ordenes-servicio/{o.id}'
    assert client.patch(url,headers=h(client),json={'kilometraje_orden':50}).status_code==200;db_session.expire_all();assert db_session.get(Vehiculo,v.id).kilometraje_actual==100
    assert client.post(url+'/cerrar',headers=h(client)).status_code==200;assert client.patch(url,headers=h(client),json={'monto':1}).status_code==409;assert client.post(url+'/cerrar',headers=h(client)).status_code==409
    hist=OrdenServicio(numero_orden='F11-H',descripcion='x',estado='HISTORICO',es_historico=True,fuente_origen='x');db_session.add(hist);db_session.commit()
    for suffix,method in (('',client.patch),('/cerrar',client.post),('/archivo',client.patch)):
        kwargs={'json':{'monto':1} if not suffix else ({'estado_archivo':'ARCHIVADO'} if suffix=='/archivo' else {})};assert method(f'/api/v1/ordenes-servicio/{hist.id}'+suffix,headers=h(client),**kwargs).status_code==409
def test_archive_and_audit(client,db_session):
    o,v,p,c=seed(db_session);url=f'/api/v1/ordenes-servicio/{o.id}'
    assert client.patch(url,headers=h(client),json={'monto':12.5}).status_code==200
    assert client.patch(url+'/archivo',headers=h(client),json={'estado_archivo':'ARCHIVADO'}).status_code==200
    assert client.post(url+'/cerrar',headers=h(client)).status_code==200
    for role in ('ADMINISTRADOR','MECANICO','CONSULTA'):
        body=client.get(url+'/auditoria',headers=h(client,role)).json();assert {x['accion'] for x in body}>={'EDITADA','ESTADO_ARCHIVO_CAMBIADO','CERRADA'}
    assert any(x['cambios'].get('monto',{}).get('despues')==12.5 for x in body)
