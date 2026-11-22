import { createApp } from "vue";
import "./styles.css";

const normalizedPath = window.location.pathname.replace(/\/+$/, "");
const isAdmin = normalizedPath.endsWith("/admin");

const component = isAdmin
  ? (await import("./AdminPanel.vue")).default
  : (await import("./App.vue")).default;

createApp(component).mount("#app");
