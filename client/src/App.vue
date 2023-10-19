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
import { GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { auth } from './firebaseConfig';

const getLogin = ref(false);
const isLoggedIn = ref(false);

// runs after firebase is initialized
auth.onAuthStateChanged(function (user) {
  if (user) {
    getLogin.value = false
    isLoggedIn.value = true;
  } else {
    getLogin.value = true;
    isLoggedIn.value = false;
  }
});

const logInUser = () => {
  const provider = new GoogleAuthProvider();
  provider.addScope('https://www.googleapis.com/auth/userinfo.email');
  signInWithPopup(auth, provider)
    .then(result => {
      // Returns the signed in user along with the provider's credential
      console.log(`${result.user.displayName} logged in.`);
      const credential = GoogleAuthProvider.credentialFromResult(result);
    })
    .catch(err => {
      console.log(`Error during sign in: ${err.message}`);
      window.alert(`Sign in failed. Retry or check your browser logs.`);
    });
}
</script>

<style>
#app {
  margin-top: 60px
}
</style>
