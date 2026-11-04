# PLATAFORMA CENTRALIZADA DE AUTOMATIZACIÓN – ÁREA DE ACTUARÍA EPS

**Versión:** 1.3  
**Estado:** Especificación funcional y arquitectura tecnológica  
**Repositorio de referencia:** Automatizacion_BusquedaContratos  
**Backend:** Python + FastAPI  
**Frontend:** React + TypeScript  
**Aplicación de escritorio:** Tauri 2  
**Base de datos:** Microsoft SQL Server  
**Modalidad inicial:** Aplicación local instalada individualmente por analista

---

# 1. Visión del producto

## 1.1. Descripción

La plataforma centralizada de automatización del área de Actuaría busca integrar en una única aplicación los procesos de extracción, procesamiento, homologación, agrupación, visualización y exportación de información utilizados en los análisis actuariales y la elaboración de notas técnicas.

La solución parte del proyecto existente `Automatizacion_BusquedaContratos`, que implementa procesos de consulta de facturas, extracción de transacciones RIPS, recuperación de cuatro categorías de tecnologías, validación de contratos y homologación de medicamentos.

La nueva aplicación reemplazará progresivamente las interfaces y ejecuciones independientes por una plataforma de escritorio modular, con backend Python y una interfaz gráfica moderna.

La primera versión estará enfocada en:

1. Conexión a SQL Server y gestión segura de credenciales.
2. Búsqueda y visualización de facturas y transacciones.
3. Extracción de información RIPS.
4. Consolidación y validación de los cuatro tipos de RIPS.
5. Exportación de resultados sin homologación.

La homologación, agrupación actuarial, análisis de frecuencias y costos se incorporarán progresivamente.

## 1.2. Objetivo general

Centralizar y automatizar los procesos operativos del área de Actuaría mediante una plataforma modular que permita consultar, transformar, homologar, analizar y exportar información proveniente de diferentes fuentes.

## 1.3. Usuarios objetivo

**Analistas de Actuaría**

Podrán iniciar sesión, conectarse a SQL Server, ejecutar extracciones, seleccionar contratos y prestadores, consultar facturas, revisar transacciones y exportar resultados.

**Responsables del proceso actuarial**

Podrán consultar resultados, validar información, revisar homologaciones, agrupaciones y resultados de los análisis actuariales.

**Administrador técnico**

Podrá gestionar las configuraciones técnicas, conexiones, parámetros y actualizaciones de la aplicación.

En la primera etapa, la autenticación estará relacionada con la conexión a SQL Server. No se contempla inicialmente implementar un sistema independiente de usuarios ni una tabla propia de cuentas de la plataforma.

---

# 2. Arquitectura tecnológica

## 2.1. Stack tecnológico aprobado

| Capa | Tecnología | Responsabilidad |
|---|---|---|
| Aplicación de escritorio | Tauri 2 | Empaquetamiento y ejecución en Windows |
| Frontend | React + TypeScript | Interfaz gráfica |
| Estilos | Tailwind CSS | Sistema de diseño |
| Componentes visuales | shadcn/ui | Formularios, menús, ventanas y controles |
| Gráficos | Apache ECharts | Dashboards y visualizaciones |
| Tablas | TanStack Table + TanStack Virtual | Consulta y visualización de registros |
| Comunicación | HTTP REST + JSON | Comunicación frontend-backend |
| Backend | Python + FastAPI | API y lógica de negocio |
| Validación | Pydantic | Validación de parámetros y respuestas |
| Procesamiento | Pandas | Transformación de datos |
| Procesamiento complementario | Polars | Optimización de operaciones cuando sea necesario |
| Conexión SQL Server | PyODBC | Consulta de información |
| Archivos Excel | OpenPyXL | Lectura y generación de archivos |
| Almacenamiento local auxiliar | SQLite | Historial y metadatos |
| Credenciales | Almacén seguro de Windows | Persistencia de credenciales |
| Pruebas backend | Pytest | Pruebas de servicios y procesos |
| Pruebas frontend | Vitest | Pruebas de componentes y lógica |

