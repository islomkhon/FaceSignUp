<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import "./admin.css";

const APP_BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
const user = ref(null);
const users = ref([]);
const loginName = ref("admin");
const loginPassword = ref("");
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const busy = ref(false);
const error = ref("");
const search = ref("");
const failedPhotos = ref(new Set());
const photoViewer = ref(null);
const photoCloseButton = ref(null);

const needsPasswordChange = computed(() => Boolean(user.value?.mustChangePassword));
const filteredUsers = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return users.value;
  return users.value.filter((item) => item.name.toLowerCase().includes(query));
});
const adminCount = computed(
  () => users.value.filter((item) => item.role === "admin").length
);

function appPath(path) {
  return `${APP_BASE}${path}`;
}

async function api(path, options = {}) {
  const response = await fetch(appPath(path), {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "Request failed.");
  }
  return data;
}

async function loadSession() {
  try {
    const data = await api("/api/auth/me");
    if (data.user.role !== "admin") {
      error.value = "This account does not have administrator access.";
      return;
    }
    user.value = data.user;
    if (!needsPasswordChange.value) await loadUsers();
  } catch {
    user.value = null;
  }
}

async function login() {
  clearError();
  busy.value = true;
  try {
    const data = await api("/api/auth/name-login", {
      method: "POST",
      body: JSON.stringify({
        display_name: loginName.value,
        password: loginPassword.value
      })
    });
    if (data.user.role !== "admin") {
      await api("/api/auth/logout", { method: "POST", body: "{}" }).catch(() => {});
      throw new Error("This account does not have administrator access.");
    }
    user.value = data.user;
    loginPassword.value = "";
    if (!needsPasswordChange.value) await loadUsers();
  } catch (loginError) {
    error.value = loginError.message;
  } finally {
    busy.value = false;
  }
}

async function changePassword() {
  clearError();
  if (newPassword.value !== confirmPassword.value) {
    error.value = "New passwords do not match.";
    return;
  }
  busy.value = true;
  try {
    const data = await api("/api/admin/password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword.value,
        new_password: newPassword.value
      })
    });
    user.value = data.user;
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
    await loadUsers();
  } catch (passwordError) {
    error.value = passwordError.message;
  } finally {
    busy.value = false;
  }
}

async function loadUsers() {
  const data = await api("/api/admin/users");
  users.value = data.users;
  failedPhotos.value.clear();
}

