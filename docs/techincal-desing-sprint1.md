# DISEÑO TÉCNICO DETALLADO – SPRINT 1
## Plataforma Centralizada de Automatización – Área de Actuaría EPS

**Versión:** 1.2  
**Backend:** Python + FastAPI  
**Frontend:** React + TypeScript  
**Aplicación de escritorio:** Tauri 2  
**Base de datos:** SQL Server  
**Modalidad:** Ejecución local individual  
**Objetivo del sprint:** Entregar una aplicación de escritorio funcional que permita conectarse a SQL Server, buscar facturas y transacciones, extraer los cuatro tipos de RIPS sin homologación y exportar los resultados.

---

# 1. Objetivo del Sprint 1

Construir la primera versión funcional de la nueva plataforma de Actuaría utilizando una arquitectura desacoplada entre la interfaz gráfica y el backend Python.

El sprint tendrá tres entregables consecutivos:

1. Inicio de sesión y guardado seguro de credenciales.
2. Interfaz para generar RIPS, buscar y visualizar facturas y transacciones.
3. Versión final para extraer RIPS sin homologación e incorporar el botón de exportación.

El resultado deberá ser una aplicación de escritorio ejecutable en Windows, preparada para evolucionar posteriormente hacia una modalidad web.

# 2. Alcance técnico

## 2.1. Incluido

- Estructura del monorepositorio.
- Configuración de Tauri 2.
- Configuración de React + TypeScript.
- Configuración de FastAPI.
- Integración del backend Python como proceso local.
- Comunicación HTTP REST entre interfaz y backend.
- Inicio de sesión para conexión SQL Server.
- Persistencia segura de credenciales.
- Búsqueda de facturas.
- Visualización de facturas.
- Consulta de transacciones.
- Interfaz de extracción.
- Extracción de consultas, procedimientos, medicamentos e insumos.
- Validación de contratos.
- Consolidación de RIPS.
- Visualización de resultados.
- Exportación de RIPS a Excel sin homologación.
- Registro de ejecuciones y errores.

## 2.2. Fuera del alcance

- Homologación de medicamentos, insumos, consultas y procedimientos.
- Agrupación actuarial.
- Cálculo de frecuencias y costos promedio.
- Migración del Monitor MEDCOL.
- Dashboard actuarial integrado.
- Administración de usuarios de la aplicación.
- Despliegue web centralizado.
- Gestión multiusuario concurrente.

# 3. Arquitectura técnica

## 3.1. Diagrama general

```text
┌─────────────────────────────────────────────┐
│              APLICACIÓN DESKTOP             │
│                                             │
│               Tauri 2                       │
│          React + TypeScript                 │
│                                             │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Inicio       │  │ Generación de RIPS   │ │
│  │ de sesión    │  │ Facturas             │ │
│  └──────────────┘  │ Transacciones        │ │
│                    │ Resultados           │ │
│                    │ Exportación          │ │
│                    └──────────────────────┘ │
└──────────────────────┬──────────────────────┘
                       │ HTTP REST local
                       ▼
┌─────────────────────────────────────────────┐
│                BACKEND PYTHON               │
│                                             │
│                  FastAPI                    │
│                                             │
│  API → Servicios → Repositorios → Procesos  │
│                                             │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Conexión DB  │  │ Extracción RIPS      │ │
│  │ Facturación  │  │ Validación contratos │ │
│  │ Transacciones│  │ Consolidación        │ │
│  └──────────────┘  └──────────────────────┘ │
└──────────┬──────────────────────┬───────────┘
           │                      │
           ▼                      ▼
┌───────────────────┐  ┌──────────────────────┐
│    SQL SERVER     │  │  ARCHIVOS LOCALES    │
│                   │  │                      │
│ Facturación       │  │ Excel de entrada     │
│ Transacciones     │  │ Resultados temporales│
│ Tablas RIPS       │  │ Excel de exportación │
└───────────────────┘  └──────────────────────┘

       SQLite: historial y metadatos locales
```

## 3.2. Responsabilidades por capa

### Tauri

- Iniciar la interfaz de escritorio.
- Iniciar el backend empaquetado.
- Gestionar el ciclo de vida de la aplicación.
- Cerrar el proceso Python cuando la aplicación finalice.
- Gestionar operaciones específicas del sistema operativo cuando sean necesarias.

### React

