<script setup lang="ts">
import { computed, ref } from 'vue'

type Stage = 'upload' | 'sheetSelection' | 'columnSelection' | 'headerForm' | 'result'

type SessionCreationResponse = {
  session_id: string
  sheet_names: string[]
}

type SheetNamesResponse = {
  req_payment_columns: string[]
  recv_payment_columns: string[]
}

type PdfHeader = {
  company_name: string
  rif: string
  doc_type: string
  doc_number: string
  sent_date: string
  process_date: string
}

const API_PREFIX = '/api/v1/receipts'

const stage = ref<Stage>('upload')
const selectedFile = ref<File | null>(null)
const sessionId = ref('')

const sheetNames = ref<string[]>([])
const reqPaymentSheet = ref('')
const recvPaymentSheet = ref('')
const reqPaymentIndex = ref<number>(0)
const recvPaymentIndex = ref<number>(0)

const reqColumns = ref<string[]>([])
const recvColumns = ref<string[]>([])
const reqColumn = ref('')
const recvColumn = ref('')

const pdfHeader = ref<PdfHeader>({
  company_name: '',
  rif: '',
  doc_type: '',
  doc_number: '',
  sent_date: '',
  process_date: '',
})

const uiError = ref('')
const loading = ref(false)
const generating = ref(false)
const generated = ref(false)
const downloading = ref(false)
const zipDownloaded = ref(false)

const stageIndex = computed(() => {
  if (stage.value === 'upload') return 1
  if (stage.value === 'sheetSelection') return 2
  if (stage.value === 'columnSelection') return 3
  if (stage.value === 'headerForm') return 4
  return 5
})

const canSubmitHeader = computed(() => {
  const values = Object.values(pdfHeader.value)
  return values.every((value) => value.trim().length > 0)
})

function handleFileChange(event: Event): void {
  const target = event.target as HTMLInputElement
  selectedFile.value = target.files?.[0] ?? null
}

async function extractError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string }
    if (payload.detail) {
      return payload.detail
    }
  } catch {
    return `Error ${response.status}: ${response.statusText}`
  }

  return `Error ${response.status}: ${response.statusText}`
}

async function uploadExcelFile(): Promise<void> {
  if (!selectedFile.value) {
    uiError.value = 'Selecciona un archivo Excel antes de continuar.'
    return
  }

  loading.value = true
  uiError.value = ''

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await fetch(`${API_PREFIX}/excel_file`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(await extractError(response))
    }

    const data = (await response.json()) as SessionCreationResponse

    sessionId.value = data.session_id
    sheetNames.value = data.sheet_names
    reqPaymentSheet.value = data.sheet_names[0] ?? ''
    recvPaymentSheet.value = data.sheet_names[0] ?? ''
    reqPaymentIndex.value = 0
    recvPaymentIndex.value = 0
    zipDownloaded.value = false

    stage.value = 'sheetSelection'
  } catch (error) {
    uiError.value = error instanceof Error ? error.message : 'No se pudo cargar el archivo.'
  } finally {
    loading.value = false
  }
}

