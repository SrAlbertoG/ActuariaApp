# Entregable 2 — Facturas y transacciones

## Alcance

El módulo permite consultar facturas, revisar su información básica, seleccionar
una o varias facturas, consultar las transacciones RIPS activas relacionadas y
preparar una selección para el siguiente entregable.

La ejecución de extracción, homologación y exportación no forma parte de este
módulo; corresponde al entregable 3.

## Fuentes de facturación

El servicio combina dos fuentes sin solapamiento por periodo:

| Periodo | Fuente | Campo de referencia |
| --- | --- | --- |
| Hasta agosto de 2026 | Base Montos Fijos | MesdeServicio |
| Desde septiembre de 2026 | SQL Server, BiPagosFPR | FechaFactura por defecto |

La fecha de corte predeterminada es 2026-09-01 y se puede cambiar mediante
ACTUARIA_INVOICE_SOURCE_CUTOFF.

El campo temporal de FPR se puede configurar con:

- ACTUARIA_FPR_PERIOD_FIELD=FechaFactura
- ACTUARIA_FPR_PERIOD_FIELD=FechaRadicacion

Ambas opciones están validadas por una lista permitida en Settings. Actuaría
debe confirmar cuál fecha corresponde al criterio oficial del periodo antes
del despliegue productivo.

## Archivo Base Montos Fijos

El backend busca por defecto:

resources/inputs/BaseMontosFijos2026.xlsx

La ubicación puede cambiarse con ACTUARIA_FIXED_COSTS_FILE. La primera hoja
del libro debe contener Nit, Contrato, Prefijo, Factura, MesdeServicio y
ValorFacturaRadicada.

El archivo no se versiona en Git: contiene información de facturación y debe
distribuirse por el canal institucional autorizado. Consulta
resources/inputs/README.md.

## API protegida

Todos los endpoints quedan bajo /api/v1 y conservan la validación del token
de sesión y la dependencia de conexión SQL Server activa.

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | /contracts | Catálogo de contratos |
| GET | /providers | Catálogo de prestadores, con filtros opcionales |
| GET | /invoices | Búsqueda de facturas con filtros y paginación |
| GET | /invoices/{invoice_id} | Detalle de factura |
| GET | /invoices/{invoice_id}/transactions | Transacciones de una factura |
| GET | /transactions | Transacciones de una selección pequeña |
| POST | /transactions/search | Consulta paginada de transacciones de una selección múltiple |

Filtros de /invoices: contract, provider_nit, invoice, start_date,
end_date, page y page_size.

El endpoint POST recibe JSON con invoice_ids, page y page_size. Se usa
para selecciones múltiples y evita colocar cientos de identificadores en la URL.
La selección admite hasta 250 facturas por consulta y cada página devuelve
hasta 100 transacciones.

Las consultas a SQL Server usan parámetros ODBC (?). Los únicos fragmentos
dinámicos de SQL corresponden a tablas y expresiones de fecha definidas en el
backend; los campos temporales se validan con una lista permitida.

## Arquitectura

- repositories/fixed_cost_repository.py: lectura, normalización, caché y
  búsqueda en Excel.
- repositories/sql_server_invoice_repository.py: catálogo y búsqueda FPR.
- repositories/sql_server_transaction_repository.py: consulta de
  RIPSArchivoTransaccion, limitada a rat_Activo = 'Activo'.
- services/invoice_service.py: reglas de fuentes, corte, combinación y
  paginación.
- services/transaction_service.py: validación de selección y búsqueda RIPS.
- services/invoice_identifiers.py: identificadores transportables para la UI.
- schemas/invoices.py: contratos Pydantic.
- api/v1/invoices.py y api/v1/transactions.py: endpoints FastAPI.
- features/extraction: tipos, cliente HTTP y pantalla React del módulo.

El servicio utiliza AuthService.connection() para abrir y cerrar una conexión
por operación. No persiste conexiones ni credenciales adicionales.

## Pruebas

Desde la carpeta backend:

python -m pytest

Las pruebas añadidas validan normalización y filtros del Excel, codificación de
identificadores, parametrización de consultas, selección máxima y paginación
entre fuentes.

Desde apps/desktop:

npm test

Para compilar la interfaz:

npm run build

## Pendientes de validación funcional

1. Confirmar con Actuaría si el corte de FPR se debe basar en FechaFactura o
   FechaRadicacion.
2. Confirmar si ValorInicioFactura de la última liquidación es el importe que
   se debe mostrar, o si debe prevalecer ValorBruto de FPR.
3. Validar en el entorno de SQL Server que los campos usados para enlazar
   transacciones (rat_NumeroFactura, rat_NumeroIdentificacion y
   rat_NumeroContrato) conservan los mismos formatos que FPR y Base Montos
   Fijos.
4. Probar con una copia autorizada del libro Excel y con un usuario SQL que
   tenga permisos de lectura sobre las tablas consultadas.
