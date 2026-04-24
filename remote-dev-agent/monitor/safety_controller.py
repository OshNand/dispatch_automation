import time
import logging
from .system_monitor import get_system_metrics
from config.settings import settings

logger = logging.getLogger(__name__)

class SafetyState:
    RUNNING = "RUNNING"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    PAUSED = "PAUSED"
    COOLDOWN = "COOLDOWN"
    RESUMING = "RESUMING"

class SafetyController:
    def __init__(self):
        self.state = SafetyState.RUNNING
        self.cooldown_end_time = 0

    def check_safety(self) -> str:
        """
        Checks current system metrics against thresholds.
        Returns the current state. If CRITICAL, transitions to COOLDOWN.
        """
        if self.state == SafetyState.COOLDOWN:
            if time.time() > self.cooldown_end_time:
                self.state = SafetyState.RESUMING
                logger.info("Cooldown finished. Resuming operations.")
                return self.state
            else:
                return self.state

        metrics = get_system_metrics()
        
        is_critical = False
        reasons = []

        if metrics['cpu_percent'] > settings.CPU_CRITICAL_PERCENT:
            is_critical = True
            reasons.append(f"CPU Critical: {metrics['cpu_percent']}%")
            
        if metrics['gpu_percent'] > settings.GPU_CRITICAL_PERCENT:
            is_critical = True
            reasons.append(f"GPU Critical: {metrics['gpu_percent']}%")
            
        if metrics['temperature'] is not None and metrics['temperature'] > settings.TEMP_CRITICAL_C:
            is_critical = True
            reasons.append(f"Temp Critical: {metrics['temperature']}°C")

        if is_critical:
            self.state = SafetyState.CRITICAL
            logger.warning(f"Safety CRITICAL. Reasons: {', '.join(reasons)}")
            self._trigger_cooldown()
        elif metrics['cpu_percent'] > 80.0 or metrics['gpu_percent'] > 80.0:
            self.state = SafetyState.WARNING
        else:
            if self.state in [SafetyState.WARNING, SafetyState.RESUMING]:
                self.state = SafetyState.RUNNING

        return self.state

    def _trigger_cooldown(self):
        self.state = SafetyState.COOLDOWN
        self.cooldown_end_time = time.time() + settings.COOLDOWN_SECONDS
        logger.info(f"Triggered COOLDOWN for {settings.COOLDOWN_SECONDS} seconds.")

    def enforce_safety(self, callback=None):
        """
        Blocks execution if the system is in COOLDOWN.
        Optionally takes a callback (e.g., to notify user via Telegram) when entering cooldown.
        """
        current_state = self.check_safety()
        
        if current_state == SafetyState.CRITICAL:
            if callback:
                callback("CRITICAL load detected. Pausing and entering COOLDOWN mode.")
        
        while self.state == SafetyState.COOLDOWN:
            time.sleep(10)  # Check every 10 seconds
            new_state = self.check_safety()
            if new_state == SafetyState.RESUMING:
                if callback:
                    callback("Cooldown complete. Resuming operations.")
                self.state = SafetyState.RUNNING
                break
                
safety_controller = SafetyController()