async function submitSheetSelection(): Promise<void> {
  if (!reqPaymentSheet.value || !recvPaymentSheet.value) {
    uiError.value = 'Debes seleccionar ambas hojas.'
    return
  }

  if (reqPaymentIndex.value < 0 || recvPaymentIndex.value < 0) {
    uiError.value = 'El indice de encabezado no puede ser negativo.'
    return
  }

  loading.value = true
  uiError.value = ''

  try {
    const response = await fetch(`${API_PREFIX}/excel_sheets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId.value,
        req_payment_sheet: reqPaymentSheet.value,
        req_payment_index: reqPaymentIndex.value,
        recv_payment_sheet: recvPaymentSheet.value,
        recv_payment_index: recvPaymentIndex.value,
      }),
    })

    if (!response.ok) {
      throw new Error(await extractError(response))
    }

    const data = (await response.json()) as SheetNamesResponse

    reqColumns.value = data.req_payment_columns
    recvColumns.value = data.recv_payment_columns
    reqColumn.value = data.req_payment_columns[0] ?? ''
    recvColumn.value = data.recv_payment_columns[0] ?? ''

    stage.value = 'columnSelection'
  } catch (error) {
    uiError.value = error instanceof Error ? error.message : 'No se pudieron cargar las columnas.'
  } finally {
    loading.value = false
  }
}

async function submitColumns(): Promise<void> {
  if (!reqColumn.value || !recvColumn.value) {
    uiError.value = 'Debes seleccionar una columna para cada tipo de pago.'
    return
  }

  loading.value = true
  uiError.value = ''

  try {
    const query = new URLSearchParams({
      session_id: sessionId.value,
      req_column: reqColumn.value,
      recv_column: recvColumn.value,
    })

    const response = await fetch(`${API_PREFIX}/columns?${query.toString()}`, {
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error(await extractError(response))
    }

    stage.value = 'headerForm'
  } catch (error) {
    uiError.value =
      error instanceof Error ? error.message : 'No se pudieron registrar las columnas seleccionadas.'
  } finally {
    loading.value = false
  }
}

async function generateReceipts(): Promise<void> {
  if (!canSubmitHeader.value) {
    uiError.value = 'Completa todos los datos del encabezado del recibo.'
    return
  }

  uiError.value = ''
  stage.value = 'result'
  generating.value = true
  generated.value = false
  zipDownloaded.value = false

  try {
    const response = await fetch(`${API_PREFIX}/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId.value,
        pdf_header: pdfHeader.value,
      }),
    })

    if (!response.ok) {
      throw new Error(await extractError(response))
    }

    generated.value = true
  } catch (error) {
    uiError.value = error instanceof Error ? error.message : 'No se pudieron generar los recibos.'
    stage.value = 'headerForm'
  } finally {
    generating.value = false
  }
}

function getDownloadFileName(contentDisposition: string | null): string {
  if (!contentDisposition) {
    return 'recibos.zip'
  }

  const match = contentDisposition.match(/filename="?([^";]+)"?/i)
  return match?.[1] ?? 'recibos.zip'
}

