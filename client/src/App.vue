<template>
  <div class="container d-flex align-items-center justify-content-center" v-if="getLogin">
    <div class="mt-5">
      <button type="button" class="btn btn-primary" id="logInButton" @click="logInUser">Log In with Google</button>
    </div>
  </div>
  <div v-if="isLoggedIn">
    <RouterView />
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'

import { ref, computed } from 'vue'; // used for conditional rendering

</script>

<style>
#app {
  margin-top: 60px
}
</style>