## 2.2. Arquitectura inicial

La aplicación se distribuirá como un programa de escritorio. Cada analista tendrá una instalación independiente en su computador.

La arquitectura estará compuesta por:

- **Tauri:** inicia y controla la aplicación de escritorio.
- **React:** presenta la interfaz y gestiona la interacción con el usuario.
- **FastAPI:** expone los servicios del backend.
- **Python:** ejecuta las consultas, reglas de negocio y procesamiento.
- **SQL Server:** proporciona la información de facturación y RIPS.
- **SQLite:** conserva información auxiliar local, como historial de ejecuciones.
- **Almacenamiento local:** conserva temporalmente los archivos y resultados generados.

El backend FastAPI se ejecutará localmente en el equipo del usuario. No se requiere un servidor central para la primera versión.

## 2.3. Evolución hacia una arquitectura web

La arquitectura deberá permitir que, en una etapa posterior, React pueda funcionar desde un navegador y consumir un backend FastAPI centralizado.

La lógica de negocio deberá permanecer independiente de Tauri y React.

De esta forma, las funcionalidades de extracción, procesamiento, validación y homologación podrán reutilizarse en las dos modalidades:

- Aplicación de escritorio.
- Aplicación web centralizada.

La futura versión web requerirá incorporar autenticación corporativa, control de acceso, gestión multiusuario y almacenamiento centralizado.

---

# 3. Estado funcional del producto

Se establecen tres estados para diferenciar lo que existe de lo que requiere desarrollo.

| Estado | Significado |
|---|---|
| Implementado | Existe código funcional en el repositorio. |
| Parcial | Existe una implementación inicial, pero requiere integración, corrección o ampliación. |
| Pendiente | No existe una implementación funcional o debe construirse dentro de la nueva arquitectura. |

## 3.1. Matriz de funcionalidades

| Módulo | Funcionalidad | Estado |
|---|---|---|
| Acceso | Conexión SQL Server mediante PyODBC | Implementado |
| Acceso | Pantalla de inicio de sesión | Pendiente |
| Acceso | Guardado seguro de credenciales | Pendiente |
| Acceso | Reconexión automática | Pendiente |
| Facturación | Lectura Base Montos Fijos | Implementado |
| Facturación | Consulta de facturas FPR | Parcial |
| Facturación | Selección automática de fuentes | Pendiente |
| Facturación | Búsqueda y visualización de facturas | Parcial |
| Extracción | Consulta de transacciones RIPS | Implementado |
| Extracción | Consulta de medicamentos | Implementado |
| Extracción | Consulta de insumos | Implementado |
| Extracción | Consulta de consultas | Implementado |
| Extracción | Consulta de procedimientos | Implementado |
| Extracción | Interfaz gráfica de generación de RIPS | Pendiente |
| Procesamiento | Consolidación de las cuatro categorías | Parcial |
| Procesamiento | Extracción sin homologación | Parcial |
| Validación | Validación y corrección de contratos | Implementado |
| Homologación | Medicamentos mediante CUM e IUM | Implementado |
| Homologación | Insumos | Pendiente |
| Homologación | Consultas y procedimientos | Pendiente |
| Agrupación | Clasificación actuarial de tecnologías | Pendiente |
| Frecuencias | Cálculo de frecuencias por tecnología y grupo | Pendiente |
| Costos | Cruce de costos por factura y mes | Parcial |
| Costos | Costo promedio por tecnología y grupo | Pendiente |
| Visualización | Monitor MEDCOL en Streamlit | Implementado |
| Visualización | Dashboard actuarial integrado | Pendiente |
| Exportación | Exportación genérica de DataFrames | Implementado |
| Exportación | Botón de exportación en la interfaz | Pendiente |
| Exportación | Exportación de RIPS sin homologación | Parcial |

---

# 4. Especificación funcional de acceso y conexión

