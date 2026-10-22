<template>
  <div>
    <div class="alert" :class="`alert-${type}`" role="alert">{{ message }}</div>
    <br/>
  </div>
</template>

<script>
export default {
  name: 'AlertMessage',
  props: {
    message: String,
    // Bootstrap alert variant, e.g. 'success' or 'danger'
    type: {
      type: String,
      default: 'success',
    },
  },
};
</script>
