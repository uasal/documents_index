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
            <button v-else type="button" class="btn btn-outline-primary mb-3" data-toggle="tooltip" 
            data-placement="top" title="Notify maintainer that entry needs to be updated" @click="sendEmail(document)">
                <font-awesome-icon icon="fa-solid fa-circle-exclamation" class="me-1" />Notify maintainer
            </button>
            <div class="row">
                <div class="col-6">
                    <p><b>Author: </b>{{ document.author }}</p>
                    <p><b>Identifier: </b>{{ document.doc_identifier }}</p>
                    <p><b>Number: </b>
                        <a v-if="document.number" :href="'/demo/docs/' + document.number.value" target="_blank" class="d-block">{{ document.number.value }}</a>
                    </p>
                    <p v-if="document.aliases"><b>Other handles: </b>
                        <a v-for="(alias, index) in document.aliases" :key="index" :href="'/demo/docs/' + alias.value" target="_blank" class="d-block">{{ alias.value }}</a>
                    </p>
                    <p><b>Type: </b><font-awesome-icon v-if="entryTypeIconMap[document.entry_type]" :icon="entryTypeIconMap[document.entry_type]" data-toggle="tooltip" data-placement="bottom" :title="document.entry_type" class="text-secondary" /></p>
                    <p><b>Change controlled: </b> {{ changeControlledValueMap[document.change_controlled] }}</p>
                    <p><b><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="URLInfo"/>URL: </b><font-awesome-icon v-if="document.compiled_url && document.compiled_url.toLowerCase().includes(gitLabANT)" icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="gitLabInfo"/><a :href=document.compiled_url target="_blank">{{ document.compiled_url }}</a></p>
                    <p><b><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="sourceURLInfo"/>Source URL: </b><font-awesome-icon v-if="document.source_url && document.source_url.toLowerCase().includes(gitLabANT)" icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="gitLabInfo"/><a :href=document.source_url target="_blank">{{ document.source_url }}</a></p>
                    <p><b>Entry maintained by: </b>{{ document.creator_email }}</p>
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
        
        <div v-if="hideContent">Sorry, this page is not available or you are not authorized to view it.</div>

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
                        <label for="editDocumentEntryType" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="DisabledInfo"/>Type:</label>
                        <select class="form-control" id="editDocumentEntryType" v-model="editDocumentForm.entry_type" disabled>
                            <option v-for="option in entryTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="editDocumentChangeControlled" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="DisabledInfo"></font-awesome-icon>Change Controlled:</label>
                        <select class="form-control" id="editDocumentChangeControlled" v-model="editDocumentForm.change_controlled" disabled>
                            <option v-for="option in changeControlledOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                        </select>
                    </div>
                    <div v-if="docModal && docModal.number" class="mb-3">
                        <label for="editDocumentDocCode" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="DisabledInfo"></font-awesome-icon>Number:</label>
                        <input type="text" class="form-control mt-2" id="editDocumentDocCode" v-model="editDocumentForm.number" readonly />
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
                        <textarea class="form-control" id="editAbstract" rows="3" v-model="editDocumentForm.abstract"
                        placeholder="Enter abstract"></textarea>
                    </div>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-primary btn-sm" @click="handleEditSubmit"
                            :disabled="!builderComplete && (editDocumentForm.change_controlled === 10) && (editDocumentForm.entry_type === 'drawing')">
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
import DrawingCodeBuilder from './DrawingCodeBuilder.vue';

const API_URL = '/api/demo';
// const API_URL = 'http://localhost:5001/api/demo';

