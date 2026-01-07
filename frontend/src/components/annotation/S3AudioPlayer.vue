<template>
  <v-card 
    class="s3-audio-player" 
    :class="{ 'dark-theme': isDark }"
    elevation="2"
  >
    <v-card-text class="pa-3">
      <!-- Waveform Visualization -->
      <div 
        ref="waveformContainer" 
        class="waveform-container"
        :class="{ 'loading': isLoading }"
      >
        <div v-if="isLoading" class="loading-overlay">
          <v-progress-circular indeterminate color="primary" size="32" />
          <span class="ml-2 text-body-2">འཇུག་བཞིན་པ། / Loading...</span>
        </div>
        <div v-if="error" class="error-overlay">
          <v-icon color="error" size="32">mdi-alert-circle</v-icon>
          <span class="ml-2 text-body-2 error--text">{{ error }}</span>
        </div>
      </div>
      
      <!-- Controls -->
      <div class="controls-row mt-3">
        <div class="d-flex align-center">
          <!-- Play/Pause Button -->
          <v-btn
            :icon="true"
            :color="isPlaying ? 'primary' : 'default'"
            variant="tonal"
            size="large"
            @click="togglePlay"
            :disabled="isLoading || !!error"
          >
            <v-icon>{{ isPlaying ? 'mdi-pause' : 'mdi-play' }}</v-icon>
          </v-btn>
          
          <!-- Stop Button -->
          <v-btn
            :icon="true"
            variant="text"
            size="small"
            class="ml-1"
            @click="stop"
            :disabled="isLoading || !!error"
          >
            <v-icon>mdi-stop</v-icon>
          </v-btn>
          
          <!-- Skip Backward -->
          <v-btn
            :icon="true"
            variant="text"
            size="small"
            class="ml-1"
            @click="skipBackward"
            :disabled="isLoading || !!error"
          >
            <v-icon>mdi-rewind-5</v-icon>
          </v-btn>
          
          <!-- Skip Forward -->
          <v-btn
            :icon="true"
            variant="text"
            size="small"
            @click="skipForward"
            :disabled="isLoading || !!error"
          >
            <v-icon>mdi-fast-forward-5</v-icon>
          </v-btn>
          
          <!-- Loop Toggle -->
          <v-btn
            :icon="true"
            variant="text"
            size="small"
            class="ml-2"
            :color="isLooping ? 'primary' : 'default'"
            @click="toggleLoop"
            :disabled="isLoading || !!error"
          >
            <v-icon>{{ isLooping ? 'mdi-repeat' : 'mdi-repeat-off' }}</v-icon>
          </v-btn>
          
          <!-- Playback Speed -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                variant="text"
                size="small"
                class="ml-1"
                v-bind="props"
                :disabled="isLoading || !!error"
              >
                {{ playbackRate }}x
              </v-btn>
            </template>
            <v-list density="compact">
              <v-list-item 
                v-for="rate in playbackRates" 
                :key="rate"
                @click="setPlaybackRate(rate)"
                :active="playbackRate === rate"
              >
                <v-list-item-title>{{ rate }}x</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
        
        <!-- Time Display -->
        <div class="time-display ml-auto">
          <span class="current-time">{{ formatTime(currentTime) }}</span>
          <span class="separator"> / </span>
          <span class="duration">{{ formatTime(duration) }}</span>
        </div>
      </div>
      
      <!-- Volume Control -->
      <div class="volume-row mt-2 d-flex align-center">
        <v-btn
          :icon="true"
          variant="text"
          size="small"
          @click="toggleMute"
        >
          <v-icon>{{ volumeIcon }}</v-icon>
        </v-btn>
        <v-slider
          v-model="volume"
          min="0"
          max="1"
          step="0.01"
          hide-details
          color="primary"
          class="volume-slider ml-2"
          @update:model-value="setVolume"
        />
      </div>
      
      <!-- Auto-Loop Status -->
      <div v-if="autoLoop" class="auto-loop-indicator mt-2">
        <v-chip size="small" color="primary" variant="tonal">
          <v-icon start size="small">mdi-repeat</v-icon>
          རང་འགུལ་བསྐྱར་ཉན། / Auto-Loop Enabled
        </v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTheme } from 'vuetify'

