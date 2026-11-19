<template>
  <div v-if="abierto" class="modal-backdrop" @click.self="cerrar">
    <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-facturacion-title">
      <div class="modal-header">
        <div>
          <h3 id="modal-facturacion-title" class="modal-title">Solicitar Factura Fiscal (CFDI)</h3>
          <p class="modal-subtitle">
            Orden: <strong>#{{ ordenId?.substring(0, 8) }}…</strong> — Importe: {{ importe }} MXN
          </p>
        </div>
        <button type="button" class="btn-close" aria-label="Cerrar" @click="cerrar">
          <AppIcon name="x" size="20" />
        </button>
      </div>

      <form @submit.prevent="guardar" class="modal-form">
        <!-- RFC -->
        <div class="form-group">
          <label for="rfc" class="form-label">RFC (Registro Federal de Contribuyentes) *</label>
          <input
            id="rfc"
            v-model="formulario.rfc"
            type="text"
            maxlength="13"
            class="input form-control text-uppercase"
            :class="{ 'input-invalid': errores.rfc }"
            placeholder="Ej. IME190101ABC"
            required
          />
          <span v-if="errores.rfc" class="input-error-msg">{{ errores.rfc }}</span>
        </div>

        <!-- Razón Social -->
        <div class="form-group">
          <label for="razon_social" class="form-label">Razón Social o Denominación de la Institución *</label>
          <input
            id="razon_social"
            v-model="formulario.razon_social"
            type="text"
            class="input form-control"
            :class="{ 'input-invalid': errores.razon_social }"
            placeholder="Ej. Instituto Modelo Educativo S.C."
            required
          />
          <span v-if="errores.razon_social" class="input-error-msg">{{ errores.razon_social }}</span>
        </div>

        <div class="form-row-2">
          <!-- Régimen Fiscal -->
          <div class="form-group">
            <label for="regimen" class="form-label">Régimen Fiscal (SAT) *</label>
            <select
              id="regimen"
              v-model="formulario.regimen"
              class="input form-control"
              :class="{ 'input-invalid': errores.regimen }"
              required
            >
              <option value="" disabled>Seleccione régimen…</option>
              <option value="601">601 - General de Ley Personas Morales</option>
              <option value="603">603 - Personas Morales con Fines no Lucrativos</option>
              <option value="612">612 - Personas Físicas con Actividades Empresariales</option>
              <option value="626">626 - Régimen Simplificado de Confianza (RESICO)</option>
            </select>
            <span v-if="errores.regimen" class="input-error-msg">{{ errores.regimen }}</span>
          </div>

          <!-- Código Postal Fiscal -->
          <div class="form-group">
            <label for="codigo_postal" class="form-label">Código Postal Fiscal *</label>
            <input
              id="codigo_postal"
              v-model="formulario.codigo_postal"
              type="text"
              maxlength="5"
              class="input form-control"
              :class="{ 'input-invalid': errores.codigo_postal }"
              placeholder="Ej. 06700"
              required
            />
            <span v-if="errores.codigo_postal" class="input-error-msg">{{ errores.codigo_postal }}</span>
          </div>
        </div>

        <!-- Uso de CFDI -->
        <div class="form-group">
          <label for="uso_cfdi" class="form-label">Uso del CFDI *</label>
          <select
            id="uso_cfdi"
            v-model="formulario.uso_cfdi"
            class="input form-control"
            :class="{ 'input-invalid': errores.uso_cfdi }"
            required
          >
            <option value="" disabled>Seleccione uso de CFDI…</option>
            <option value="G03">G03 - Gastos en general</option>
            <option value="I08">I08 - Otra maquinaria y equipo (Software)</option>
            <option value="P01">P01 - Por definir</option>
            <option value="CP01">CP01 - Pagos</option>
          </select>
          <span v-if="errores.uso_cfdi" class="input-error-msg">{{ errores.uso_cfdi }}</span>
        </div>

        <div class="sat-notice">
          <AppIcon name="info" size="16" />
          <span>
            De acuerdo con la regulación fiscal vigente en México (CFDI 4.0), los datos deben coincidir
            exactamente con la Constancia de Situación Fiscal de la institución.
          </span>
        </div>

        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" :disabled="enviando" @click="cerrar">
            Cancelar
          </button>
          <button type="submit" class="btn btn-primary" :disabled="enviando">
            <span v-if="enviando" class="spinner spinner-white"></span>
            <span v-else>Emitir Solicitud</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue';
import AppIcon from '../../../../components/AppIcon.vue';
import { validarDatosFacturacion } from '../domain/comercialCalculos';

const props = defineProps({
  abierto: {
    type: Boolean,
    default: false,
  },
  ordenId: {
    type: String,
    default: '',
  },
  importe: {
    type: [String, Number],
    default: '0.00',
  },
  enviando: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['cerrar', 'solicitar']);

const formulario = reactive({
  rfc: '',
  razon_social: '',
  regimen: '603',
  codigo_postal: '',
  uso_cfdi: 'G03',
});

const errores = ref({});

watch(
  () => props.abierto,
  (abierto) => {
    if (abierto) {
      errores.value = {};
    }
  },
);

function cerrar() {
  emit('cerrar');
}

function guardar() {
  const resultado = validarDatosFacturacion(formulario);
  if (!resultado.valido) {
    errores.value = resultado.errores;
    return;
  }
  errores.value = {};
  emit('solicitar', {
    orden: props.ordenId,
    rfc: resultado.rfcFormateado,
    razon_social: formulario.razon_social,
    regimen: formulario.regimen,
    codigo_postal: formulario.codigo_postal,
    uso_cfdi: formulario.uso_cfdi,
  });
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 540px;
  width: 100%;
  padding: 1.75rem;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.75rem;
}

.modal-title {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0;
}

.modal-subtitle {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0.25rem 0 0;
}

.btn-close {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-light);
  padding: 0.25rem;
  border-radius: var(--radius-sm);
}

.btn-close:hover {
  color: var(--text-main);
  background: var(--bg-surface);
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.form-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
}

.form-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 600px) {
  .form-row-2 {
    grid-template-columns: 1fr;
  }
}

.input-invalid {
  border-color: var(--danger) !important;
  box-shadow: 0 0 0 1px var(--danger);
}

.input-error-msg {
  font-size: 0.75rem;
  color: var(--danger);
  font-weight: 600;
}

.sat-notice {
  display: flex;
  gap: 0.5rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  line-height: 1.4;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
</style>