## 4.1. Inicio de sesión

La aplicación tendrá una pantalla inicial de conexión a SQL Server.

El usuario deberá ingresar los datos de conexión requeridos por la configuración institucional:

- Servidor.
- Base de datos, cuando aplique.
- Usuario.
- Contraseña.
- Tipo de autenticación, cuando corresponda.

La aplicación deberá validar la conexión antes de permitir el acceso a los módulos que requieren información de SQL Server.

## 4.2. Guardado de credenciales

La aplicación permitirá seleccionar una opción para recordar las credenciales.

El comportamiento esperado será:

1. El usuario ingresa las credenciales.
2. El sistema valida la conexión.
3. Cuando la conexión es exitosa, ofrece guardar las credenciales.
4. Las credenciales se almacenan mediante el almacén seguro del sistema operativo.
5. En el siguiente inicio de la aplicación, el sistema recupera las credenciales guardadas e intenta establecer la conexión.
6. Si la conexión falla, solicita nuevamente la información necesaria.
7. El usuario podrá cerrar la sesión y eliminar las credenciales guardadas.

Las contraseñas no deberán almacenarse en texto plano, archivos de configuración, Excel ni SQLite.

---

# 5. Especificación funcional de facturación

## 5.1. Fuentes de facturación

El sistema tendrá dos fuentes de información.

### 5.1.1. Base Montos Fijos

Archivo identificado en el repositorio:

`data/BaseMontosFijos2026.xlsx`

Columnas utilizadas:

- Nit.
- Contrato.
- Prefijo.
- Factura.
- MesdeServicio.
- ValorFacturaRadicada.

La aplicación deberá:

1. Leer únicamente las columnas requeridas.
2. Normalizar los campos de identificación.
3. Filtrar por NIT del prestador.
4. Filtrar por contrato.
5. Construir el número completo de factura concatenando Prefijo y Factura.
6. Eliminar identificadores duplicados.
7. Conservar el valor y periodo de servicio para los cruces posteriores.

### 5.1.2. SQL Server – FPR

El repositorio contiene una consulta que relaciona:

- `BoxaludBI_Comfenalco.dbo.BiPagosFPR`
- `BoxaludBI_Comfenalco.dbo.BiPagosLiquidacion`
- `Boxalud_Comfenalco.pagos.fpr_FacturaPrestador`

Relaciones:

- BiPagosFPR con BiPagosLiquidacion mediante `B.NumRadicadoBoxalud = A.fpr_Id`.
- BiPagosFPR con fpr_FacturaPrestador mediante `A.fpr_Id = C.fpr_Id`.

La consulta recupera información de identificación de facturas, prestadores, contratos, liquidaciones, valores radicados, valores aprobados, descuentos, anticipos, devoluciones, glosas, notas crédito y retenciones.

La aplicación deberá normalizar su resultado para que tenga una estructura compatible con la información obtenida desde Excel.

### 5.1.3. Selección automática de fuentes

Regla funcional propuesta:

- Hasta agosto de 2026: Base Montos Fijos.
- Desde septiembre de 2026: SQL Server.
- Periodos que incluyan ambas fuentes: extracción combinada.

La fecha de corte deberá ser configurable y validada con el área de Actuaría.

También deberá definirse qué campo determina el periodo de selección: FechaFactura, FechaRadicacion o MesdeServicio.

## 5.2. Búsqueda y visualización de facturas

El usuario podrá consultar las facturas disponibles mediante filtros como:

- Contrato.
- NIT del prestador.
- Código de prestador.
- Número de factura.
- Periodo.
- Fuente de información.

La interfaz deberá mostrar los datos relevantes de las facturas, permitir consultar su detalle y seleccionar las facturas que participarán en el proceso de extracción.

## 5.3. Visualización de transacciones

Tabla:

`dbo.RIPSArchivoTransaccion`

Condición existente:

`rat_Activo = 'Activo'`

Campos recuperados:

