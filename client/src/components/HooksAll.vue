<template>
  <div class="container" v-if="superuser">
    <div class="row">
      <div class="col-12">
        <h1>Slack Hooks</h1>
        <hr><br><br>
        <div>
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
          <p>Each hook posts to one Slack channel whenever an entry is given one of the hook's labels,
            either when the entry is added or when it is edited. Create the hook URL in Slack as an
            incoming webhook for the channel. Once saved, the URL cannot be viewed again, only replaced.</p>
          <p>Messages include the entry's title, author, URL and source URL.</p>
        </div>
        <br>
        <alert :message=message :type=messageType v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" @click="toggleAddHookModal">
          Add Hook
        </button>
        <table class="table table-hover mt-3" v-if="hooks.length > 0">
          <thead>
            <tr>
              <th style="min-width: 10%;" scope="col">Name</th>
              <th style="min-width: 10%;" scope="col">Labels</th>
              <th style="min-width: 10%;" scope="col">URL</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="hook in hooks" :key="hook.pk">
              <td>{{ hook.name }}</td>
              <td>
                <span v-for="label in hook.labels" :key="label.pk" class="badge bg-secondary me-1">{{ label.name }}</span>
                <span v-if="hook.labels.length === 0" class="text-muted">No labels</span>
              </td>
              <td><code>{{ hook.url_hint }}</code></td>
              <td>
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-warning btn-sm" @click="toggleEditHookModal(hook)">
                    Update
                  </button>
                  <button type="button" class="btn btn-info btn-sm" @click="testHook(hook.pk)">
                    Send test message
                  </button>
                  <button type="button" class="btn btn-danger btn-sm" @click="handleDeleteHook(hook)">
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="mt-3">
          <p>No hooks created yet.</p>
        </div>
      </div>
    </div>

    <!-- add / edit hook modal -->
    <div class="modal fade" :class="{ show: activeHookModal, 'd-block': activeHookModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ hookForm.pk ? 'Update hook' : 'Add a new hook' }}</h5>
            <button type="button" class="btn-close" aria-label="Close" @click="closeHookModal"></button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="hookName" class="form-label">Name:</label>
                <input type="text" class="form-control" maxlength="100" id="hookName" v-model="hookForm.name"
                  placeholder="e.g. #optics channel">
              </div>
              <div class="mb-3">
                <label for="hookUrl" class="form-label">Slack webhook URL:</label>
                <input type="password" class="form-control" maxlength="500" id="hookUrl" v-model="hookForm.url"
                  autocomplete="off"
                  :placeholder="hookForm.pk ? 'Leave blank to keep the current URL' : 'https://hooks.slack.com/services/...'">
              </div>
              <div class="mb-3">
                <label for="hookLabels" class="form-label">Labels (Ctrl/Cmd+click to select multiple):</label>
                <select class="form-control" id="hookLabels" v-model="hookForm.label_ids" multiple>
                  <option v-for="label in labels" :key="label.pk" :value="label.pk">{{ label.name }}</option>
                </select>
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleHookSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="closeHookModal">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeHookModal" class="modal-backdrop fade show"></div>

    <!-- delete hook confirmation modal -->
    <div v-if="deleteTarget" class="modal fade show d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirm Delete</h5>
            <button type="button" class="btn-close" aria-label="Close" @click="closeDeleteHookModal"></button>
          </div>
          <div class="modal-body">
            <p class="mb-0">Delete the hook "{{ deleteTarget.name }}"? Its channel will stop receiving notifications.
              To use it again, the URL will need to be added again.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeDeleteHookModal">Cancel</button>
            <button type="button" class="btn btn-danger" @click="confirmDeleteHook">Delete</button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="deleteTarget" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import axios from 'axios';
import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { auth } from '../firebaseConfig';
import AlertMessage from './AlertMessage.vue';

const API_URL = '/api';
// const API_URL = 'http://localhost:5001/api';

