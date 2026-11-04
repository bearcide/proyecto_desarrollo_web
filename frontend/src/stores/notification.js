import { defineStore } from 'pinia';

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    toasts: [],
  }),
  actions: {
    add({ message, type = 'info', timeout = 4000 }) {
      const id = Date.now() + Math.random().toString(36).substring(2, 9);
      this.toasts.push({ id, message, type });
      if (timeout > 0) {
        setTimeout(() => {
          this.remove(id);
        }, timeout);
      }
    },
    success(message, timeout) {
      this.add({ message, type: 'success', timeout });
    },
    error(message, timeout = 6000) {
      this.add({ message, type: 'danger', timeout });
    },
    warning(message, timeout) {
      this.add({ message, type: 'warning', timeout });
    },
    info(message, timeout) {
      this.add({ message, type: 'info', timeout });
    },
    remove(id) {
      this.toasts = this.toasts.filter((t) => t.id !== id);
    },
  },
});
