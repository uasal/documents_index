<template>
  <div class="container" v-if="superuser">
    <div class="row">
      <div class="col-12">
        <h1>Labels</h1>
        <hr><br><br>
        <div>
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
        </div>
        <br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" @click="toggleAddLabelModal">
          Add Label
        </button>
        <div class="my-3" v-if="show_label_table">
          <input type="text" placeholder="Filter table by name" v-model="label_filter" />
        </div>
        <table class="table table-hover" v-if="show_label_table">
          <thead>
            <tr>
              <th style="min-width: 10%;" scope="col">Name</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(lbl, index) in filteredLabels" :key="index">
              <td>{{ lbl.name }}</td>
              <td>
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-warning btn-sm" @click="toggleEditLabelModal(lbl)">
                    Update
                  </button>
                  <button type="button" class="btn btn-danger btn-sm" @click="handleDeleteLabel(lbl)">
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else>
          <p>No labels created yet.</p>
        </div>
      </div>
    </div>

    <!-- add new label modal -->
    <div ref="addLabelModal" class="modal fade"
      :class="{ show: activeAddLabelModal, 'd-block': activeAddLabelModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="label">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add a new label</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleAddLabelModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="addLabelName" class="form-label">Name:</label>
                <input type="text" class="form-control" id="addLabelName" v-model="addLabelForm.name"
                  placeholder="Enter label name">
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleAddLabelSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleAddLabelReset">
                  Reset
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeAddLabelModal" class="modal-backdrop fade show"></div>

    <!-- edit label modal -->
    <div ref="editLabelModal" class="modal fade"
      :class="{ show: activeEditLabelModal, 'd-block': activeEditLabelModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="label">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Update</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleEditLabelModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="editLabelName" class="form-label">Name:</label>
                <input type="text" class="form-control" maxlength="100" id="editLabelName"
                  v-model="editLabelForm.name" placeholder="Enter label name">
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleEditLabelSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleEditLabelCancel">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeEditLabelModal" class="modal-backdrop fade show"></div>
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
  name: 'LabelsAll',
  data() {
    return {
      activeAddLabelModal: false,
      activeEditLabelModal: false,
      addLabelForm: {
        name: '',
      },
      editLabelForm: {
        pk: '',
        name: '',
      },
      label_filter: '',
      labels: [],
      show_label_table: false,
      message: '',
      showMessage: false,
      superuser: false,
    };
  },
  components: {
    alert: AlertMessage,
  },
  watch: {
    labels: function (newVal, oldVal) {
      if (this.labels && this.labels.length > 0) {
        this.show_label_table = true;
      } else {
        this.show_label_table = false;
      }
    },
  },
  computed: {
    filteredLabels() {
      if (this.label_filter === '') {
        return this.labels;
      } else {
        return this.labels.filter(lbl => {
          const searchTerm = this.label_filter.toLowerCase();
          const name = lbl.name.toString().toLowerCase();
          return name.includes(searchTerm);
        });
      }
    },
    isLoggedIn() {
      if (auth.currentUser) {
        return true;
      } else {
        return false;
      }
    },
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
          const credential = GoogleAuthProvider.credentialFromResult(result);
        })
        .catch(err => {
          console.log(`Error during sign in: ${err.message}`);
          window.alert(`Sign in failed. Retry or check your browser logs.`);
        });
    },
    addLabel(payload) {
      const path = `${API_URL}/labels`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.post(path, payload, config)
          .then((res) => {
            this.getLabels();
            if (res.data.status == 'success') {
              this.message = 'Label added!';
            } else {
              this.message = 'Label not added, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.log(error);
            this.getLabels();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
    getLabels() {
      const path = `${API_URL}/labels`;
      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.get(path, config)
          .then((res) => {
            this.labels = res.data.labels || [];
            this.superuser = res.data.superuser || false;
          })
          .catch((error) => {
            console.error(error);
            this.labels = [];
            this.superuser = false;
          });
      }).catch(function (error) {
        console.log(error)
        this.superuser = false;
      });
    },
    handleAddLabelReset() {
      this.initLabelForm();
    },
    handleAddLabelSubmit() {
      this.toggleAddLabelModal();
      const payload = {
        name: this.addLabelForm.name,
      };
      this.addLabel(payload);
      this.initLabelForm();
    },
    handleDeleteLabel(lbl) {
      this.removeLabel(lbl.pk);
    },
    handleEditLabelCancel() {
      this.toggleEditLabelModal(null);
      this.initLabelForm();
      this.getLabels();
    },
    handleEditLabelSubmit() {
      this.toggleEditLabelModal(null);
      const payload = {
        name: this.editLabelForm.name,
      };
      this.updateLabel(payload, this.editLabelForm.pk);
    },
    initLabelForm() {
      this.addLabelForm.name = '';
      this.editLabelForm.pk = '';
      this.editLabelForm.name = '';
    },
    removeLabel(lpk) {
      const path = `${API_URL}/labels/${lpk}`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.delete(path, config)
          .then((res) => {
            this.getLabels();
            if (res.data.status == 'success') {
              this.message = 'Label removed!';
            } else {
              this.message = 'Label not removed, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getLabels();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
    toggleAddLabelModal() {
      const body = document.querySelector('body');
      this.activeAddLabelModal = !this.activeAddLabelModal;
      if (this.activeAddLabelModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    toggleEditLabelModal(lbl) {
      if (lbl) {
        this.editLabelForm = { ...lbl };
      }
      const body = document.querySelector('body');
      this.activeEditLabelModal = !this.activeEditLabelModal;
      if (this.activeEditLabelModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    updateLabel(payload, lpk) {
      const path = `${API_URL}/labels/${lpk}`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.put(path, payload, config)
          .then((res) => {
            this.getLabels();
            if (res.data.status == 'success') {
              this.message = 'Label updated!';
            } else {
              this.message = 'Label not updated, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getLabels();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
  },
  created() {
    this.getLabels();
  },
};
</script>