- Presentar las pantallas.
- Capturar parámetros.
- Mostrar facturas y transacciones.
- Mostrar estados de las extracciones.
- Presentar tablas de resultados.
- Activar las exportaciones.
- Consumir los endpoints de FastAPI.

La interfaz no deberá conectarse directamente con SQL Server ni contener reglas de negocio.

### FastAPI

- Exponer los servicios mediante endpoints REST.
- Validar las solicitudes.
- Gestionar conexiones.
- Ejecutar los servicios de negocio.
- Controlar procesos de extracción.
- Devolver resultados y estados de ejecución.
- Registrar errores.

### Python

- Consultar facturas.
- Consultar transacciones.
- Extraer las cuatro categorías RIPS.
- Validar contratos.
- Consolidar DataFrames.
- Generar archivos Excel.
- Administrar conexiones y credenciales.

---

# 4. Estructura inicial del proyecto

```text
plataforma-actuaria/
│
├── apps/
│   ├── desktop/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── layouts/
│   │   │   ├── pages/
│   │   │   ├── features/
│   │   │   │   ├── authentication/
│   │   │   │   ├── extraction/
│   │   │   │   ├── invoices/
│   │   │   │   ├── transactions/
│   │   │   │   └── results/
│   │   │   ├── services/
│   │   │   ├── hooks/
│   │   │   ├── types/
│   │   │   └── App.tsx
│   │   ├── src-tauri/
│   │   └── package.json
│   │
│   └── web/
│       └── (futura implementación)
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── invoices.py
│   │   │       ├── transactions.py
│   │   │       ├── extractions.py
│   │   │       ├── results.py
│   │   │       └── exports.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   │
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── processors/
│   │   ├── integrations/
│   │   │   └── sql_server/
│   │   ├── storage/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── resources/
│   ├── templates/
│   └── homologaciones/
│
├── docs/
├── scripts/
├── .gitignore
└── README.md
```

La carpeta `apps/web` se incorporará posteriormente. El backend deberá quedar preparado desde el inicio para no depender de Tauri.

---

# 5. Entregable 1: Inicio de sesión y guardado de credenciales

## 5.1. Objetivo

Construir el mecanismo de acceso a la aplicación y conexión a SQL Server.

El alcance de autenticación de este entregable corresponde a las credenciales necesarias para conectarse a SQL Server, no a un sistema independiente de cuentas de usuario de la plataforma.

## 5.2. Funcionalidades

1. Mostrar pantalla de inicio de sesión.
2. Capturar los datos de conexión.
3. Validar la conexión con SQL Server.
4. Mostrar errores de autenticación o disponibilidad.
5. Permitir guardar las credenciales.
6. Recuperar credenciales almacenadas al iniciar la aplicación.
7. Intentar conexión automática.
8. Permitir cerrar sesión.
9. Permitir eliminar las credenciales recordadas.

## 5.3. Datos de conexión

La pantalla deberá contemplar los campos que requiera la configuración institucional:

- Servidor.
- Base de datos.
- Usuario.
- Contraseña.
- Tipo de autenticación, cuando aplique.
- Recordar mis credenciales.

La aplicación deberá contemplar la posibilidad de autenticación integrada de Windows si la configuración de SQL Server y las políticas de la organización lo permiten.

## 5.4. Persistencia segura

No se almacenará la contraseña en SQLite, archivos JSON, archivos `.env`, `config.py` ni registros de ejecución.

Se utilizará un almacén seguro del sistema operativo Windows, mediante una integración como Python Keyring y el almacén de credenciales correspondiente.

Comportamiento:

```text
Inicio de aplicación
        |
        v
¿Existen credenciales guardadas?
        |
    ┌───┴───┐
    |       |
   Sí       No
    |       |
    v       v
Intentar   Mostrar
conexión   login
    |
    v
¿Conexión exitosa?
    |
 ┌──┴──┐
 |     |
Sí     No
 |     |
 v     v
Abrir  Solicitar
app    credenciales
```

La sesión de conexión activa estará en memoria. No se persistirá el objeto de conexión.

## 5.5. Endpoints

| Método | Endpoint | Responsabilidad |
|---|---|---|
| POST | `/api/v1/auth/sql-server/login` | Validar credenciales y establecer conexión |
| GET | `/api/v1/auth/sql-server/status` | Consultar estado de conexión |
| POST | `/api/v1/auth/sql-server/remember` | Guardar credenciales de forma segura |
| DELETE | `/api/v1/auth/sql-server/credentials` | Eliminar credenciales guardadas |
| POST | `/api/v1/auth/sql-server/logout` | Cerrar conexión |

