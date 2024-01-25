<template>
  <div class="container">
    <div class="row">
      <div class="col-12" v-if="isAuthorized">
        <div class="row">
          <div>
            <div class="d-inline-flex float-start">
              <h1>Documents</h1>
            </div>
            <div class="d-inline-flex float-end" v-if="superuser">
              <a role="button" class="btn btn-success" href="collaborators" target="_blank">Edit collaborators</a>
            </div>
          </div>
        </div>
        <hr><br><br>
        <div>
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
          <p>Add a new document using the button below. You can edit or delete documents you have added.</p>
          <p>To see all details related to a document click on its Title or its Doc Identifier,
            or, for a given Doc Identifier, add "/docs/&lt;doc_identifier&gt;" to the current URL.</p>
        </div>
        <br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" @click="toggleAddDocumentModal">
          Add Document
        </button>
        <button type="button" class="btn btn-success btn-sm ms-4" @click="toggleUploadFileModal">
          Upload File
        </button>
        <div class="my-3" v-if="show_table">
          <input type="text" placeholder="Filter table by any column" v-model="filter" />
        </div>
        <table class="table table-hover" v-if="show_table">
          <thead>
            <tr>
              <th style="min-width: 10%;" scope="col">Title</th>
              <th style="min-width: 10%;" scope="col">Author</th>
              <th style="min-width: 10%;" scope="col">Doc Identifier</th>
              <th style="min-width: 10%;" scope="col">Doc Code</th>
              <th style="min-width: 10%;" scope="col">Compiled URL</th>
              <th style="min-width: 10%;" scope="col">Source URL</th>
              <th style="min-width: 20%;" scope="col">Abstract</th>
              <th style="min-width: 10%;" scope="col">Created By</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(doc, index) in filteredDocuments" :key="index">
              <td data-toggle="tooltip" data-placement="bottom" :title="doc.title" style="cursor: default"
                v-if="doc.title.length > 30">
                <a :href="'docs/' + doc.doc_identifier" target="_blank">{{
                  truncate(doc.title, 30) }}</a>
              </td>
              <td v-else><a :href="'docs/' + doc.doc_identifier" target="_blank">{{ doc.title }}</a></td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.author" style="cursor: default"
                v-if="doc.author.length > 30">{{ truncate(doc.author, 30) }}</td>
              <td v-else>{{ doc.author }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.doc_identifier" style="cursor: default"
                v-if="doc.doc_identifier.length > 30">
                <a :href="'docs/' + doc.doc_identifier" target="_blank">{{
                  truncate(doc.doc_identifier, 30) }}</a>
              </td>
              <td v-else><a :href="'docs/' + doc.doc_identifier" target="_blank">{{ doc.doc_identifier }}</a></td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.doc_code" style="cursor: default"
                v-if="doc.doc_code.length > 30">{{ truncate(doc.doc_code, 30) }}</td>
              <td v-else>{{ doc.doc_code }}</td>

              <td>
                <a v-if="doc.compiled_url" :href="doc.compiled_url" target="_blank">document link</a>
                <!-- <a class="ms-3" :href=doc.compiled_url target="_blank" download><font-awesome-icon
                    icon="fa-solid fa-download" /></a> -->
              </td>

              <td>
                <a v-if="doc.source_url" :href="doc.source_url" target="_blank">source link</a>
                <!-- <a class="ms-3" :href=doc.source_url target="_blank" download><font-awesome-icon
                    icon="fa-solid fa-download" /></a> -->
              </td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.abstract" style="cursor: default"
                v-if="doc.abstract.length > 30">{{ truncate(doc.abstract, 30) }}</td>
              <td v-else>{{ doc.abstract }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.creator_email" style="cursor: default"
                v-if="doc.creator_email.length > 15">{{ truncate(doc.creator_email, 15) }}</td>
              <td v-else>{{ doc.creator_email }}</td>

              <td v-if="(email == doc.creator_email) || superuser">
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-warning btn-sm" @click="toggleEditDocumentModal(doc)">
                    Update
                  </button>
                  <button type="button" class="btn btn-danger btn-sm" @click="handleDeleteDocument(doc)">
                    Delete
                  </button>
                </div>
              </td>
              <td v-else></td>
            </tr>
          </tbody>
        </table>
        <div v-else>
          <p v-if="filter === ''">No documents stored.</p>
          <p v-else>Sorry, no documents found containing <b>{{ filter }}</b>. Try a different filter.</p>
        </div>
      </div>
      <!-- <div v-if="hideContent">Sorry, this page is not available or you are not authorized to view it.</div> -->
    </div>

    <!-- add new document modal -->
    <div ref="addDocumentModal" class="modal fade"
      :class="{ show: activeAddDocumentModal, 'd-block': activeAddDocumentModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add a new document</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleAddDocumentModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="addDocumentTitle" class="form-label">Title:</label>
                <input type="text" class="form-control" id="addDocumentTitle" v-model="addDocumentForm.title"
                  placeholder="Enter title">
              </div>
              <div class="mb-3">
                <label for="addDocumentAuthor" class="form-label">Author:</label>
                <input type="text" class="form-control" id="addDocumentAuthor" v-model="addDocumentForm.author"
                  placeholder="Enter author">
              </div>
              <div class="mb-3">
                <label for="addDocumentDocCode" class="form-label">Doc Code (optional):</label>
                <input type="text" class="form-control" id="addDocCode" v-model="addDocumentForm.doc_code"
                  placeholder="Enter document code">
              </div>
              <div class="mb-3">
                <label for="addDocumentCompiledUrl" class="form-label">Compiled URL:</label>
                <input type="text" class="form-control" id="addCompiledUrl" v-model="addDocumentForm.compiled_url"
                  placeholder="Enter compiled URL">
              </div>
              <div class="mb-3">
                <label for="addDocumentSourceUrl" class="form-label">Source URL:</label>
                <input type="text" class="form-control" id="addSourceUrl" v-model="addDocumentForm.source_url"
                  placeholder="Enter source URL">
              </div>
              <div class="mb-3">
                <label for="addDocumentAbstract" class="form-label">Abstract:</label>
                <textarea class="form-control" id="addAbstract" rows="3" v-model="addDocumentForm.abstract"
                  placeholder="Enter abstract"></textarea>
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
    <div v-if="activeAddDocumentModal" class="modal-backdrop fade show"></div>

    <!-- add documents via file upload modal -->
    <div ref="uploadFileModal" class="modal fade"
      :class="{ show: activeUploadFileModal, 'd-block': activeUploadFileModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Upload a txt file with metadata for new documents</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleUploadFileModal">
            </button>
          </div>
          <div class="modal-body">
            <p>Upload a file with values separated by bars (|).</p>
            <p>The file must have entries for the following fields (in this order): Title | Author | Doc Code | Compiled
              URL | Source URL | Abstract</p>
            <p>If the file has fewer or more columns than 6, the upload will result in an error.</p>
            <p>Columns that are optional (Doc Code and Abstract), should be included, but left blank if no value is to be
              included.</p>
            <p>Lines starting with '#' will be omitted.</p>
            <p>Do not use bars in the input values.</p>
            <p>File example:</p>
            <div class="mb-4 text-nowrap" style="overflow-x: scroll; font-family: courier; font-size: 12px;">
              <p class="mb-0"># Title | Author | Doc Code | Compiled URL | Source URL | Abstract</p>
              <p class="mb-0">Extra Solar Camera: Design and User Guide | Ewan Douglas, Jared Males, Daewook Kim, and the
                STP Space Coronagraph Working Groups ||
                https://github.com/uasal/spacecoron_design_docs/raw/compiled/coronagraph_guide.pdf |
                https://github.com/uasal/spacecoron_design_docs | ESC high-level design doc.</p>
              <p class="mb-0">IOB Drawing Tree | Various ||
                https://github.com/uasal/spacecoron_design_docs/blob/main/mgmt/Drawing_Tree.png |
                https://github.com/uasal/spacecoron_design_docs/blob/main/mgmt/Drawing_Tree.drawio | Pearl Instrument
                Drawing Tree</p>
            </div>
            <form>
              <div class="mb-3">
                <input type="file" class="form-control btn-primary" id="uploadFile" @change="addFile" accept=".txt"
                  placeholder="Upload file">
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleFileUpload">
                  Submit
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div v-if="activeUploadFileModal" class="modal-backdrop fade show"></div>

    <!-- edit document modal -->
    <div ref="editDocumentModal" class="modal fade"
      :class="{ show: activeEditDocumentModal, 'd-block': activeEditDocumentModal }" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Update</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
              @click="toggleEditDocumentModal">
            </button>
          </div>
          <div class="modal-body">
            <form>
              <div class="mb-3">
                <label for="editDocumentTitle" class="form-label">Title:</label>
                <input type="text" class="form-control" maxlength="100" id="editDocumentTitle"
                  v-model="editDocumentForm.title" placeholder="Enter title">
              </div>
              <div class="mb-3">
                <label for="editDocumentAuthor" class="form-label">Author:</label>
                <input type="text" class="form-control" maxlength="100" id="editDocumentAuthor"
                  v-model="editDocumentForm.author" placeholder="Enter author">
              </div>
              <div class="mb-3">
                <label for="editDocumentDocCode" class="form-label">Doc Code (optional):</label>
                <input type="text" class="form-control" maxlength="20" id="editDocCode"
                  v-model="editDocumentForm.doc_code" placeholder="Enter document code">
              </div>
              <div class="mb-3">
                <label for="editDocumentCompiledUrl" class="form-label">Compiled URL:</label>
                <input type="text" class="form-control" maxlength="100" id="editCompiledUrl"
                  v-model="editDocumentForm.compiled_url" placeholder="Enter compiled URL">
              </div>
              <div class="mb-3">
                <label for="editDocumentSourceUrl" class="form-label">Source URL:</label>
                <input type="text" class="form-control" maxlength="100" id="editSourceUrl"
                  v-model="editDocumentForm.source_url" placeholder="Enter source URL">
              </div>
              <div class="mb-3">
                <label for="editDocumentAbstract" class="form-label">Abstract:</label>
                <textarea class="form-control" id="editAbstract" rows="3" v-model="editDocumentForm.abstract"
                  placeholder="Enter abstract"></textarea>
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
    <div v-if="activeEditDocumentModal" class="modal-backdrop fade show"></div>
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
  name: 'DocumentsAll',
  data() {
    return {
      activeAddDocumentModal: false,
      activeEditDocumentModal: false,
      activeUploadFileModal: false,
      addDocumentForm: {
        title: '',
        author: '',
        doc_code: '',
        compiled_url: '',
        source_url: '',
        abstract: '',
      },
      filter: '',
      documents: [],
      show_table: false,
      editDocumentForm: {
        pk: '',
        title: '',
        author: '',
        doc_identifier: '',
        doc_code: '',
        compiled_url: '',
        source_url: '',
        abstract: '',
      },
      message: '',
      showMessage: false,
      isAuthorized: false,
      // hideContent: false,
      superuser: false,
      file: null,
    };
  },
  components: {
    alert: AlertMessage,
  },
  watch: {
    documents: function (newVal, oldVal) {
      if (this.documents.length > 0) {
        this.show_table = true;
      } else {
        this.show_table = false;
      }
    }
  },
  computed: {
    filteredDocuments() {
      if (this.filter === '') {
        return this.documents;
      } else {
        return this.documents.filter(doc => {
          const searchTerm = this.filter.toLowerCase();

          const title = doc.title.toString().toLowerCase();
          const author = doc.author.toString().toLowerCase();
          const doc_identifier = doc.doc_identifier.toString().toLowerCase();
          const doc_code = doc.doc_code.toString().toLowerCase();
          const compiled_url = doc.compiled_url.toString().toLowerCase();
          const source_url = doc.source_url.toString().toLowerCase();
          const abstract = doc.abstract.toString().toLowerCase();

          return title.includes(searchTerm) ||
            author.includes(searchTerm) ||
            doc_identifier.includes(searchTerm) ||
            doc_code.includes(searchTerm) ||
            compiled_url.includes(searchTerm) ||
            source_url.includes(searchTerm) ||
            abstract.includes(searchTerm);
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
    addDocument(payload) {
      const path = `${API_URL}/documents`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.post(path, payload, config)
          .then((res) => {
            this.getDocuments();
            if (res.data.status == 'success') {
              this.message = 'Document added!';
            } else {
              this.message = 'Document not added, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.log(error);
            this.getDocuments();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
    getDocuments() {
      const path = `${API_URL}/documents`;
      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.get(path, config)
          .then((res) => {
            this.documents = res.data.documents;
            this.superuser = res.data.superuser;
            this.isAuthorized = true;
          })
          .catch((error) => {
            console.error(error);
            this.superuser = false;
            this.isAuthorized = error.response.data.isAuthorized;
            // this.hideContent = !this.isAuthorized;
          });
      }).catch(function (error) {
        console.log(error)
        this.superuser = false;
        this.isAuthorized = false;
        // this.hideContent = true;
      });
    },
    handleAddReset() {
      this.initForm();
    },
    handleAddSubmit() {
      this.toggleAddDocumentModal();
      const payload = {
        title: this.addDocumentForm.title,
        author: this.addDocumentForm.author,
        doc_code: this.addDocumentForm.doc_code,
        compiled_url: this.addDocumentForm.compiled_url,
        source_url: this.addDocumentForm.source_url,
        abstract: this.addDocumentForm.abstract,
        creator_email: this.email,
      };
      this.addDocument(payload);
      this.initForm();
    },
    handleDeleteDocument(document) {
      this.removeDocument(document.doc_identifier);
    },
    handleEditCancel() {
      this.toggleEditDocumentModal(null);
      this.initForm();
      this.getDocuments(); // why?
    },
    handleEditSubmit() {
      this.toggleEditDocumentModal(null);
      const payload = {
        title: this.editDocumentForm.title,
        author: this.editDocumentForm.author,
        doc_code: this.editDocumentForm.doc_code,
        compiled_url: this.editDocumentForm.compiled_url,
        source_url: this.editDocumentForm.source_url,
        abstract: this.editDocumentForm.abstract,
      };
      this.updateDocument(payload, this.editDocumentForm.doc_identifier);
    },
    initForm() {
      this.addDocumentForm.title = '';
      this.addDocumentForm.author = '';
      this.addDocumentForm.doc_code = '';
      this.addDocumentForm.compiled_url = '';
      this.addDocumentForm.source_url = '';
      this.addDocumentForm.abstract = '';
      this.editDocumentForm.pk = '';
      this.editDocumentForm.title = '';
      this.editDocumentForm.author = '';
      this.editDocumentForm.doc_identifier = '';
      this.editDocumentForm.doc_code = '';
      this.editDocumentForm.compiled_url = '';
      this.editDocumentForm.source_url = '';
      this.editDocumentForm.abstract = '';
    },
    removeDocument(docID) {
      const path = `${API_URL}/documents/${docID}`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.delete(path, config)
          .then((res) => {
            this.getDocuments();
            if (res.data.status == 'success') {
              this.message = 'Document removed!';
            } else {
              this.message = 'Document not removed, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getDocuments();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
    toggleAddDocumentModal() {
      const body = document.querySelector('body');
      this.activeAddDocumentModal = !this.activeAddDocumentModal;
      if (this.activeAddDocumentModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    toggleEditDocumentModal(doc) {
      if (doc) {
        this.editDocumentForm = doc;
      }
      const body = document.querySelector('body');
      this.activeEditDocumentModal = !this.activeEditDocumentModal;
      if (this.activeEditDocumentModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    toggleUploadFileModal() {
      const body = document.querySelector('body');
      this.activeUploadFileModal = !this.activeUploadFileModal;
      if (this.activeUploadFileModal) {
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    updateDocument(payload, docID) {
      const path = `${API_URL}/documents/${docID}`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.put(path, payload, config)
          .then((res) => {
            this.getDocuments();
            if (res.data.status == 'success') {
              this.message = 'Document updated!';
            } else {
              this.message = 'Document not updated, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getDocuments();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
    truncate(value, length) {
      if (value.length > length) {
        return value.substring(0, length) + "...";
      } else {
        return value;
      }
    },
    addFile(e) {
      this.file = e.target.files[0];
    },
    handleFileUpload() {
      this.toggleUploadFileModal(null);
      const payload = {
        file: this.file,
      };
      this.uploadFile(payload);
    },
    uploadFile(payload) {
      const path = `${API_URL}/documents/upload_file`;

      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}`, }
        };

        axios.postForm(path, payload, config)
          .then((res) => {
            this.getDocuments();
            if (res.data.status == 'success') {
              this.message = 'Documents added!';
            } else {
              this.message = 'Documents not added, error occured';
            }
            this.showMessage = true;
          })
          .catch((error) => {
            console.error(error);
            this.getDocuments();
          });
      }).catch(function (error) {
        console.log(error)
      });
    },
  },
  created() {
    this.getDocuments();
  },
};
</script>
