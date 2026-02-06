<template>
  <div class="container">
    <div class="row">
      <div class="col-12" v-if="isAuthorized">
        <div class="row">
          <div>
            <div class="d-inline-flex float-start">
              <h1>Documents</h1>
            </div>
            <div class="d-inline-flex float-end">
              <a role="button" class="btn btn-primary" href="/numbers" target="_blank">View Assigned Numbers</a>
              <a v-if="superuser" role="button" class="btn btn-primary ms-4" href="/collaborators" target="_blank">Edit collaborators</a>
            </div>
          </div>
        </div>
        <hr><br><br>
        <div class="row">
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
          <p>Add a new document using the button below. You can edit or delete documents you have added.</p>
          <p>To see all details related to a document click on its Title / Name or its Doc Identifier,
            or, for a given Doc Identifier, add "/docs/&lt;doc_identifier&gt;" to the current URL.</p>
          <p>If you encounter a problem, please contact one of teledoc's admins at:
            <span v-for="(admin, index) in admins" :key="index">
              <a :href="`mailto:${admin}`">{{ admin }}</a>{{ index !== admins.length - 1 ? ', ' : '.' }}
            </span>
          </p>
          <p>If you notice and error in one of the entries, please click the warning button on the associated 
            row to email and inform the entry's maintainer, as well as the admins.</p>
        </div>
        <br>
        <alert :message=message v-if="showMessage"></alert>

        <div class="row row-cols-auto mb-4" style="margin-left: initial;margin-right: initial;">
          <button type="button" class="btn btn-primary btn-sm" @click="toggleAddDocumentModal">
            Add Document
          </button>
          <!-- <button type="button" class="btn btn-primary btn-sm ms-4" @click="toggleUploadFileModal">
            Upload File
          </button> -->

          <!-- Filter toggle button -->
          <button v-if="show_table" type="button" class="btn btn-primary btn-sm ms-4" :title="filterButtonText" @click="toggleAdvancedFilter">
            <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="showFilters"/>
            <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="!showFilters"/>
          </button>

          <!-- General Filter -->
          <div class="ps-0">
            <input v-if="!showFilters" type="text" class="form-control" v-model="filter" placeholder="Search across all columns"/>
            <input v-if="showFilters" type="text" class="form-control invisible"/>
          </div>

          <!-- Button for exporting to Excel -->
          <button type="button" class="btn btn-primary btn-sm float-right" style="margin-left: auto;" @click="exportToExcel">Export to Excel</button>          
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
                <input type="text" class="form-control" id="columnFiltersDocNb" v-model="columnFilters.number" placeholder="Filter by #">
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

        <table class="table table-hover" v-if="show_table">
          <thead>
            <tr>
              <th @click='sortColumn("title")' style="min-width: 10%;" scope="col">Title / Name
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='title' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='title' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("author")' style="min-width: 10%;" scope="col">Author
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='author' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='author' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("doc_identifier")' style="min-width: 10%;" scope="col">Identifier
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='doc_identifier' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='doc_identifier' && this.sortOrder==-1"/>                
              </th>
              <th @click='sortColumn("number")' style="min-width: 15%;" scope="col">Doc #
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='number' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='number' && this.sortOrder==-1"/>                
              </th>
              <th @click='sortColumn("entry_type")' style="min-width: 5%;" scope="col">Type
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='entry_type' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='entry_type' && this.sortOrder==-1"/>                
              </th>
              <th @click='sortColumn("compiled_url")' style="min-width: 10%;" scope="col"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="URLInfo"/>URL
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='compiled_url' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='compiled_url' && this.sortOrder==-1"/>
              </th>
              <th @click='sortColumn("source_url")' style="min-width: 10%;" scope="col"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="sourceURLInfo"/>Source URL
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='source_url' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='source_url' && this.sortOrder==-1"/>                
              </th>
              <th @click='sortColumn("abstract")' style="min-width: 20%;" scope="col">Abstract
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='abstract' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='abstract' && this.sortOrder==-1"/>                
              </th>
              <th @click='sortColumn("creator_email")' style="min-width: 10%;" scope="col">Maintained By
                <font-awesome-icon icon="fa-solid fa-sort-up" style="vertical-align: bottom" v-if="this.sortBy=='creator_email' && this.sortOrder==1"/>
                <font-awesome-icon icon="fa-solid fa-sort-down" style="vertical-align: top" v-if="this.sortBy=='creator_email' && this.sortOrder==-1"/>                
              </th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(doc, index) in filteredDocuments" :key="index" :style="changeControlledStyleMap[doc.change_controlled]">
              <td data-toggle="tooltip" data-placement="bottom" :title="doc.title" style="cursor: default"
                v-if="doc.title.length > 30">
                <a :href="'/docs/' + doc.doc_identifier" target="_blank">{{
                  truncate(doc.title, 30) }}</a>
              </td>
              <td v-else><a :href="'/docs/' + doc.doc_identifier" target="_blank">{{ doc.title }}</a></td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.author" style="cursor: default"
                v-if="doc.author.length > 30">{{ truncate(doc.author, 30) }}</td>
              <td v-else>{{ doc.author }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.doc_identifier" style="cursor: default"
                v-if="doc.doc_identifier.length > 30">
                <a :href="'/docs/' + doc.doc_identifier" target="_blank">{{
                  truncate(doc.doc_identifier, 30) }}</a>
              </td>
              <td v-else><a :href="'/docs/' + doc.doc_identifier" target="_blank">{{ doc.doc_identifier }}</a></td>

              <td v-if="doc.number" data-toggle="tooltip" data-placement="bottom" :title="doc.number" style="cursor: default">
                <ul>
                  <li>
                    <a v-if="(doc.number.value.length > 30)" :href="'/docs/' + doc.number.value" target="_blank" class="d-block">{{ truncate(doc.number.value, 30) }}</a>
                    <a v-else :href="'/docs/' + doc.number.value" target="_blank" class="d-block">{{ doc.number.value }}</a>
                  </li>
                  
                  <!-- No truncation for aliases, pretty awkward to solve. Will revisit if it becomes a problem -->
                  <li v-if="doc.aliases.length > 0">
                    <a v-for="(alias, index) in doc.aliases" :key="index" :href="'/docs/' + alias.value" target="_blank" class="d-block">{{ alias.value }}</a>
                  </li>
                </ul>
              </td>
              <td v-else>
                <ul>
                  <!-- No truncation for aliases, pretty awkward to solve. Will revisit if it becomes a problem -->
                  <li v-if="doc.aliases.length > 0">
                    <a v-for="(alias, index) in doc.aliases" :key="index" :href="'demo/docs/' + alias.value" target="_blank" class="d-block">{{ alias.value }}</a>
                  </li>
                </ul>
              </td>
              
              <td><font-awesome-icon v-if="entryTypeIconMap[doc.entry_type]" :icon="entryTypeIconMap[doc.entry_type]" data-toggle="tooltip" data-placement="bottom" :title="doc.entry_type" class="text-secondary" /></td>

              <td>
                <font-awesome-icon v-if="doc.compiled_url && doc.compiled_url.toLowerCase().includes(gitLabANT)" icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="gitLabInfo"/>
                <a v-if="doc.compiled_url" :href="doc.compiled_url" target="_blank">link</a>
                <!-- <a class="ms-3" :href=doc.compiled_url target="_blank" download><font-awesome-icon
                    icon="fa-solid fa-download" /></a> -->
              </td>

              <td>
                <font-awesome-icon v-if="doc.source_url && doc.source_url.toLowerCase().includes(gitLabANT)" icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="gitLabInfo"/>
                <a v-if="doc.source_url" :href="doc.source_url" target="_blank">link</a>
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
              <td v-else>
                <button type="button" class="btn text-primary" data-toggle="tooltip" 
                data-placement="top" title="Notify maintainer that entry needs to be updated" @click="sendEmail(doc)">
                  <font-awesome-icon icon="fa-solid fa-circle-exclamation" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else>
          <p v-if="filter === ''">No documents stored.</p>
          <p v-else>Sorry, no documents found containing <b>{{ filter }}</b>. Try a different filter.</p>
        </div>
      </div>
      <div class="col-12" v-else>
        <h3>Sorry, you are not authorized to view this page.</h3>
        <p>If you think you should have access, please contact your project PI to request access.</p>
      </div>    
      <div v-if="hideContent">Sorry, this page is not available or you are not authorized to view it.</div>
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
            <div v-if="showAddFormError" class="alert alert-danger">
              <p class="mb-1">Please fix the following errors before submitting:</p>
              <ul class="mb-0">
                <li v-for="(err, idx) in addFormErrorList" :key="idx">{{ err }}</li>
              </ul>
            </div>
            <form>
              <div class="mb-3">
                <label for="addDocumentTitle" class="form-label">Title / Name: <span class="text-danger">*</span></label>
                <input type="text" :class="['form-control', { 'is-invalid': addFormTitleMissing }]" id="addDocumentTitle" v-model="addDocumentForm.title"
                  placeholder="Enter title">
                <div v-if="addFormTitleMissing" class="form-text text-danger">This field is required.</div>
              </div>
              <div class="mb-3">
                <label for="addDocumentAuthor" class="form-label">Author:</label>
                <input type="text" class="form-control" id="addDocumentAuthor" v-model="addDocumentForm.author"
                  placeholder="Enter author">
              </div>
              <div class="mb-3">
                <label for="addDocumentEntryType" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="TypeInfo"/>Type: <span class="text-danger">*</span></label>
                <select :class="['form-control', { 'is-invalid': addFormEntryTypeMissing }]" id="addEntryType" v-model="addDocumentForm.entry_type">
                  <option v-for="option in entryTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
                <div v-if="addFormEntryTypeMissing" class="form-text text-danger">This field is required.</div>
              </div>
              <div class="mb-3">
                <label for="addDocumentChangeControlled" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="CCInfo"/>Change Controlled: <span class="text-danger">*</span></label>
                <select :class="['form-control', { 'is-invalid': addFormChangeControlledMissing }]" id="addDocumentChangeControlled" v-model="addDocumentForm.change_controlled">
                  <option v-for="option in changeControlledOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
                <div v-if="addFormChangeControlledMissing" class="form-text text-danger">This field is required.</div>
              </div>
              <div class="mb-3" v-if="(addDocumentForm.change_controlled === 10) && (addDocumentForm.entry_type === 'drawing')">
                <label for="addDocumentDocCode" class="form-label">New Number:</label>
                <!-- Adding key ensures full re-render on reset -->
                <DrawingCodeBuilder
                  :initialSteps="codeStepsDrawing"
                  @codeComplete="handleAddCodeComplete"
                  @resetCode="handleAddCodeReset"
                  @partialCodeUpdate="handleAddPartialCodeUpdate"
                  :key="builderKey"
                />
                <div class="mt-2 ps-5" style="width: 90%" v-if="builderComplete && activeAddDocumentModal">
                  <label class="form-label">Optional 3-digit number of an existing entry (will increment config):</label>
                  <input type="text" class="form-control" v-model="addDocumentForm.provided_number" maxlength="3" placeholder="e.g. 001" />
                </div>
                <input type="text" class="form-control mt-2" id="addDocumentDocCode" v-model="addDocumentForm.number" readonly />
              </div>
              <div class="mb-3">
                <label for="addDocumentUrl" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="URLInfo"/>URL:</label>
                <input type="text" class="form-control" id="addUrl" v-model="addDocumentForm.compiled_url"
                  placeholder="Enter URL">
              </div>
              <div class="mb-3">
                <label for="addDocumentSourceUrl" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="sourceURLInfo"/>Source URL:</label>
                <input type="text" class="form-control" id="addSourceUrl" v-model="addDocumentForm.source_url"
                  placeholder="Enter source URL">
              </div>
              <div class="mb-3" v-if="superuser">
                <label for="addDocumentCreatedBy" class="form-label">Maintained By (superuser field):</label>
                <input type="text" class="form-control" id="addCreatedBy" v-model="addDocumentForm.creator_email"
                  placeholder="Enter Maintainer Email">
              </div>              
              <div class="mb-3">
                <label for="addDocumentAbstract" class="form-label">Abstract:</label>
                <textarea class="form-control" id="addAbstract" rows="3" v-model="addDocumentForm.abstract"
                  placeholder="Enter abstract"></textarea>
              </div>
              <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="handleAddSubmit"
                      :disabled="!builderComplete && (addDocumentForm.change_controlled === 10) && (addDocumentForm.entry_type === 'drawing')">
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
    <!-- <div ref="uploadFileModal" class="modal fade"
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
            <p>The file must have entries for the following fields (in this order): Title | Author | Doc # | URL | Source URL | Abstract</p>
            <p>If the file has fewer or more columns than 6, the upload will result in an error.</p>
            <p>Columns that are optional (Doc # and Abstract), should be included, but left blank if no value is to be
              included.</p>
            <p>Lines starting with '#' will be omitted.</p>
            <p>Do not use bars in the input values.</p>
            <p>File example:</p>
            <div class="mb-4 text-nowrap" style="overflow-x: scroll; font-family: courier; font-size: 12px;">
              <p class="mb-0"># Title | Author | Doc # | URL | Source URL | Abstract</p>
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
    <div v-if="activeUploadFileModal" class="modal-backdrop fade show"></div> -->

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
            <div v-if="showEditFormError" class="alert alert-danger">
              <p class="mb-1">Please fix the following errors before submitting:</p>
              <ul class="mb-0">
                <li v-for="(err, idx) in editFormErrorList" :key="idx">{{ err }}</li>
              </ul>
            </div>
            <form>
              <div class="mb-3">
                <label for="editDocumentTitle" class="form-label">Title / Name:</label>
                <input type="text" class="form-control" maxlength="500" id="editDocumentTitle"
                  v-model="editDocumentForm.title" placeholder="Enter title">
              </div>
              <div class="mb-3">
                <label for="editDocumentAuthor" class="form-label">Author:</label>
                <input type="text" class="form-control" maxlength="500" id="editDocumentAuthor"
                  v-model="editDocumentForm.author" placeholder="Enter author">
              </div>
              <div class="mb-3">
                <label for="editDocumentEntryType" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="TypeInfo"/>Type:</label>
                <select class="form-control" id="editDocumentEntryType" v-model="editDocumentForm.entry_type" :disabled="editDocumentForm.number!=''">
                  <option v-for="option in entryTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="editDocumentChangeControlled" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="CCInfo"/>Change Controlled:</label>
                <select class="form-control" id="editDocumentChangeControlled" v-model="editDocumentForm.change_controlled" :disabled="editDocumentForm.number!=''">
                  <option v-for="option in changeControlledOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </div>
              <div v-if="docModal && docModal.number" class="mb-3">
                <label for="editDocumentDocCode" class="form-label">Number:</label>

                <!-- This should only be shown if user made the entry change controlled of type "drawing" and 
                  either no number is already linked or, if it is, it's a document-type number-->
                  <!-- Adding key ensures full re-render on reset -->
                <DrawingCodeBuilder
                  v-if="(editDocumentForm.change_controlled === 10) && (editDocumentForm.entry_type === 'drawing') && docModal.number.entry_type === 'document'"
                  :initialSteps="codeStepsDrawing"
                  @codeComplete="handleEditCodeComplete"
                  @resetCode="handleEditCodeReset"
                  @partialCodeUpdate="handleEditPartialCodeUpdate"
                  :key="builderKey"
                />

                <input type="text" class="form-control mt-2" id="editDocumentDocCode" v-model="editDocumentForm.number" readonly :disabled="(editDocumentForm.change_controlled === 10) && (editDocumentForm.entry_type === 'drawing')" />
              </div>
              <div v-else-if="(editDocumentForm.change_controlled === 10) && (editDocumentForm.entry_type === 'drawing')" class="mb-3">
                <label for="editDocumentDocCode" class="form-label">New Number:</label>

                <!-- This should only be shown if user made the entry change controlled of type "drawing" and 
                  either no number is already linked or, if it is, it's a document-type number-->
                  <!-- Adding key ensures full re-render on reset -->
                <DrawingCodeBuilder
                  :initialSteps="codeStepsDrawing"
                  @codeComplete="handleEditCodeComplete"
                  @resetCode="handleEditCodeReset"
                  @partialCodeUpdate="handleEditPartialCodeUpdate"
                  :key="builderKey"
                />

                <div class="mt-2 ps-5" style="width: 90%" v-if="builderComplete && activeEditDocumentModal">
                  <label class="form-label">Optional 3-digit number of an existing entry (will increment config):</label>
                  <input type="text" class="form-control" v-model="editDocumentForm.provided_number" maxlength="3" placeholder="e.g. 001" />
                </div>
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
                      :disabled="(editDocumentForm.change_controlled === 10) && (editDocumentForm.entry_type === 'drawing') && !builderComplete && !editDocumentForm.number">
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
  <!-- Confirmation Modal -->
  <div v-if="confirmModalActive" class="modal fade show d-block" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Confirm Number</h5>
          <button type="button" class="btn-close" aria-label="Close" @click="confirmModalCancel"></button>
        </div>
        <div class="modal-body">
          <div v-html="confirmModalMessageHtml"></div>
          <p><strong>Suggested:</strong> {{ confirmModalSuggested }}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="confirmModalCancel">Cancel</button>
          <button type="button" class="btn btn-primary" @click="confirmModalAccept">Accept suggested</button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="confirmModalActive" class="modal-backdrop fade show"></div>

  <!-- Delete Confirmation Modal -->
  <div v-if="activeDeleteDocumentModal" class="modal fade show d-block" tabindex="-1" role="dialog">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Confirm Delete</h5>
          <button type="button" class="btn-close" aria-label="Close" @click="cancelDeleteDocument"></button>
        </div>
        <div class="modal-body">
          <p>{{ deleteMessage }}</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="cancelDeleteDocument">Cancel</button>
          <button type="button" class="btn btn-danger" @click="confirmDeleteDocument">Delete</button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="activeDeleteDocumentModal" class="modal-backdrop fade show"></div>
</template>

<script>

import axios from 'axios';
import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { auth } from '../firebaseConfig';
import ExcelJS from 'exceljs';
import AlertMessage from './AlertMessage.vue';
import DrawingCodeBuilder from './DrawingCodeBuilder.vue';

const API_URL = '/api';
// const API_URL = 'http://localhost:5001/api';

export default {
  name: 'DocumentsAll',
  data() {
    return {
      showFilters: false,
      filterButtonText: 'Advanced Filter',      
      columnFilters: {
        title: '',
        author: '',
        doc_identifier: '',
        number: '',
        entry_type: '',
        change_controlled: '',
        compiled_url: '',
        source_url: '',
        abstract: '',
        creator_email: ''
      },
      activeAddDocumentModal: false,
      activeEditDocumentModal: false,
      activeUploadFileModal: false,
      addDocumentForm: {
        title: '',
        author: '',
        number: '',
        _stub: '',
        provided_number: '',
        entry_type: '',
        change_controlled: '',
        compiled_url: '',
        source_url: '',
        creator_email: this.email,
        abstract: '',
      },
      // Add-form error display
      addFormErrorList: [],
      showAddFormError: false,
      // Edit-form error display
      editFormErrorList: [],
      showEditFormError: false,
      codeStepsDrawing: [
        {
          label: 'Category:',
          options: [
              { label: 'Extra-Solar Coronograph', value: 'ESC' },
              { label: 'Widefield Context Camera', value: 'WCC' },
            ],
          connectorAfter: '-'
        },
        {
          label: 'Development Category:',
          options: {
            ESC: [
            { label: 'Flight', value: 'F' },
            { label: 'GSE', value: 'G' },
            { label: 'Test Development Unit / Prototype', value: 'T' },
            ], 
            WCC: [
            { label: 'Flight', value: 'F' },
            { label: 'GSE', value: 'G' },
            { label: 'Test Development Unit / Prototype', value: 'T' },
            ], 
          },
          connectorAfter: ''
        },
        {
          label: 'Engineering Subset:',
          options: {
            ESC_F: [
            { label: 'Assembly', value: 'A' },
            { label: 'Part', value: 'P' },
            { label: 'Interface Control Drawing', value: 'X' },
            ], 
            ESC_G: [
            { label: 'Assembly', value: 'A' },
            { label: 'Part', value: 'P' },
            { label: 'Interface Control Drawing', value: 'X' },
            ], 
            ESC_T: [
            { label: 'Assembly', value: 'A' },
            { label: 'Part', value: 'P' },
            { label: 'Interface Control Drawing', value: 'X' },
            ], 
            WCC_F: [
            { label: 'Assembly', value: 'A' },
            { label: 'Part', value: 'P' },
            { label: 'Interface Control Drawing', value: 'X' },
            ], 
            WCC_G: [
            { label: 'Assembly', value: 'A' },
            { label: 'Part', value: 'P' },
            { label: 'Interface Control Drawing', value: 'X' },
            ], 
            WCC_T: [
            { label: 'Assembly', value: 'A' },
            { label: 'Part', value: 'P' },
            { label: 'Interface Control Drawing', value: 'X' },
            ], 
          },
          connectorAfter: '-'
        },
      ],
      builderComplete: false,
      builderKey: 0,
      filter: '',
      documents: [],
      admins: [],
      show_table: false,
      editDocumentForm: {
        pk: '',
        title: '',
        author: '',
        doc_identifier: '',
        number: '',
        _stub: '',
        provided_number: '',
        entry_type: '',
        change_controlled: '',
        compiled_url: '',
        source_url: '',
        creator_email: '',
        abstract: '',
      },
      docModal: null,
      TypeInfo: 'Choosing Type "drawing" and Change Controlled "yes" will give the option to generate a new Drawing Number (unless one already assigned).',
      CCInfo: 'Choosing Type "drawing" and Change Controlled "yes" will give the option to generate a new Drawing Number (unless one already assigned).',
      URLInfo: 'The URL of the file described by the metadata in this entry.',
      sourceURLInfo: '(optional) The URL of the source components (Git repository, Power Point presentation etc.) used to compile / build the file described by the metadata in this entry.',
      gitLabInfo: 'This URL requires the ANT VPN to be activated.',
      gitLabANT: 'gitlab.sc.ascendingnode.tech',
      message: '',
      showMessage: false,
      isAuthorized: false,
      hideContent: false,
      superuser: false,
      file: null,
      sortBy: "doc_identifier",
      sortOrder: -1,
      entryTypeOptions: [],
      entryTypeIconMap: {},
      entryTypeDefault: null,
      changeControlledOptions: [],
      changeControlledStyleMap: {},
      changeControlledDefault: null,
      // Confirmation modal state
      confirmModalActive: false,
      confirmModalMessage: '',
      confirmModalSuggested: '',
      confirmModalType: '',
      confirmPendingPayload: null,
      confirmPendingDocID: null,
      // Delete-confirmation modal state
      activeDeleteDocumentModal: false,
      deleteTarget: null,
      deleteMessage: '',
    };
  },
  components: {
    alert: AlertMessage,
    DrawingCodeBuilder: DrawingCodeBuilder,
  },
  watch: {
    documents: function (newVal, oldVal) {
      if (this.documents.length > 0) {
        this.show_table = true;
      } else {
        this.show_table = false;
      }
    },
    'addDocumentForm.change_controlled'(newVal) {
      if (newVal === 0) {
        this.addDocumentForm.number = "";
      };
      if (newVal === 10) {
        this.resetDrawingCodeBuilder();
      };
    },
    'addDocumentForm.entry_type'(newVal) {
      this.resetDrawingCodeBuilder();
    },
    'addDocumentForm.provided_number'(newVal) {
      // keep only digits, max 3
      if (newVal === undefined) return;
      const digits = newVal.replace(/\D/g, '').slice(0,3);
      if (digits !== newVal) this.addDocumentForm.provided_number = digits;
      const stub = this.addDocumentForm._stub || '';
      if (stub) {
        this.addDocumentForm.number = digits ? `${stub}${digits.padStart(3,'0')}` : stub;
      }
    },
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
    'editDocumentForm.provided_number'(newVal) {
      if (newVal === undefined) return;
      const digits = newVal.replace(/\D/g, '').slice(0,3);
      if (digits !== newVal) this.editDocumentForm.provided_number = digits;
      const stub = this.editDocumentForm._stub || '';
      if (stub) {
        this.editDocumentForm.number = digits ? `${stub}${digits.padStart(3,'0')}` : stub;
      }
    },
  },
  computed: {
    filteredDocuments() {
      // Apply general filter if advanced filters are not shown
      if (!this.showFilters) {
        if (this.filter === '') {
          return this.documents;
        } else {
          return this.documents.filter(doc => {
            const searchTerm = this.filter.toLowerCase();

            const title = doc.title ? doc.title.toString().toLowerCase() : doc.title;
            const author = doc.author ? doc.author.toString().toLowerCase() : doc.author;
            const doc_identifier = doc.doc_identifier ? doc.doc_identifier.toString().toLowerCase() : doc.doc_identifier;
            const number = (doc.number && doc.number.value) ? doc.number.value.toString().toLowerCase() : doc.number.value;
            const entry_type = doc.entry_type ? doc.entry_type.toString().toLowerCase() : doc.entry_type;
            const compiled_url = doc.compiled_url ? doc.compiled_url.toString().toLowerCase() : doc.compiled_url;
            const source_url = doc.source_url ? doc.source_url.toString().toLowerCase() : doc.source_url;
            const abstract = doc.abstract ? doc.abstract.toString().toLowerCase() : doc.abstract;
            const creator_email = doc.creator_email ? doc.creator_email.toString().toLowerCase() : doc.creator_email;

            // Also check if searchTerm is in any alias
            const foundInAliases = doc.aliases && doc.aliases.some(alias => {
              const value = alias.value ? alias.value.toString().toLowerCase() : null;
              return value && value.includes(searchTerm);
            });

            return (title && title.includes(searchTerm)) ||
              (author && author.includes(searchTerm)) ||
              (doc_identifier && doc_identifier.includes(searchTerm)) ||
              (number && number.includes(searchTerm)) ||
              (entry_type && entry_type.includes(searchTerm)) ||
              (compiled_url && compiled_url.includes(searchTerm)) ||
              (source_url && source_url.includes(searchTerm)) ||
              (abstract && abstract.includes(searchTerm)) ||
              (creator_email && creator_email.includes(searchTerm)) ||
              foundInAliases;
          });
        }
      }

      // Apply advanced filters
      return this.documents.filter(doc => {
        return Object.keys(this.columnFilters).every(key => {
          if (key === "number") {
            const searchTerm = this.columnFilters["number"].toLowerCase();
            const value = doc.number ? doc.number.value.toString().toLowerCase() : '';
            // Check if string in associated number
            if (value.includes(searchTerm)) {
              return true;
            // If string not found, check aliases too
            } else if (doc.aliases && doc.aliases.length > 0) {
              return doc.aliases.some(alias => {
                  const aliasValue = alias.value ? alias.value.toString().toLowerCase() : '';
                  return aliasValue.includes(searchTerm);
                });
            // String not found in any associated object
            }
            return false;
          } else if (typeof (this.columnFilters[key]) === 'number') {
            const searchTerm = this.columnFilters[key];
            const value = doc[key]
            return value === searchTerm;
          } else if (typeof (this.columnFilters[key]) === 'string') {
            const searchTerm = this.columnFilters[key].toLowerCase();
            const value = doc[key] ? doc[key].toString().toLowerCase() : '';
            return value.includes(searchTerm);
          }
        });
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
    confirmModalMessageHtml() {
      const msg = this.confirmModalMessage || '';
      const escape = (s) => {
        return s.replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
      };

      const lines = msg.split('\n');
      let html = '';
      let inList = false;
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith('- ')) {
          if (!inList) { html += '<ul>'; inList = true; }
          html += '<li>' + escape(line.slice(2)) + '</li>';
        } else {
          if (inList) { html += '</ul>'; inList = false; }
          if (line.trim() === '') {
            html += '<br/>';
          } else {
            html += '<p>' + escape(line) + '</p>';
          }
        }
      }
      if (inList) html += '</ul>';
      return html;
    },
    // Validation for add document form
    addFormTitleMissing() {
      if (!this.showAddFormError) return false;
      return !this.addDocumentForm.title || this.addDocumentForm.title.trim() === '';
    },
    addFormEntryTypeMissing() {
      if (!this.showAddFormError) return false;
      return !this.addDocumentForm.entry_type || this.addDocumentForm.entry_type === '';
    },
    addFormChangeControlledMissing() {
      if (!this.showAddFormError) return false;
      return this.addDocumentForm.change_controlled === '' || this.addDocumentForm.change_controlled === null || this.addDocumentForm.change_controlled === undefined;
    },
    isAddFormValid() {
      if (this.addFormTitleMissing) return false;
      if (this.addFormEntryTypeMissing) return false;
      if (this.addFormChangeControlledMissing) return false;
      // If drawing and change controlled == 10, require builderComplete
      if (this.addDocumentForm.entry_type === 'drawing' && Number(this.addDocumentForm.change_controlled) === 10) {
        if (!this.builderComplete) return false;
      }
      return true;
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
            // Handle server signals for number confirmation or out-of-order by showing modal
            if (res.data.status === 'confirm' || res.data.status === 'out_of_order') {
              this.confirmModalActive = true;
              this.confirmModalType = res.data.status;
              this.confirmModalMessage = res.data.message;
              this.confirmModalSuggested = res.data.suggested_value || res.data.suggested_next || '';
              this.confirmPendingPayload = payload; // store for later resubmission
              this.confirmPendingDocID = null;
              return;
            }

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
            this.documents = this.sortDocuments();            
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
    handleAddReset() {
      this.initForm();
    },
    handleAddSubmit() {
      // Validate required fields on submit and show inline errors without closing the modal
      const missing = [];
      if (!this.addDocumentForm.title || this.addDocumentForm.title.trim() === '') missing.push('Title is required');
      if (!this.addDocumentForm.entry_type || this.addDocumentForm.entry_type === '') missing.push('Type is required');
      if (this.addDocumentForm.change_controlled === '' || this.addDocumentForm.change_controlled === null || this.addDocumentForm.change_controlled === undefined) missing.push('Change Controlled is required');
      if (this.addDocumentForm.entry_type === 'drawing' && Number(this.addDocumentForm.change_controlled) === 10 && !this.builderComplete) missing.push('Drawing code must be completed to generate a number');
      if (missing.length > 0) {
        this.addFormErrorList = missing;
        this.showAddFormError = true;
        return;
      }
      // All good: clear any previous errors and proceed to submit
      this.showAddFormError = false;
      this.addFormErrorList = [];
      // Combine sanitized stub and optional provided 3-digit number (prefer stub if available)
      const stub = this.addDocumentForm._stub ? this.addDocumentForm._stub.replace(/^-+|-+$/g,'') : '';
      const providedRaw = this.addDocumentForm.provided_number ? this.addDocumentForm.provided_number.replace(/\D/g,'') : '';
      const provided = providedRaw ? providedRaw.padStart(3,'0') : '';
      const combinedNumber = stub ? (provided ? `${stub}${provided}` : stub) : (this.addDocumentForm.number || '');

      const payload = {
        title: this.addDocumentForm.title,
        author: this.addDocumentForm.author,
        number: combinedNumber,
        entry_type: this.addDocumentForm.entry_type,
        change_controlled: this.addDocumentForm.change_controlled,
        compiled_url: this.addDocumentForm.compiled_url,
        source_url: this.addDocumentForm.source_url,
        creator_email: this.addDocumentForm.creator_email || this.email,        
        abstract: this.addDocumentForm.abstract,
      };
      this.toggleAddDocumentModal();
      this.addDocument(payload);
      this.initForm();
    },
    handleDeleteDocument(doc) {
      // For change-controlled entries open a styled confirmation modal.
      const isChangeControlled = Number(doc.change_controlled) === 10;
      if (isChangeControlled) {
        this.deleteTarget = doc.doc_identifier;
        this.deleteMessage = 'WARNING: This entry is marked as change-controlled. Deleting it may affect linked numbers and audit trails. Are you sure you want to proceed?';
        const body = window.document.querySelector('body');
        this.activeDeleteDocumentModal = true;
        body.classList.add('modal-open');
        return;
      }
      this.removeDocument(doc.doc_identifier);
    },
    handleEditCancel() {
      this.toggleEditDocumentModal(null);
      this.initForm();
      this.getDocuments(); // initForm sets values of doc open in modal to empty, so repopulate them
    },
    handleEditSubmit() {
      // Validate required fields and show inline errors without closing the modal
      const missing = [];
      if (!this.editDocumentForm.title || this.editDocumentForm.title.trim() === '') missing.push('Title is required');
      if (!this.editDocumentForm.entry_type || this.editDocumentForm.entry_type === '') missing.push('Type is required');
      if (this.editDocumentForm.change_controlled === '' || this.editDocumentForm.change_controlled === null || this.editDocumentForm.change_controlled === undefined) missing.push('Change Controlled is required');
      if (this.editDocumentForm.entry_type === 'drawing' && Number(this.editDocumentForm.change_controlled) === 10 && !this.builderComplete && !this.editDocumentForm.number) missing.push('Drawing code must be completed to generate a number');
      if (missing.length > 0) {
        this.editFormErrorList = missing;
        this.showEditFormError = true;
        return;
      }
      this.showEditFormError = false;
      this.editFormErrorList = [];

      const stub = this.editDocumentForm._stub ? this.editDocumentForm._stub.replace(/^-+|-+$/g,'') : '';
      const providedRaw = this.editDocumentForm.provided_number ? this.editDocumentForm.provided_number.replace(/\D/g,'') : '';
      const provided = providedRaw ? providedRaw.padStart(3,'0') : '';
      const combinedNumber = stub ? (provided ? `${stub}${provided}` : stub) : (this.editDocumentForm.number || '');

      const payload = {
        title: this.editDocumentForm.title,
        author: this.editDocumentForm.author,
        number: combinedNumber,
        entry_type: this.editDocumentForm.entry_type,
        change_controlled: this.editDocumentForm.change_controlled,
        compiled_url: this.editDocumentForm.compiled_url,
        source_url: this.editDocumentForm.source_url,
        creator_email: this.editDocumentForm.creator_email || this.email,
        abstract: this.editDocumentForm.abstract,
      };
      // Close modal only after successful client validation
      this.toggleEditDocumentModal(null);
      this.updateDocument(payload, this.editDocumentForm.doc_identifier);
    },
    initForm() {
      this.addDocumentForm.title = '';
      this.addDocumentForm.author = '';
      this.addDocumentForm.number = '';
      this.addDocumentForm._stub = '';
      this.addDocumentForm.provided_number = '';
      this.addDocumentForm.entry_type = this.entryTypeDefault;
      this.addDocumentForm.change_controlled = this.changeControlledDefault;
      this.addDocumentForm.compiled_url = '';
      this.addDocumentForm.source_url = '';
      this.addDocumentForm.creator_email = this.email;
      this.addDocumentForm.abstract = '';
      this.showAddFormError = false;
      this.addFormErrorList = [];
      this.editDocumentForm.pk = '';
      this.editDocumentForm.title = '';
      this.editDocumentForm.author = '';
      this.editDocumentForm.doc_identifier = '';
      this.editDocumentForm.number = '';
      this.editDocumentForm._stub = '';
      this.editDocumentForm.provided_number = '';
      this.editDocumentForm.entry_type = '';
      this.editDocumentForm.change_controlled = '';
      this.editDocumentForm.compiled_url = '';
      this.editDocumentForm.source_url = '';
      this.editDocumentForm.creator_email = '';      
      this.editDocumentForm.abstract = '';
      this.showEditFormError = false;
      this.editFormErrorList = [];
      this.docModal = null;
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

    confirmDeleteDocument() {
      // Called when user confirms deletion in modal
      this.removeDocument(this.deleteTarget);
      this.deleteTarget = null;
      this.deleteMessage = '';
      this.activeDeleteDocumentModal = false;
      const body = document.querySelector('body');
      body.classList.remove('modal-open');
    },

    cancelDeleteDocument() {
      // Close modal without deleting
      this.deleteTarget = null;
      this.deleteMessage = '';
      this.activeDeleteDocumentModal = false;
      const body = document.querySelector('body');
      body.classList.remove('modal-open');
    },
    handleAddCodeComplete(code) {
      const stub = code ? code.replace(/^-+|-+$/g,'') : '';
      this.addDocumentForm._stub = stub;
      // if user already entered a provided_number, compose final preview
      const provided = this.addDocumentForm.provided_number ? this.addDocumentForm.provided_number.replace(/\D/g,'').padStart(3,'0') : '';
      this.addDocumentForm.number = provided ? `${stub}${provided}` : stub;
      this.builderComplete = true;
    },
    handleAddPartialCodeUpdate(partialCode) {
        this.addDocumentForm.number = partialCode;
    },
    handleAddCodeReset() {
      // Reset document code on builder reset
      this.addDocumentForm.number = "";
      this.builderComplete = false;
    },
    handleEditCodeComplete(code) {
      const stub = code ? code.replace(/^-+|-+$/g,'') : '';
      this.editDocumentForm._stub = stub;
      const provided = this.editDocumentForm.provided_number ? this.editDocumentForm.provided_number.replace(/\D/g,'').padStart(3,'0') : '';
      this.editDocumentForm.number = provided ? `${stub}${provided}` : stub;
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
      // We want to reset the field for both forms here
      // (Don't see any risk in doing so)
      this.addDocumentForm.number = "";
      this.addDocumentForm.provided_number = "";
      this.addDocumentForm._stub = "";
      this.editDocumentForm.number = this.resetEditNumber();
      this.editDocumentForm.provided_number = "";
      this.editDocumentForm._stub = "";
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
    toggleAddDocumentModal() {
      const body = document.querySelector('body');
      this.activeAddDocumentModal = !this.activeAddDocumentModal;
      if (this.activeAddDocumentModal) {
        this.initForm();
        body.classList.add('modal-open');
      } else {
        body.classList.remove('modal-open');
      }
    },
    toggleEditDocumentModal(doc) {
      if (doc) {
        this.editDocumentForm = { ...doc };
        this.editDocumentForm.entry_type = doc.entry_type;
        this.editDocumentForm.change_controlled = doc.change_controlled;
        this.editDocumentForm.number = doc.number && doc.number.value;
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
            // Handle server signals for number confirmation or out-of-order by showing modal
            if (res.data.status === 'confirm' || res.data.status === 'out_of_order') {
              this.confirmModalActive = true;
              this.confirmModalType = res.data.status;
              this.confirmModalMessage = res.data.message;
              this.confirmModalSuggested = res.data.suggested_value || res.data.suggested_next || '';
              this.confirmPendingPayload = payload; // store for later resubmission
              this.confirmPendingDocID = docID;
              return;
            }

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
    confirmModalAccept() {
      if (!this.confirmPendingPayload) return;
      // attach suggested confirmed number and resubmit
      this.confirmPendingPayload.confirmed_number = this.confirmModalSuggested;
      const payload = this.confirmPendingPayload;
      const docID = this.confirmPendingDocID;

      // clear modal state
      this.confirmModalActive = false;
      this.confirmModalMessage = '';
      this.confirmModalSuggested = '';
      this.confirmPendingPayload = null;
      this.confirmPendingDocID = null;

      if (docID) {
        this.updateDocument(payload, docID);
      } else {
        this.addDocument(payload);
      }
    },
    confirmModalCancel() {
      this.confirmModalActive = false;
      this.confirmModalMessage = '';
      this.confirmModalSuggested = '';
      this.confirmPendingPayload = null;
      this.confirmPendingDocID = null;
      this.message = 'Action cancelled by user.';
      this.showMessage = true;
      this.getDocuments();
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
    sortColumn(sortBy){
    	if(this.sortBy === sortBy) {
      	this.sortOrder = -this.sortOrder;
      } else {
      	this.sortBy = sortBy;
        this.sortOrder = 1;
      };

      this.documents = this.sortDocuments();
    }, 
    sortDocuments() {
      return this.documents.sort((a,b) => {
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
    sendEmail(doc) {
      // alert(`Sending email to ${doc.creator_email}`);
      const emailSubject = encodeURIComponent(`Teledocs Alert: Document '${doc.title}' is out of date`);
      const emailBody = encodeURIComponent(`Hi,\n\n
This is to inform you that the document '${doc.title}' was reported as being out of date. The data currently associated with it is:\n
Title / Name: ${doc.title}\n
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
    exportToExcel() {
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Documents');

      worksheet.columns = [
        { title: 'Title / Name', key: 'title'},
        { author: 'Author', key: 'author'},
        { doc_identifier: 'Doc Identifier', key: 'doc_identifier'},
        { number: 'Doc #', key: 'number'},
        { entry_type: 'Type', key: 'entry_type'},
        { change_controlled: 'Change Controlled', key: 'change_controlled'},
        { compiled_url: 'URL', key: 'compiled_url'},        
        { source_url: 'Source URL', key: 'source_url'},        
        { abstract: 'Abstract', key: 'abstract'},        
        { creator_email: 'Maintainer Email', key: 'creator_email'},        
      ];

      worksheet.addRow({
        title: 'Title / Name',
        author: 'Author',
        doc_identifier: 'Doc Identifier',
        number: 'Doc #',
        entry_type: 'Type',
        change_controlled: 'Change Controlled',
        compiled_url: 'URL',        
        source_url: 'Source URL',
        abstract: 'Abstract',
        creator_email: 'Maintainer Email',
      })

      this.filteredDocuments.forEach(doc => {
        worksheet.addRow({
          title: doc.title,
          author: doc.author,
          doc_identifier: doc.doc_identifier,
          number: doc.number.value,
          entry_type: doc.entry_type,
          change_controlled: doc.change_controlled,
          compiled_url: doc.compiled_url,
          source_url: doc.source_url,
          abstract: doc.abstract,
          creator_email: doc.creator_email,
        });
      });

      // Save the workbook
      workbook.xlsx.writeBuffer().then(buffer => {
        const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const fileName = 'exported_teledocs_entries.xlsx';

        // Create a link element, simulate click to trigger download
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = fileName;
        link.click();

        // Clean up
        window.URL.revokeObjectURL(link.href);
      });
    },
    getEntryTypeOptions() {
      const path = `${API_URL}/entry_types`;
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
          this.entryTypeDefault = res.data.default;
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
    this.getDocuments();
    this.getAdmins();
    this.getEntryTypeOptions();
    this.getChangeControlledOptions();
  },
  mounted() {
    // Initialize steps for the current value of addDocumentEntryType
    this.resetDrawingCodeBuilder();
  }
};
</script>