La implementación deberá evitar registrar contraseñas en logs o mensajes de error.

## 5.6. Interfaz

La pantalla de acceso deberá incluir:

- Nombre de la plataforma.
- Servidor.
- Base de datos.
- Usuario.
- Contraseña.
- Opción para recordar credenciales.
- Botón de conectar.
- Indicador de conexión.
- Mensajes de error.

Estados visuales:

- Sin conexión.
- Conectando.
- Conexión exitosa.
- Credenciales incorrectas.
- Servidor no disponible.
- Error de permisos.

## 5.7. Criterios de aceptación

- El usuario puede ingresar sus credenciales.
- La aplicación valida la conexión real con SQL Server.
- Las credenciales pueden guardarse de manera segura.
- Al reiniciar la aplicación, intenta reconectarse automáticamente.
- Si falla la reconexión, permite ingresar nuevas credenciales.
- El usuario puede eliminar las credenciales guardadas.
- No aparecen contraseñas en los logs.
- La interfaz no permite acceder a las pantallas que requieren SQL Server cuando no hay conexión.

---

# 6. Entregable 2: Interfaz de generación de RIPS, búsqueda y visualización de facturas y transacciones

## 6.1. Objetivo

Construir la interfaz principal de la plataforma y permitir que el analista consulte las facturas disponibles, revise sus transacciones y seleccione la información que participará en la extracción.

## 6.2. Navegación principal

La aplicación contará inicialmente con los siguientes módulos:

- Inicio.
- Generación de RIPS.
- Facturas.
- Transacciones.
- Resultados.

La navegación deberá ser modular para incorporar posteriormente homologación, agrupación y dashboard actuarial.

## 6.3. Flujo funcional

```text
Inicio
  |
  v
Seleccionar contrato
  |
  v
Seleccionar prestador
  |
  v
Seleccionar periodo
  |
  v
Buscar facturas
  |
  v
Visualizar facturas
  |
  v
Seleccionar facturas
  |
  v
Consultar transacciones
  |
  v
Visualizar transacciones
  |
  v
Confirmar selección
  |
  v
Preparar extracción
```

## 6.4. Pantalla de generación

La pantalla deberá incluir:

### Parámetros de búsqueda

- Contrato.
- Prestador.
- Fecha inicial.
- Fecha final.
- Periodo de servicio.
- Factura, cuando se necesite una búsqueda específica.

Los filtros definitivos deberán corresponder a los campos disponibles en las fuentes de datos.

### Tabla de facturas

Columnas propuestas:

- Selección.
- Factura.
- NIT.
- Prestador.
- Contrato.
- Mes de servicio.
- Valor radicado.
- Fuente.

La tabla deberá permitir:

- Buscar.
- Ordenar.
- Filtrar.
- Seleccionar una o varias facturas.
- Consultar detalle.
- Navegar resultados mediante paginación o virtualización.

### Tabla de transacciones

Columnas propuestas:

- Selección.
- Código de transacción.
- Factura.
- Contrato.
- NIT del prestador.
- Código del prestador.
- Fecha de cargue RIPS.
- Fecha de radicación.

La información deberá proceder de la consulta a `dbo.RIPSArchivoTransaccion`, respetando la condición `rat_Activo = 'Activo'`.

El usuario deberá poder consultar qué transacciones están asociadas a cada factura.

## 6.5. Endpoints

| Método | Endpoint | Responsabilidad |
|---|---|---|
| GET | `/api/v1/contracts` | Obtener contratos |
| GET | `/api/v1/providers` | Obtener prestadores |
| GET | `/api/v1/invoices` | Buscar facturas |
| GET | `/api/v1/invoices/{id}` | Consultar detalle de factura |
| GET | `/api/v1/transactions` | Consultar transacciones |
| GET | `/api/v1/invoices/{id}/transactions` | Consultar transacciones por factura |

Los endpoints deberán recibir parámetros de filtrado y paginación.

## 6.6. Servicios backend

Se implementarán los siguientes servicios:

- `InvoiceService`: búsqueda y normalización de facturas.
- `TransactionService`: búsqueda de transacciones.
- `ContractService`: consulta de contratos.
- `ProviderService`: consulta de prestadores.
- `ExtractionPreparationService`: preparación de los identificadores seleccionados.

