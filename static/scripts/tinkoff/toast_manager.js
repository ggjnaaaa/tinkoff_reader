class ToastManager {
    constructor() {
        this.container = document.getElementById("toast-container");
    }

    showToast(message, type = "notification", duration = 5000) {
        if (!message || !message.trim()) return;

        // Создаём тост
        const toast = document.createElement("div");
        toast.classList.add("toast", type);
        toast.textContent = message;
        this.container.appendChild(toast);

        // Показываем тост
        setTimeout(() => {
            toast.classList.add("show");
        }, 10);

        // Автоматическое удаление
        setTimeout(() => {
            this.hideToast(toast);
        }, duration);
    }

    hideToast(toast) {
        toast.classList.remove("show");

        setTimeout(() => {
            toast.remove();
        }, 400);
    }
}