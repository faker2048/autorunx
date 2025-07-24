"""日志管理系统."""

import os
import time
import logging
import gzip
from pathlib import Path
from typing import Optional, List, Dict, Any
from .config import ConfigManager


class LogManager:
    """日志管理器."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """设置应用程序日志."""
        # 创建日志目录
        log_dir = Path(self.config_manager.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置主日志
        log_file = log_dir / "autostartx.log"
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, self.config_manager.config.log_level))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)  # 只在控制台显示警告和错误
        
        # 配置根日志器
        root_logger = logging.getLogger('autostartx')
        root_logger.setLevel(getattr(logging, self.config_manager.config.log_level))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # 避免重复添加处理器
        root_logger.propagate = False
    
    def get_service_log_path(self, service_id: str) -> str:
        """获取服务日志路径."""
        return self.config_manager.get_service_log_path(service_id)
    
    def read_service_logs(self, service_id: str, lines: int = 100, 
                         since: Optional[float] = None) -> List[str]:
        """读取服务日志."""
        log_path = self.get_service_log_path(service_id)
        
        if not os.path.exists(log_path):
            return []
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # 如果指定了时间过滤
            if since:
                filtered_lines = []
                for line in all_lines:
                    # 尝试解析时间戳（这是一个简化版本）
                    if self._line_is_after_time(line, since):
                        filtered_lines.append(line)
                all_lines = filtered_lines
            
            # 返回最后N行
            return all_lines[-lines:] if lines > 0 else all_lines
            
        except Exception as e:
            logging.getLogger('autostartx').error(f"读取服务日志失败: {e}")
            return []
    
    def clear_service_logs(self, service_id: str) -> bool:
        """清空服务日志."""
        log_path = self.get_service_log_path(service_id)
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("")
            logging.getLogger('autostartx').info(f"已清空服务 {service_id} 的日志")
            return True
        except Exception as e:
            logging.getLogger('autostartx').error(f"清空服务日志失败: {e}")
            return False
    
    def rotate_service_logs(self, service_id: str) -> bool:
        """轮转服务日志."""
        log_path = self.get_service_log_path(service_id)
        
        if not os.path.exists(log_path):
            return True
        
        try:
            # 检查文件大小
            file_size = os.path.getsize(log_path)
            max_size = self._parse_size(self.config_manager.config.max_log_size)
            
            if file_size < max_size:
                return True
            
            # 执行轮转
            timestamp = int(time.time())
            rotated_path = f"{log_path}.{timestamp}"
            
            # 重命名当前日志文件
            os.rename(log_path, rotated_path)
            
            # 压缩旧日志
            self._compress_log_file(rotated_path)
            
            # 创建新的空日志文件
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"=== 日志轮转: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            
            logging.getLogger('autostartx').info(f"已轮转服务 {service_id} 的日志")
            return True
            
        except Exception as e:
            logging.getLogger('autostartx').error(f"轮转日志失败: {e}")
            return False
    
    def cleanup_old_logs(self) -> None:
        """清理过期日志."""
        log_dir = Path(self.config_manager.config.log_dir)
        if not log_dir.exists():
            return
        
        retention_days = self.config_manager.config.log_retention_days
        cutoff_time = time.time() - (retention_days * 24 * 3600)
        
        try:
            for log_file in log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logging.getLogger('autostartx').info(f"已删除过期日志: {log_file}")
            
            # 清理压缩日志
            for gz_file in log_dir.glob("*.gz"):
                if gz_file.stat().st_mtime < cutoff_time:
                    gz_file.unlink()
                    logging.getLogger('autostartx').info(f"已删除过期压缩日志: {gz_file}")
                    
        except Exception as e:
            logging.getLogger('autostartx').error(f"清理过期日志失败: {e}")
    
    def get_log_stats(self, service_id: str) -> Dict[str, Any]:
        """获取日志统计信息."""
        log_path = self.get_service_log_path(service_id)
        
        if not os.path.exists(log_path):
            return {
                "exists": False,
                "size": 0,
                "lines": 0,
                "last_modified": None,
            }
        
        try:
            stat = os.stat(log_path)
            
            # 统计行数
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f)
            
            return {
                "exists": True,
                "size": stat.st_size,
                "size_mb": stat.st_size / 1024 / 1024,
                "lines": lines,
                "last_modified": stat.st_mtime,
                "last_modified_str": time.strftime('%Y-%m-%d %H:%M:%S', 
                                                 time.localtime(stat.st_mtime)),
            }
            
        except Exception as e:
            logging.getLogger('autostartx').error(f"获取日志统计失败: {e}")
            return {"exists": False, "error": str(e)}
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数."""
        size_str = size_str.upper()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # 假设是字节
            return int(size_str)
    
    def _compress_log_file(self, file_path: str) -> None:
        """压缩日志文件."""
        try:
            compressed_path = f"{file_path}.gz"
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            # 删除原文件
            os.remove(file_path)
            
        except Exception as e:
            logging.getLogger('autostartx').error(f"压缩日志文件失败: {e}")
    
    def _line_is_after_time(self, line: str, since_time: float) -> bool:
        """检查日志行是否在指定时间之后."""
        # 这是一个简化版本，实际应该解析日志时间戳
        # 这里假设日志行不包含时间戳，或者使用文件修改时间
        return True


class ServiceLogRotator:
    """服务日志轮转器."""
    
    def __init__(self, log_manager: LogManager):
        self.log_manager = log_manager
    
    def rotate_if_needed(self, service_id: str) -> bool:
        """如果需要则轮转日志."""
        stats = self.log_manager.get_log_stats(service_id)
        
        if not stats.get("exists"):
            return True
        
        max_size = self.log_manager._parse_size(
            self.log_manager.config_manager.config.max_log_size
        )
        
        if stats["size"] >= max_size:
            return self.log_manager.rotate_service_logs(service_id)
        
        return True
    
    def rotate_all_services(self, service_ids: List[str]) -> Dict[str, bool]:
        """轮转所有服务的日志."""
        results = {}
        
        for service_id in service_ids:
            results[service_id] = self.rotate_if_needed(service_id)
        
        return results