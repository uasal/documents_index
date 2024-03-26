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
              <a role="button" class="btn btn-primary me-4" href="/" target="_blank">View Documents and Drawings</a>
            </div>
          </div>
        </div>
        <hr><br><br>
        <div class="row">
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
          <p>If you encounter a problem, please contact one of teledoc's admins at:
            <span v-for="(admin, index) in admins" :key="index">
              <a :href="`mailto:${admin}`">{{ admin }}</a>{{ index !== admins.length - 1 ? ', ' : '.' }}
            </span>
          </p>
        </div>
        <br>
        <alert :message=message v-if="showMessage"></alert>

        <div class="row row-cols-auto mb-4" style="margin-left: initial;margin-right: initial;">

          <!-- Filter toggle button -->
          <button v-if="show_table" type="button" class="btn btn-primary btn-sm" :title="filterButtonText" @click="toggleAdvancedFilter">
            <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="showFilters"/>
            <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="!showFilters"/>
          </button>

          <!-- General Filter -->
          <div class="ps-0">
            <input v-if="!showFilters" type="text" class="form-control" v-model="filter" placeholder="Search across all columns"/>
            <input v-if="showFilters" type="text" class="form-control invisible"/>
          </div>

        </div>

        <!-- Advanced Filter Fields -->
        <transition name="slide">
          <div class="container mt-3 mb-5" v-if="showFilters">
            <div class="row row-cols-auto">
              <div class="col mb-3">
                <!-- <label for="columnFiltersTitle" class="form-label">Title:</label> -->
                <input type="text" class="form-control" id="columnFiltersTitle" v-model="columnFilters.title" placeholder="Filter by Title / Name">           
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
                <input type="text" class="form-control" id="columnFiltersDocNb" v-model="columnFilters.value" placeholder="Filter by #">
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

        <!-- Toggle Button to Switch Between Documents and Drawings -->
        <div class="form-check form-switch mb-3">
          <input
            class="form-check-input"
            type="checkbox"
            id="toggleSwitch"
            v-model="showDrawingsOnly"
          />
          <label class="form-check-label" for="toggleSwitch">
            {{ showDrawingsOnly ? "Showing Drawings" : "Showing Documents" }}
          </label>
        </div>

        <table class="table table-hover" v-if="show_table">
          <thead>
            <tr>
              <th @click='sortColumn("value")' style="min-width: 10%;" scope="col">
                {{ showDrawingsOnly ? 'Drawing Number' : 'Document Number' }}
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='value' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='value' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("doc_identifier")' style="min-width: 10%;" scope="col">Associated Identifier
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='doc_identifier' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='doc_identifier' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("title")' style="min-width: 10%;" scope="col">Title / Name
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
            <tr v-for="entry in filteredNumbers" :key="entry.value">
              <td v-if="entry.document" :style="changeControlledStyleMap[entry.document.change_controlled]">
                <ul>
                  <li>
                    <a :href="'/docs/' + entry.value" target="_blank" class="d-block">{{ entry.value }}</a>
                  </li>
                  
                  <li v-if="entry.document.aliases.length > 0" v-for="(alias, index) in entry.document.aliases" :key="index">
                    <a :href="'/docs/' + alias.value" target="_blank" class="d-block">{{ alias.value }}</a>
                  </li>
                </ul>
              </td>
              <td v-else>{{ entry.value }}</td>

              <!-- <td data-toggle="tooltip" data-placement="bottom" :title="entry.document.doc_identifier" style="cursor: default"
                v-if="entry.document.doc_identifier.length > 30">
                <a :href="'/docs/' + entry.document.doc_identifier" target="_blank">{{
                  truncate(entry.document.doc_identifier, 30) }}</a>
              </td>
              <td v-else><a :href="'/docs/' + entry.document.doc_identifier" target="_blank">{{ entry.document.doc_identifier }}</a></td> -->

              <td v-if="entry.document" data-toggle="tooltip" data-placement="bottom" :title="entry.document.doc_identifier" style="cursor: default">
                <a v-if="entry.document.doc_identifier.length > 30" :href="'/docs/' + entry.document.doc_identifier" target="_blank" class="d-block">{{ truncate(entry.document.doc_identifier, 30) }}</a>
                <a v-else :href="'/docs/' + entry.document.doc_identifier" target="_blank" class="d-block">{{ entry.document.doc_identifier }}</a>
              </td>
              <td v-else>-</td>

              <td v-if="entry.document" data-toggle="tooltip" data-placement="bottom" :title="entry.document.title" style="cursor: default">
                <a v-if="entry.document.title.length > 30" :href="'/docs/' + entry.document.doc_identifier" target="_blank">{{
                  truncate(entry.document.title, 30) }}</a>
                <a v-else :href="'/docs/' + entry.document.doc_identifier" target="_blank">{{ entry.document.title }}</a>
              </td>
              <td v-else>-</td>

              <td v-if="entry.document" data-toggle="tooltip" data-placement="bottom" :title="entry.author" style="cursor: default">
                <span v-if="entry.document.author.length > 30">{{ truncate(entry.document.author, 30) }}</span>
                <span v-else>{{ entry.document.author }}</span>
              </td>
              <td v-else>-</td>

              <td v-if="entry.document" data-toggle="tooltip" data-placement="bottom" :title="entry.document.creator_email" style="cursor: default">
                <span v-if="entry.document.creator_email.length > 15">{{ truncate(entry.document.creator_email, 15) }}</span>
                <span v-else>{{ entry.document.creator_email }}</span>
              </td>
              <td v-else>-</td>
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
      <div v-if="hideContent">Sorry, this page is not available or you are not authorized to view it.</div>
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
import AlertMessage from './AlertMessage.vue';