async function downloadZip(): Promise<void> {
  if (zipDownloaded.value) {
    return
  }

  downloading.value = true
  uiError.value = ''

  try {
    const query = new URLSearchParams({ session_id: sessionId.value })

    const response = await fetch(`${API_PREFIX}/zip?${query.toString()}`)

    if (!response.ok) {
      throw new Error(await extractError(response))
    }

    const blob = await response.blob()
    const fileName = getDownloadFileName(response.headers.get('content-disposition'))

    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.href = url
    link.download = fileName
    document.body.append(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    zipDownloaded.value = true
  } catch (error) {
    uiError.value = error instanceof Error ? error.message : 'No se pudo descargar el archivo .zip.'
  } finally {
    downloading.value = false
  }
}

function resetFlow(): void {
  stage.value = 'upload'
  selectedFile.value = null
  sessionId.value = ''
  sheetNames.value = []
  reqPaymentSheet.value = ''
  recvPaymentSheet.value = ''
  reqPaymentIndex.value = 0
  recvPaymentIndex.value = 0
  reqColumns.value = []
  recvColumns.value = []
  reqColumn.value = ''
  recvColumn.value = ''
  pdfHeader.value = {
    company_name: '',
    rif: '',
    doc_type: '',
    doc_number: '',
    sent_date: '',
    process_date: '',
  }
  uiError.value = ''
  loading.value = false
  generating.value = false
  generated.value = false
  downloading.value = false
  zipDownloaded.value = false
}
</script>

<template>
  <main class="page-shell">
    <section class="hero">
      <p class="hero__tag">Payment Receipt Generator</p>
      <h1 class="hero__title">Generador de Recibos</h1>
      <p class="hero__subtitle">Sube un archivo Excel, configura la informacion y descarga todos los recibos en un solo .zip.</p>
      <p class="hero__progress">Paso {{ stageIndex }} de 5</p>
    </section>

    <section class="panel">
      <p v-if="uiError" class="error-banner">{{ uiError }}</p>

      <form v-if="stage === 'upload'" class="stack" @submit.prevent="uploadExcelFile">
        <h2 class="panel__title">1) Cargar archivo Excel</h2>
        <label class="field">
          <span>Archivo</span>
          <input type="file" accept=".xlsx,.xls" @change="handleFileChange" />
        </label>
        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? 'Subiendo...' : 'Continuar' }}
        </button>
      </form>

      <form v-else-if="stage === 'sheetSelection'" class="stack" @submit.prevent="submitSheetSelection">
        <h2 class="panel__title">2) Seleccion de hojas</h2>

        <div class="grid-two">
          <label class="field">
            <span>Pagos Solicitados</span>
            <select v-model="reqPaymentSheet">
              <option v-for="sheet in sheetNames" :key="`req-${sheet}`" :value="sheet">{{ sheet }}</option>
            </select>
          </label>

          <label class="field">
            <span>Pagos Recibidos</span>
            <select v-model="recvPaymentSheet">
              <option v-for="sheet in sheetNames" :key="`recv-${sheet}`" :value="sheet">{{ sheet }}</option>
            </select>
          </label>
        </div>

        <div class="grid-two">
          <label class="field">
            <span>Indice de Encabezado de Columnas</span>
            <input v-model.number="reqPaymentIndex" type="number" min="0" step="1" />
          </label>

          <label class="field">
            <span>Indice de Encabezado de Columnas</span>
            <input v-model.number="recvPaymentIndex" type="number" min="0" step="1" />
          </label>
        </div>

        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? 'Cargando columnas...' : 'Continuar' }}
        </button>
      </form>

      <form v-else-if="stage === 'columnSelection'" class="stack" @submit.prevent="submitColumns">
        <h2 class="panel__title">3) Seleccion de columnas</h2>

        <div class="grid-two">
          <label class="field">
            <span>Pagos Solicitados</span>
            <select v-model="reqColumn">
              <option v-for="column in reqColumns" :key="`req-col-${column}`" :value="column">{{ column }}</option>
            </select>
          </label>

          <label class="field">
            <span>Pagos Recibidos</span>
            <select v-model="recvColumn">
              <option v-for="column in recvColumns" :key="`recv-col-${column}`" :value="column">{{ column }}</option>
            </select>
          </label>
        </div>

        <button class="btn" type="submit" :disabled="loading">
          {{ loading ? 'Guardando seleccion...' : 'Continuar' }}
        </button>
      </form>

      <form v-else-if="stage === 'headerForm'" class="stack" @submit.prevent="generateReceipts">
        <h2 class="panel__title">4) Encabezado del recibo</h2>

        <div class="grid-two">
          <label class="field">
            <span>Company Name</span>
            <input v-model="pdfHeader.company_name" type="text" />
          </label>

          <label class="field">
            <span>RIF</span>
            <input v-model="pdfHeader.rif" type="text" />
          </label>

          <label class="field">
            <span>Doc Type</span>
            <input v-model="pdfHeader.doc_type" type="text" />
          </label>

          <label class="field">
            <span>Doc Number</span>
            <input v-model="pdfHeader.doc_number" type="text" />
          </label>

          <label class="field">
            <span>Sent Date</span>
            <input v-model="pdfHeader.sent_date" type="text" placeholder="YYYY-MM-DD" />
          </label>

          <label class="field">
            <span>Process Date</span>
            <input v-model="pdfHeader.process_date" type="text" placeholder="YYYY-MM-DD" />
          </label>
        </div>

        <button class="btn" type="submit" :disabled="generating || !canSubmitHeader">
          {{ generating ? 'Generando Recibos...' : 'Generar Recibos' }}
        </button>
      </form>

      <section v-else class="result">
        <h2 class="panel__title">5) Resultado</h2>

        <p v-if="generating" class="status">Generando Recibos...</p>

        <div v-else-if="generated" class="download-box">
          <span class="download-icon" aria-hidden="true">📄</span>
          <p>Recibos generados exitosamente.</p>
          <button class="btn" type="button" :disabled="downloading || zipDownloaded" @click="downloadZip">
            {{ downloading ? 'Descargando...' : zipDownloaded ? 'Zip downloaded' : 'Descargar' }}
          </button>
          <button class="btn btn--secondary" type="button" @click="resetFlow">Reiniciar Flujo</button>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.page-shell {
  width: min(920px, 100%);
  margin: 3rem auto;
  display: grid;
  gap: 1.5rem;
}