Los servicios utilizarán repositorios para acceder a SQL Server o a las fuentes Excel.

## 6.7. Criterios de aceptación

- El usuario puede seleccionar contratos, prestadores y periodos.
- Puede consultar las facturas disponibles.
- Puede filtrar y buscar facturas.
- Puede visualizar el detalle de una factura.
- Puede consultar las transacciones asociadas.
- Puede seleccionar las facturas y transacciones requeridas.
- Los datos presentados coinciden con las consultas del backend.
- La interfaz puede manejar conjuntos grandes de resultados sin intentar cargar todos los registros en el navegador.

---

## 6.8. Reglas implementadas para elegibilidad, duplicados y selección

### Elegibilidad de facturas FPR

La consulta a `BiPagosFPR` deberá restringir los registros a:

- `EstadoFacturarad = 'Finalizada'`; o
- `EstadoFacturarad = 'Para respuesta prestador'` cuando
  `ValorPagarrad` no sea nulo, pueda convertirse a decimal y sea distinto
  de cero.

Los estados se comparan después de quitar espacios externos. Para el segundo
estado, valores nulos, cero y no numéricos se excluyen.

### Deduplicación contra Base Montos Fijos

El repositorio Excel normaliza los identificadores y expone las claves
`(NIT, contrato, Prefijo + Factura)`. El repositorio FPR carga esas claves en
una tabla temporal de SQL Server y usa `NOT EXISTS` para excluir coincidencias.
La misma exclusión se aplica al conteo, a cada página y a la consulta de detalle.
No se debe deduplicar solo por número de factura, porque puede repetirse entre
prestadores o contratos.

Si no se encuentra el archivo, la API devuelve una advertencia que informa
tanto la indisponibilidad de los periodos históricos como la imposibilidad de
garantizar la deduplicación de FPR contra el Excel.

### Filtros de transacciones

`POST /api/v1/transactions/search` recibe `invoice_ids` y, opcionalmente,
`provider_nit`, `contract` e `invoice`. El backend construye filtros
parametrizados solo para los criterios no vacíos, sobre
`rat_NumeroIdentificacion`, `rat_NumeroContrato` y
`rat_NumeroFactura`, respectivamente. Siempre conserva el filtro por números
de factura seleccionados y `rat_Activo = 'Activo'`.

`POST /api/v1/extraction/prepare` recibe los mismos criterios y los vuelve a
aplicar al validar los identificadores. De esta forma, no se confía únicamente
en la selección que mantiene React.

### Interfaz

- Los campos de contrato y NIT son inputs de texto libre con sugerencias
  remotas que se filtran mientras el analista escribe.
- Seleccionar todas las facturas recupera todas las páginas del conjunto
  actual, hasta un máximo de 1.000.
- La consulta de transacciones carga todas las coincidencias hasta un máximo
  de 1.000; se preseleccionan todas las filas elegibles y la paginación se
  realiza en el cliente para conservar la selección al cambiar de página.
- Si el resultado supera el máximo, se informa y se exige refinar filtros; no
  se presenta una selección parcial como completa.
- El tema claro/oscuro es global, se aplica mediante una clase raíz y se
  persiste en el almacenamiento local del frontend.

# 7. Entregable 3: Versión final de extracción RIPS sin homologación y exportación

## 7.1. Objetivo

Integrar el motor de extracción con la nueva interfaz y permitir obtener los cuatro conjuntos de RIPS sin aplicar reglas de homologación.

El usuario deberá poder ejecutar el proceso, hacer seguimiento, consultar los resultados y exportarlos.

## 7.2. Flujo completo

```text
Facturas seleccionadas
        |
        v
Validar contratos
        |
        v
Consultar transacciones
        |
        v
Extraer identificadores rat_Id
        |
        v
Consultar tablas RIPS
        |
        +-----------------------------+
        |             |               |
        v             v               v
     Consulta    Procedimiento    Medicamento
        |             |               |
        +-------------+---------------+
                      |
                      v
                   Insumos
                      |
                      v
             Normalizar estructuras
                      |
                      v
             Consolidar resultados
                      |
                      v
              Mostrar resultados
                      |
                      v
               Exportar Excel
```

## 7.3. Extracción de tecnologías

Se conservarán las relaciones existentes en el repositorio:

