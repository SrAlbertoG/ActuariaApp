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
| GET | /invoices | Búsqueda paginada tradicional de facturas |\n| GET | /invoices/dataset | Recupera el conjunto completo acotado de facturas para paginación local |
| GET | /invoices/{invoice_id} | Detalle de factura |
| GET | /invoices/{invoice_id}/transactions | Transacciones de una factura |
| GET | /transactions | Transacciones de una selección pequeña |
| POST | /transactions/search | Consulta paginada tradicional de transacciones |\n| POST | /transactions/dataset | Recupera el conjunto completo acotado de transacciones para paginación local |
| POST | /extraction/prepare | Valida y confirma la selección sin ejecutar extracción |

Filtros de /invoices: contract, provider_nit, invoice, start_date,
end_date, page y page_size.

El endpoint POST recibe JSON con invoice_ids, page y page_size, y admite
contract, provider_nit e invoice para conservar los criterios no vacíos de la
búsqueda original. Se usa para selecciones múltiples y evita colocar cientos de
identificadores en la URL.
La pantalla de generación utiliza los endpoints de dataset para realizar una
consulta por búsqueda de facturas y una consulta por conjunto de facturas
seleccionadas para transacciones. El backend devuelve todos los registros cuando
el resultado no supera 1.000; React conserva ese conjunto en memoria y realiza
la paginación de 25 filas localmente, sin ejecutar SQL al cambiar de página.
Si una búsqueda supera 1.000 facturas o una selección supera 1.000 transacciones,
el backend responde HTTP 413 con un mensaje que solicita refinar los filtros.
Los endpoints paginados tradicionales se conservan para compatibilidad con otros
consumidores.

La búsqueda de transacciones siempre se limita a los números completos de las
facturas seleccionadas y a `rat_Activo = 'Activo'`. Además, recibe únicamente
los criterios no vacíos que el analista utilizó al buscar las facturas:

- `provider_nit`: compara con `rat_NumeroIdentificacion`.
- `contract`: compara con `rat_NumeroContrato`.
- `invoice`: compara con `rat_NumeroFactura` usando el texto de búsqueda.

No se inventan filtros para campos que el analista dejó vacíos. Si la búsqueda
se hizo solo por NIT, se aplica solo NIT; si se hizo por contrato, solo contrato;
y si se usaron NIT, contrato y factura, se aplican los tres simultáneamente.
Estos mismos parámetros se envían a `/extraction/prepare` y se vuelven a
validar en SQL Server antes de aceptar los identificadores seleccionados.

Las consultas a SQL Server usan parámetros ODBC (?). Los únicos fragmentos
dinámicos de SQL corresponden a tablas y expresiones de fecha definidas en el
backend; los campos temporales se validan con una lista permitida.

## Reglas funcionales de elegibilidad de facturas

Para los registros provenientes de `BiPagosFPR`, la consulta solo incluye:

1. `NombreEstadoFactura = 'Finalizada'`.
2. `NombreEstadoFactura = 'Para respuesta prestador'` y `ValorPagar`
   convertido a un valor numérico distinto de cero.

Por tanto, se excluyen los demás estados, los valores nulos de
`ValorPagarrad`, los valores iguales a cero y los valores no numéricos para
el estado `Para respuesta prestador`. Los espacios al inicio o al final del
estado se normalizan antes de compararlo.

### Exclusión de duplicados frente a Base Montos Fijos

Antes de devolver facturas SQL, el backend compara cada registro con las claves
normalizadas del Excel de costos fijos. La clave natural es:

`(NIT, contrato, prefijo + factura)`

Las claves se extraen de todas las filas que tengan NIT, contrato y factura
completos, incluso si su MesdeServicio está vacío o no es válido. Esas filas no
se presentan como facturas históricas, pero sí participan en la deduplicación.