| Campo original | Campo normalizado |
|---|---|
| rat_Id | CodigoTransaccion |
| rat_NumeroFactura | Factura |
| rat_NumeroContrato | Contrato |
| rat_NumeroIdentificacion | NitPrestador |
| rat_CodigoPrestador | CodigoPrestador |
| FechaCargueRips | FechaRips |
| FechaRadicacionFactura | FechaRadicacion |

La consulta utilizará las facturas identificadas en la etapa de facturación.

La interfaz permitirá consultar las transacciones asociadas a las facturas y revisar su identificación antes de extraer los detalles RIPS.

---

## 5.4. Reglas obligatorias de elegibilidad y deduplicación

Para las facturas provenientes de `BiPagosFPR`, únicamente se tendrán en
cuenta los registros con estos estados:

- **Finalizada:** la factura se incluye.
- **Para respuesta prestador:** la factura se incluye solamente cuando
  `ValorPagar` no sea nulo y su valor numérico sea diferente de cero.

Los demás estados se descartan. Para el estado Para respuesta prestador también
se descartan los valores nulos, cero o que no puedan convertirse a un número.

Antes de presentar facturas de SQL Server, el sistema debe verificar que no
exista la misma factura en Base Montos Fijos. La comparación usa la clave
natural normalizada formada por NIT, contrato y número completo de factura
(`Prefijo + Factura`). Se consideran todas las filas con esa clave completa,
incluso cuando `MesdeServicio` esté vacío o no sea válido; esas filas no se
presentan en resultados históricos, pero sí se utilizan para bloquear
duplicados. La regla debe aplicarse en el conteo, paginación y detalle, no
únicamente en la primera página.

Si el archivo de costos fijos falta o no puede leerse, el backend debe fallar
de forma segura: omite tanto las facturas históricas como las FPR, devuelve cero
resultados y adjunta una advertencia. El detalle de facturas FPR también queda
bloqueado hasta que pueda comprobarse la deduplicación contra el Excel.

## 5.5. Criterios de búsqueda y selección de transacciones

La búsqueda de transacciones parte de las facturas seleccionadas y conserva la
condición `rat_Activo = 'Activo'`. Además, debe aplicar únicamente los
parámetros que el analista utilizó para buscar facturas:

- Si se escribió NIT, comparar con `rat_NumeroIdentificacion`.
- Si se escribió contrato, comparar con `rat_NumeroContrato`.
- Si se escribió número o fragmento de factura, comparar con
  `rat_NumeroFactura`.
- Si se utilizaron varios criterios, deben cumplirse todos.
- Los criterios que quedaron vacíos no deben agregarse al filtro.

La interfaz preseleccionará las transacciones que cumplan las reglas en todas
las páginas. La preparación de extracción volverá a comprobar tanto la
actividad como la relación de cada transacción con las facturas y los filtros
originales.

## 5.6. Comportamiento de la interfaz

Los filtros de contrato y NIT serán campos de texto libre, no listas desplegables
nativas. Las sugerencias del catálogo se mostrarán inmediatamente debajo del
campo y se actualizarán conforme se escribe. El analista podrá conservar el
texto sin elegir una sugerencia.

Las sugerencias admitirán teclado: flechas arriba/abajo para recorrer opciones,
Enter para elegir la sugerencia activa y Escape para cerrar la lista. El envío
del formulario seguirá funcionando con texto libre.

**Seleccionar todas las facturas** recuperará las páginas del conjunto completo
de la búsqueda y seleccionará todos sus resultados, no solo los de la página
visible. La tabla de transacciones ofrecerá **Seleccionar todas las
transacciones** y **Quitar selección global** para operar sobre todas las
coincidencias ya consultadas, aunque se esté visualizando otra página. Las
selecciones individuales y globales se conservarán al paginar.

Las transacciones coincidentes se preseleccionarán automáticamente en el
conjunto completo consultado. El analista podrá desmarcar filas individuales o
quitar la selección global.

