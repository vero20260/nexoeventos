from sqlalchemy import Column, DateTime, func, Integer, String, Date, Float, ForeignKey, Text, Boolean, CheckConstraint, Numeric, Enum
from sqlalchemy.orm import relationship, backref #backref sirve para crear una ruta bidireccional entre dos clases, es como un camino entre ambas que deja pasar de la una a la otra.
from .database import Base
import enum


#CLIENTES

class ClienteEntity(Base):
    __tablename__= "clientes"
    id_cliente = Column(Integer, primary_key = True, index=True)
    tipo_cliente = Column(String(50), nullable = False) #El CheckConstraint se pone despues en el __table_args__, ahi se hacen las validaciones.
    documento = Column(String(20), nullable = False, unique = True)
    nombre = Column(String(100), nullable = False)
    correo = Column(String(100), nullable = False)
    telefono = Column (String(30), nullable = False)
    fecha_registro = Column(Date, nullable = False)

    __table_args__ = (
        CheckConstraint("LOWER (tipo_cliente) IN ('persona natural', 'empresa')", name = 'check_tipo_cliente'),
    )

    #relaciones entre tablas
    eventos = relationship("EventoEntity", back_populates="cliente")

#SERVICIOS

class ServicioEntity(Base):
    __tablename__ = "servicios"
    id_servicio = Column(Integer, primary_key = True, index=True)
    nombre_servicio = Column(String(150), nullable = False)
    categoria = Column(String(50), nullable=False) #Hacer check constraint
    modo_cobro = Column(String(20), nullable=False) #En este es para ver si se cobra por persona, unidad, etc. NO ES MEDIO DE PAGO
    precio_unitario = Column(Numeric(10,2), nullable=False) #Hacer check de que sea mayor que 0

    __table_args__ = (
        CheckConstraint( "LOWER (categoria) IN ('bebidas', 'refrigerios', 'audiovisuales')", name = 'check_categoria_servicio'), #Poner las categorias
        CheckConstraint("LOWER (modo_cobro) IN ('por persona', 'por hora', 'por unidad')", name='check_modo_cobro'),#poner si es unitario, por persona, etc.
        CheckConstraint('precio_unitario > 0', name='check_precio_unitario_servicio'),
    )
    #Relaciones tablas
    evento_servicios = relationship("Evento_ServiciosEntity", back_populates="servicio")



##SALONES

#Crea una clase pero que no es tabla sino que es tipo de dato. Optimiza si despues quiero usar salones en otra cosa.
#Ademas me va a permitir hacer un menu desplegable en frontend
class NombreSalon (str, enum.Enum):
    salon_orquidea = "Salón Orquídea"
    salon_heliconia = "Salón Heliconia"
    salon_guayacan = "Salón Guayacán"
    salon_ceiba = "Salón Ceiba"
    gran_salon_condor = "Gran Salón Cóndor"
    auditorio_principal = "Auditorio Principal"

class TamanoSalon (str, enum.Enum):
    pequeno = "Pequeño"
    mediano = "Mediano"
    grande = "Grande"

class SalonEntity(Base):
    __tablename__= 'salones'
    id_salon = Column(Integer, primary_key = True, index=True)
    nombre_salon = Column(Enum(NombreSalon), nullable=False) #Ahora es un tipo de dato, no un string normal
    tamano = Column(Enum(TamanoSalon), nullable=False) #Tamaños disponibles
    capacidad = Column(Integer,nullable=False) #Hacer check>0
    precio_hora = Column(Numeric(12,2), nullable=False) #Hacer check > 0
    disponible = Column(Boolean, default=True) #Por defecto es true, osea que esta disponible.

    __table_args__= (
        CheckConstraint('capacidad > 0', name='check_capacidad'),
        CheckConstraint('precio_hora > 0', name='check_precio_hora')
    )

    #Relaciones tablas
    eventos = relationship("EventoEntity", back_populates="salon")

#STAFF

class AreaStaff(str, enum.Enum):
    direccion = "Dirección"
    operaciones = "Operaciones"
    comercial = "Comercial"
    logistica = "Logística"
    alimentos_y_bebidas = "Alimentos y Bebidas"
    audiovisuales = "Audiovisuales"

class StaffEntity(Base):
    __tablename__ = 'staff'
    id_staff = Column(Integer, primary_key = True, index=True)
    nombre_staff = Column(String(150), nullable=False)
    cargo = Column(String(100), nullable=False)
    area = Column(Enum(AreaStaff), nullable=False) #Check de las areas disponibles
    correo = Column(String(150), nullable=False, unique=True)
    fecha_ingreso = Column(Date, nullable=False)
    jefe_id = Column(Integer, ForeignKey('staff.id_staff'), nullable=True) #Para saber quien es el jefe del jefe
    #Como determinamos quien es jefe de quien?
    
    #Relaciones gtablas
    #jerarquia (Jefe-subordinado) se debe hacer una autoreferencia, es decir referenciamos la mimsa tabla
    subordinados = relationship("StaffEntity", backref=backref("jefe", remote_side=[id_staff])) #el backred le dice a SQLALchemy que cree una propiedad llamada .jefe en cada objeto de la clase Staff, para que apunte a su superior directo-
    #Aca 'subordinados' va a permitir consultar la lista de personas a cargo de un jefe (se utilizaria usando jefe.subordinados)
    eventos_coordinador = relationship("EventoEntity", back_populates = "coordinador") #relaciona al staff con los eventos que coordina. Es una relacion bidireccional con el atributo 'coordinador0 en la tabla eventos.


