<template>
  <div class="container" v-if="superuser">
    <div class="row">
      <div class="col-12">
        <h1>Collaborators</h1>
        <hr><br><br>
        <div>
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
        </div>
        <br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" @click="toggleAddDomainModal">
          Add Domain
        </button>
        <div class="my-3" v-if="show_domain_table">
          <input type="text" placeholder="Filter table by email" v-model="domain_filter" />
        </div>
        <table class="table table-hover" v-if="show_domain_table">
          <thead>
            <tr>
              <th style="min-width: 10%;" scope="col">Email Domain</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(col, index) in filteredDomains" :key="index">
              <td>{{ col.email_domain }}</td>
              <td>
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-warning btn-sm" @click="toggleEditDomainModal(col)">
                    Update
                  </button>
                  <button type="button" class="btn btn-danger btn-sm" @click="handleDeleteDomain(col)">
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <br><br>
        <button type="button" class="btn btn-success btn-sm" @click="toggleAddCollaboratorModal">
          Add Collaborator
        </button>
        <div class="my-3" v-if="show_collaborator_table">
          <input type="text" placeholder="Filter table by email" v-model="collaborator_filter" />
        </div>
        <table class="table table-hover" v-if="show_collaborator_table">
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
        <div v-if="!show_collaborator_table && !show_domain_table">
          <p>No collaborators.</p>
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
                <button type="button" class="btn btn-primary btn-sm" @click="handleAddCollaboratorSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleAddCollaboratorReset">
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
                <button type="button" class="btn btn-primary btn-sm" @click="handleEditCollaboratorSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleEditCollaboratorCancel">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeEditCollaboratorModal" class="modal-backdrop fade show"></div>

    <!-- add new domain modal -->
    <div ref="addDomainModal" class="modal fade" :class="{ show: activeAddDomainModal, 'd-block': activeAddDomainModal }"
      tabindex="-1" role="dialog">
      <div class="modal-dialog" role="domain">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add a new domain</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleAddDomainModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="addDomainEmail" class="form-label">Email Domain:</label>
                <input type="text" class="form-control" id="addDomainEmail" v-model="addDomainForm.email_domain"
                  placeholder="Enter email domain">
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleAddDomainSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleAddDomainReset">
                  Reset
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeAddDomainModal" class="modal-backdrop fade show"></div>

    <!-- edit domain modal -->
    <div ref="editDomainModal" class="modal fade"
      :class="{ show: activeEditDomainModal, 'd-block': activeEditDomainModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="collaborator">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Update</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleEditDomainModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="editDomainEmail" class="form-label">Email:</label>
                <input type="text" class="form-control" maxlength="100" id="editDomainEmail"
                  v-model="editDomainForm.email" placeholder="Enter domain email">
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleEditDomainSubmit">
                  Submit
                </button>
                <button type="button" class="btn btn-danger btn-sm" @click="handleEditDomainCancel">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeEditDomainModal" class="modal-backdrop fade show"></div>
  </div>
</template>