| Tabla | Categoría | Identificador |
|---|---|---|
| `RIPSArchivoConsulta` | Consulta | `rao_Id` |
| `RIPSArchivoProcedimiento` | Procedimiento | `rar_Id` |
| `RIPSArchivoMedicamento` | Medicamento | `ram_Id` |
| `RIPSArchivoOtroServicio` | Insumo | `ras_Id` |

Las consultas deberán relacionar las tablas mediante `rat_Id`.

Los identificadores de transacción se deberán procesar en bloques cuando el volumen de información lo requiera, evitando construir consultas SQL excesivamente grandes.

Todas las consultas deberán estar parametrizadas.

## 7.4. Normalización

Los resultados deberán mantener una estructura consistente para que puedan visualizarse y exportarse sin depender de la tabla SQL de origen.

Campos esperados:

- Id.
- CodigoTransaccion.
- CodigoPrestador.
- CodigoUsuario.
- Factura.
- CodigoTecnologia.
- Descripcion.
- Valor.
- TipoTecnologia.
- NumeroUnidad.
- FechaServicio.
- FechaFactura.
- Tipo.

Los campos que no estén disponibles para una categoría deberán tratarse de manera explícita, sin asignar valores inventados.

Se conservarán los códigos originales y las descripciones obtenidas directamente de las fuentes.

## 7.5. Validación de contratos

Se integrará el procedimiento existente:

1. Identificar facturas con contratos diferentes de los seleccionados.
2. Consultar `dbo.BiPagosFPR`.
3. Identificar el contrato correcto.
4. Corregir cuando sea válido.
5. Descartar facturas que no puedan validarse.
6. Registrar los motivos de corrección y descarte.

El resumen de ejecución deberá permitir identificar:

- Facturas consultadas.
- Facturas válidas.
- Facturas corregidas.
- Facturas descartadas.
- Transacciones encontradas.
- Registros extraídos por categoría.
- Errores.

## 7.6. Ejecución como tarea de backend

La extracción no deberá ejecutarse dentro de una solicitud HTTP que permanezca abierta durante todo el proceso.

Comportamiento:

1. La interfaz envía los parámetros.
2. FastAPI registra una ejecución.
3. El backend devuelve un identificador.
4. Python ejecuta la extracción.
5. La interfaz consulta periódicamente el estado.
6. El backend actualiza el progreso.
7. Al finalizar, se presentan los resultados.

Endpoints propuestos:

| Método | Endpoint | Responsabilidad |
|---|---|---|
| POST | `/api/v1/extractions` | Crear ejecución |
| GET | `/api/v1/extractions/{id}` | Consultar estado |
| GET | `/api/v1/extractions/{id}/results` | Obtener resultados |
| POST | `/api/v1/extractions/{id}/cancel` | Solicitar cancelación, si es técnicamente segura |
| GET | `/api/v1/exports/{id}` | Obtener archivo exportado |

La primera versión podrá usar un gestor local de tareas en el backend, sin incorporar Redis ni Celery.

## 7.7. Interfaz de resultados

Cuando finalice la extracción, la aplicación deberá mostrar:

- Estado de la ejecución.
- Fecha de inicio y finalización.
- Contratos consultados.
- Facturas procesadas.
- Transacciones encontradas.
- Total de registros por categoría.
- Errores y advertencias.
- Acceso a las tablas de resultados.

El usuario podrá consultar por separado:

- Consultas.
- Procedimientos.
- Medicamentos.
- Insumos.

Las tablas deberán disponer de búsqueda, filtros, ordenamiento y paginación o virtualización.

## 7.8. Botón de exportación

El botón de exportación estará disponible cuando existan resultados válidos.

Etiqueta propuesta:

**Exportar RIPS a Excel**

La primera implementación deberá generar un archivo Excel con las hojas:

1. Facturas.
2. Transacciones.
3. Consultas.
4. Procedimientos.
5. Medicamentos.
6. Insumos.
7. Resumen.

La estructura podrá ajustarse después de validar el formato esperado por los analistas.

El archivo deberá:

- Conservar códigos originales.
- Conservar las descripciones originales disponibles.
- Mantener identificadores de factura y transacción.
- Identificar la categoría de cada registro.
- Evitar aplicar homologaciones.
- Conservar los parámetros de la ejecución en el resumen.
- Informar la ubicación del archivo generado.

La generación se realizará desde Python, utilizando OpenPyXL inicialmente.

## 7.9. Criterios de aceptación