#EVENTOS
class EstadoEvento(str, enum.Enum):
    cotizado = "Cotizado"
    confirmado = "Confirmado"
    finalizado = "Finalizado"
    cancelado = "Cancelado"

class EventoEntity(Base):
    __tablename__= 'eventos'
    id_evento = Column(Integer, primary_key = True, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id_cliente'), nullable=False)
    salon_id = Column(Integer, ForeignKey('salones.id_salon'), nullable=False)
    nombre_evento = Column(String(150), nullable=False)
    tipo = Column(String(50), nullable=False)
    inicio_evento = Column(DateTime, nullable=False)
    fin_evento = Column(DateTime, nullable=False)
    aforo_esperado = Column(Integer, nullable=False) #Hacer check > 0
    coordinador_id = Column(Integer, ForeignKey('staff.id_staff'), nullable=False)
    estado_evento = Column(Enum(EstadoEvento), nullable=False, default = 'Cotizado') #hacer check entre los estados disponibles
    subtotal = Column(Numeric(14,2), nullable=False) #Hacer check de que sea > 0 #Este subtotal es el precio por hora del salon
    tasa_asistencia = Column(Numeric(5,2), nullable = True)

    __table_args__= (
        CheckConstraint('aforo_esperado >= 0', name = "check_aforo_evento"),
        CheckConstraint('subtotal > 0', name = "check_subtotal_evento"),
        CheckConstraint('fin_evento > inicio_evento', name="check_rango_fechas"),
    ) 
    #Relaciones tablas
    cliente = relationship("ClienteEntity", back_populates="eventos")
    salon = relationship("SalonEntity", back_populates="eventos")
    coordinador = relationship("StaffEntity", back_populates="eventos_coordinador")
    servicios = relationship("Evento_ServiciosEntity", back_populates="evento")
    inscripciones = relationship("InscripcionesEntity", back_populates="evento")
    auditorias = relationship("Auditoria_EventosEntity", back_populates="evento")
    
#EVENTOS Y SERVICIOS

class Evento_ServiciosEntity(Base):
    __tablename__ = 'evento_servicios'
    id_evento_servicio = Column(Integer, primary_key = True, index=True)
    id_evento = Column(Integer, ForeignKey('eventos.id_evento'), nullable=False)
    id_servicio = Column(Integer, ForeignKey('servicios.id_servicio'), nullable=False)
    cantidad = Column(Numeric(10,2), nullable=False) #Hacer chech>0
    precio_unitario = Column(Numeric(10,2), nullable=False) #Hacer chech>0
    total_evento_servicios = Column(Numeric(10,2), nullable=False) #Hacer chech>0

    __table_args__ = (
        CheckConstraint('cantidad > 0', name="check_cantidad_servicio"),
        CheckConstraint('precio_unitario > 0', name="check_precio_unitario_evento_servicio"),
        CheckConstraint('total_evento_servicios > 0', name="check_total_evento_servicios"),
    )
    #relaciones tablals
    evento = relationship("EventoEntity", back_populates="servicios") #me permite navegar desde el detalle del servicio hacia el evento que tiene asociado
    servicio = relationship("ServicioEntity", back_populates = "evento_servicios") #me permite ir del detalle hacia el servicio que se contrato.

#ASISTENTES

class AsistenteEntity(Base):
    __tablename__ = 'asistentes'
    id_asistente = Column(Integer, primary_key = True, index=True)
    documento = Column(String(20), nullable = False, unique=True)
    nombre_asistente = Column(String(150), nullable=False)
    correo = Column(String(150), nullable=False, unique=True)
    empresa = Column(String(150), nullable=True)

    #Relaciones
    inscripciones = relationship("InscripcionesEntity", back_populates="asistente")


#INSCRIPCIONES
class InscripcionesEntity(Base):
    __tablename__ = "inscripciones"
    id_inscripciones = Column(Integer, primary_key = True, index=True)
    id_evento = Column(Integer, ForeignKey('eventos.id_evento'), nullable=False)
    id_asistente = Column(Integer, ForeignKey('asistentes.id_asistente'), nullable=False)
    fecha_inscripcion= Column(DateTime, nullable=False)
    check_in = Column(DateTime, nullable=True)
    
    #relaciones tablas
    evento = relationship("EventoEntity", back_populates="inscripciones")
    asistente = relationship("AsistenteEntity", back_populates="inscripciones")


#AUDITORIA_EVENTOS

class Auditoria_EventosEntity(Base):
#Auditoria_Eventos es el nombre de la clase en python que mapea la tabla
#auditoria_eventos es el nombre de la tabla en postgress
#auditorias es el nombre del atributo con el que se puede navegar por python , ej: evento.auditorias
    __tablename__ = "auditoria_eventos"
    id_auditoria = Column(Integer, primary_key=True, index=True)
    id_evento = Column(Integer, ForeignKey('eventos.id_evento'), nullable=False)
    campo = Column(String(30), nullable=False) #En campo se va a decir que columna de la tabla eventos fue cambiada, es decir puede ser, estado_evento, subtotal, aforo_esperado, inicio_evento, fin_evento, nombre_evento
    valor_anterior = Column(String(255), nullable=True)
    valor_nuevo = Column(String(255), nullable=True)
    fecha_cambio = Column(DateTime, nullable=False, default=func.now())
    usuario_cambio = Column(String(100), nullable=True) #Para saber quien hizo el cambio.

    #relaciones tablas
    evento = relationship("EventoEntity", back_populates = "auditorias")

