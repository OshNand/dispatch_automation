import psutil
import GPUtil

def get_system_metrics() -> dict:
    """
    Returns a dictionary of current system metrics.
    """
    metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1.0),
        "ram_percent": psutil.virtual_memory().percent,
        "battery_percent": None,
        "battery_plugged": None,
        "gpu_percent": 0.0,
        "gpu_memory_used": 0.0,
        "gpu_memory_total": 0.0,
        "temperature": None
    }
    
    # Battery info (if available)
    if hasattr(psutil, "sensors_battery"):
        battery = psutil.sensors_battery()
        if battery:
            metrics["battery_percent"] = battery.percent
            metrics["battery_plugged"] = battery.power_plugged

    # GPU info
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]  # Take the first GPU
            metrics["gpu_percent"] = gpu.load * 100
            metrics["gpu_memory_used"] = gpu.memoryUsed
            metrics["gpu_memory_total"] = gpu.memoryTotal
            metrics["temperature"] = gpu.temperature
    except Exception:
        pass
    
    return metrics

def format_system_status() -> str:
    """
    Returns a formatted string of system metrics for Telegram.
    """
    metrics = get_system_metrics()
    
    status_lines = [
        f"🖥️ CPU: {metrics['cpu_percent']}%",
        f"🧠 RAM: {metrics['ram_percent']}%"
    ]
    
    if metrics['gpu_memory_total'] > 0:
        status_lines.append(
            f"🎮 GPU: {metrics['gpu_percent']:.1f}% ({metrics['gpu_memory_used']:.0f}MB/{metrics['gpu_memory_total']:.0f}MB)"
        )
    else:
        status_lines.append("🎮 GPU: Not Available")

    if metrics['temperature'] is not None:
        status_lines.append(f"🌡️ Temp: {metrics['temperature']}°C")
    else:
        status_lines.append("🌡️ Temp: Not Available")
        
    if metrics['battery_percent'] is not None:
        plugged = "🔌" if metrics['battery_plugged'] else "🔋"
        status_lines.append(f"🔋 Battery: {metrics['battery_percent']}% {plugged}")
    
    return "\n".join(status_lines)

if __name__ == "__main__":
    print(format_system_status())