- Se pueden ejecutar las cuatro consultas de RIPS.
- Los registros se relacionan correctamente con las transacciones y facturas.
- Se ejecuta la validación de contratos.
- Los resultados quedan organizados por categoría.
- No se aplica homologación.
- Los códigos originales permanecen intactos.
- La interfaz presenta resultados y errores.
- Se puede exportar un archivo Excel.
- El archivo contiene las hojas definidas.
- El resultado exportado coincide con los registros mostrados en la aplicación.
- La extracción deja un registro de los parámetros y resultados de la ejecución.

---

# 8. Diseño de API y contratos de datos

## 8.1. Convenciones

- Prefijo: `/api/v1`.
- Comunicación mediante JSON.
- Fechas en formato ISO 8601.
- Identificadores de ejecuciones únicos.
- Errores con estructura consistente.
- Paginación para resultados de gran volumen.
- No devolver credenciales ni secretos.

## 8.2. Ejemplo de creación de extracción

Solicitud conceptual:

```json
{
  "contracts": ["CONTRATO_001"],
  "providers": ["900000000"],
  "start_date": "2026-01-01",
  "end_date": "2026-01-31",
  "invoice_ids": ["FACTURA_001", "FACTURA_002"],
  "categories": [
    "consulta",
    "procedimiento",
    "medicamento",
    "insumo"
  ],
  "homologate": false
}
```

La propiedad `homologate` deberá mantenerse explícitamente en `false` para esta primera versión.

Respuesta conceptual:

```json
{
  "execution_id": "uuid",
  "status": "queued",
  "message": "Extracción registrada correctamente"
}
```

## 8.3. Estados de ejecución

- `queued`: en espera.
- `running`: en ejecución.
- `completed`: finalizada.
- `completed_with_warnings`: finalizada con advertencias.
- `failed`: error.
- `cancelled`: cancelada.

Los estados deberán ser consistentes entre backend y frontend.

---

# 9. Gestión de datos y rendimiento

## 9.1. Procesamiento

La aplicación deberá evitar cargar volúmenes completos en memoria cuando no sea necesario.

Se aplicarán:

- Consultas específicas por facturas y transacciones seleccionadas.
- Procesamiento por bloques.
- Selección explícita de columnas.
- Eliminación de duplicados según identificadores definidos.
- Paginación en consultas de interfaz.
- Virtualización de tablas.
- Liberación de recursos al finalizar las ejecuciones.

Pandas será la herramienta inicial de procesamiento para aprovechar el código existente. Polars podrá incorporarse después de comparar rendimiento en operaciones concretas.

## 9.2. Almacenamiento local

SQLite podrá almacenar:

- Identificador de ejecución.
- Fecha de ejecución.
- Parámetros no sensibles.
- Estado.
- Totales procesados.
- Ubicación de resultados.
- Mensajes de error resumidos.

No almacenará contraseñas SQL ni información clínica completa innecesariamente.

## 9.3. Archivos temporales

Los archivos deberán gestionarse en directorios controlados por la aplicación.

Se deberá definir:

- Directorio de trabajo.
- Convención de nombres.
- Identificador de ejecución.
- Política de limpieza.
- Separación entre archivos temporales y archivos exportados por el usuario.

---

# 10. Seguridad y operación local

La aplicación deberá implementar:

1. FastAPI escuchando exclusivamente en `127.0.0.1`.
2. Puerto local asignado de manera controlada para evitar conflictos.
3. Token de sesión temporal entre Tauri y FastAPI.
4. Validación de las solicitudes locales.
5. Credenciales almacenadas en el almacén seguro de Windows.
6. Consultas SQL parametrizadas.
7. No registrar contraseñas, cadenas de conexión completas ni datos sensibles en logs.
8. Liberación de conexiones al cerrar la aplicación.
9. Control de errores sin exponer detalles internos innecesarios.
10. Uso de permisos mínimos para acceder a SQL Server.

Tauri será responsable de iniciar y cerrar el proceso Python empaquetado.

En la construcción de Windows se utilizará PyInstaller para generar el ejecutable del backend y Tauri para incorporarlo como proceso externo.

---

# 11. Pruebas

## 11.1. Pruebas del entregable 1

- Conexión exitosa.
- Usuario incorrecto.
- Contraseña incorrecta.
- Servidor no disponible.
- Guardado de credenciales.
- Recuperación de credenciales.
- Eliminación de credenciales.
- Reconexión automática.
- Ausencia de contraseñas en logs.

## 11.2. Pruebas del entregable 2

