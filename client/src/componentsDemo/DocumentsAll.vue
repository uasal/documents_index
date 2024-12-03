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
              <a role="button" class="btn btn-primary" href="/demo/numbers" target="_blank">View Assigned Numbers</a>
              <a v-if="superuser" role="button" class="btn btn-primary ms-4" href="/demo/collaborators" target="_blank">Edit collaborators</a>
            </div>
          </div>
        </div>
        <hr><br><br>
        <div class="row">
          <p>Hello, {{ username }}, you are logged in with the account {{ email }}</p>
          <p>Add a new document using the button below. You can edit or delete documents you have added.</p>
          <p>To see all details related to a document click on its Title or its Doc Identifier,
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
          <button type="button" class="btn btn-primary btn-sm ms-4" @click="toggleUploadFileModal">
            Upload File
          </button>

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
              <th @click='sortColumn("title")' style="min-width: 10%;" scope="col">Title
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
                <a :href="'demo/docs/' + doc.doc_identifier" target="_blank">{{
                  truncate(doc.title, 30) }}</a>
              </td>
              <td v-else><a :href="'demo/docs/' + doc.doc_identifier" target="_blank">{{ doc.title }}</a></td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.author" style="cursor: default"
                v-if="doc.author.length > 30">{{ truncate(doc.author, 30) }}</td>
              <td v-else>{{ doc.author }}</td>

              <td data-toggle="tooltip" data-placement="bottom" :title="doc.doc_identifier" style="cursor: default"
                v-if="doc.doc_identifier.length > 30">
                <a :href="'demo/docs/' + doc.doc_identifier" target="_blank">{{
                  truncate(doc.doc_identifier, 30) }}</a>
              </td>
              <td v-else><a :href="'demo/docs/' + doc.doc_identifier" target="_blank">{{ doc.doc_identifier }}</a></td>

              <td v-if="doc.number" data-toggle="tooltip" data-placement="bottom" :title="doc.number" style="cursor: default">
                <ul>
                  <li>
                    <a v-if="(doc.number.value.length > 30)" :href="'demo/docs/' + doc.number.value" target="_blank" class="d-block">{{ truncate(doc.number.value, 30) }}</a>
                    <a v-else :href="'demo/docs/' + doc.number.value" target="_blank" class="d-block">{{ doc.number.value }}</a>
                  </li>
                  
                  <!-- No truncation for aliases, pretty awkward to solve. Will revisit if it becomes a problem -->
                  <li v-if="doc.aliases.length > 0">
                    <a v-for="(alias, index) in doc.aliases" :key="index" :href="'demo/docs/' + alias.value" target="_blank" class="d-block">{{ alias.value }}</a>
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
                  <button v-if="!doc.number || superuser" type="button" class="btn btn-danger btn-sm" @click="handleDeleteDocument(doc)">
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
                <label for="addDocumentEntryType" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="TypeInfo"/>Type:</label>
                <select class="form-control" id="addEntryType" v-model="addDocumentForm.entry_type">
                  <option v-for="option in entryTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="addDocumentChangeControlled" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="CCInfo"/>Change Controlled:</label>
                <select class="form-control" id="addDocumentChangeControlled" v-model="addDocumentForm.change_controlled">
                  <option v-for="option in changeControlledOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
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
                <select class="form-control" id="editDocumentEntryType" v-model="editDocumentForm.entry_type"
                  v-if="!editDocumentForm.number || superuser">
                  <option v-for="option in entryTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
                <select class="form-control" id="editDocumentEntryType" v-model="editDocumentForm.entry_type"
                  v-else disabled>
                  <option v-for="option in entryTypeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label for="editDocumentChangeControlled" class="form-label"><font-awesome-icon icon="fa-solid fa-circle-info" class="me-1 text-secondary" data-toggle="tooltip" data-placement="bottom" :title="CCInfo"/>Change Controlled:</label>
                <select class="form-control" id="editDocumentChangeControlled" v-model="editDocumentForm.change_controlled"
                  v-if="!editDocumentForm.number || superuser">
                  <option v-for="option in changeControlledOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
                <select class="form-control" id="editDocumentChangeControlled" v-model="editDocumentForm.change_controlled"
                v-else disabled>
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

                <input type="text" class="form-control mt-2" id="editDocumentDocCode" v-model="editDocumentForm.number" readonly />
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
import ExcelJS from 'exceljs';
import AlertMessage from './AlertMessage.vue';
import DrawingCodeBuilder from './DrawingCodeBuilder.vue';

const API_URL = '/api/demo';
// const API_URL = 'http://localhost:5001/api/demo';

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
        entry_type: '',
        change_controlled: '',
        compiled_url: '',
        source_url: '',
        creator_email: this.email,
        abstract: '',
      },
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
      this.toggleAddDocumentModal();
      const payload = {
        title: this.addDocumentForm.title,
        author: this.addDocumentForm.author,
        number: this.addDocumentForm.number,
        entry_type: this.addDocumentForm.entry_type,
        change_controlled: this.addDocumentForm.change_controlled,
        compiled_url: this.addDocumentForm.compiled_url,
        source_url: this.addDocumentForm.source_url,
        creator_email: this.addDocumentForm.creator_email || this.email,        
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
      this.getDocuments(); // initForm sets values of doc open in modal to empty, so repopulate them
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
      this.addDocumentForm.title = '';
      this.addDocumentForm.author = '';
      this.addDocumentForm.number = '';
      this.addDocumentForm.entry_type = this.entryTypeDefault;
      this.addDocumentForm.change_controlled = this.changeControlledDefault;
      this.addDocumentForm.compiled_url = '';
      this.addDocumentForm.source_url = '';
      this.addDocumentForm.creator_email = this.email;
      this.addDocumentForm.abstract = '';
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
    handleAddCodeComplete(code) {
      this.addDocumentForm.number = code;
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
      // We want to reset the field for both forms here
      // (Don't see any risk in doing so)
      this.addDocumentForm.number = "";
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
    exportToExcel() {
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Documents');

      worksheet.columns = [
        { title: 'Title', key: 'title'},
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
        title: 'Title',
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
      const path = `${API_URL}/../change_controlled_types`;
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