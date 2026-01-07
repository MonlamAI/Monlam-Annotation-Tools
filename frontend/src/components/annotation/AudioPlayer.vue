<template>
  <div class="audio-player-container">
    <v-card class="pa-4">
      <div class="d-flex align-center">
        <!-- Play/Pause Button -->
        <v-btn
          :icon="isPlaying ? 'mdi-pause' : 'mdi-play'"
          :color="isPlaying ? 'warning' : 'primary'"
          size="large"
          @click="togglePlay"
        />
        
        <!-- Progress Bar -->
        <div class="flex-grow-1 mx-4">
          <v-slider
            v-model="currentTime"
            :max="duration"
            :step="0.1"
            hide-details
            color="primary"
            track-color="grey-lighten-2"
            @update:modelValue="seek"
          >
            <template #prepend>
              <span class="text-caption">{{ formatTime(currentTime) }}</span>
            </template>
            <template #append>
              <span class="text-caption">{{ formatTime(duration) }}</span>
            </template>
          </v-slider>
        </div>
        
        <!-- Volume -->
        <v-menu>
          <template #activator="{ props }">
            <v-btn
              :icon="volumeIcon"
              variant="text"
              v-bind="props"
            />
          </template>
          <v-card class="pa-2" width="150">
            <v-slider
              v-model="volume"
              :min="0"
              :max="1"
              :step="0.1"
              hide-details
              @update:modelValue="updateVolume"
            />
          </v-card>
        </v-menu>
        
        <!-- Loop indicator (auto-enabled for STT) -->
        <v-chip v-if="autoLoop" size="small" color="primary" class="ml-2">
          <v-icon start size="small">mdi-repeat</v-icon>
          Loop
        </v-chip>
      </div>
      
      <!-- Waveform visualization (optional) -->
      <div v-if="showWaveform" class="waveform-container mt-4">
        <canvas ref="waveformCanvas" height="60"></canvas>
      </div>
    </v-card>
    
    <!-- Hidden audio element -->
    <audio
      ref="audioRef"
      :src="src"
      :loop="autoLoop"
      preload="metadata"
      @loadedmetadata="onLoadedMetadata"
      @timeupdate="onTimeUpdate"
      @ended="onEnded"
      @play="onPlay"
      @pause="onPause"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  autoPlay: {
    type: Boolean,
    default: true
  },
  autoLoop: {
    type: Boolean,
    default: true
  },
  showWaveform: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['play', 'pause', 'ended', 'timeupdate'])

// Refs
const audioRef = ref(null)
const waveformCanvas = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1)

// Computed
const volumeIcon = computed(() => {
  if (volume.value === 0) return 'mdi-volume-mute'
  if (volume.value < 0.5) return 'mdi-volume-low'
  return 'mdi-volume-high'
})

// Methods
function togglePlay() {
  if (!audioRef.value) return
  
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play().catch(handleAutoPlayBlocked)
  }
}

function seek(time) {
  if (audioRef.value) {
    audioRef.value.currentTime = time
  }
}

function updateVolume(vol) {
  if (audioRef.value) {
    audioRef.value.volume = vol
  }
}

function formatTime(seconds) {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function handleAutoPlayBlocked(error) {
  console.log('Autoplay blocked, waiting for user interaction')
  // Add click listener to play on first interaction
  const playOnClick = () => {
    if (audioRef.value) {
      audioRef.value.play().catch(() => {})
    }
    document.removeEventListener('click', playOnClick)
  }
  document.addEventListener('click', playOnClick, { once: true })
}

// Event handlers
function onLoadedMetadata() {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
    
    // Auto-play if enabled
    if (props.autoPlay) {
      audioRef.value.play().catch(handleAutoPlayBlocked)
    }
  }
}

function onTimeUpdate() {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
    emit('timeupdate', currentTime.value)
  }
}

function onEnded() {
  if (!props.autoLoop) {
    isPlaying.value = false
  }
  emit('ended')
}

function onPlay() {
  isPlaying.value = true
  emit('play')
}

function onPause() {
  isPlaying.value = false
  emit('pause')
}

// Watch for src changes
watch(() => props.src, (newSrc) => {
  if (newSrc && audioRef.value) {
    audioRef.value.load()
    currentTime.value = 0
    if (props.autoPlay) {
      audioRef.value.play().catch(handleAutoPlayBlocked)
    }
  }
})

// Lifecycle
onMounted(() => {
  if (audioRef.value) {
    audioRef.value.volume = volume.value
  }
})

onBeforeUnmount(() => {
  if (audioRef.value) {
    audioRef.value.pause()
  }
})
</script>

<style scoped>
.audio-player-container {
  width: 100%;
}

.waveform-container {
  width: 100%;
  background: #f5f5f5;
  border-radius: 4px;
}

.waveform-container canvas {
  width: 100%;
}
</style>