Solo se incluyen registros FPR cuya clave no exista en Base Montos Fijos. La
exclusión se aplica tanto al conteo como a la paginación y al detalle de factura,
de modo que un duplicado no reaparezca al cambiar de página ni al consultar su
detalle. Si el archivo falta o no puede leerse, el backend omite tanto los periodos
históricos como las facturas FPR, devuelve cero resultados con una advertencia y
bloquea el detalle FPR. No expone registros SQL cuando no puede demostrar que
no están duplicados en Base Montos Fijos.

### Interfaz y selección

- Contrato y NIT son campos de texto libre con sugerencias debajo del campo;
  no se utilizan selects nativos. Se conserva el texto aun cuando no se elija
  una sugerencia.
- Las sugerencias admiten navegación por teclado: flechas arriba/abajo, Enter
  para seleccionar la opción activa y Escape para cerrar.
- **Seleccionar todas** las facturas descarga y selecciona todas las páginas
  del resultado, no solo las filas visibles.
- El encabezado de transacciones dispone de **Seleccionar todas las
  transacciones** y **Quitar selección global**, que operan sobre el conjunto
  completo consultado aunque la tabla esté mostrando otra página.
- Las transacciones coincidentes se preseleccionan automáticamente. Los cambios
  manuales y globales se conservan al paginar.
- La preferencia de tema claro/oscuro se aplica a toda la aplicación y se
  conserva localmente entre aperturas.
- La selección global está limitada a 1.000 facturas y 1.000 transacciones por
  preparación. Si se supera ese límite, se muestra un mensaje y no se presenta
  una selección parcial como si estuviera completa.

## Arquitectura

- repositories/fixed_cost_repository.py: lectura, normalización, caché y
  búsqueda en Excel.
- repositories/sql_server_invoice_repository.py: catálogo y búsqueda FPR.
- repositories/sql_server_transaction_repository.py: consulta de
  RIPSArchivoTransaccion, limitada a rat_Activo = 'Activo'.
- services/invoice_service.py: reglas de fuentes, corte, combinación y
  paginación.
- services/transaction_service.py: validación de selección y búsqueda RIPS.
- services/contract_service.py y services/provider_service.py: catálogos independientes.
- services/extraction_preparation_service.py: validación de selección activa para el siguiente entregable.
- services/invoice_identifiers.py: identificadores transportables para la UI.
- schemas/invoices.py: contratos Pydantic.
- api/v1/invoices.py y api/v1/transactions.py: endpoints FastAPI.
- features/extraction: tipos, cliente HTTP y pantalla React del módulo.

El servicio utiliza AuthService.connection() para abrir y cerrar una conexión
por operación. No persiste conexiones ni credenciales adicionales.

El endpoint /extraction/prepare valida que los IDs de transacción seleccionados
continúen activos y correspondan a los números de factura enviados. Devuelve un
resumen validado (fecha, conteos, contratos y NIT de RIPS); no crea una ejecución
ni consulta todavía las cuatro tablas de detalle.

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


## Optimización de rendimiento y paginación

- La pantalla consume `GET /invoices/dataset` y `POST /transactions/dataset`.
- Cada endpoint devuelve un conjunto completo de hasta 1.000 registros. La
  paginación de 25 filas se realiza en memoria en React; cambiar de página no
  vuelve a consultar SQL Server ni deja filas esperando una petición.
- Se solicita internamente un registro adicional para detectar excedentes y
  responder HTTP 413 antes de presentar una selección parcial.
- El filtro de números de factura en RIPS usa `IN (?, ...)` parametrizado en
  lugar de una cadena de predicados `OR`.
- La tabla temporal de exclusión de Base Montos Fijos dispone de un índice
  compuesto por NIT, contrato y factura para acelerar el anti-join `NOT EXISTS`.
- No se crean índices permanentes en la base institucional desde la aplicación.
  Se recomienda que el DBA evalúe índices sobre `BiPagosLiquidacion
  (NumRadicadoBoxalud, FechaLiquidacion, IdLiquidacion) INCLUDE
  (ValorInicioFactura)` y sobre los campos de filtro/orden de
  `BiPagosFPR` y `RIPSArchivoTransaccion`, validando los planes de ejecución y
  la carga de escritura antes de aplicarlos.