<script>
import axios from 'axios';
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
      activeAddDomainModal: false,
      activeEditDomainModal: false,
      addDomainForm: {
        email_domain: '',
      },
      collaborator_filter: '',
      domain_filter: '',
      collaborators: [],
      domains: [],
      show_collaborator_table: false,
      show_domain_table: false,
      editCollaboratorForm: {
        pk: '',
        email: '',
        superuser: '',
      },
      editDomainForm: {
        pk: '',
        email_domain: '',
      },
      message: '',
      showMessage: false,
    };
  },
  components: {
    alert: AlertMessage,
  },
  watch: {
    collaborators: function (newVal, oldVal) {
      if (this.collaborators.length > 0) {
        this.show_collaborator_table = true;
      } else {
        this.show_collaborator_table = false;
      }
    },
    domains: function (newVal, oldVal) {
      if (this.domains.length > 0) {
        this.show_domain_table = true;
      } else {
        this.show_domain_table = false;
      }
    }
  },
  computed: {
    filteredCollaborators() {
      if (this.collaborator_filter === '') {
        return this.collaborators;
      } else {
        return this.collaborators.collaborator_filter(collaborator => {
          const searchTerm = this.collaborator_filter.toLowerCase();

          const email = collaborator.email.toString().toLowerCase();

          return email.includes(searchTerm);
        });
      }
    },
    filteredDomains() {
      if (this.domain_filter === '') {
        return this.domains;
      } else {
        return this.domains.domain_filter(domain => {
          const searchTerm = this.domain_filter.toLowerCase();

          const email_domain = domain.email_domain.toString().toLowerCase();

          return email_domain.includes(searchTerm);
        });
      }
    },
  },
  methods: {
    addCollaborator(payload) {
      const path = `${API_URL}/users`;

      axios.post(path, payload, config)
          .then((res) => {
            this.getCollaborators();
            this.getDomains();
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
            this.getDomains();
          });
    },
    getCollaborators() {
      const path = `${API_URL}/users`;
        axios.get(path, config)
          .then((res) => {
            this.collaborators = res.data.collaborators;
          })
          .catch((error) => {
            console.error(error);
          });
    },
    handleAddCollaboratorReset() {
      this.initCollaboratorForm();
    },
    handleAddCollaboratorSubmit() {
      this.toggleAddCollaboratorModal();
      const payload = {
        email: this.addCollaboratorForm.email,
        superuser: this.addCollaboratorForm.superuser,
        creator_email: this.email,
      };
      this.addCollaborator(payload);
      this.initCollaboratorForm();
    },
    handleDeleteCollaborator(collaborator) {
      this.removeCollaborator(collaborator.pk);
    },
    handleEditCollaboratorCancel() {
      this.toggleEditCollaboratorModal(null);
      this.initCollaboratorForm();
      this.getCollaborators();
      this.getDomains();
    },
    handleEditCollaboratorSubmit() {
      this.toggleEditCollaboratorModal(null);
      const payload = {
        email: this.editCollaboratorForm.email,
        superuser: this.editCollaboratorForm.superuser,
      };
      this.updateCollaborator(payload, this.editCollaboratorForm.pk);
    },
    initCollaboratorForm() {
      this.addCollaboratorForm.email = '';
      this.addCollaboratorForm.superuser = '';
      this.editCollaboratorForm.pk = '';
      this.editCollaboratorForm.email = '';
      this.editCollaboratorForm.superuser = '';
    },
    removeCollaborator(cpk) {
      const path = `${API_URL}/users/${cpk}`;

        axios.delete(path, config)
          .then((res) => {
            this.getCollaborators();
            this.getDomains();
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
            this.getDomains();
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

        axios.put(path, payload, config)
          .then((res) => {
            this.getCollaborators();
            this.getDomains();
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
            this.getDomains();
          });
    },
    addDomain(payload) {
      const path = `${API_URL}/domains`;

      axios.post(path, payload, config)
          .then((res) => {
            this.getCollaborators();
            this.getDomains();
            if (res.data.status == 'success') {
              this.message = 'Domain added!';
            } else {
              this.message = 'Domain not added, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.log(error);
            this.getCollaborators();
            this.getDomains();
          });
    },
    getDomains() {
      const path = `${API_URL}/domains`;
        axios.get(path, config)
          .then((res) => {
            this.domains = res.data.domains;
          })
          .catch((error) => {
            console.error(error);
            this.superuser = false;
          });
    },
    handleAddDomainReset() {
      this.initDomainForm();
    },
    handleAddDomainSubmit() {
      this.toggleAddDomainModal();
      const payload = {
        email_domain: this.addDomainForm.email_domain,
        creator_email: this.email,
      };
      this.addDomain(payload);
      this.initDomainForm();
    },
    handleDeleteDomain(collaborator) {
      this.removeDomain(collaborator.pk);
    },
    handleEditDomainCancel() {
      this.toggleEditDomainModal(null);
      this.initDomainForm();
      this.getCollaborators();
      this.getDomains();
    },
    handleEditDomainSubmit() {
      this.toggleEditDomainModal(null);
      const payload = {
        email_domain: this.editDomainForm.email_domain,
      };
      this.updateDomain(payload, this.editDomainForm.pk);
    },
    initDomainForm() {
      this.addDomainForm.email_domain = '';
      this.editDomainForm.pk = '';
      this.editDomainForm.email_domain = '';
    },
    removeDomain(cpk) {
      const path = `${API_URL}/users/${cpk}`;

        axios.delete(path, config)
          .then((res) => {
            this.getCollaborators();
            this.getDomains();
            if (res.data.status == 'success') {
              this.message = 'Domain removed!';
            } else {
              this.message = 'Domain not removed, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getCollaborators();
            this.getDomains();
          });
    },
    toggleAddDomainModal() {
      const body = document.querySelector('body');
      this.activeAddDomainModal = !this.activeAddDomainModal;
      if (this.activeAddDomainModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    toggleEditDomainModal(col) {
      if (col) {
        this.editDomainForm = col;
      }
      const body = document.querySelector('body');
      this.activeEditDomainModal = !this.activeEditDomainModal;
      if (this.activeEditDomainModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    updateDomain(payload, cpk) {
      const path = `${API_URL}/domains/${cpk}`;

        axios.put(path, payload, config)
          .then((res) => {
            this.getCollaborators();
            this.getDomains();
            if (res.data.status == 'success') {
              this.message = 'Domain updated!';
            } else {
              this.message = 'Domain not updated, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getCollaborators();
            this.getDomains();
          });
    },
  },
  created() {
    this.getCollaborators();
    this.getDomains();
  },
};
</script>
