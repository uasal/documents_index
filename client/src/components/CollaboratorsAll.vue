<template>
  <div class="container" v-if="superuser">
    <div class="row">
      <div class="col-12">
        <h1>Collaborators</h1>
        <hr><br><br>
        <div>
          <p>Hello, {{ username }}</p>
        </div>
        <br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" @click="toggleAddCollaboratorModal">
          Add Collaborator
        </button>
        <div class="my-3" v-if="show_table">
          <input type="text" placeholder="Filter table by email" v-model="filter" />
        </div>
        <table class="table table-hover" v-if="show_table">
          <thead>
            <tr>
              <th style="min-width: 10%;" scope="col">Email</th>
              <th style="min-width: 10%;" scope="col">Superuser</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(col, index) in filteredCollaborators" :key="index">
              <td>{{ col.email }}</td>
              <td>{{ col.superuser }}</td>
              <td>
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-warning btn-sm" @click="toggleEditCollaboratorModal(col)">
                    Update
                  </button>
                  <button type="button" class="btn btn-danger btn-sm" @click="handleDeleteCollaborator(col)">
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else>
          <p v-if="filter === ''">No collaborators.</p>
          <p v-else>Sorry, no emails found containing <b>{{ filter }}</b>. Try a different filter.</p>
        </div>
      </div>
    </div>

    <!-- add new collaborator modal -->
    <div ref="addCollaboratorModal" class="modal fade"
      :class="{ show: activeAddCollaboratorModal, 'd-block': activeAddCollaboratorModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="collaborator">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add a new collaborator</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleAddCollaboratorModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="addCollaboratorEmail" class="form-label">Email:</label>
                <input type="text" class="form-control" id="addCollaboratorEmail" v-model="addCollaboratorForm.email"
                  placeholder="Enter email">
              </div>
              <div class="mb-3">
                <input type="checkbox" class="form-check-input me-2" id="addCollaboratorSuperuser"
                  v-model="addCollaboratorForm.superuser">
                <label class="form-check-label" for="addCollaboratorSuperuser">Are they superuser?</label>
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleAddSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleAddReset">
                  Reset
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeAddCollaboratorModal" class="modal-backdrop fade show"></div>

    <!-- edit collaborator modal -->
    <div ref="editCollaboratorModal" class="modal fade"
      :class="{ show: activeEditCollaboratorModal, 'd-block': activeEditCollaboratorModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="collaborator">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Update</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleEditCollaboratorModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="editCollaboratorEmail" class="form-label">Email:</label>
                <input type="text" class="form-control" maxlength="100" id="editCollaboratorEmail"
                  v-model="editCollaboratorForm.email" placeholder="Enter email">
              </div>
              <div class="mb-3">
                <input type="checkbox" class="form-check-input me-2" id="editCollaboratorSuperuser"
                  v-model="editCollaboratorForm.superuser">
                <label class="form-check-label" for="editCollaboratorSuperuser">Are they superuser?</label>
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleEditSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleEditCancel">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeEditCollaboratorModal" class="modal-backdrop fade show"></div>
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
  name: 'CollaboratorsAll',
  data() {
    return {
      activeAddCollaboratorModal: false,
      activeEditCollaboratorModal: false,
      addCollaboratorForm: {
        email: '',
        superuser: '',
      },
      filter: '',
      collaborators: [],
      show_table: false,
      editCollaboratorForm: {
        pk: '',
        email: '',
        superuser: '',
      },
      message: '',
      showMessage: false,
      superuser: false,
    };
  },
  components: {
    alert: AlertMessage,
  },
  watch: {
    collaborators: function (newVal, oldVal) {
      if (this.collaborators.length > 0) {
        this.show_table = true;
      } else {
        this.show_table = false;
      }
    }
  },
  computed: {
    filteredCollaborators() {
      if (this.filter === '') {
        return this.collaborators;
      } else {
        return this.collaborators.filter(collaborator => {
          const searchTerm = this.filter.toLowerCase();

          const email = collaborator.email.toString().toLowerCase();

          return email.includes(searchTerm);
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
          // Returns the signed in user along with the provider's credential
          console.log(`${result.user.displayName} logged in.`);
          const credential = GoogleAuthProvider.credentialFromResult(result);
          // this.token = credential.accessToken;
          // // The signed-in user info.
          // this.username = result.user.displayName;
          // this.email = result.user.email;
        })
        .catch(err => {
          console.log(`Error during sign in: ${err.message}`);
          window.alert(`Sign in failed. Retry or check your browser logs.`);
        });
    },
    addCollaborator(payload) {
      const path = `${API_URL}/users`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.post(path, payload, config)
          .then((res) => {
            this.getCollaborators();
            if (res.data.status == 'success') {
              this.message = 'Collaborator added!';
            } else {
              this.message = 'Collaborator not added, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.log(error);
            this.getCollaborators();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
    getCollaborators() {
      const path = `${API_URL}/users`;
      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.get(path, config)
          .then((res) => {
            this.collaborators = res.data.collaborators;
            this.superuser = res.data.superuser;
          })
          .catch((error) => {
            console.error(error);
            this.superuser = false;
          });
      }).catch(function (error) {
        console.log(error)
        this.superuser = false;
      });
    },
    handleAddReset() {
      this.initForm();
    },
    handleAddSubmit() {
      this.toggleAddCollaboratorModal();
      const payload = {
        email: this.addCollaboratorForm.email,
        superuser: this.addCollaboratorForm.superuser,
        creator_email: this.email,
      };
      this.addCollaborator(payload);
      this.initForm();
    },
    handleDeleteCollaborator(collaborator) {
      this.removeCollaborator(collaborator.pk);
    },
    handleEditCancel() {
      this.toggleEditCollaboratorModal(null);
      this.initForm();
      this.getCollaborators(); // why?
    },
    handleEditSubmit() {
      this.toggleEditCollaboratorModal(null);
      const payload = {
        email: this.editCollaboratorForm.email,
        superuser: this.editCollaboratorForm.superuser,
      };
      this.updateCollaborator(payload, this.editCollaboratorForm.pk);
    },
    initForm() {
      this.addCollaboratorForm.email = '';
      this.addCollaboratorForm.superuser = '';
      this.editCollaboratorForm.pk = '';
      this.editCollaboratorForm.email = '';
      this.editCollaboratorForm.superuser = '';
    },
    removeCollaborator(cpk) {
      const path = `${API_URL}/users/${cpk}`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.delete(path, config)
          .then((res) => {
            this.getCollaborators();
            if (res.data.status == 'success') {
              this.message = 'Collaborator removed!';
            } else {
              this.message = 'Collaborator not removed, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getCollaborators();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
    toggleAddCollaboratorModal() {
      const body = document.querySelector('body');
      this.activeAddCollaboratorModal = !this.activeAddCollaboratorModal;
      if (this.activeAddCollaboratorModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    toggleEditCollaboratorModal(col) {
      if (col) {
        this.editCollaboratorForm = col;
      }
      const body = document.querySelector('body');
      this.activeEditCollaboratorModal = !this.activeEditCollaboratorModal;
      if (this.activeEditCollaboratorModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    updateCollaborator(payload, cpk) {
      const path = `${API_URL}/users/${cpk}`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.put(path, payload, config)
          .then((res) => {
            this.getCollaborators();
            if (res.data.status == 'success') {
              this.message = 'Collaborator updated!';
            } else {
              this.message = 'Collaborator not updated, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getCollaborators();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
  },
  created() {
    this.getCollaborators();
  },
};
</script>
