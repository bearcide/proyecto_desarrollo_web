<template>
  <div v-if="abierto" class="modal-backdrop">
    <div class="modal-card demo-modal" role="dialog" aria-modal="true">
      <div class="demo-icon-wrapper">
        <AppIcon name="shield" size="32" class="demo-icon" />
      </div>

      <h3 class="demo-title">Sesión de Contratación — Modo DEMO</h3>
      <span class="badge badge-warning demo-badge">COMMERCIAL_PROVIDER = DEMO</span>

      <p class="demo-text">
        El backend está configurado en modalidad de pruebas DEMO (sin pasarela bancaria real conectada).
        Tu orden ha sido registrada oficialmente en el servidor en estado <strong>PENDIENTE</strong>:
      </p>

      <div class="orden-pill">
        <span class="orden-label">Folio de Orden:</span>
        <code class="orden-code">{{ ordenId }}</code>
      </div>

      <div class="demo-rules-box">
        <div class="rule-item">
          <AppIcon name="lock" size="16" class="text-success" />
          <span>No se realizó ningún cobro bancario ni se transmitieron datos de tarjeta.</span>
        </div>
        <div class="rule-item">
          <AppIcon name="info" size="16" class="text-blue" />
          <span>
            En producción, Stripe Checkout redirige al cliente a su pasarela HTTPS cifrada.
            En DEMO, la orden queda lista para ser aprobada por el operador o propietario.
          </span>
        </div>
      </div>

      <div class="demo-actions">
        <button
          type="button"
          class="btn btn-primary btn-block"
          @click="irAResultado"
        >
          <span>Ir a Verificar Estado de la Orden</span>
          <AppIcon name="arrow-right" size="16" />
        </button>

      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import AppIcon from '../../../../components/AppIcon.vue';

const props = defineProps({
  abierto: {
    type: Boolean,
    default: false,
  },
  ordenId: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['cerrar']);
const router = useRouter();

function irAResultado() {
  emit('cerrar');
  router.push({
    path: '/admin/comercial/checkout/resultado',
    query: { orden_id: props.ordenId },
  });
}

</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-card.demo-modal {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 100%;
  padding: 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.demo-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--warning-bg);
  border: 2px solid var(--warning-border);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.demo-icon {
  color: var(--warning-text);
}

.demo-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--text-main);
  margin: 0 0 0.5rem;
}

.demo-badge {
  font-family: monospace;
  font-size: 0.75rem;
  margin-bottom: 1rem;
}

.demo-text {
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.45;
  margin: 0 0 1.25rem;
}

.orden-pill {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.65rem 1rem;
  width: 100%;
  margin-bottom: 1.25rem;
}

.orden-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  color: var(--text-light);
  font-weight: 700;
  letter-spacing: 0.05em;
}

.orden-code {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary);
  word-break: break-all;
}

.demo-rules-box {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  text-align: left;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
  padding: 0.85rem;
  margin-bottom: 1.5rem;
  width: 100%;
  font-size: 0.78rem;
  color: var(--text-muted);
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  line-height: 1.35;
}

.demo-actions {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  width: 100%;
}

.sim-btn {
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}
</style>
