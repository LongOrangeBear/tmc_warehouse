"""Сервис для работы с веб-камерой."""
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, QThread, QMutex
from PySide6.QtGui import QImage

from client.src.config import get_config

logger = logging.getLogger(__name__)


class CameraWorker(QThread):
    """Поток для захвата видео с камеры."""
    frame_ready = Signal(QImage)
    error = Signal(str)

    def __init__(self, camera_index: int, resolution: tuple, fps: int):
        super().__init__()
        self.camera_index = camera_index
        self.resolution = resolution
        self.fps = fps
        self.running = False
        self.capture = None
        self.mutex = QMutex()

        # Для записи
        self.recording = False
        self.video_writer = None
        self.output_path = None
        
        # Для снапшотов
        self.last_frame = None
        self.last_frame_mutex = QMutex()

    def run(self):
        """Основной цикл захвата."""
        if self.camera_index == -1:
            logger.info("Starting CameraWorker in MOCK mode")
            self.capture = None
        else:
            # Выбор бэкенда в зависимости от ОС
            import platform
            system = platform.system()
            backend = cv2.CAP_ANY
            
            if system == "Windows":
                backend = cv2.CAP_DSHOW
            elif system == "Linux":
                backend = cv2.CAP_V4L2
                
            logger.info(f"Opening camera {self.camera_index} with backend {backend} (System: {system})")
            self.capture = cv2.VideoCapture(self.camera_index, backend)
            
            if not self.capture.isOpened():
                # Fallback to ANY if specific backend fails
                logger.warning(f"Failed to open with backend {backend}, trying CAP_ANY")
                self.capture = cv2.VideoCapture(self.camera_index, cv2.CAP_ANY)
                
            if not self.capture.isOpened():
                self.error.emit("Не удалось открыть камеру")
                return

            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)

        self.running = True

        while self.running:
            if self.camera_index == -1:
                # Mock frame generation
                frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                # Random noise background
                noise = np.random.randint(0, 256, (self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                frame = cv2.addWeighted(frame, 0.5, noise, 0.5, 0)
                
                # Add timestamp text
                cv2.putText(
                    frame, 
                    f"NO CAMERA FOUND (MOCK)", 
                    (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 0, 255), 
                    2
                )
                cv2.putText(
                    frame, 
                    f"{datetime.now().strftime('%H:%M:%S')}", 
                    (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 0), 
                    2
                )
                
                # Add recording indicator
                if self.recording:
                    cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            else:
                ret, frame = self.capture.read()
                if not ret:
                    continue

            # Записать кадр если идёт запись (protected by mutex)
            self.mutex.lock()
            try:
                if self.recording and self.video_writer:
                    self.video_writer.write(frame)
            finally:
                self.mutex.unlock()
                
            # Сохранить последний кадр для снапшотов
            self.last_frame_mutex.lock()
            self.last_frame = frame.copy()
            self.last_frame_mutex.unlock()

            # Конвертировать в QImage для отображения
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.frame_ready.emit(q_image.copy())

            # Ограничить FPS
            self.msleep(int(1000 / self.fps))

        # Очистка
        self.mutex.lock()
        try:
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
        finally:
            self.mutex.unlock()
            
        if self.capture:
            self.capture.release()
        logger.info("Camera worker stopped")

    def start_recording(self, output_path: Path):
        """Начать запись видео."""
        self.mutex.lock()
        config = get_config()
        codec = cv2.VideoWriter_fourcc(*config["camera"]["codec"])
        self.output_path = output_path
        self.video_writer = cv2.VideoWriter(
            str(output_path),
            codec,
            self.fps,
            self.resolution
        )
        self.recording = True
        self.mutex.unlock()
        logger.info(f"Started recording to {output_path}")

    def stop_recording(self) -> Optional[Path]:
        """Остановить запись и вернуть путь к файлу."""
        self.mutex.lock()
        self.recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        path = self.output_path
        self.output_path = None
        self.mutex.unlock()
        logger.info(f"Stopped recording: {path}")
        return path

    def stop(self):
        """Остановить захват."""
        self.running = False
        self.wait()

    def get_last_frame_jpeg(self) -> Optional[bytes]:
        """Получить последний кадр в формате JPEG."""
        self.last_frame_mutex.lock()
        try:
            if self.last_frame is None:
                return None
            _, buffer = cv2.imencode('.jpg', self.last_frame)
            return buffer.tobytes()
        finally:
            self.last_frame_mutex.unlock()


class CameraService(QObject):
    """Сервис управления камерой."""
    frame_ready = Signal(QImage)
    recording_started = Signal()
    recording_stopped = Signal(str)  # путь к файлу
    recording_size_updated = Signal(int)  # размер файла в байтах
    recording_limit_exceeded = Signal(str)  # причина остановки
    error = Signal(str)

    def __init__(self):
        super().__init__()
        config = get_config()
        self.camera_index = config["camera"]["default_index"]
        self.resolution = tuple(config["camera"]["resolution"])
        self.fps = config["camera"]["fps"]
        self.container = config["camera"]["container"]
        self.max_duration_seconds = config["camera"].get("max_duration_seconds", 300)
        self.max_size_mb = config["camera"].get("max_size_mb", 100)
        
        self.worker: Optional[CameraWorker] = None
        self.current_video_path: Optional[Path] = None
        self.recording_start_time: Optional[datetime] = None
        
        # Таймер для обновления размера видео
        from PySide6.QtCore import QTimer
        self.size_update_timer = QTimer(self)
        self.size_update_timer.timeout.connect(self._update_video_size)
        self.size_update_timer.setInterval(1000)  # Каждую секунду

    @staticmethod
    def list_available_cameras(max_check: int = 5) -> List[int]:
        """Получить список доступных камер."""
        available = []
        import platform
        system = platform.system()
        backend = cv2.CAP_ANY
        
        if system == "Windows":
            backend = cv2.CAP_DSHOW
        elif system == "Linux":
            backend = cv2.CAP_V4L2
            
        for i in range(max_check):
            cap = cv2.VideoCapture(i, backend)
            if cap.isOpened():
                available.append(i)
                cap.release()
            else:
                # Try fallback
                cap = cv2.VideoCapture(i, cv2.CAP_ANY)
                if cap.isOpened():
                    available.append(i)
                    cap.release()
                    
        return available

    def start_preview(self, camera_index: Optional[int] = None):
        """Запустить превью с камеры."""
        if self.worker and self.worker.isRunning():
            self.stop_preview()

        index = camera_index if camera_index is not None else self.camera_index
        
        # Check if camera is available, otherwise use mock
        if index != -1:
            cap = cv2.VideoCapture(index)
            is_opened = cap.isOpened()
            cap.release()
            
            if not is_opened:
                logger.warning(f"Camera {index} not found. Switching to MOCK mode.")
                index = -1
        
        self.worker = CameraWorker(index, self.resolution, self.fps)
        self.worker.frame_ready.connect(self.frame_ready.emit)
        self.worker.error.connect(self.error.emit)
        self.worker.start()

    def stop_preview(self):
        """Остановить превью."""
        if self.worker:
            self.worker.stop()
            self.worker = None

    def start_recording(self, output_dir: Path) -> Path:
        """Начать запись видео."""
        if not self.worker:
            raise RuntimeError("Camera not started")

        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"video_{datetime.now().strftime('%H%M%S')}.{self.container}"
        output_path = output_dir / filename

        self.worker.start_recording(output_path)
        self.current_video_path = output_path
        self.recording_start_time = datetime.now()
        self.size_update_timer.start()
        self.recording_started.emit()
        return output_path

    def stop_recording(self) -> Optional[Path]:
        """Остановить запись и вернуть путь."""
        if not self.worker:
            return None

        self.size_update_timer.stop()
        path = self.worker.stop_recording()
        self.current_video_path = None
        self.recording_start_time = None
        if path:
            self.recording_stopped.emit(str(path))
        return path

    def is_recording(self) -> bool:
        """Проверить идёт ли запись."""
        return self.worker is not None and self.worker.recording
    
    def _update_video_size(self):
        """Обновить размер видеофайла и отправить сигнал."""
        if self.current_video_path and self.current_video_path.exists():
            try:
                size = self.current_video_path.stat().st_size
                self.recording_size_updated.emit(size)
                
                # Проверка лимитов
                if self.recording_start_time:
                    elapsed = (datetime.now() - self.recording_start_time).total_seconds()
                    size_mb = size / (1024 * 1024)
                    
                    if elapsed >= self.max_duration_seconds:
                        logger.info(f"Recording stopped: duration limit exceeded ({elapsed:.1f}s >= {self.max_duration_seconds}s)")
                        self.recording_limit_exceeded.emit(
                            f"⏱ Запись остановлена\n\nПревышен лимит времени\n({int(elapsed)}с / {self.max_duration_seconds}с)"
                        )
                        self.stop_recording()
                    elif size_mb >= self.max_size_mb:
                        logger.info(f"Recording stopped: size limit exceeded ({size_mb:.1f}MB >= {self.max_size_mb}MB)")
                        self.recording_limit_exceeded.emit(
                            f"💾 Запись остановлена\n\nПревышен лимит размера\n({size_mb:.1f}MB / {self.max_size_mb}MB)"
                        )
                        self.stop_recording()
            except Exception as e:
                logger.warning(f"Failed to get video size: {e}")

    def take_snapshot(self) -> Optional[bytes]:
        """Сделать снимок текущего кадра."""
        if not self.worker:
            return None
            
        # We need to get the current frame from the worker
        # Since worker emits signals, we can't easily "pull" the frame synchronously without storing it
        # But for a snapshot, we can just capture one frame from the device if we are in the main thread, 
        # OR better: let the worker store the last frame and access it safely.
        
        # However, accessing worker state from main thread requires care.
        # Let's add a request_snapshot method to worker or just grab a frame directly if possible?
        # Direct capture is bad if camera is busy.
        
        # Simplest approach: The worker is already running. We can add a 'last_frame' property to worker protected by mutex.
        return self.worker.get_last_frame_jpeg()