- Búsqueda por contrato.
- Búsqueda por prestador.
- Búsqueda por factura.
- Filtrado por periodo.
- Consulta de detalle de factura.
- Consulta de transacciones relacionadas.
- Facturas sin transacciones.
- Resultados paginados.
- Volúmenes grandes de información.
- Facturas FPR con estado Finalizada.
- Facturas FPR Para respuesta prestador con ValorPagarrad nulo, cero, no numérico o distinto de cero.
- Exclusión de duplicados FPR frente a Base Montos Fijos por NIT, contrato y número completo de factura.
- Búsqueda de transacciones usando únicamente los filtros originales suministrados por el analista.
- Rechazo en preparación de transacciones inactivas o que no cumplan los filtros originales.
- Selección global de facturas y transacciones entre páginas.
- Preselección automática de transacciones coincidentes.
- Sugerencias en los campos de contrato y NIT.
- Persistencia de la preferencia de tema claro/oscuro.
- Validación de consistencia entre interfaz y SQL Server.

## 11.3. Pruebas del entregable 3

- Extracción de consultas.
- Extracción de procedimientos.
- Extracción de medicamentos.
- Extracción de insumos.
- Relación mediante `rat_Id`.
- Validación y corrección de contratos.
- Facturas descartadas.
- Consolidación.
- Ausencia de homologación.
- Preservación de códigos originales.
- Generación de Excel.
- Integridad del archivo exportado.
- Errores durante la extracción.

---

# 12. Criterios generales de finalización del Sprint 1

El sprint se considerará terminado cuando:

- La aplicación pueda instalarse y abrirse en Windows.
- Tauri inicie el backend Python correctamente.
- React se comunique con FastAPI.
- El inicio de sesión permita conectarse a SQL Server.
- Las credenciales puedan recordarse de manera segura.
- El usuario pueda buscar y visualizar facturas.
- El usuario pueda consultar las transacciones relacionadas.
- El usuario pueda ejecutar la extracción de las cuatro categorías RIPS.
- Los resultados se encuentren consolidados y separados por categoría.
- La extracción no aplique homologaciones.
- La aplicación permita exportar los resultados a Excel.
- Existan pruebas de los principales flujos.
- Se documenten los errores conocidos y las limitaciones.

# 13. Dependencias y riesgos

| Riesgo o dependencia | Impacto | Acción |
|---|---|---|
| Acceso a SQL Server | Bloquea las consultas | Validar conectividad y permisos al inicio |
| Credenciales almacenadas | Riesgo de seguridad | Utilizar almacén seguro de Windows |
| Volumen de RIPS | Rendimiento | Procesar por bloques y paginar |
| Consultas SQL existentes | Integridad de resultados | Comparar contra el proceso actual |
| Facturas duplicadas | Duplicidad de información | Definir identificadores y reglas de deduplicación |
| Contratos inconsistentes | Pérdida de información válida | Conservar validación y registrar correcciones |
| Campos incompletos | Errores de consolidación | Validar esquemas por categoría |
| Construcción Tauri/Python | Problemas de empaquetado | Probar el ejecutable desde el primer entregable |

# 14. Evolución posterior

Los siguientes módulos se desarrollarán después de estabilizar la primera versión:

1. Homologación de medicamentos, insumos, consultas y procedimientos.
2. Agrupación actuarial.
3. Cálculo de frecuencias por tecnología y grupo.
4. Cálculo de costos promedio por tecnología y grupo.
5. Migración del Monitor MEDCOL desde Streamlit.
6. Dashboard actuarial integrado.
7. Modalidad web centralizada.

El Monitor MEDCOL se tratará como una fase posterior del producto. No será una dependencia para completar el Sprint 1.

La meta final será consolidar en un dashboard actuarial los costos por factura y mes, las frecuencias por tecnología y grupo, y los costos promedio correspondientes.

---

# 15. Referencias técnicas

- Tauri 2: https://v2.tauri.app/
- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/docs/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- Tailwind CSS: https://tailwindcss.com/docs
- shadcn/ui: https://ui.shadcn.com/
- Apache ECharts: https://echarts.apache.org/
- TanStack Table: https://tanstack.com/table/latest
- PyODBC: https://github.com/mkleehammer/pyodbc
- OpenPyXL: https://openpyxl.readthedocs.io/
- PyInstaller: https://pyinstaller.org/
- Pytest: https://docs.pytest.org/