export default {
    name: 'DocumentsItem',
    data() {
        return {
            activeEditDocumentModal: false,
            document: {},
            admins: [],
            codeStepsDrawing: [
                {
                label: 'Category:',
                options: [
                    { label: 'Telescope', value: 'TEL' },
                    { label: 'Analyses', value: 'A' },
                    { label: 'Spacecraft Bus', value: 'BUS' },
                    { label: 'Interface Control Drawing', value: 'ICD' },
                    ]
                },
                {
                label: 'Assembly:',
                options: {
                    PRL_TEL: [
                    { label: 'Aft Optics Aseembly', value: 'AOA' },
                    { label: 'Fore Optics Assembly', value: 'FOA' },
                    { label: 'Interface Control Drawing', value: 'ICD' },
                    ], 
                }
                },
                {
                label: 'Main Element:',
                options: {
                    PRL_TEL_ICD: [
                    { label: 'Interface Control Drawing', value: '00' },
                    { label: 'Telescope-BUS ICD', value: '01' },
                    { label: 'Telescope Optical Definition', value: '02' },
                    ],
                    PRL_TEL_FOA: [
                    { label: 'Top Level Assembly', value: 'ASY' },
                    { label: 'COTS Parts', value: 'COT' },
                    { label: 'Electrical (not in IBS, M1S, etc.)', value: 'ELE' },
                    { label: 'Ground Support Equipment', value: 'GSE' },
                    { label: 'Inner Baffle System', value: 'IBS' },
                    { label: 'Interface Control Drawing', value: 'ICD' },
                    { label: 'Primary Mirror System', value: 'M1S' },
                    { label: 'Secondary Mirror System', value: 'M2S' },
                    ],
                    PRL_TEL_AOA: [
                    { label: 'Piece Parts', value: '9' },
                    { label: 'Coronagraph', value: 'ESC' },
                    { label: 'Interface Control Drawing', value: 'ICD' },
                    { label: 'IR Spectograph', value: 'IFS' },
                    { label: 'Optics', value: 'OPT' },
                    { label: 'Scrappy', value: 'SCR' },
                    { label: 'Structure', value: 'STC' },
                    { label: 'Shack-Hartmann Wavefront Sensor', value: 'SWS' },
                    { label: 'UV Spectograph', value: 'UVS' },
                    { label: 'Context Camera Assembly', value: 'WCC' },
                    ],
                }
                },
                {
                label: 'Sub Element:',
                options: {
                    // PRL_TEL_FOA_ASY: [
                    //   { label: 'ASY Subasssembly', value: '00' },
                    //   ],
                    PRL_TEL_FOA_COT: [
                    { label: 'COT Subasssembly', value: '00' },
                    { label: 'COT Electrical - Subasssembly', value: '10' },
                    { label: 'COT Electrical - Part', value: '11' },
                    { label: 'COT Mechanical - Subasssembly', value: '30' },
                    { label: 'COT Mechanical - Part', value: '31' },
                    ],
                    PRL_TEL_FOA_ELE: [
                    { label: 'ELE Subassembly', value: '00' },
                    { label: 'ELE Thermal Control - Subassembly', value: '10' },
                    { label: 'ELE Thermal Control - Part', value: '11' },
                    { label: 'ELE Hardware & Cabling - Subassembly', value: '20' },
                    { label: 'ELE Hardware & Cabling - Part', value: '21' },
                    { label: 'ELE Other - Subassembly', value: '30' },
                    { label: 'ELE Other - Part', value: '31' },
                    ],
                    PRL_TEL_FOA_GSE: [
                    { label: 'GSE Subassembly', value: '10' },
                    { label: 'GSE Part', value: '11' },
                    ],
                    PRL_TEL_FOA_IBS: [
                    { label: 'IBS Subassembly', value: '00' },
                    { label: 'IBS Thermal Control - Subassembly', value: '10' },
                    { label: 'IBS Thermal Control - Part', value: '11' },
                    { label: 'IBS Hardware & Cabling - Subassembly', value: '20' },
                    { label: 'IBS Hardware & Cabling - Part', value: '21' },
                    { label: 'IBS Inner Baffle - Subassembly', value: '30' },
                    { label: 'IBS Inner Baffle - Part', value: '31' },
                    ],
                    // PRL_FOA_ICD: [
                    //   { label: 'Interface Control Drawing', value: '00' },
                    // ],
                    PRL_TEL_FOA_M1S: [
                    { label: 'M1S Subassembly', value: '00' },
                    { label: 'M1S Thermal Control - Subassembly', value: '10' },
                    { label: 'M1S Thermal Control - Part', value: '11' },
                    { label: 'M1S Hardware & Cabling - Subassembly', value: '20' },
                    { label: 'M1S Hardware & Cabling - Part', value: '21' },
                    { label: 'M1S Mirror - Subassembly', value: '30' },
                    { label: 'M1S Mirror - Part', value: '31' },
                    ],
                    PRL_TEL_FOA_M2S: [
                    { label: 'M2S Subassembly', value: '00' },
                    { label: 'M2S Thermal Control - Subassembly', value: '10' },
                    { label: 'M2S Thermal Control - Part', value: '11' },
                    { label: 'M2S Hardware & Cabling - Subassembly', value: '20' },
                    { label: 'M2S Hardware & Cabling - Part', value: '21' },
                    { label: 'M2S Mirror - Subassembly', value: '30' },
                    { label: 'M2S Mirror - Part', value: '31' },
                    { label: 'M2S Hub - Subassembly', value: '40' },
                    { label: 'M2S Hub - Part', value: '41' },
                    { label: 'M2S Tripod - Subassembly', value: '50' },
                    { label: 'M2S Tripod - Part', value: '51' },
                    ],
                    PRL_TEL_FOA_PMS: [
                    { label: 'PMS Subassembly', value: '00' },
                    { label: 'PMS Thermal Control - Subassembly', value: '10' },
                    { label: 'PMS Thermal Control - Part', value: '11' },
                    { label: 'PMS Hardware & Cabling - Subassembly', value: '20' },
                    { label: 'PMS Hardware & Cabling - Part', value: '21' },
                    { label: 'PMS PMSS - Subassembly', value: '30' },
                    { label: 'PMS PMSS - Part', value: '31' },
                    { label: 'PMS Hardpoint - Subassembly', value: '40' },
                    { label: 'PMS Hardpoint - Part', value: '41' },
                    { label: 'PMS Actuator - Subassembly', value: '50' },
                    { label: 'PMS Actuator - Part', value: '51' },
                    ],
                    // PRL_TEL_AOA_9: [
                    //   { label: 'Piece Parts', value: '00' },
                    // ],
                    // PRL_TEL_AOA_ESC: [
                    //   { label: 'Coronagraph', value: '00' },
                    // ],
                    PRL_TEL_AOA_ICD: [
                    { label: 'Mechanical ICD', value: '10' },
                    { label: 'UV Spectograph ICD', value: '31' },
                    { label: 'Mechanical ICD', value: '32' },
                    ],
                    // PRL_TEL_AOA_IFS: [
                    //   { label: 'IR Spectograph', value: '00' },
                    // ],
                    PRL_TEL_AOA_OPT: [
                    { label: 'M4 Tripod Assembly', value: '1' },
                    { label: 'M3 Assembly', value: '2' },
                    ],
                    PRL_TEL_AOA_SCR: [
                    { label: 'Scrappy', value: '1' },
                    ],
                    PRL_TEL_AOA_STC: [
                    { label: 'Piece Parts', value: '9' },
                    { label: 'AOA Horizontal Handling Fixture', value: 'G1' },
                    { label: 'AOA Breakover Fixture', value: 'G11' },
                    { label: 'AOA Primary Structure Analysis', value: 'A1' },
                    ],
                    // PRL_TEL_AOA_SWS: [
                    //   { label: 'Shack-Hartmann Wavefront Sensor', value: '00' },
                    // ],
                    // PRL_TEL_AOA_UVS: [
                    //   { label: 'UV Spectograph', value: '00' },
                    // ],
                    PRL_TEL_AOA_WCC: [
                    { label: 'Context Camera Assembly', value: '1' },
                    { label: 'Context Camera Deployable Cover Assembly', value: '2' },
                    ],
                },
                },
            ],
            builderComplete: false,
            builderKey: 0,
            editDocumentForm: {
                pk: '',
                title: '',
                author: '',
                doc_identifier: '',
                number: '',
                entry_type: '',
                change_controlled: '',
                compiled_url: '',
                source_url: '',
                creator_email: '',                
                abstract: '',
            },
            docModal: null,
            DisabledInfo: 'Field can only be edited from the main Documents & Drawing page',
            URLInfo: 'The URL of the file described by the metadata in this entry.',
            sourceURLInfo: '(optional) The URL of the source components (Git repository, Power Point presentation etc.) used to compile / build the file described by the metadata in this entry.',            
            gitLabInfo: 'This URL requires the ANT VPN to be activated.',
            gitLabANT: 'gitlab.sc.ascendingnode.tech',
            message: '',
            showMessage: false,
            isAuthorized: false,
            hideContent: false,
            superuser: false,
            entryTypeOptions: [],
            entryTypeIconMap: {},
            changeControlledOptions: [],
            changeControlledValueMap: {},
        };
    },
    components: {
        alert: AlertMessage,
        DrawingCodeBuilder: DrawingCodeBuilder,
    },
    watch: {
        'editDocumentForm.change_controlled'(newVal) {
            // Reset only if type drawing, otherwise we don't really care
            if (newVal === 0) {
                this.editDocumentForm.number = this.resetEditNumber();
            };

            if (newVal === 10) {
                this.resetDrawingCodeBuilder();
            };
        },
        'editDocumentForm.entry_type'(newVal, oldVal) {
            this.resetDrawingCodeBuilder();
        },
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
                        this.hideContent = !this.isAuthorized;
                    });
            }).catch(function (error) {
                console.log(error)
                this.superuser = false;
                this.isAuthorized = false;
                this.hideContent = true;
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
                number: this.editDocumentForm.number,
                entry_type: this.editDocumentForm.entry_type,
                change_controlled: this.editDocumentForm.change_controlled,
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
            this.editDocumentForm.number = '';
            this.editDocumentForm.entry_type = '';
            this.editDocumentForm.change_controlled = '';
            this.editDocumentForm.compiled_url = '';
            this.editDocumentForm.source_url = '';
            this.editDocumentForm.creator_email = '';            
            this.editDocumentForm.abstract = '';
            this.docModal = null;
        },
        handleEditCodeComplete(code) {
            this.editDocumentForm.number = code;
            this.builderComplete = true;
        },
        handleEditPartialCodeUpdate(partialCode) {
            this.editDocumentForm.number = partialCode;
        },
        handleEditCodeReset() {
            // Reset document code on builder reset
            this.editDocumentForm.number = this.resetEditNumber();
            this.builderComplete = false;
        },
        resetDrawingCodeBuilder() {
            this.editDocumentForm.number = this.resetEditNumber();
            this.builderComplete = false;
            // Change the key to force a re-render of DrawingCodeBuilder
            this.builderKey++;
        },
        resetEditNumber() {
            if (this.docModal) {
                if ( this.editDocumentForm.entry_type === this.docModal.entry_type ) {
                    return this.docModal.number && this.docModal.number.value || "";
                } else {
                    return "";
                }
            } else {
                return "";
            }
        },
        toggleEditDocumentModal(doc) {
            if (doc) {
                this.editDocumentForm = { ...doc };
                this.editDocumentForm.entry_type = doc.entry_type;
                this.editDocumentForm.change_controlled = doc.change_controlled;
                this.editDocumentForm.number = (doc.number && doc.number.value);
                this.docModal = doc;
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
        getEntryTypeOptions() {
            const path = `${API_URL}/../entry_types`;
            auth.currentUser.getIdToken(true).then(idToken => {
            const config = {
                headers: { Authorization: `${idToken}` }
            };

            axios.get(path, config)
                .then((res) => {
                    this.entryTypeOptions = res.data.entry_types;
                    this.entryTypeIconMap = this.entryTypeOptions.reduce((map, option) => {
                        map[option.value] = option.icon;
                        return map;
                    }, {});
                })
                .catch((error) => {
                    console.error(error);
                    this.superuser = false;
                    this.isAuthorized = error.response.data.isAuthorized;
                });
            }).catch(function (error) {
                console.log(error)
                this.superuser = false;
                this.isAuthorized = false;
            });
        },
        getChangeControlledOptions() {
            const path = `${API_URL}/../change_controlled_types`;
            auth.currentUser.getIdToken(true).then(idToken => {
            const config = {
                headers: { Authorization: `${idToken}` }
            };

            axios.get(path, config)
                .then((res) => {
                this.changeControlledOptions = res.data.change_controlled_types;
                this.changeControlledValueMap = this.changeControlledOptions.reduce((map, option) => {
                    map[option.value] = option.label;
                    return map;
                }, {});
                })
                .catch((error) => {
                console.error(error);
                this.superuser = false;
                this.isAuthorized = error.response.data.isAuthorized;
                });
            }).catch(function (error) {
                console.log(error)
                this.superuser = false;
                this.isAuthorized = false;
            });
        },    
    },
    created() {
        this.getDocument();
        this.getAdmins();
        this.getEntryTypeOptions();
        this.getChangeControlledOptions();
    },
};
</script>