La aplicación admitirá hasta 1.000 facturas y 1.000 transacciones por
preparación; si se supera el límite, se informará al usuario y no se aceptará
una selección parcial como si fuera total.

La aplicación ofrecerá tema claro y oscuro para todas las pantallas y recordará
la preferencia local del analista.

# 6. Especificación funcional de extracción RIPS

## 6.1. Categorías de tecnologías

Se conservarán las cuatro tablas identificadas en `backend/detalleFacturas.py`.

| Tabla | Categoría | Identificador |
|---|---|---|
| RIPSArchivoConsulta | Consulta | rao_Id |
| RIPSArchivoProcedimiento | Procedimiento | rar_Id |
| RIPSArchivoMedicamento | Medicamento | ram_Id |
| RIPSArchivoOtroServicio | Insumo | ras_Id |

La relación entre las tablas se realiza mediante `rat_Id`, asociado al identificador de transacción.

## 6.2. Estructura normalizada

El resultado normalizado deberá contemplar:

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

La categoría deberá identificarse de manera independiente del subtipo de tecnología.

Para consultas y procedimientos, la descripción no está siendo recuperada actualmente en la consulta del repositorio. Se deberá definir su fuente antes de ampliar el modelo.

## 6.3. Extracción sin homologación

La primera versión funcional deberá generar los cuatro conjuntos de datos sin aplicar homologaciones.

Esto implica:

1. Recuperar la información original de las tablas RIPS.
2. Asociar los registros a su transacción.
3. Asociar las transacciones a las facturas correspondientes.
4. Normalizar nombres y estructuras de columnas.
5. Conservar los códigos originales.
6. Conservar las descripciones originales disponibles.
7. Consolidar cada categoría.
8. Informar registros procesados y errores.
9. Permitir visualizar los resultados.
10. Permitir exportarlos.

La extracción sin homologación será el resultado base sobre el cual se construirán posteriormente las etapas de homologación y agrupación actuarial.

La homologación no deberá ejecutarse de forma automática en este proceso.

---

# 7. Validación de contratos

El proceso existente identifica facturas cuyo contrato no pertenece a los contratos seleccionados.

Posteriormente consulta:

`dbo.BiPagosFPR`

Para identificar el contrato correspondiente.

Comportamiento:

1. Identificar facturas con contrato diferente.
2. Consultar el contrato correspondiente en BiPagosFPR.
3. Corregir el contrato cuando pertenezca a los contratos válidos.
4. Descartar facturas que no puedan validarse.
5. Informar las cantidades corregidas y descartadas.

La plataforma deberá conservar este comportamiento y registrar los motivos de corrección y descarte para facilitar la auditoría.

---

# 8. Exportación de RIPS

La primera versión deberá incorporar un botón de exportación disponible una vez que la extracción finalice correctamente.

El archivo deberá conservar los datos originales sin homologación.

Como estructura inicial propuesta, el archivo Excel podrá incluir:

- Hoja de Facturas.
- Hoja de Transacciones.
- Hoja de Consultas.
- Hoja de Procedimientos.
- Hoja de Medicamentos.
- Hoja de Insumos.
- Hoja de Resumen de ejecución.

La estructura definitiva, los nombres de las hojas y la granularidad de exportación deberán validarse con los usuarios del proceso.

La exportación deberá conservar, cuando aplique:

- Número de factura.
- Contrato.
- Prestador.
- Identificador de transacción.
- Código de usuario.
- Código original de tecnología.
- Descripción original.
- Fecha de servicio.
- Valor.
- Cantidad o unidades.
- Categoría de RIPS.

El sistema deberá informar la ubicación del archivo generado y permitir acceder a él desde la interfaz.

---

# 9. Homologación y agrupación actuarial

La homologación se implementará después de estabilizar la extracción y exportación sin homologación.

## 9.1. Homologación de medicamentos existente

Fuente:

`data/FOR_GIF_021_VADEMÉCUM_INSTITUCIONAL.xlsx`

