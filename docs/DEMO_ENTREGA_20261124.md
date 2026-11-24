# Demostración de InscripcionMadeEasy V2 · 24 de noviembre de 2026

La demostración usa SQLite y el proveedor DEMO de Django. Cada aprobación queda en la base de demostración, junto con su orden, transacción, suscripción y licencia. La configuración de la demo deshabilita Stripe.

## Iniciar desde un checkout de la rama de entrega

Desde la raíz del repositorio usa un nombre de base nuevo con el prefijo `demo_pagos_`. El inicializador rechaza un archivo existente.

```bash
python3 -m venv /tmp/ime-demo-20261124-venv
/tmp/ime-demo-20261124-venv/bin/python -m pip install -r backend/requirements.txt
export PAGOS_DEMO_DATABASE="$PWD/backend/demo_pagos_presentacion_$(date +%s).sqlite3"
/tmp/ime-demo-20261124-venv/bin/python backend/demo_pagos.py --database "$PAGOS_DEMO_DATABASE"
/tmp/ime-demo-20261124-venv/bin/python backend/manage.py migrate --check --settings=config.settings_pagos_demo
/tmp/ime-demo-20261124-venv/bin/python backend/manage.py runserver 127.0.0.1:18082 --noreload --settings=config.settings_pagos_demo
```

En otra terminal, también desde la raíz:

```bash
cd frontend
npm ci
VITE_API_BASE_URL=http://127.0.0.1:18082/api/v1 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Abre [la interfaz local](http://127.0.0.1:5174/). El comando de siembra muestra la contraseña exclusivamente ficticia de estas cuentas. Usa perfiles de navegador distintos para evitar que el almacenamiento de sesión se comparta entre roles.

## Guion

1. Entra como `admin_demo`. En **Mi Suscripción** verás que todavía no hay una suscripción. La API académica exige una licencia vigente.
2. Abre **Planes Comerciales** y selecciona **Horizonte DEMO** en el configurador. Elige **Mensual**, deja **1 alumno** y comprueba **102.50 MXN** en el resumen y en checkout. Acepta los términos y crea la orden. Copia el identificador mostrado y abre la consulta de estado. La orden debe figurar pendiente.
3. Entra como `propietario_demo`. En el panel comercial actualiza **Órdenes DEMO pendientes**, localiza el identificador y pulsa **Aprobar orden DEMO**. La fila desaparece de pendientes. El ingreso confirmado se muestra identificado como DEMO.
4. En la sesión de administrador vuelve a consultar la orden. Debe figurar confirmada. Comprueba la suscripción mensual y la licencia. Abre **Asignaciones**, genera y publica el horario.
5. Entra como `alumno_pagos_demo` y consulta **Mi Horario**. La sesión de `admin_otro_demo` sirve para verificar que la otra institución no puede descargar la orden.

Para verificar solo la API, repite la siembra con `--verificar` y otro nombre de archivo. Para la presentación, omite ese parámetro para conservar la base inicial sin compras.

## Límites de la entrega

- Los planteles extra y módulos adicionales quedan fuera de la cotización y se muestran como no disponibles. Los contratos empresariales requieren un contrato vigente para cotizar.
- La solicitud fiscal sigue siendo un registro. El PDF es un comprobante interno. Timbrado CFDI/PAC, ERP, reembolsos, disputas, conciliación y prorrateos siguen en la hoja de ruta.
- Los retornos de Stripe se pueden recorrer en Vue sin Stripe. La suite valida firmas, deduplicación, renovaciones y cancelación con el SDK simulado. La validación externa requiere una cuenta y un webhook de Stripe Sandbox. Tampoco se da por validada la concurrencia PostgreSQL con pruebas SQLite.
