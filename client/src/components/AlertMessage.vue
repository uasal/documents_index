<template>
  <div>
    <div class="alert alert-success" role="alert">{{ message }}</div>
    <br/>
  </div>
</template>

<script>
export default {
  name: 'AlertMessage',
  props: ['message'],
};
</script>
