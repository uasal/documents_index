<template>
    <div class="container">
        <div v-if="isAuthorized">
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
            <button v-if="(email == document.creator_email) || superuser" type="button" class="btn btn-warning btn-sm mb-3"
                @click="toggleEditDocumentModal(document)">
                Update
            </button>
            <div class="row">
                <div class="col-6">
                    <p><b>Author: </b>{{ document.author }}</p>
                    <p><b>Document identifier: </b>{{ document.doc_identifier }}</p>
                    <p><b>Document code: </b>{{ document.doc_code }}</p>
                    <p><b>Compiled URL: </b><a :href=document.compiled_url target="_blank">{{ document.compiled_url }}</a>
                    </p>
                    <p><b>Source URL: </b><a :href=document.source_url target="_blank">{{ document.source_url }}</a></p>
                    <p><b>Document entry created by: </b>{{ document.creator_email }}</p>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <p>{{ document.abstract }}</p>
                </div>
            </div>
        </div>
        <!-- <div v-if="hideContent">Sorry, this page is not available or you are not authorized to view it.</div> -->

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
                                <input type="text" class="form-control" maxlength="500" id="editDocumentTitle"
                                    v-model="editDocumentForm.title" placeholder="Enter title">
                            </div>
                            <div class="mb-3">
                                <label for="editDocumentAuthor" class="form-label">Author:</label>
                                <input type="text" class="form-control" maxlength="500" id="editDocumentAuthor"
                                    v-model="editDocumentForm.author" placeholder="Enter author">
                            </div>
                            <div class="mb-3">
                                <label for="editDocumentDocCode" class="form-label">Doc Code (optional):</label>
                                <input type="text" class="form-control" maxlength="10" id="editDocCode"
                                    v-model="editDocumentForm.doc_code" placeholder="Enter document code">
                            </div>
                            <div class="mb-3">
                                <label for="editDocumentCompiledUrl" class="form-label">Compiled URL:</label>
                                <input type="text" class="form-control" maxlength="500" id="editCompiledUrl"
                                    v-model="editDocumentForm.compiled_url" placeholder="Enter compiled URL">
                            </div>
                            <div class="mb-3">
                                <label for="editDocumentSourceUrl" class="form-label">Source URL:</label>
                                <input type="text" class="form-control" maxlength="500" id="editSourceUrl"
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
import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { auth } from '../firebaseConfig';
import AlertMessage from './AlertMessage.vue';

const API_URL = '/api';
// const API_URL = 'http://localhost:5001/api';

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
            isAuthorized: false,
            // hideContent: false,
            superuser: false,
        };
    },
    components: {
        alert: AlertMessage,
    },
    computed: {
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
                    //   const credential = GoogleAuthProvider.credentialFromResult(result);
                    //   this.token = credential.accessToken;
                    //   // The signed-in user info.
                    //   this.username = result.user.displayName;
                    //   this.email = result.user.email;
                })
                .catch(err => {
                    console.log(`Error during sign in: ${err.message}`);
                    window.alert(`Sign in failed. Retry or check your browser logs.`);
                });
        },
        getDocument() {
            const path = `${API_URL}/documents/${this.$route.params.docID}`;

            auth.currentUser.getIdToken(true).then(idToken => {
                const config = {
                    headers: { Authorization: `${idToken}` }
                };

                axios.get(path, config)
                    .then((res) => {
                        this.document = res.data.document;
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

            auth.currentUser.getIdToken(true).then(idToken => {
                const config = {
                    headers: { Authorization: `${idToken}` }
                };
                axios.put(path, payload, config)
                    .then((res) => {
                        this.getDocument();
                        if (res.data.status == 'success') {
                            this.message = 'Document updated!';
                        } else {
                            this.message = 'Document not updated, error occured';
                        }
                        this.showMessage = true;
                    })
                    .catch((error) => {
                        console.error(error);
                        this.getDocument();
                    });
            }).catch(function (error) {
                console.log(error)
            });
        },
    },
    created() {
        this.getDocument();
    },
};
</script>
