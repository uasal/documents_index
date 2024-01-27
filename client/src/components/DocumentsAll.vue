<template>
  <div class="container">
    <div class="row">
      <div class="col-12">
        <h1>Documents</h1>
        <hr><br><br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" @click="toggleAddDocumentModal">
          Add Document
        </button>
        <div class="my-3">
          <input type="text" placeholder="Filter table by any column" v-model="filter" />
        </div>
        <table class="table table-hover" v-if="filteredDocuments.length > 0">
          <thead>
            <tr>
              <th style="min-width: 15%;" scope="col">Title</th>
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
                v-if="doc.title.length > 30"><a :href="'documents/' + doc.doc_identifier" target="_blank">{{
                  truncate(doc.title, 30) }}</a></td>
              <td v-else><a :href="'documents/' + doc.doc_identifier" target="_blank">{{ doc.title }}</a></td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.author" style="cursor: default"
                v-if="doc.author.length > 30">{{ truncate(doc.author, 30) }}</td>
              <td v-else>{{ doc.author }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.doc_identifier" style="cursor: default"
                v-if="doc.doc_identifier.length > 30">{{ truncate(doc.doc_identifier, 30) }}</td>
              <td v-else>{{ doc.doc_identifier }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.doc_code" style="cursor: default"
                v-if="doc.doc_code.length > 30">{{ truncate(doc.doc_code, 30) }}</td>
              <td v-else>{{ doc.doc_code }}</td>

              <a v-if="doc.compiled_url" :href="doc.compiled_url" target="_blank">document link</a>

              <a v-if="doc.source_url" :href="doc.source_url" target="_blank">source link</a>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.abstract" style="cursor: default"
                v-if="doc.abstract.length > 30">{{ truncate(doc.abstract, 30) }}</td>
              <td v-else>{{ doc.abstract }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.creator_email" style="cursor: default"
                v-if="doc.creator_email.length > 15">{{ truncate(doc.creator_email, 15) }}</td>
              <td v-else>{{ doc.creator_email }}</td>

              <td>
                <div class="btn-group" role="group">
                  <button type="button" class="btn btn-warning btn-sm" @click="toggleEditDocumentModal(doc)">
                    Update
                  </button>
                  <button type="button" class="btn btn-danger btn-sm" @click="handleDeleteDocument(doc)">
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else>
          <p v-if="filter === ''">No documents stored.</p>
          <p v-else>Sorry, no documents found containing <b>{{ filter }}</b>. Try a different filter.</p>
        </div>
      </div>
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
import AlertMessage from './AlertMessage.vue';

const API_URL = 'http://127.0.0.1:5001';

export default {
  name: 'DocumentsAll',
  data() {
    return {
      activeAddDocumentModal: false,
      activeEditDocumentModal: false,
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
    };
  },
  components: {
    alert: AlertMessage,
  },
  computed: {
    filteredDocuments() {
      if (this.filter === '') {
        return this.documents;
      } else {
        return this.documents.filter(doc => {
          const searchTerm = this.filter.toLowerCase();

          const title = doc.title ? doc.title.toString().toLowerCase() : doc.title;
          const author = doc.author ? doc.author.toString().toLowerCase() : doc.author;
          const doc_identifier = doc.doc_identifier ? doc.doc_identifier.toString().toLowerCase() : doc.doc_identifier;
          const doc_code = doc.doc_code ? doc.doc_code.toString().toLowerCase() : doc.doc_code;
          const compiled_url = doc.compiled_url ? doc.compiled_url.toString().toLowerCase() : doc.compiled_url;
          const source_url = doc.source_url ? doc.source_url.toString().toLowerCase() : doc.source_url;
          const abstract = doc.abstract ? doc.abstract.toString().toLowerCase() : doc.abstract;
          const creator_email = doc.creator_email ? doc.creator_email.toString().toLowerCase() : doc.creator_email;

          return (title && title.includes(searchTerm)) ||
            (author && author.includes(searchTerm)) ||
            (doc_identifier && doc_identifier.includes(searchTerm)) ||
            (doc_code && doc_code.includes(searchTerm)) ||
            (compiled_url && compiled_url.includes(searchTerm)) ||
            (source_url && source_url.includes(searchTerm)) ||
            (abstract && abstract.includes(searchTerm)) ||
            (creator_email && creator_email.includes(searchTerm));
        });
      }
    },
  },
  methods: {
    addDocument(payload) {
      const path = `${API_URL}/documents`;
      axios.post(path, payload)
        .then(() => {
          this.getDocuments();
          this.message = 'Document added!';
          this.showMessage = true;
        })
        .catch((error) => {
          console.log(error);
          this.getDocuments();
        });
    },
    getDocuments() {
      const path = `${API_URL}/documents`;
      axios.get(path)
        .then((res) => {
          this.documents = res.data.documents;
        })
        .catch((error) => {

          console.error(error);
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
      axios.delete(path)
        .then(() => {
          this.getDocuments();
          this.message = 'Document removed!';
          this.showMessage = true;
        })
        .catch((error) => {
          console.error(error);
          this.getDocuments();
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
    updateDocument(payload, docID) {
      const path = `${API_URL}/documents/${docID}`;
      axios.put(path, payload)
        .then(() => {
          this.getDocuments();
          this.message = 'Document updated!';
          this.showMessage = true;
        })
        .catch((error) => {
          console.error(error);
          this.getDocuments();
        });
    },
    truncate(value, length) {
      if (value.length > length) {
        return value.substring(0, length) + "...";
      } else {
        return value;
      }
    },
  },
  created() {
    this.getDocuments();
  },
};
</script>
