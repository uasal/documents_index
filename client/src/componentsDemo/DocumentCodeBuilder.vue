<template>
    <div class="doc-code-builder">
        <div class="steps-container" :style="{ transform: `translateX(-${currentStep * 100}%)` }">
            <div v-for="(step, index) in steps" :key="index" class="step-panel">
                <label :for="`step-${index}`" class="form-label">{{ step.label }}</label>
                <select
                    :id="`step-${index}`"
                    class="form-control"
                    v-model="selectedOptions[index]"
                    @change="handleOptionChange(index)"
                >
                    <option value="" disabled selected hidden>Select an option</option>
                    <option v-for="option in step.options" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
            </div>
        </div>
  
        <div class="doc-code-controls">
            <button v-if="currentStep > 0" type="button" class="btn btn-primary btn-sm" @click="previousStep">
            Back
            </button>
            <button v-if="currentStep < steps.length - 1" type="button" class="btn btn-primary btn-sm" @click="nextStep">
            Next
            </button>
            <button v-if="currentStep === steps.length - 1" type="button" class="btn btn-success btn-sm" @click="submitCode">
            Complete
            </button>
            <button type="button" class="btn btn-secondary btn-sm" @click="resetBuilder">Reset</button>
        </div>
    </div>
</template>

<style scoped>
.doc-code-builder {
position: relative;
overflow: hidden;
width: 80%;
margin-left: auto;
margin-right: auto;
}

.steps-container {
display: flex;
transition: transform 0.4s ease-in-out;
/* width: calc(100% * 5); */
}

.step-panel {
flex: 1 0 100%;
/* padding: 10px; */
}

.doc-code-controls {
display: flex;
justify-content: space-between;
margin-top: 0.5em;
}
</style>
  
<script>
export default {
    props: {
        initialSteps: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            steps: this.initialSteps,
            selectedOptions: Array(this.initialSteps.length).fill(""),
            currentStep: 0
        };
    },
    watch: {
        steps(newSteps) {
            this.resetBuilder(); // Reset if steps change
        },
        selectedOptions: {
            handler() {
                this.emitPartialCode();
            },
            deep: true
        }
    },
    methods: {
        handleOptionChange(stepIndex) {
            const selectedValue = this.selectedOptions[stepIndex];
            
            if (stepIndex < this.steps.length - 1) {
                this.loadNextOptions(stepIndex, selectedValue);
            }
        },
        loadNextOptions(stepIndex, selectedValue) {
            // Logic to update options for the next step based on the selected value of the current step
            // Update `this.steps[stepIndex + 1].options` based on selectedValue
            pass;
        },
        previousStep() {
            if (this.currentStep > 0) {
                this.selectedOptions[this.currentStep] = "";
                this.currentStep--;
                this.emitPartialCode();
            }
        },
        nextStep() {
            if (this.currentStep < this.steps.length - 1) {
                this.currentStep++;
                this.emitPartialCode();
            }
        },
        submitCode() {
            const documentCode = this.selectedOptions.filter(option => option).join("-");
            this.$emit("codeComplete", documentCode);
        },
        resetBuilder() {
            this.selectedOptions.fill("");
            this.currentStep = 0;
            this.$emit("resetCode");
        },
        emitPartialCode() {
            const partialCode = this.selectedOptions
                .filter(option => option)
                .join("-");
            this.$emit("partialCodeUpdate", partialCode);
        }
    }
};
</script>
  