const props = defineProps({
  audioUrl: {
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
  }
})

const emit = defineEmits(['play', 'pause', 'ended', 'error', 'timeupdate'])

const theme = useTheme()
const isDark = computed(() => theme.global.current.value.dark)

// Refs
const waveformContainer = ref(null)
const wavesurfer = ref(null)

// State
const isLoading = ref(true)
const isPlaying = ref(false)
const isLooping = ref(props.autoLoop)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)
const isMuted = ref(false)
const playbackRate = ref(1)
const error = ref(null)

const playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2]

// Computed
const volumeIcon = computed(() => {
  if (isMuted.value || volume.value === 0) return 'mdi-volume-off'
  if (volume.value < 0.3) return 'mdi-volume-low'
  if (volume.value < 0.7) return 'mdi-volume-medium'
  return 'mdi-volume-high'
})

// Methods
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const initWaveSurfer = async () => {
  if (!props.audioUrl) {
    error.value = 'No audio URL provided'
    isLoading.value = false
    return
  }
  
  try {
    // Dynamic import WaveSurfer
    const WaveSurfer = (await import('wavesurfer.js')).default
    
    wavesurfer.value = WaveSurfer.create({
      container: waveformContainer.value,
      waveColor: isDark.value ? '#6B7280' : '#9CA3AF',
      progressColor: isDark.value ? '#C5A572' : '#A88B4E',
      cursorColor: '#C5A572',
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      responsive: true,
      height: 64,
      normalize: true,
      backend: 'MediaElement', // Better for streaming S3 audio
    })
    
    // Events
    wavesurfer.value.on('ready', () => {
      isLoading.value = false
      duration.value = wavesurfer.value.getDuration()
      wavesurfer.value.setVolume(volume.value)
      
      if (props.autoPlay) {
        wavesurfer.value.play()
      }
    })
    
    wavesurfer.value.on('play', () => {
      isPlaying.value = true
      emit('play')
    })
    
    wavesurfer.value.on('pause', () => {
      isPlaying.value = false
      emit('pause')
    })
    
    wavesurfer.value.on('audioprocess', (time) => {
      currentTime.value = time
      emit('timeupdate', time)
    })
    
    wavesurfer.value.on('finish', () => {
      emit('ended')
      if (isLooping.value) {
        wavesurfer.value.seekTo(0)
        wavesurfer.value.play()
      }
    })
    
    wavesurfer.value.on('error', (e) => {
      console.error('WaveSurfer error:', e)
      error.value = 'Failed to load audio'
      isLoading.value = false
      emit('error', e)
    })
    
    // Load audio
    wavesurfer.value.load(props.audioUrl)
    
  } catch (e) {
    console.error('Failed to initialize WaveSurfer:', e)
    // Fallback to native audio element
    initNativeAudio()
  }
}