Hoja:

`Vademécum`

Columnas utilizadas:

- CODIGO GENERICO.
- DESCRIPCION GENERICA.
- IUM.
- CUM INVIMA.

Orden de homologación:

1. Buscar CodigoTecnologia en CUM INVIMA.
2. Recuperar código y descripción genérica.
3. Si no existe resultado, buscar mediante IUM.
4. Asignar CodigoGenerico.
5. Actualizar Descripcion con la descripción genérica.
6. Mantener registros sin homologación para revisión.

La plataforma deberá incorporar posteriormente las fuentes de homologación de insumos, consultas y procedimientos.

## 9.2. Agrupación actuarial

Se desarrollará un módulo que permita clasificar las tecnologías de acuerdo con las reglas y agrupaciones definidas por el área de Actuaría.

Las reglas de agrupación deberán estar separadas de la interfaz y ser administrables desde el backend.

## 9.3. Frecuencias y costos promedio

En una fase posterior, el sistema deberá calcular:

- Frecuencias por tecnología.
- Frecuencias por grupo.
- Costo total por tecnología.
- Costo total por grupo.
- Costo promedio por tecnología.
- Costo promedio por grupo.
- Evolución mensual de los indicadores.

La definición exacta de frecuencia, unidades y denominadores de costo promedio deberá validarse con la metodología actuarial correspondiente.

---

# 10. Monitor MEDCOL y dashboard actuarial

## 10.1. Estado actual

El Monitor MEDCOL es un dashboard independiente desarrollado con Streamlit y Plotly.

Actualmente permite analizar el comportamiento del costo de las facturas por mes y cuenta con funcionalidades como:

- Filtros por contrato.
- Filtros por mes de servicio.
- Indicador de costo total.
- Cantidad de facturas.
- Promedio por factura.
- Cantidad de contratos.
- Gráfico de costo mensual.
- Heatmap de contrato y mes.
- Gráfico de costo por factura.
- Detalle de facturas.
- Variación mensual.
- Selección interactiva de gráficos.

## 10.2. Evolución futura

El Monitor MEDCOL no forma parte del alcance inicial del Sprint 1.

Se conservará como referencia funcional para una etapa posterior, en la que sus capacidades serán trasladadas e integradas a un dashboard actuarial más completo.

El dashboard futuro deberá permitir visualizar conjuntamente:

1. Costo de cada factura por mes.
2. Frecuencias o cantidades por tecnología.
3. Frecuencias o cantidades por grupo.
4. Costo promedio por tecnología.
5. Costo promedio por grupo.
6. Evolución mensual de costos y frecuencias.

Esta integración se realizará después de completar las etapas principales del proceso actuarial: extracción, homologación, agrupación y cálculo de frecuencias.

La ruta absoluta de Windows utilizada por el Monitor MEDCOL deberá eliminarse durante su futura migración.

---

# 11. Reglas generales de negocio

1. Una factura debe conservar su relación con el prestador y el contrato.
2. Las transacciones deberán estar activas para participar en la extracción.
3. Los consumos RIPS deberán asociarse mediante CodigoTransaccion.
4. La categoría de tecnología deberá conservarse durante todas las transformaciones.
5. Los registros descartados deberán poder contabilizarse.
6. La extracción inicial no deberá modificar los códigos originales.
7. Los registros sin homologación deberán permanecer disponibles.
8. Los filtros de visualización no deberán modificar los datos originales.
9. Los resultados exportados deberán conservar los identificadores necesarios para su trazabilidad.
10. Las fechas y parámetros de extracción deberán quedar registrados.
11. Las credenciales no deberán almacenarse en texto plano.
12. Los módulos de visualización no deberán ejecutar directamente consultas SQL.

---

# 12. Requerimientos no funcionales