export default {
  name: 'HooksAll',
  data() {
    return {
      activeHookModal: false,
      hookForm: {
        pk: '',
        name: '',
        url: '',
        label_ids: [],
      },
      hooks: [],
      labels: [],
      deleteTarget: null,
      message: '',
      messageType: 'success',
      showMessage: false,
      superuser: false,
    };
  },
  components: {
    alert: AlertMessage,
  },
  computed: {
    username() {
      if (auth.currentUser) {
        return auth.currentUser.displayName;
      } else {
        this.logInUser()
        return '';
      }
    },
    email() {
      if (auth.currentUser) {
        return auth.currentUser.email;
      } else {
        this.logInUser()
        return '';
      }
    },
  },
  methods: {
    logInUser() {
      const provider = new GoogleAuthProvider();
      provider.addScope('https://www.googleapis.com/auth/userinfo.email');
      signInWithPopup(auth, provider)
        .then(result => {
          console.log(`${result.user.displayName} logged in.`);
        })
        .catch(err => {
          console.log(`Error during sign in: ${err.message}`);
          window.alert(`Sign in failed. Retry or check your browser logs.`);
        });
    },
    // Runs an API request with the user's token. The hooks API is admin only,
    // so a 403 means the user isn't an admin and is sent back to the main page.
    request(method, path, payload) {
      return auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          method,
          url: `${API_URL}${path}`,
          data: payload,
          headers: { Authorization: `${idToken}` },
        };
        return axios(config).catch((error) => {
          if (error.response && error.response.status === 403) {
            this.superuser = false;
            this.$router.replace('/');
          }
          throw error;
        });
      });
    },
    showResult(res, fallback) {
      this.message = res.data.message || fallback;
      this.messageType = res.data.status === 'success' ? 'success' : 'danger';
      this.showMessage = true;
    },
    showError(message) {
      this.message = message;
      this.messageType = 'danger';
      this.showMessage = true;
    },
    getHooks() {
      this.request('get', '/hooks')
        .then((res) => {
          this.hooks = res.data.hooks || [];
          this.superuser = res.data.superuser || false;
        })
        .catch((error) => {
          console.error(error);
          this.hooks = [];
        });
    },
    getLabels() {
      this.request('get', '/labels')
        .then((res) => {
          this.labels = res.data.labels || [];
        })
        .catch((error) => {
          console.error(error);
          this.labels = [];
        });
    },
    handleHookSubmit() {
      const payload = {
        name: this.hookForm.name,
        url: this.hookForm.url,
        label_ids: this.hookForm.label_ids,
      };
      const request = this.hookForm.pk
        ? this.request('put', `/hooks/${this.hookForm.pk}`, payload)
        : this.request('post', '/hooks', payload);
      this.closeHookModal();

      request
        .then((res) => this.showResult(res, 'Hook saved!'))
        .catch((error) => {
          console.error(error);
          this.showError('Hook not saved, error occured');
        })
        .finally(() => this.getHooks());
    },
    testHook(pk) {
      this.message = 'Sending test message...';
      this.messageType = 'success';
      this.showMessage = true;
      this.request('post', `/hooks/${pk}/test`)
        .then((res) => this.showResult(res, 'Test message sent!'))
        .catch((error) => {
          console.error(error);
          this.showError('Test message not sent, error occured');
        });
    },
    handleDeleteHook(hook) {
      this.deleteTarget = hook;
      document.querySelector('body').classList.add('modal-open');
    },
    confirmDeleteHook() {
      const pk = this.deleteTarget.pk;
      this.closeDeleteHookModal();
      this.request('delete', `/hooks/${pk}`)
        .then((res) => this.showResult(res, 'Hook removed!'))
        .catch((error) => {
          console.error(error);
          this.showError('Hook not removed, error occured');
        })
        .finally(() => this.getHooks());
    },
    closeDeleteHookModal() {
      this.deleteTarget = null;
      document.querySelector('body').classList.remove('modal-open');
    },
    initHookForm() {
      this.hookForm = { pk: '', name: '', url: '', label_ids: [] };
    },
    toggleAddHookModal() {
      this.initHookForm();
      this.activeHookModal = true;
      document.querySelector('body').classList.add('modal-open');
    },
    toggleEditHookModal(hook) {
      this.hookForm = {
        pk: hook.pk,
        name: hook.name,
        url: '',
        label_ids: hook.labels.map(label => label.pk),
      };
      this.activeHookModal = true;
      document.querySelector('body').classList.add('modal-open');
    },
    closeHookModal() {
      this.activeHookModal = false;
      this.initHookForm();
      document.querySelector('body').classList.remove('modal-open');
    },
  },
  created() {
    this.getHooks();
    this.getLabels();
  },
};
</script>
