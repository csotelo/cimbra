import { ref, onUnmounted } from "vue";
import api from "@/api/index";

const toasts = ref([]);
const unreadCount = ref(0);
const notifications = ref([]);
let socket = null;
let toastIdCounter = 0;

function addToast(notification) {
    const id = ++toastIdCounter;
    toasts.value.unshift({ ...notification, _toastId: id });
    setTimeout(() => removeToast(id), 6000);
}

function removeToast(id) {
    toasts.value = toasts.value.filter((t) => t._toastId !== id);
}

async function loadUnreadCount() {
    try {
        const res = await api.get("/api/notifications/unread/");
        unreadCount.value = res.data.count;
    } catch { /* silent */ }
}

async function loadNotifications() {
    try {
        const res = await api.get("/api/notifications/");
        notifications.value = res.data;
        unreadCount.value = res.data.filter((n) => !n.is_read).length;
    } catch { /* silent */ }
}

async function markAllRead() {
    try {
        await api.post("/api/notifications/read-all/");
        notifications.value = notifications.value.map((n) => ({ ...n, is_read: true }));
        unreadCount.value = 0;
    } catch { /* silent */ }
}

function connectWebSocket(userId) {
    if (socket) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const host = `${proto}://${window.location.hostname}:8000`;
    socket = new WebSocket(`${host}/ws/notifications/`);

    socket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        notifications.value.unshift({ ...data, is_read: false });
        unreadCount.value++;
        addToast(data);
    };

    socket.onclose = () => {
        socket = null;
        setTimeout(() => connectWebSocket(userId), 3000);
    };
}

function disconnect() {
    if (socket) {
        socket.onclose = null;
        socket.close();
        socket = null;
    }
}

export function useNotifications() {
    return {
        toasts,
        unreadCount,
        notifications,
        addToast,
        removeToast,
        loadUnreadCount,
        loadNotifications,
        markAllRead,
        connectWebSocket,
        disconnect,
    };
}