const initNativeAudio = () => {
  // Fallback: Create a simple audio element
  const audio = new Audio(props.audioUrl)
  
  audio.addEventListener('loadedmetadata', () => {
    isLoading.value = false
    duration.value = audio.duration
    if (props.autoPlay) audio.play()
  })
  
  audio.addEventListener('play', () => {
    isPlaying.value = true
    emit('play')
  })
  
  audio.addEventListener('pause', () => {
    isPlaying.value = false
    emit('pause')
  })
  
  audio.addEventListener('timeupdate', () => {
    currentTime.value = audio.currentTime
    emit('timeupdate', audio.currentTime)
  })
  
  audio.addEventListener('ended', () => {
    emit('ended')
    if (isLooping.value) {
      audio.currentTime = 0
      audio.play()
    }
  })
  
  audio.addEventListener('error', (e) => {
    error.value = 'Failed to load audio'
    isLoading.value = false
    emit('error', e)
  })
  
  wavesurfer.value = {
    play: () => audio.play(),
    pause: () => audio.pause(),
    stop: () => { audio.pause(); audio.currentTime = 0 },
    seekTo: (ratio) => { audio.currentTime = audio.duration * ratio },
    skip: (seconds) => { audio.currentTime = Math.max(0, Math.min(audio.duration, audio.currentTime + seconds)) },
    setVolume: (v) => { audio.volume = v },
    setPlaybackRate: (r) => { audio.playbackRate = r },
    getDuration: () => audio.duration,
    getCurrentTime: () => audio.currentTime,
    isPlaying: () => !audio.paused,
    destroy: () => { audio.pause(); audio.src = '' }
  }
}

const togglePlay = () => {
  if (!wavesurfer.value) return
  
  if (isPlaying.value) {
    wavesurfer.value.pause()
  } else {
    wavesurfer.value.play()
  }
}

const stop = () => {
  if (!wavesurfer.value) return
  if (wavesurfer.value.stop) {
    wavesurfer.value.stop()
  } else {
    wavesurfer.value.pause()
    wavesurfer.value.seekTo(0)
  }
  isPlaying.value = false
}

const skipBackward = () => {
  if (!wavesurfer.value) return
  if (wavesurfer.value.skip) {
    wavesurfer.value.skip(-5)
  } else {
    const newTime = Math.max(0, currentTime.value - 5)
    wavesurfer.value.seekTo(newTime / duration.value)
  }
}

const skipForward = () => {
  if (!wavesurfer.value) return
  if (wavesurfer.value.skip) {
    wavesurfer.value.skip(5)
  } else {
    const newTime = Math.min(duration.value, currentTime.value + 5)
    wavesurfer.value.seekTo(newTime / duration.value)
  }
}

const toggleLoop = () => {
  isLooping.value = !isLooping.value
}

const toggleMute = () => {
  isMuted.value = !isMuted.value
  if (wavesurfer.value) {
    wavesurfer.value.setVolume(isMuted.value ? 0 : volume.value)
  }
}

const setVolume = (v) => {
  if (wavesurfer.value) {
    wavesurfer.value.setVolume(v)
  }
  if (v > 0) isMuted.value = false
}

const setPlaybackRate = (rate) => {
  playbackRate.value = rate
  if (wavesurfer.value && wavesurfer.value.setPlaybackRate) {
    wavesurfer.value.setPlaybackRate(rate)
  }
}

// Watch for URL changes
watch(() => props.audioUrl, (newUrl) => {
  if (newUrl && wavesurfer.value) {
    isLoading.value = true
    error.value = null
    if (wavesurfer.value.load) {
      wavesurfer.value.load(newUrl)
    }
  }
})

// Lifecycle
onMounted(() => {
  initWaveSurfer()
})

onUnmounted(() => {
  if (wavesurfer.value && wavesurfer.value.destroy) {
    wavesurfer.value.destroy()
  }
})
</script>

<style scoped>
.s3-audio-player {
  border-radius: 12px;
  background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%);
}

.s3-audio-player.dark-theme {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.waveform-container {
  height: 64px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.dark-theme .waveform-container {
  background: rgba(255, 255, 255, 0.05);
}

.waveform-container.loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: inherit;
}

.controls-row {
  display: flex;
  align-items: center;
}

.time-display {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.875rem;
  color: var(--v-theme-on-surface);
  opacity: 0.8;
}

.current-time {
  font-weight: 600;
}

.separator {
  opacity: 0.5;
  margin: 0 2px;
}

.volume-slider {
  max-width: 120px;
}

.auto-loop-indicator {
  text-align: center;
}
</style>