// const API_URL = '/api';
const API_URL = 'http://localhost:5001/api';

export default {
  name: 'NumbersAll',
  data() {
    return {
      showFilters: false,
      filterButtonText: 'Advanced Filter',      
      columnFilters: {
        value: '',
        doc_identifier: '',
        title: '',
        author: '',
        creator_email: ''
      },
      filter: '',
      numbers: [],
      admins: [],
      show_table: true,
      showDrawingsOnly: true,
      message: '',
      showMessage: false,
      isAuthorized: true,
      hideContent: false,
      superuser: false,
      sortBy: null,
      sortOrder: -1,
      entryTypeOptions: [],
      entryTypeIconMap: {},
      entryTypeDefault: null,
      changeControlledStyleMap: {},
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
      // Initially filter entries based on whether we're showing documents or drawing
      let filtered = this.numbers.filter((entry) => {
        const isDrawing = entry.entry_type.includes('drawing');
        return this.showDrawingsOnly ? isDrawing : !isDrawing;
      });

      // Then add any extra user filter
      // First apply general filter if advanced filters are not shown
      if (!this.showFilters) {
        if (this.filter === '') {
          return filtered;
        } else {
          const searchTerm = this.filter.toLowerCase();

          filtered = filtered.filter(nb => {
            const title = nb.document && nb.document.title ? nb.document.title.toString().toLowerCase() : '';
            const author = nb.document && nb.document.author ? nb.document.author.toString().toLowerCase() : '';
            const doc_identifier = nb.document && nb.document.doc_identifier ? nb.document.doc_identifier.toString().toLowerCase() : '';
            const number = nb.value ? nb.value.toString().toLowerCase() : '';
            const creator_email = nb.document && nb.document.creator_email ? nb.document.creator_email.toString().toLowerCase() : '';

            // Check aliases
            const foundInAliases = nb.document && nb.document.aliases && nb.document.aliases.some(alias => {
              const value = alias.value ? alias.value.toString().toLowerCase() : null;
              return value && value.includes(searchTerm);
            });

            return (title && title.includes(searchTerm)) ||
              (author && author.includes(searchTerm)) ||
              (doc_identifier && doc_identifier.includes(searchTerm)) ||
              (number && number.includes(searchTerm)) ||
              (creator_email && creator_email.includes(searchTerm)) ||
              foundInAliases;
          });
        }
      }

      // Apply advanced filters
      if (this.columnFilters && Object.keys(this.columnFilters).length > 0) {
        filtered = filtered.filter(nb => {
          return Object.keys(this.columnFilters).every(key => {
            if (key === "value") {
              const searchTerm = this.columnFilters["value"].toLowerCase();
              const value = nb.value ? nb.value.toString().toLowerCase() : '';
              // Check if string in associated number
              if (value.includes(searchTerm)) {
                return true;
              } else if (nb.document && nb.document.aliases && nb.document.aliases.length > 0) {
                // Check aliases for the number
                return nb.document.aliases.some(alias => {
                  const aliasValue = alias.value ? alias.value.toString().toLowerCase() : '';
                  return aliasValue.includes(searchTerm);
                });
              }
              return false;
            } else if (typeof (this.columnFilters[key]) === 'number') {
              const searchTerm = this.columnFilters[key];
              const value = nb.document && nb.document[key];
              return value === searchTerm;
            } else if (typeof (this.columnFilters[key]) === 'string') {
              const searchTerm = this.columnFilters[key].toLowerCase();
              const value = ( nb.document && nb.document[key] ) ? nb.document[key].toString().toLowerCase() : '';
              return value.includes(searchTerm);
            }
            return true;
          });
        });
      }

      return filtered;
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
    getNumbers() {
      const path = `${API_URL}/numbers`;
      auth.currentUser.getIdToken(true).then(idToken => {
        const config = {
          headers: { Authorization: `${idToken}` }
        };

        axios.get(path, config)
          .then((res) => {
            this.numbers = res.data.numbers;
            // this.numbers = this.sortNumbers();            
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
    toggleTableView() {
      this.showDrawingsOnly = !this.showDrawingsOnly;
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
    getChangeControlledOptions() {
      const path = `${API_URL}/change_controlled_types`;
      auth.currentUser.getIdToken(true).then(idToken => {
      const config = {
        headers: { Authorization: `${idToken}` }
      };

      axios.get(path, config)
        .then((res) => {
          this.changeControlledOptions = res.data.change_controlled_types;
          this.changeControlledStyleMap = this.changeControlledOptions.reduce((map, option) => {
            map[option.value] = option.tr_style;
            return map;
          }, {});
          this.changeControlledDefault = res.data.default;
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
    this.getNumbers();
    this.getAdmins();
    this.getChangeControlledOptions();
  },
};
</script>