- Compatibilidad inicial con Windows.
- Ejecución local independiente por analista.
- Arquitectura preparada para despliegue web.
- Procesamiento eficiente de grandes volúmenes de información.
- Conexiones SQL administradas centralmente desde el backend.
- Credenciales protegidas mediante mecanismos seguros del sistema operativo.
- Consultas SQL parametrizadas.
- Manejo controlado de errores.
- Registro de ejecuciones.
- Separación entre interfaz y lógica de negocio.
- Posibilidad de incorporar nuevos módulos sin modificar los existentes.
- Protección de información personal y datos sensibles de salud.
- Exportaciones trazables.
- Interfaz adaptable a diferentes resoluciones de pantalla.

---

# 13. Alcance de la primera implementación

La primera implementación de la nueva aplicación se divide en tres entregables.

## Entregable 1. Inicio de sesión y guardado de credenciales

- Pantalla de inicio de sesión.
- Ingreso de credenciales SQL Server.
- Validación de conexión.
- Opción para recordar credenciales.
- Almacenamiento seguro.
- Recuperación automática de credenciales al iniciar.
- Gestión de cierre de sesión y eliminación de credenciales.

## Entregable 2. Interfaz de generación de RIPS y consulta de facturas y transacciones

- Interfaz principal de la aplicación.
- Selección de contratos y prestadores.
- Selección de periodos.
- Búsqueda de facturas.
- Visualización del detalle de facturas.
- Consulta de transacciones asociadas.
- Visualización de información de transacciones.
- Selección de facturas y transacciones que participarán en la extracción.
- Inicio y seguimiento de la generación de RIPS.

## Entregable 3. Versión final de extracción y exportación de RIPS sin homologación

- Integración del proceso de extracción de las cuatro categorías.
- Validación de contratos.
- Consolidación de resultados.
- Conservación de códigos y descripciones originales.
- Visualización de resultados.
- Control de registros procesados y errores.
- Botón de exportación.
- Generación de Excel sin homologación.

## Exclusiones de esta primera implementación

No forman parte de estos tres entregables:

- Homologación ampliada.
- Agrupación actuarial.
- Frecuencias por tecnología y grupo.
- Costos promedio por tecnología y grupo.
- Migración del Monitor MEDCOL.
- Dashboard actuarial integrado.
- Despliegue multiusuario web.

---

# 14. Indicadores de éxito

- Inicio de sesión y reconexión sin ingresar repetidamente las credenciales.
- Conexión estable con SQL Server.
- Búsqueda correcta de facturas.
- Visualización de transacciones relacionadas.
- Integridad de los cuatro conjuntos de RIPS.
- Consistencia de resultados frente al proceso existente.
- Conservación de los códigos originales sin homologación.
- Exportaciones completas y trazables.
- Reducción de tareas manuales.
- Arquitectura preparada para futuras funcionalidades actuariales.

---

# 15. Referencias del código fuente

- [main.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/main.py)
- [config.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/config.py)
- [connection.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/connection.py)
- [backend/prestadores.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/backend/prestadores.py)
- [backend/detalleFacturas.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/backend/detalleFacturas.py)
- [backend/utilidades.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/backend/utilidades.py)
- [backend/homologacion.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/backend/homologacion.py)
- [backend/monitorDeCostos.py](https://github.com/SrAlbertoG/Automatizacion_BusquedaContratos/blob/master/backend/monitorDeCostos.py)



## Comportamiento de búsqueda y paginación del Entregable 2

En la pantalla de facturas, el backend prepara el conjunto completo de resultados
cuando contiene hasta 1.000 registros. La interfaz muestra 25 filas por página,
pero el cambio de página es local y no vuelve a consultar la base de datos. La
selección global de facturas marca inmediatamente los registros ya cargados; la
consulta de transacciones ocurre después, sin retrasar la actualización visual
del checkbox.

Si la búsqueda supera 1.000 facturas o la selección produce más de 1.000
transacciones, se solicita al analista reducir los filtros. El sistema no debe
mostrar conjuntos truncados como si fueran completos. Las transacciones también
se recuperan en una única consulta de dataset y se paginan localmente.
