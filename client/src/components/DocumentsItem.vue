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
            <button v-else type="button" class="btn btn-outline-warning mb-3" data-toggle="tooltip" 
            data-placement="top" title="Notify maintainer that entry needs to be updated" @click="sendEmail(document)">
                <font-awesome-icon icon="fa-solid fa-circle-exclamation" class="me-1" />Notify maintainer
            </button>
            <div class="row">
                <div class="col-6">
                    <p><b>Author: </b>{{ document.author }}</p>
                    <p><b>Document identifier: </b>{{ document.doc_identifier }}</p>
                    <p><b>Document number: </b>{{ document.doc_code }}</p>
                    <p><b><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="URLInfo"/>URL: </b><font-awesome-icon v-if="document.compiled_url && document.compiled_url.toLowerCase().includes(gitLabANT)" icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="gitLabInfo"/><a :href=document.compiled_url target="_blank">{{ document.compiled_url }}</a></p>
                    <p><b><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="sourceURLInfo"/>Source URL: </b><font-awesome-icon v-if="document.source_url && document.source_url.toLowerCase().includes(gitLabANT)" icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="gitLabInfo"/><a :href=document.source_url target="_blank">{{ document.source_url }}</a></p>
                    <p><b>Document entry maintained by: </b>{{ document.creator_email }}</p>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <p>{{ document.abstract }}</p>
                </div>
            </div>
        </div>
        <div class="col-12" v-else>
            <h3>Sorry, you are not authorized to view this page.</h3>
            <p>If you think you should have access, please contact your project PI to request access.</p>
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
                                <label for="editDocumentDocCode" class="form-label">Doc # (optional):</label>
                                <input type="text" class="form-control" maxlength="30" id="editDocCode"
                                v-if="!editDocumentForm.doc_code || superuser"
                                v-model="editDocumentForm.doc_code" placeholder="Enter document number">
                                <input type="text" class="form-control-plaintext" maxlength="30" id="editDocCode"
                                v-else readonly 
                                v-model="editDocumentForm.doc_code">
                            </div>
                            <div class="mb-3">
                                <label for="editDocumentUrl" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="URLInfo"/>URL:</label>
                                <input type="text" class="form-control" maxlength="500" id="editUrl"
                                    v-model="editDocumentForm.compiled_url" placeholder="Enter URL">
                            </div>
                            <div class="mb-3">
                                <label for="editDocumentSourceUrl" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="sourceURLInfo"/>Source URL:</label>
                                <input type="text" class="form-control" maxlength="500" id="editSourceUrl"
                                    v-model="editDocumentForm.source_url" placeholder="Enter source URL">
                            </div>
                            <div class="mb-3" v-if="superuser">
                                <label for="editDocumentCreatedBy" class="form-label">Maintained By (superuser field):</label>
                                <input type="text" class="form-control" id="editCreatedBy" v-model="editDocumentForm.creator_email"
                                placeholder="Enter Maintainer Email">
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

// const API_URL = '/api';
const API_URL = 'http://localhost:5001/api';

export default {
    name: 'DocumentsItem',
    data() {
        return {
            activeEditDocumentModal: false,
            document: {},
            admins: [],            
            editDocumentForm: {
                pk: '',
                title: '',
                author: '',
                doc_identifier: '',
                doc_code: '',
                compiled_url: '',
                source_url: '',
                creator_email: '',                
                abstract: '',
            },
            URLInfo: 'The URL of the file described by the metadata in this entry.',
            sourceURLInfo: '(optional) The URL of the source components (Git repository, Power Point presentation etc.) used to compile / build the file described by the metadata in this entry.',            
            gitLabInfo: 'This URL requires the ANT VPN to be activated.',
            gitLabANT: 'gitlab.sc.ascendingnode.tech',
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
        getAdmins() {
            const path = `${API_URL}/admins`;
            auth.currentUser.getIdToken(true).then(idToken => {
                const config = {
                headers: { Authorization: `${idToken}` }
                };

                axios.get(path, config)
                .then((res) => {
                    this.admins = res.data.admins;
                })
                .catch((error) => {
                    console.error(error);
                });
            }).catch(function (error) {
                console.log(error)
            });
        },        
        handleEditCancel() {
            this.toggleEditDocumentModal(null);
            this.initForm();
            this.getDocument(); // initForm sets values of doc to empty, so repopulate them
        },
        handleEditSubmit() {
            this.toggleEditDocumentModal(null);
            const payload = {
                title: this.editDocumentForm.title,
                author: this.editDocumentForm.author,
                doc_code: this.editDocumentForm.doc_code,
                compiled_url: this.editDocumentForm.compiled_url,
                source_url: this.editDocumentForm.source_url,
                creator_email: this.editDocumentForm.creator_email || this.email,                  
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
            this.editDocumentForm.creator_email = '';            
            this.editDocumentForm.abstract = '';
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
        sendEmail(doc) {
            // alert(`Sending email to ${doc.creator_email}`);
            const emailSubject = encodeURIComponent(`Teledocs Alert: Document '${doc.title}' is out of date`);
            const emailBody = encodeURIComponent(`Hi,\n\n
This is to inform you that the document '${doc.title}' was reported as being out of date. The data currently associated with it is:\n
Title: ${doc.title}\n
Author: ${doc.author}\n
URL: ${doc.compiled_url}\n
Source URL: ${doc.source_url}\n
Abstract: ${doc.abstract}\n\n
Please update the entry at your earliest convenience.\n\nRegards,\nteledocs`);
            const emailCC = this.admins.join(', ');
            const mailtoUrl = `mailto:${doc.creator_email}?cc=${emailCC}&subject=${emailSubject}&body=${emailBody}`;

            // Create a hidden <a> element (otherwise you need to use window.open and that opens a new tab)
            const hiddenLink = document.createElement('a');
            hiddenLink.href = mailtoUrl;

            // Trigger click on the hidden <a> element
            hiddenLink.style.display = 'none';
            document.body.appendChild(hiddenLink);
            hiddenLink.click();
            document.body.removeChild(hiddenLink);
        },        
    },
    created() {
        this.getDocument();
        this.getAdmins();
    },
};
</script>
