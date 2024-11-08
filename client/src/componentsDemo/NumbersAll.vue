<template>
  <div class="container">
    <div class="row">
      <div class="col-12" v-if="isAuthorized">
        <div class="row">
          <div>
            <div class="d-inline-flex float-start">
              <h1>Assigned Numbers</h1>
            </div>
            <div class="d-inline-flex float-end">
              <a role="button" class="btn btn-primary me-4" href="/demo/" target="_blank">View Documents and Diagrams</a>
            </div>
          </div>
        </div>
        <hr><br><br>
        <div class="row">
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
          <!-- <p>If you encounter a problem, please contact one of teledoc's admins at:
            <span v-for="(admin, index) in admins" :key="index">
              <a :href="`mailto:${admin}`">{{ admin }}</a>{{ index !== admins.length - 1 ? ', ' : '.' }}
            </span>
          </p> -->
        </div>
        <br>
        <alert :message=message v-if="showMessage"></alert>

        <!-- <div class="row row-cols-auto mb-4" style="margin-left: initial;margin-right: initial;"> -->

          <!-- Filter toggle button -->
          <!-- <button v-if="show_table" type="button" class="btn btn-primary btn-sm ms-4" :title="filterButtonText" @click="toggleAdvancedFilter">
            <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="showFilters"/>
            <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="!showFilters"/>
          </button> -->

          <!-- General Filter -->
          <!-- <div class="ps-0">
            <input v-if="!showFilters" type="text" class="form-control" v-model="filter" placeholder="Search across all columns"/>
            <input v-if="showFilters" type="text" class="form-control invisible"/>
          </div>

        </div> -->

        <!-- Advanced Filter Fields -->
        <transition name="slide">
          <div class="container mt-3 mb-5" v-if="showFilters">
            <div class="row row-cols-auto">
              <div class="col mb-3">
                <!-- <label for="columnFiltersTitle" class="form-label">Title:</label> -->
                <input type="text" class="form-control" id="columnFiltersTitle" v-model="columnFilters.title" placeholder="Filter by Title">           
              </div>          
              <div class="col mb-3">
                <!-- <label for="columnFiltersAuthor" class="form-label">Author:</label> -->
                <input type="text" class="form-control" id="columnFiltersAuthor" v-model="columnFilters.author" placeholder="Filter by Author">
              </div>             
              <div class="col mb-3">
                <!-- <label for="columnFiltersAuthor" class="form-label">Doc Identifier:</label> -->
                <input type="text" class="form-control" id="columnFiltersDocIdentifier" v-model="columnFilters.doc_identifier" placeholder="Filter by Identifier">                            
              </div>             
              <div class="col mb-3">
                <!-- <label for="columnFiltersDocNb" class="form-label">Doc #:</label> -->
                <input type="text" class="form-control" id="columnFiltersDocNb" v-model="columnFilters.doc_code" placeholder="Filter by #">
              </div>             
              <div class="col mb-3">
                <select class="form-control" id="columnFiltersEntryType" v-model="columnFilters.entry_type">
                  <option value="">All Types</option> <!-- Option to clear the filter -->
                  <option v-for="option in entryTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>             
              <div class="col mb-3">
                <select class="form-control" id="columnFiltersChangeControlled" v-model="columnFilters.change_controlled">
                  <option value="">All Change Control Levels</option> <!-- Option to clear the filter -->
                  <option v-for="option in changeControlledOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>             
              <div class="col mb-3">
                <!-- <label for="columnFiltersURL" class="form-label">URL:</label> -->
                <input type="text" class="form-control" id="columnFiltersURL" v-model="columnFilters.compiled_url" placeholder="Filter by URL">
              </div>             
              <div class="col mb-3">
                <!-- <label for="columnFiltersSourceURL" class="form-label">Source URL:</label> -->
                <input type="text" class="form-control" id="columnFiltersSourceURL" v-model="columnFilters.source_url" placeholder="Filter by Source URL">
              </div>             
              <div class="col mb-3">
                <!-- <label for="columnFiltersAbstract" class="form-label">Abstract:</label> -->
                <input type="text" class="form-control" id="columnFiltersAbstract" v-model="columnFilters.abstract" placeholder="Filter by Abstract">
              </div>             
              <div class="col mb-3">
                <!-- <label for="columnFiltersCreatorEmail" class="form-label">Maintainer Email:</label> -->
                <input type="text" class="form-control" id="columnFiltersCreatorEmail" v-model="columnFilters.creator_email" placeholder="Filter by Maintainer Email">
              </div>         
            </div>    
            <div class="row row-cols-auto" style="margin-left: 0.1rem;">
              <button type="button" class="col btn btn-primary btn-sm" @click="resetFilters">Reset Filters</button>            
            </div>
          </div>
        </transition>

        <!-- Toggle Button to Switch Between Documents and Diagrams -->
        <div class="form-check form-switch mb-3">
          <input
            class="form-check-input"
            type="checkbox"
            id="toggleSwitch"
            v-model="showDocumentsOnly"
          />
          <label class="form-check-label" for="toggleSwitch">
            {{ showDocumentsOnly ? "Showing Documents" : "Showing Diagrams" }}
          </label>
        </div>

        <table class="table table-hover" v-if="show_table">
          <thead>
            <tr>
              <th @click='sortColumn("doc_code")' style="min-width: 10%;" scope="col">
                {{ showDocumentsOnly ? 'Document Number' : 'Drawing Number' }}
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='doc_code' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='doc_code' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("assembly")' style="min-width: 10%;" scope="col">Assembly
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='assembly' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='assembly' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("doc_identifier")' style="min-width: 10%;" scope="col">Associated Identifier
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='doc_identifier' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='doc_identifier' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("title")' style="min-width: 10%;" scope="col">Title
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='title' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='title' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("author")' style="min-width: 10%;" scope="col">Author
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='author' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='author' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("creator_email")' style="min-width: 10%;" scope="col">Maintained By
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='creator_email' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='creator_email' && this.sortOrder==-1"/>                
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in filteredNumbers" :key="entry.doc_code">
              <td>{{ entry.doc_code }}</td>
              <td>{{ entry.assembly }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="entry.doc_identifier" style="cursor: default"
                v-if="entry.doc_identifier.length > 30">
                <a :href="'docs/' + entry.doc_identifier" target="_blank">{{
                  truncate(entry.doc_identifier, 30) }}</a>
              </td>
              <td v-else><a :href="'docs/' + entry.doc_identifier" target="_blank">{{ entry.doc_identifier }}</a></td>

              <td data-toggle="tooltip" data-placement="bottom" :title="entry.title" style="cursor: default"
                v-if="entry.title.length > 30">
                <a :href="'docs/' + entry.doc_identifier" target="_blank">{{
                  truncate(entry.title, 30) }}</a>
              </td>
              <td v-else><a :href="'docs/' + entry.doc_identifier" target="_blank">{{ entry.title }}</a></td>

              <td data-toggle="tooltip" data-placement="bottom" :title="entry.author" style="cursor: default"
                v-if="entry.author.length > 30">{{ truncate(entry.author, 30) }}</td>
              <td v-else>{{ entry.author }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="entry.creator_email" style="cursor: default"
                v-if="entry.creator_email.length > 15">{{ truncate(entry.creator_email, 15) }}</td>
              <td v-else>{{ entry.creator_email }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else>
          <p v-if="filter === ''">No numbers stored.</p>
          <p v-else>Sorry, no numbers found containing <b>{{ filter }}</b>. Try a different filter.</p>
        </div>
      </div>
      <div class="col-12" v-else>
        <h3>Sorry, you are not authorized to view this page.</h3>
        <p>If you think you should have access, please contact your project PI to request access.</p>
      </div>    
      <!-- <div v-if="hideContent">Sorry, this page is not available or you are not authorized to view it.</div> -->
    </div>
  </div>
</template>

<style>
  .form-check-input:not(:checked) {
    background-color: #198754;
    border-color: #198754 !important;
  }

  .form-check-input, .form-check-input:focus {
    box-shadow: none !important;
  }

  .form-check-input:active {
    filter: brightness(100%) !important;
  }
</style>

<script>

import axios from 'axios';
import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { auth } from '../firebaseConfig';
import ExcelJS from 'exceljs';
import AlertMessage from './AlertMessage.vue';
import DocumentCodeBuilder from './DocumentCodeBuilder.vue';

const API_URL = '/api/demo';
// const API_URL = 'http://localhost:5001/api/demo';

export default {
  name: 'NumbersAll',
  data() {
    return {
      showFilters: false,
      filterButtonText: 'Advanced Filter',      
      columnFilters: {
        doc_code: '',
        assembly: '',
        doc_identifier: '',
        title: '',
        author: '',
        creator_email: ''
      },
      filter: '',
      numbers: [
        { doc_code: 'PRL-TEL-FOA-DOC-00001', assembly: 'FOA', doc_identifier: 'stp202310_0001', title: 'Test doc updated', author: 'Me Me', creator_email: 'istefan@arizona.edu' },
        { doc_code: 'PRL-TEL-FOA-DOC-00002', assembly: 'FOA', doc_identifier: 'stp202310_0003', title: "Some test with an extremely long name that I can't imagine would be possible but I should test since", author: 'Me Me', creator_email: 'istefan@arizona.edu' },
        { doc_code: 'PRL-TEL-AOA-DOC-00001', assembly: 'AOA', doc_identifier: 'stp202310_0006', title: 'An interesting title', author: 'Me Me', creator_email: 'istefan@arizona.edu' },
        { doc_code: 'PRL-TEL-AOA-DOC-00002', assembly: 'AOA', doc_identifier: 'stp202310_0007', title: 'A test', author: 'Another author', creator_email: 'author@arizona.edu' },
        { doc_code: 'PRL-TEL-FOA-ASY-0001', assembly: 'FOA', doc_identifier: 'stp202310_0004', title: 'My test', author: 'Me Me', creator_email: 'istefan@arizona.edu' },
        { doc_code: 'PRL-TEL-FOA-GSE-1101', assembly: 'FOA', doc_identifier: 'stp202411_0001', title: 'Drawing1', author: 'Diagram Author', creator_email: 'istefan@arizona.edu' },
        { doc_code: 'PRL-TEL-FOA-PMS-0001', assembly: 'FOA', doc_identifier: 'stp202411_0002', title: 'FOA Drawing', author: 'Another Author', creator_email: 'istefan@arizona.edu' },
        { doc_code: 'PRL-TEL-AOA-ESC-0001', assembly: 'AOA', doc_identifier: 'stp202411_0003', title: 'AOA Drawing', author: 'Drawing Author', creator_email: 'istefan@arizona.edu' },
        { doc_code: 'PRL-TEL-AOA-OPT-2001', assembly: 'AOA', doc_identifier: 'stp202411_0004', title: 'Drawing2', author: 'Author Author', creator_email: 'istefan@arizona.edu' },
      ],
      // admins: [],
      show_table: true,
      showDocumentsOnly: true,
      message: '',
      showMessage: false,
      isAuthorized: true,
      // hideContent: false,
      superuser: false,
      sortBy: "doc_code",
      sortOrder: -1,
      entryTypeOptions: [],
      entryTypeIconMap: {},
      entryTypeDefault: null,
    };
  },
  components: {
    alert: AlertMessage,
  },
  watch: {
    numbers: function (newVal, oldVal) {
      if (this.numbers.length > 0) {
        this.show_table = true;
      } else {
        this.show_table = false;
      }
    },
  },
  computed: {
    filteredNumbers() {
      // Filters entries based on whether we're showing documents or diagrams
      return this.numbers.filter((entry) => {
        const isDocument = entry.doc_code.includes('-DOC-');
        return this.showDocumentsOnly ? isDocument : !isDocument;
      });
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
    // getNumbers() {
    //   const path = `${API_URL}/numbers`;
    //   auth.currentUser.getIdToken(true).then(idToken => {
    //     const config = {
    //       headers: { Authorization: `${idToken}` }
    //     };

    //     axios.get(path, config)
    //       .then((res) => {
    //         this.numbers = res.data.numbers;
    //         this.numbers = this.sortNumbers();            
    //         this.superuser = res.data.superuser;
    //         this.isAuthorized = true;
    //       })
    //       .catch((error) => {
    //         console.error(error);
    //         this.superuser = false;
    //         this.isAuthorized = error.response.data.isAuthorized;
    //         // this.hideContent = !this.isAuthorized;
    //       });
    //   }).catch(function (error) {
    //     console.log(error)
    //     this.superuser = false;
    //     this.isAuthorized = false;
    //     // this.hideContent = true;
    //   });
    // },
    // getAdmins() {
    //   const path = `${API_URL}/admins`;
    //   auth.currentUser.getIdToken(true).then(idToken => {
    //     const config = {
    //       headers: { Authorization: `${idToken}` }
    //     };

    //     axios.get(path, config)
    //       .then((res) => {
    //         this.admins = res.data.admins;
    //       })
    //       .catch((error) => {
    //         console.error(error);
    //       });
    //   }).catch(function (error) {
    //     console.log(error)
    //   });
    // },
    toggleTableView() {
      this.showDocumentsOnly = !this.showDocumentsOnly;
    },
    truncate(value, length) {
      if (value.length > length) {
        return value.substring(0, length) + "...";
      } else {
        return value;
      }
    },
    sortColumn(sortBy){
    	if(this.sortBy === sortBy) {
      	this.sortOrder = -this.sortOrder;
      } else {
      	this.sortBy = sortBy;
        this.sortOrder = 1;
      };

      this.numbers = this.sortNumbers();
    }, 
    sortNumbers() {
      return this.numbers.sort((a,b) => {
          if (a[this.sortBy] >= b[this.sortBy]) {
          return this.sortOrder
        }
          return -this.sortOrder
        });
    },
    toggleAdvancedFilter() {
      this.showFilters = !this.showFilters;
      this.filterButtonText = this.showFilters ? 'General Filter' : 'Advanced Filter';
      // Reset general filter when switching to advanced filters
      if (this.showFilters) {
        this.filter = '';
      } else {
        this.resetFilters(); // Reset column filters when switching back to general
      }
    },
    resetFilters() {
      // Reset all filter inputs and checkboxes
      Object.keys(this.columnFilters).forEach(key => {
        this.columnFilters[key] = '';
      });
    },
  },
  created() {
    // this.getNumbers();
    // this.getAdmins();
  },
};
</script>
