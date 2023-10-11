<template>
    <div class="container">
        <div class="row">
            <div class="col-12">
                <div class="h1">
                    <!-- <a class="me-3" href="/"><font-awesome-icon icon="fa-solid fa-circle-arrow-left" size="sm" /></a> -->
                    <span>{{ document.title }}</span>
                </div>
                <hr><br><br>
            </div>
        </div>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-warning btn-sm mb-3" @click="toggleEditDocumentModal(document)">
            Update
        </button>
        <div class="row">
            <div class="col-6">
                <p><b>Author: </b>{{ document.author }}</p>
                <p><b>Document identifier: </b>{{ document.doc_identifier }}</p>
                <p><b>Document code: </b>{{ document.doc_code }}</p>
                <p><b>Compiled URL: </b><a :href=document.compiled_url target="_blank">{{ document.compiled_url }}</a></p>
                <p><b>Source URL: </b><a :href=document.source_url target="_blank">{{ document.source_url }}</a></p>
            </div>
        </div>
        <div class="row">
            <div class="col-12">
                <p>{{ document.abstract }}</p>
            </div>
        </div>

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
                                <textarea class="form-control" id="editAbstract" rows="3"
                                    v-model="editDocumentForm.abstract" placeholder="Enter abstract"></textarea>
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
    name: 'DocumentsItem',
    data() {
        return {
            activeEditDocumentModal: false,
            document: {},
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
    methods: {
        getDocument() {
            const path = `${API_URL}/documents/${this.$route.params.docID}`;
            axios.get(path)
                .then((res) => {
                    this.document = res.data.document;
                })
                .catch((error) => {

                    console.error(error);
                });
        },
        handleEditCancel() {
            this.toggleEditDocumentModal(null);
            this.initForm();
            this.getDocument(); // why?
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
            this.editDocumentForm.pk = '';
            this.editDocumentForm.title = '';
            this.editDocumentForm.author = '';
            this.editDocumentForm.doc_identifier = '';
            this.editDocumentForm.doc_code = '';
            this.editDocumentForm.compiled_url = '';
            this.editDocumentForm.source_url = '';
            this.editDocumentForm.abstract = '';
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
                    this.getDocument();
                    this.message = 'Document updated!';
                    this.showMessage = true;
                })
                .catch((error) => {
                    console.error(error);
                    this.getDocument();
                });
        },
    },
    created() {
        this.getDocument();
    },
};
</script>
