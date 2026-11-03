# Archivos de entrada locales

Esta carpeta está reservada para archivos operativos que no deben versionarse
en Git, por contener información de facturación y datos institucionales.

## Base Montos Fijos

Para consultar periodos anteriores a septiembre de 2026, ubica el archivo:

`BaseMontosFijos2026.xlsx`

en esta carpeta. El backend lee la primera hoja y requiere estas columnas:

- `Nit`
- `Contrato`
- `Prefijo`
- `Factura`
- `MesdeServicio`
- `ValorFacturaRadicada`

No incluyas este Excel en commits ni solicitudes de extracción. Cada instalación
debe recibir el archivo mediante el canal institucional autorizado.

Si el archivo se encuentra en otra ubicación, configura la variable de entorno
`ACTUARIA_FIXED_COSTS_FILE` con la ruta absoluta del archivo.

## Campo de fecha para facturación FPR

El corte por defecto utiliza `FechaFactura` para seleccionar registros desde
el 1 de septiembre de 2026. La alternativa `FechaRadicacion` también está
habilitada:

- `ACTUARIA_FPR_PERIOD_FIELD=FechaFactura`
- `ACTUARIA_FPR_PERIOD_FIELD=FechaRadicacion`

El área de Actuaría debe confirmar cuál campo representa el periodo funcional
antes de liberar la aplicación a los analistas.