.hero {
  color: var(--ink-950);
}

.hero__tag {
  display: inline-flex;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.72rem;
  font-weight: 700;
  background: color-mix(in hsl, var(--teal-500) 18%, white);
  color: var(--teal-700);
}

.hero__title {
  margin-top: 0.9rem;
  font-size: clamp(1.9rem, 3vw, 2.8rem);
  line-height: 1.05;
}

.hero__subtitle {
  margin-top: 0.8rem;
  max-width: 62ch;
  color: var(--ink-700);
}

.hero__progress {
  margin-top: 0.8rem;
  font-size: 0.95rem;
  color: var(--ink-600);
}

.panel {
  padding: 1.3rem;
  border-radius: 1.1rem;
  border: 1px solid var(--ink-200);
  background: var(--surface);
  box-shadow: 0 10px 30px rgba(11, 28, 42, 0.08);
}

.panel__title {
  font-size: 1.18rem;
  margin-bottom: 0.8rem;
}

.stack {
  display: grid;
  gap: 1rem;
}

.grid-two {
  display: grid;
  gap: 0.9rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 0.4rem;
}

.field span {
  color: var(--ink-700);
  font-size: 0.88rem;
  font-weight: 600;
}

.field input,
.field select {
  border-radius: 0.7rem;
  border: 1px solid var(--ink-300);
  background: white;
  padding: 0.68rem 0.75rem;
  font: inherit;
  color: var(--ink-900);
}

.field input:focus,
.field select:focus {
  outline: none;
  border-color: var(--teal-500);
  box-shadow: 0 0 0 3px color-mix(in hsl, var(--teal-500) 25%, transparent);
}

.btn {
  border: 0;
  border-radius: 0.75rem;
  padding: 0.72rem 0.95rem;
  font: inherit;
  font-weight: 700;
  color: #effbff;
  background: linear-gradient(130deg, var(--teal-600), var(--cobalt-600));
  cursor: pointer;
  width: fit-content;
  transition: transform 140ms ease, box-shadow 140ms ease;
}

.btn:hover:enabled {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(20, 96, 120, 0.24);
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.64;
}

.btn--secondary {
  color: var(--ink-900);
  background: linear-gradient(180deg, #ffffff, #eff5fb);
  border: 1px solid var(--ink-250);
}

.error-banner {
  margin-bottom: 1rem;
  border-radius: 0.65rem;
  border: 1px solid #f8b6b3;
  padding: 0.62rem 0.75rem;
  color: #9b1c1c;
  background: #fff4f4;
}

.result {
  display: grid;
  gap: 1rem;
}

.status {
  font-size: 1.03rem;
  color: var(--ink-700);
}

.download-box {
  display: grid;
  place-items: center;
  gap: 0.8rem;
  padding: 1.3rem;
  border-radius: 0.95rem;
  border: 1px solid var(--ink-250);
  background: linear-gradient(160deg, #fff, #f8fffd);
}

.download-icon {
  font-size: 2.5rem;
}

@media (max-width: 760px) {
  .page-shell {
    margin: 1.2rem auto;
  }

  .panel {
    padding: 1rem;
  }

  .grid-two {
    grid-template-columns: 1fr;
  }

  .btn {
    width: 100%;
  }
}
</style>
