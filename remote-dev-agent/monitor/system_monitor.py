import logging
import psutil
import GPUtil

logger = logging.getLogger(__name__)

def get_system_metrics() -> dict:
    """
    Returns a dictionary of current system metrics.
    Gracefully handles missing sensors.
    """
    metrics = {
        "cpu_percent": 0.0,
        "ram_percent": 0.0,
        "ram_used_mb": 0.0,
        "ram_total_mb": 0.0,
        "battery_percent": None,
        "battery_plugged": None,
        "gpu_percent": 0.0,
        "gpu_memory_used": 0.0,
        "gpu_memory_total": 0.0,
        "temperature": None
    }
    
    try:
        metrics["cpu_percent"] = psutil.cpu_percent(interval=0.5)
    except Exception as e:
        logger.debug(f"Could not get CPU metrics: {e}")
    
    try:
        vm = psutil.virtual_memory()
        metrics["ram_percent"] = vm.percent
        metrics["ram_used_mb"] = vm.used / (1024 * 1024)
        metrics["ram_total_mb"] = vm.total / (1024 * 1024)
    except Exception as e:
        logger.debug(f"Could not get RAM metrics: {e}")
    
    # Battery info (if available)
    try:
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                metrics["battery_percent"] = battery.percent
                metrics["battery_plugged"] = battery.power_plugged
    except Exception as e:
        logger.debug(f"Could not get battery metrics: {e}")

    # GPU info
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]  # Take the first GPU
            metrics["gpu_percent"] = gpu.load * 100
            metrics["gpu_memory_used"] = gpu.memoryUsed
            metrics["gpu_memory_total"] = gpu.memoryTotal
            metrics["temperature"] = gpu.temperature
    except Exception as e:
        logger.debug(f"Could not get GPU metrics: {e}")
    
    return metrics

def format_system_status() -> str:
    """
    Returns a formatted string of system metrics for Telegram.
    """
    metrics = get_system_metrics()
    
    status_lines = [
        "🖥️ **SYSTEM STATUS**\n",
        f"CPU: {metrics['cpu_percent']:.1f}%",
        f"RAM: {metrics['ram_percent']:.1f}% ({metrics['ram_used_mb']:.0f}MB / {metrics['ram_total_mb']:.0f}MB)",
    ]
    
    if metrics['gpu_memory_total'] > 0:
        status_lines.append(
            f"GPU: {metrics['gpu_percent']:.1f}% ({metrics['gpu_memory_used']:.0f}MB/{metrics['gpu_memory_total']:.0f}MB)"
        )

    if metrics['temperature'] is not None:
        temp_status = "🟢"
        if metrics['temperature'] > 80:
            temp_status = "🔴"
        elif metrics['temperature'] > 70:
            temp_status = "🟡"
        status_lines.append(f"Temp: {temp_status} {metrics['temperature']:.1f}°C")
        
    if metrics['battery_percent'] is not None:
        plugged = "🔌" if metrics['battery_plugged'] else "🔋"
        status_lines.append(f"Battery: {metrics['battery_percent']:.0f}% {plugged}")
    
    return "\n".join(status_lines)

if __name__ == "__main__":
    print(format_system_status())
