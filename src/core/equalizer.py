"""
均衡器和音频处理模块（简化版）
提供基本的音频处理功能
"""

import numpy as np
from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum
import threading


class AudioEffect(Enum):
    """音频效果枚举"""
    NONE = "none"
    REVERB = "reverb"
    ECHO = "echo"


@dataclass
class EqualizerBand:
    """均衡器频段"""
    frequency: float  # 中心频率 (Hz)
    gain: float       # 增益 (dB)
    q_factor: float   # Q因子


class AudioEqualizer:
    """
    音频均衡器类（简化版）
    提供10频段参数均衡器功能
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.bands: List[EqualizerBand] = []
        self._init_default_bands()
        self._lock = threading.Lock()
    
    def _init_default_bands(self):
        """初始化默认均衡器频段"""
        frequencies = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        for freq in frequencies:
            band = EqualizerBand(frequency=freq, gain=0.0, q_factor=1.41)
            self.bands.append(band)
    
    def set_band_gain(self, band_index: int, gain: float):
        """设置指定频段的增益"""
        with self._lock:
            if 0 <= band_index < len(self.bands):
                gain = max(-12.0, min(12.0, gain))
                self.bands[band_index].gain = gain
    
    def get_band_gain(self, band_index: int) -> float:
        """获取指定频段的增益"""
        if 0 <= band_index < len(self.bands):
            return self.bands[band_index].gain
        return 0.0
    
    def reset(self):
        """重置所有频段"""
        with self._lock:
            for band in self.bands:
                band.gain = 0.0
                band.q_factor = 1.41
    
    def apply_preset(self, preset_name: str):
        """应用预设的均衡器设置"""
        presets = {
            "flat": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "rock": [5, 4, 3, 1, -1, 1, 3, 4, 5, 5],
            "pop": [-2, -1, 0, 2, 4, 4, 2, 0, -1, -2],
            "jazz": [4, 3, 1, 2, -2, -2, 0, 2, 3, 4],
            "classical": [5, 4, 3, 2, -1, -1, 0, 2, 3, 4],
            "bass_boost": [6, 5, 4, 3, 1, 0, 0, 0, 0, 0],
            "treble_boost": [0, 0, 0, 0, 0, 1, 3, 4, 5, 6],
            "vocal": [-2, -3, -3, 2, 5, 5, 4, 2, 0, -2],
            "dance": [5, 6, 4, 0, -2, -2, 0, 4, 5, 5],
            "electronic": [5, 4, 2, 0, -2, -1, 0, 3, 5, 5]
        }
        
        if preset_name in presets:
            gains = presets[preset_name]
            with self._lock:
                for i, gain in enumerate(gains):
                    if i < len(self.bands):
                        self.bands[i].gain = gain
    
    def process_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """处理音频数据（简化版：仅应用增益）"""
        with self._lock:
            if len(audio_data) == 0:
                return audio_data
            
            if audio_data.dtype != np.float64:
                audio_data = audio_data.astype(np.float64)
            
            processed_data = audio_data.copy()
            
            # 简化版：仅应用整体增益
            total_gain = sum(band.gain for band in self.bands) / len(self.bands)
            if total_gain != 0.0:
                gain_linear = 10 ** (total_gain / 20)
                processed_data *= gain_linear
            
            return processed_data


class AudioAnalyzer:
    """
    音频分析器（简化版）
    提供音频频谱分析和可视化数据
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.fft_size = 2048
        self.window = np.hanning(self.fft_size)
    
    def compute_spectrum(self, audio_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """计算音频频谱"""
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)))
        
        frame = audio_data[-self.fft_size:]
        windowed = frame * self.window
        spectrum = np.fft.rfft(windowed)
        magnitude = np.abs(spectrum)
        freqs = np.fft.rfftfreq(self.fft_size, 1 / self.sample_rate)
        
        return freqs, magnitude
    
    def compute_octave_bands(self, audio_data: np.ndarray, num_bands: int = 10) -> List[float]:
        """计算倍频程频段"""
        freqs, magnitude = self.compute_spectrum(audio_data)
        center_freqs = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        
        band_values = []
        for i, center_freq in enumerate(center_freqs[:num_bands]):
            if i == 0:
                low_freq = 1
            else:
                low_freq = center_freqs[i - 1] * 1.414
            
            if i == len(center_freqs) - 1:
                high_freq = self.sample_rate / 2
            else:
                high_freq = center_freq * 1.414
            
            freq_indices = np.where((freqs >= low_freq) & (freqs <= high_freq))[0]
            
            if len(freq_indices) > 0:
                band_magnitude = magnitude[freq_indices]
                rms = np.sqrt(np.mean(band_magnitude ** 2))
                band_values.append(rms)
            else:
                band_values.append(0.0)
        
        return band_values
    
    def compute_waveform(self, audio_data: np.ndarray, num_points: int = 100) -> np.ndarray:
        """计算波形数据（用于可视化）"""
        if len(audio_data) == 0:
            return np.zeros(num_points)
        
        segment_size = len(audio_data) // num_points
        if segment_size == 0:
            segment_size = 1
        
        waveform = []
        for i in range(0, len(audio_data), segment_size):
            segment = audio_data[i:i + segment_size]
            if len(segment) > 0:
                peak = np.max(np.abs(segment))
                waveform.append(peak)
        
        while len(waveform) < num_points:
            waveform.append(0.0)
        
        return np.array(waveform[:num_points])
    
    def compute_rms(self, audio_data: np.ndarray) -> float:
        """计算音频的RMS值"""
        if len(audio_data) == 0:
            return 0.0
        return np.sqrt(np.mean(audio_data ** 2))
    
    def compute_peak(self, audio_data: np.ndarray) -> float:
        """计算音频的峰值"""
        if len(audio_data) == 0:
            return 0.0
        return np.max(np.abs(audio_data))


class AudioEffectProcessor:
    """
    音频效果处理器（简化版）
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def normalize(self, audio_data: np.ndarray, target_level: float = -3.0) -> np.ndarray:
        """标准化音频"""
        if len(audio_data) == 0:
            return audio_data
        
        current_peak = np.max(np.abs(audio_data))
        if current_peak == 0:
            return audio_data
        
        target_peak = 10 ** (target_level / 20)
        gain = target_peak / current_peak
        
        return audio_data * gain