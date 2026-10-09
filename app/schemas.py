from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from .models import NombreSalon, TamanoSalon, AreaStaff, EstadoEvento   
#El Base va a agrupar los campos que tienen en comun lo que se envia y lo que se responde.
#El Create se usa para validar los datos recibidos en los POST o PUT (El post crea y el put reemplaza o actualiza)
#create no incluye la validacion del id porque lo genero automaticamente la bd
#El Response se usa para dar un formato de respuesta, que es loo qye va a recibir el usuario utilizando la bd.

# TABLAS CLIENTES

class ClienteBase(BaseModel):
#En Field(...), '...' indica que el campo es obligatorio
#max_lenghth mira que no se supere cierto numero.
    documento: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=100)
    correo: EmailStr #valida que tenga un formato de correo.
    telefono: str = Field(..., max_length=30)
    tipo_cliente: str = Field(..., max_length=50)
    
class ClienteCreate(ClienteBase):
    pass #hereda todos los campos de ClienteBase sin agregar nada extra

class ClienteResponse(ClienteBase): #El ClienteResponse corresponde a la info que se le va a devolver ak usuario.
    id_cliente: int #Devuelvo el id generado por la base de datos
    fecha_registro: date #devuelvo tmb la fecha en la que se registro el cliente.
    
    class Config:
        from_attributes = True


#TABLAS SERIVICIOS

class ServicioBase(BaseModel):
    nombre_servicio: str = Field(..., max_length=150)
    categoria: str = Field(..., max_length=50)
    modo_cobro: str = Field(..., max_length=20)
    precio_unitario: Decimal = Field(..., gt=0, decimal_places=2) #gt=0 --> greater than 0

class ServicioCreate(ServicioBase):
    pass

class ServicioResponse(ServicioBase):
    id_servicio: int
    class Config:
        from_attributes = True


#TABLAS SALON

class SalonBase(BaseModel):
    #nombre_salon: str = Field(..., max_length=100)
    nombre_salon: NombreSalon 
    #tamano: str = Field(..., max_length=20)
    tamano: TamanoSalon
    capacidad: int = Field(..., gt=0) #La capacidad del salon no puede ser menor a 0
    precio_hora: Decimal = Field(..., gt=0, decimal_places=2)
    disponible: bool = True

class SalonCreate(SalonBase):
    pass

class SalonResponse (SalonBase):
    id_salon: int
    class Config:
        from_attributes = True


#TABLAS STAFF

class StaffBase(BaseModel):
    nombre_staff: str = Field(..., max_length=150)
    cargo: str = Field(..., max_length=100)
    #area: str = Field(..., max_length=50)
    area: AreaStaff
    correo: EmailStr
    jefe_id: Optional[int] = None #No todos los staff tienen jefe, por lo que es opcional.

class StaffCreate(StaffBase):
    pass

class StaffResponse(StaffBase):
    id_staff: int
    fecha_ingreso: date
    class Config:
        from_attributes = True

#TABLAS EVENTO

class EventoBase(BaseModel):
    cliente_id: int
    salon_id: int
    coordinador_id: int
    nombre_evento: str = Field(..., max_length=150)
    tipo: str = Field(..., max_length=50)
    inicio_evento: datetime
    fin_evento: datetime
    aforo_esperado: int = Field(..., gt=0)
    #estado_evento: str = Field(default = "Cotizado")
    estado_evento: EstadoEvento = EstadoEvento.cotizado #por defecto es cotizado. ###Ver si yo intento poner algo que no sea cotizado me deja?

class EventoCreate(EventoBase):
    pass

class EventoResponse(EventoBase):
    id_evento: int
    subtotal: Decimal = Field(..., gt=0, decimal_places=2)
    tasa_asistencia: Optional[Decimal] = None
    class Config:
        from_attributes = True


#TABLAS EVENTO_SERVICIOS

class Evento_ServiciosBase(BaseModel):
    id_servicio: int
    cantidad: Optional[Decimal] = Field(None, gt=0)

class Evento_ServiciosCreate(Evento_ServiciosBase):
    pass

class Evento_ServiciosResponse(Evento_ServiciosBase):
    id_evento_servicio: int
    id_evento: int
    cantidad: Decimal #Se pone porque aca ya tiene que devolverse obligatoriamente.
    precio_unitario: Decimal
    total_evento_servicios: Decimal

    class Config:
        from_attributes = True


#TABLAS ASISTENTES


class AsistenteBase(BaseModel):
    documento: str = Field(..., max_length=20)
    nombre_asistente: str = Field(..., max_length=100)
    correo: EmailStr
    empresa: Optional[str] = Field(None, max_length=150)

class AsistenteCreate(AsistenteBase):
    pass

class AsistenteResponse(AsistenteBase):
    id_asistente: int
    class Config:
        from_attributes = True

#TABLAS INSCRIPCIONES
class InscripcionesBase(BaseModel):
    id_evento: int
    id_asistente: int

class InscripcionCreate(InscripcionesBase):
    pass

class InscripcionResponse(InscripcionesBase):
    id_inscripcion: int
    fecha_inscripcion: datetime
    check_in: Optional[datetime] = None

    class Config:
        from_attributes = True

#TABLAS AUDITORIA

class Auditoria_EventoBase(BaseModel):
    id_evento: int
    campo: str = Field(..., max_length=100)
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    usuario_cambio: Optional[str] = Field(None, max_length=100)

class Auditoria_EventoCreate(Auditoria_EventoBase):
    pass

class Auditoria_EventoResponse(Auditoria_EventoBase):
    id_auditoria: int
    fecha_cambio: datetime
    
    class Config:
        from_attributes = True
    



##FALTA PONER LO DE LOS TRIGGERS, FUNCIONES, WINDOWS, etc.