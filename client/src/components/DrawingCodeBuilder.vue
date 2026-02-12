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
                    :disabled="isComplete"
                >
                    <option value="" disabled selected hidden>Select an option</option>
                    <option v-for="option in step.options" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
            </div>
        </div>
  
        <div class="doc-code-controls">
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-primary btn-sm" @click="previousStep" :disabled="currentStep == 0 || isComplete">
                Back
                </button>
                <button v-if="!branchEnd && (currentStep < steps.length - 1)" type="button" class="btn btn-primary btn-sm" @click="nextStep" :disabled="!selectedOptions[currentStep] || isComplete">
                Next
                </button>
                <button v-if="branchEnd || (currentStep === steps.length - 1)" type="button" class="btn btn-success btn-sm" @click="submitCode" :disabled="!selectedOptions[currentStep]">
                Complete
                </button>
            </div>
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
            steps: JSON.parse(JSON.stringify(this.initialSteps)), // deep clone, otherwise can't revert to initialSteps
            // root: "PRL",
            selectedOptions: Array(this.initialSteps.length+1).fill(""),
            currentStep: 0,
            isComplete: false,
            branchEnd: false ,
            defaultConnector: '-' 
        };
    },
    watch: {
        initialSteps: {
            handler(newSteps) {
                this.steps = JSON.parse(JSON.stringify(newSteps));
                this.resetBuilder();
            },
            deep: true
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

            // Reset all subsequent selections
            for (let i = stepIndex + 1; i < this.steps.length; i++) {
                this.selectedOptions[i] = "";
                this.steps[i].options = JSON.parse(JSON.stringify(this.initialSteps[i].options));
            }

            // Load next options dynamically
            if ((stepIndex < this.steps.length - 1) && selectedValue) {
                this.loadNextOptions(stepIndex, selectedValue);
            }
        },
        loadNextOptions(stepIndex) {
            var key = this.buildCode("_");
            if (stepIndex < this.steps.length - 1) {
                const nextOptions = this.steps[stepIndex + 1].options[key] || [];
                this.steps[stepIndex + 1].options = nextOptions;

                // Check if the next step has valid options
                this.branchEnd = nextOptions.length === 0;
            }
        },
        previousStep() {
            if (this.currentStep > 0) {
                this.selectedOptions[this.currentStep] = "";
                this.branchEnd = false;
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
            this.isComplete = true;
            const drawingCode = this.buildCode();
            this.$emit("codeComplete", drawingCode);
        },
        resetBuilder() {
            this.isComplete = false;
            this.branchEnd = false;
            this.selectedOptions.fill("");
            this.currentStep = 0;
            this.steps = JSON.parse(JSON.stringify(this.initialSteps));
            this.$emit("resetCode");
        },
        emitPartialCode() {
            const partialCode = this.buildCode();
            this.$emit("partialCodeUpdate", partialCode);
        },
        buildCode(connectorOverride) {
            // connectorOverride: undefined | string | array
            const opts = this.selectedOptions;

            const hasSelectedAfter = (i) => {
                for (let j = i + 1; j < opts.length; j++) {
                    if (opts[j]) return true;
                }
                return false;
            };

            const resolveConnector = (i) => {
                if (connectorOverride === undefined || connectorOverride === null) {
                    // prefer step-level connector, fall back to defaultConnector
                    const step = (this.initialSteps && this.initialSteps[i]) || (this.steps && this.steps[i]);
                    if (step && step.connectorAfter !== undefined) return step.connectorAfter;
                    return this.defaultConnector || '';
                }

                if (typeof connectorOverride === 'string') return connectorOverride;
                if (Array.isArray(connectorOverride)) return connectorOverride[i] || '';
                return '';
            };

            const parts = [];
            for (let i = 0; i < opts.length; i++) {
                const val = opts[i];
                if (val) {
                    parts.push(val);
                    if (hasSelectedAfter(i)) {
                        const conn = resolveConnector(i);
                        if (conn) parts.push(conn);
                    }
                }
            }

            return parts.join('');
        }
    },
};
</script>