async function updateRole(item, event) {
  clearError();
  const role = event.target.value;
  try {
    await api(`/api/admin/users/${encodeURIComponent(item.id)}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role })
    });
    await loadUsers();
  } catch (roleError) {
    error.value = roleError.message;
    await loadUsers().catch(() => {});
  }
}

async function deleteUser(item) {
  if (!window.confirm(`Permanently delete ${item.name} and their face data?`)) return;
  clearError();
  try {
    await api(`/api/admin/users/${encodeURIComponent(item.id)}`, {
      method: "DELETE"
    });
    await loadUsers();
  } catch (deleteError) {
    error.value = deleteError.message;
  }
}

async function signOut() {
  closePhoto();
  await api("/api/auth/logout", { method: "POST", body: "{}" }).catch(() => {});
  user.value = null;
  users.value = [];
}

function clearError() {
  error.value = "";
}

function photoUrl(userId) {
  return appPath(`/api/admin/users/${encodeURIComponent(userId)}/photo`);
}

function markPhotoFailed(userId) {
  failedPhotos.value.add(userId);
}

function openPhoto(item) {
  if (!item.hasPhoto || failedPhotos.value.has(item.id)) return;
  photoViewer.value = item;
  document.body.classList.add("admin-photo-open");
  nextTick(() => photoCloseButton.value?.focus());
}

function closePhoto() {
  photoViewer.value = null;
  document.body.classList.remove("admin-photo-open");
}

function handlePhotoError(item) {
  markPhotoFailed(item.id);
  closePhoto();
}

function handleKeydown(event) {
  if (event.key === "Escape" && photoViewer.value) closePhoto();
}

onMounted(() => {
  loadSession();
  window.addEventListener("keydown", handleKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeydown);
  document.body.classList.remove("admin-photo-open");
});
</script>

<template>
  <main class="admin-shell">
    <header class="admin-topbar">
      <a class="admin-brand" :href="appPath('/faceScanner')">
        <span>F</span>
        <strong>FaceSignUp</strong>
        <em>Admin</em>
      </a>
      <button
        v-if="user"
        class="admin-secondary"
        type="button"
        @click="signOut"
      >
        Sign out
      </button>
    </header>

    <section v-if="!user" class="admin-login-card">
      <p class="admin-eyebrow">Administration</p>
      <h1>Sign in to manage users</h1>
      <p>Use the administrator credentials provided by the system operator.</p>
      <form @submit.prevent="login">
        <label for="admin-name">Administrator name</label>
        <input id="admin-name" v-model="loginName" autocomplete="username" required />
        <label for="admin-password">Password</label>
        <input
          id="admin-password"
          v-model="loginPassword"
          type="password"
          autocomplete="current-password"
          required
        />
        <p v-if="error" class="admin-error">{{ error }}</p>
        <button class="admin-primary" :disabled="busy" type="submit">
          {{ busy ? "Signing in…" : "Sign in" }}
        </button>
      </form>
    </section>

    <section v-else-if="needsPasswordChange" class="admin-login-card">
      <p class="admin-eyebrow">Security update</p>
      <h1>Change the default password</h1>
      <p>This administrator is still using the known initial password.</p>
      <form @submit.prevent="changePassword">
        <label for="current-password">Current password</label>
        <input
          id="current-password"
          v-model="currentPassword"
          type="password"
          autocomplete="current-password"
          required
        />
        <label for="new-password">New password</label>
        <input
          id="new-password"
          v-model="newPassword"
          type="password"
          autocomplete="new-password"
          minlength="10"
          required
        />
        <label for="confirm-password">Confirm new password</label>
        <input
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          minlength="10"
          required
        />
        <p v-if="error" class="admin-error">{{ error }}</p>
        <button class="admin-primary" :disabled="busy" type="submit">
          {{ busy ? "Updating…" : "Update password" }}
        </button>
      </form>
    </section>

    <section v-else class="admin-dashboard">
      <div class="admin-heading">
        <div>
          <p class="admin-eyebrow">User management</p>
          <h1>Accounts and roles</h1>
        </div>
        <div class="admin-stats">
          <span><strong>{{ users.length }}</strong> users</span>
          <span><strong>{{ adminCount }}</strong> admins</span>
        </div>
      </div>

      <div class="admin-toolbar">
        <input
          v-model="search"
          type="search"
          placeholder="Search by name"
          aria-label="Search users"
        />
        <button class="admin-secondary" type="button" @click="loadUsers">
          Refresh
        </button>
      </div>

      <p v-if="error" class="admin-error">{{ error }}</p>

      <div class="admin-table">
        <div class="admin-table-head">
          <span>User</span>
          <span>Role</span>
          <span>Face</span>
          <span>Created</span>
          <span></span>
        </div>
        <div v-for="item in filteredUsers" :key="item.id" class="admin-row">
          <div class="admin-user">
            <button
              v-if="item.hasPhoto && !failedPhotos.has(item.id)"
              class="admin-avatar-button"
              type="button"
              :aria-label="`View ${item.name}'s photo`"
              @click="openPhoto(item)"
            >
              <img
                class="admin-avatar"
                :src="photoUrl(item.id)"
                :alt="`${item.name} profile photo`"
                width="46"
                height="46"
                loading="lazy"
                decoding="async"
                @error="markPhotoFailed(item.id)"
              />
            </button>
            <span v-else class="admin-avatar admin-avatar-fallback">
              {{ item.name.charAt(0).toUpperCase() }}
            </span>
            <div>
              <strong>{{ item.name }}</strong>
              <small v-if="item.mustChangePassword">Password change required</small>
              <button
                v-if="item.hasPhoto && !failedPhotos.has(item.id)"
                class="admin-photo-link"
                type="button"
                @click="openPhoto(item)"
              >
                View photo
              </button>
            </div>
          </div>
          <select
            :value="item.role"
            :disabled="item.id === user.id"
            :aria-label="`Role for ${item.name}`"
            @change="updateRole(item, $event)"
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
          <span class="admin-status" :class="{ enrolled: item.hasFace }">
            {{ item.hasFace ? "Enrolled" : "Not enrolled" }}
          </span>
          <time>{{ new Date(item.createdAt).toLocaleDateString() }}</time>
          <button
            class="admin-delete"
            type="button"
            :disabled="item.id === user.id"
            @click="deleteUser(item)"
          >
            Delete
          </button>
        </div>
      </div>
    </section>
  </main>

  <Teleport to="body">
    <div
      v-if="photoViewer"
      class="admin-photo-backdrop"
      @click.self="closePhoto"
    >
      <section
        class="admin-photo-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-photo-title"
      >
        <header class="admin-photo-header">
          <div>
            <p class="admin-eyebrow">User photo</p>
            <h2 id="admin-photo-title">{{ photoViewer.name }}</h2>
          </div>
          <button
            ref="photoCloseButton"
            class="admin-photo-close"
            type="button"
            aria-label="Close photo"
            @click="closePhoto"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>
        <div class="admin-photo-frame">
          <img
            :src="photoUrl(photoViewer.id)"
            :alt="`${photoViewer.name} profile photo`"
            decoding="async"
            @error="handlePhotoError(photoViewer)"
          />
        </div>
        <p class="admin-photo-hint">Press Escape or click outside the photo to close.</p>
      </section>
    </div>
  </Teleport>
</template>
